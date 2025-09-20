"""
Enterprise features for Docx2Shelf.

This module provides enterprise-grade functionality including:
- Batch processing and automation
- Configuration management
- User management and permissions
- Reporting and analytics
- API and webhook integration
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

try:
    import fastapi
    import uvicorn
    from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
    from fastapi.security import HTTPBasic, HTTPBasicCredentials
except ImportError:
    fastapi = None
    FastAPI = None
    HTTPException = None
    Depends = None
    BackgroundTasks = None
    HTTPBasic = None
    HTTPBasicCredentials = None
    uvicorn = None

try:
    import requests
except ImportError:
    requests = None


@dataclass
class BatchJob:
    """Represents a batch conversion job."""
    id: str
    name: str
    input_pattern: str
    output_directory: str
    config: Dict[str, Any]
    processing_mode: str = "files"  # "files" or "books" (subfolders as books)
    status: str = "pending"  # pending, running, completed, failed, cancelled
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0
    total_items: int = 0  # files or books depending on mode
    processed_items: int = 0
    failed_items: int = 0
    total_files: int = 0  # total files across all items
    processed_files: int = 0
    failed_files: int = 0
    error_log: List[str] = field(default_factory=list)
    success_log: List[str] = field(default_factory=list)
    book_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # book name -> results
    user_id: Optional[str] = None
    webhook_url: Optional[str] = None


@dataclass
class EnterpriseConfig:
    """Enterprise configuration settings."""
    max_concurrent_jobs: int = 4
    max_files_per_job: int = 1000
    job_timeout_hours: int = 24
    auto_cleanup_days: int = 30
    enable_webhooks: bool = True
    enable_api: bool = True
    api_port: int = 8080
    api_host: str = "localhost"
    log_level: str = "INFO"
    storage_directory: Optional[str] = None
    database_url: Optional[str] = None


@dataclass
class User:
    """Enterprise user account."""
    id: str
    username: str
    email: str
    role: str  # admin, user, viewer
    permissions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None
    active: bool = True
    api_key: Optional[str] = None


@dataclass
class JobStatistics:
    """Job execution statistics."""
    total_jobs: int = 0
    running_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    avg_processing_time: float = 0.0
    total_files_processed: int = 0
    success_rate: float = 100.0


class BatchProcessor:
    """Handles batch processing of multiple documents."""

    def __init__(self, config: EnterpriseConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_jobs)
        self.running_jobs: Dict[str, BatchJob] = {}
        self.job_futures: Dict[str, Any] = {}
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Set up enterprise logging."""
        logger = logging.getLogger("docx2shelf.enterprise")
        logger.setLevel(getattr(logging, self.config.log_level))

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def submit_batch_job(self, job: BatchJob) -> str:
        """Submit a batch job for processing."""
        # Validate job
        input_path = Path(job.input_pattern)
        if not input_path.exists():
            raise ValueError(f"Input path does not exist: {input_path}")

        # Find input items based on processing mode
        if job.processing_mode == "books":
            input_items = self._find_book_folders(job.input_pattern)
            if not input_items:
                raise ValueError(f"No book folders found in: {job.input_pattern}")
        else:
            input_items = self._find_input_files(job.input_pattern)
            if not input_items:
                raise ValueError(f"No files found matching pattern: {job.input_pattern}")

        # Count total files for validation
        total_files = 0
        if job.processing_mode == "books":
            for book_folder in input_items:
                book_files = self._find_files_in_folder(book_folder)
                total_files += len(book_files)
        else:
            total_files = len(input_items)

        if total_files > self.config.max_files_per_job:
            raise ValueError(f"Too many files ({total_files}), max is {self.config.max_files_per_job}")

        job.total_items = len(input_items)
        job.total_files = total_files
        job.status = "pending"

        # Submit to executor
        future = self.executor.submit(self._process_batch_job, job, input_items)
        self.job_futures[job.id] = future
        self.running_jobs[job.id] = job

        mode_desc = f"{len(input_items)} books" if job.processing_mode == "books" else f"{len(input_items)} files"
        self.logger.info(f"Submitted batch job {job.id} with {mode_desc} ({total_files} total files)")
        return job.id

    def _find_input_files(self, pattern: str) -> List[Path]:
        """Find files matching the input pattern."""
        from glob import glob
        files = []

        # Support both glob patterns and directory paths
        if Path(pattern).is_dir():
            # Process all supported files in directory
            for ext in ["*.docx", "*.doc", "*.md", "*.txt", "*.html"]:
                files.extend(Path(pattern).glob(ext))
        else:
            # Use glob pattern
            files = [Path(f) for f in glob(pattern)]

        return sorted(files)

    def _find_book_folders(self, directory: str) -> List[Path]:
        """Find subfolders that contain book projects."""
        base_dir = Path(directory)
        if not base_dir.is_dir():
            return []

        book_folders = []
        for item in base_dir.iterdir():
            if item.is_dir():
                # Check if folder contains any supported files
                if self._find_files_in_folder(item):
                    book_folders.append(item)

        return sorted(book_folders)

    def _find_files_in_folder(self, folder: Path) -> List[Path]:
        """Find all supported files in a folder."""
        files = []
        for ext in ["*.docx", "*.doc", "*.md", "*.txt", "*.html"]:
            files.extend(folder.glob(ext))
            # Also check subfolders
            files.extend(folder.glob(f"**/{ext}"))
        return sorted(files)

    def _process_batch_job(self, job: BatchJob, input_items: List[Path]) -> None:
        """Process a batch job."""
        try:
            job.status = "running"
            job.started_at = datetime.now().isoformat()

            output_dir = Path(job.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)

            if job.processing_mode == "books":
                self._process_book_folders(job, input_items, output_dir)
            else:
                self._process_individual_files(job, input_items, output_dir)

            # Mark job as completed
            if job.status != "cancelled":
                job.status = "completed" if job.failed_items == 0 else "failed"

            job.completed_at = datetime.now().isoformat()

            # Send webhook notification if configured
            if job.webhook_url and self.config.enable_webhooks:
                self._send_webhook(job)

            if job.processing_mode == "books":
                self.logger.info(f"Batch job {job.id} completed. Books processed: {job.processed_items}, Failed: {job.failed_items}")
            else:
                self.logger.info(f"Batch job {job.id} completed. Files processed: {job.processed_files}, Failed: {job.failed_files}")

        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now().isoformat()
            error_msg = f"Batch job {job.id} failed: {str(e)}"
            job.error_log.append(error_msg)
            self.logger.error(error_msg)

        finally:
            # Clean up
            if job.id in self.running_jobs:
                del self.running_jobs[job.id]
            if job.id in self.job_futures:
                del self.job_futures[job.id]

    def _process_book_folders(self, job: BatchJob, book_folders: List[Path], output_dir: Path) -> None:
        """Process book folders (each folder = one book)."""
        for i, book_folder in enumerate(book_folders):
            try:
                # Check if job was cancelled
                if job.status == "cancelled":
                    break

                book_name = book_folder.name
                self.logger.info(f"Processing book {i+1}/{len(book_folders)}: {book_name}")

                # Create output path for this book
                book_output = output_dir / f"{book_name}.epub"

                # Process the book folder
                success, files_processed, files_failed = self._process_book_folder(book_folder, book_output, job.config)

                # Update job statistics
                job.processed_files += files_processed
                job.failed_files += files_failed

                if success:
                    job.processed_items += 1
                    job.success_log.append(f"Successfully processed book: {book_name}")
                    job.book_results[book_name] = {
                        "status": "success",
                        "output_file": str(book_output),
                        "files_processed": files_processed,
                        "files_failed": files_failed
                    }
                else:
                    job.failed_items += 1
                    job.error_log.append(f"Failed to process book: {book_name}")
                    job.book_results[book_name] = {
                        "status": "failed",
                        "files_processed": files_processed,
                        "files_failed": files_failed
                    }

                job.progress = int((i + 1) / len(book_folders) * 100)

            except Exception as e:
                job.failed_items += 1
                error_msg = f"Error processing book {book_folder.name}: {str(e)}"
                job.error_log.append(error_msg)
                self.logger.error(error_msg)
                job.book_results[book_folder.name] = {
                    "status": "error",
                    "error": str(e)
                }

    def _process_individual_files(self, job: BatchJob, input_files: List[Path], output_dir: Path) -> None:
        """Process individual files (original mode)."""
        for i, input_file in enumerate(input_files):
            try:
                # Check if job was cancelled
                if job.status == "cancelled":
                    break

                self.logger.info(f"Processing file {i+1}/{len(input_files)}: {input_file}")

                # Process single file
                success = self._process_single_file(input_file, output_dir, job.config)

                if success:
                    job.processed_files += 1
                    job.processed_items += 1
                    job.success_log.append(f"Successfully processed: {input_file}")
                else:
                    job.failed_files += 1
                    job.failed_items += 1
                    job.error_log.append(f"Failed to process: {input_file}")

                job.progress = int((i + 1) / len(input_files) * 100)

            except Exception as e:
                job.failed_files += 1
                job.failed_items += 1
                error_msg = f"Error processing {input_file}: {str(e)}"
                job.error_log.append(error_msg)
                self.logger.error(error_msg)

    def _process_book_folder(self, book_folder: Path, output_file: Path, config: Dict[str, Any]) -> tuple[bool, int, int]:
        """Process all files in a folder as a single book."""
        try:
            from .assemble import assemble_epub
            from .convert import convert_document
            from .metadata import BuildOptions, EpubMetadata

            # Find all files in the book folder
            book_files = self._find_files_in_folder(book_folder)
            if not book_files:
                return False, 0, 0

            files_processed = 0
            files_failed = 0

            # Create metadata from config, defaulting to folder name
            book_name = book_folder.name
            metadata = EpubMetadata(
                title=config.get("title", book_name),
                author=config.get("author", "Unknown"),
                language=config.get("language", "en"),
                description=config.get("description", f"Generated from {book_name}"),
                publisher=config.get("publisher", ""),
                subjects=config.get("subjects", []),
                keywords=config.get("keywords", [])
            )

            # Check for metadata.txt file in the book folder
            metadata_file = book_folder / "metadata.txt"
            if metadata_file.exists():
                try:
                    from .utils import parse_kv_file
                    book_metadata = parse_kv_file(metadata_file)
                    # Override with book-specific metadata
                    if "title" in book_metadata:
                        metadata.title = book_metadata["title"]
                    if "author" in book_metadata:
                        metadata.author = book_metadata["author"]
                    if "description" in book_metadata:
                        metadata.description = book_metadata["description"]
                    if "language" in book_metadata:
                        metadata.language = book_metadata["language"]
                except Exception as e:
                    self.logger.warning(f"Could not parse metadata file for {book_name}: {e}")

            # Look for cover image in the book folder
            cover_path = None
            for cover_name in ["cover.jpg", "cover.png", "cover.jpeg", "cover.gif"]:
                potential_cover = book_folder / cover_name
                if potential_cover.exists():
                    cover_path = potential_cover
                    break

            # Create build options
            options = BuildOptions(
                theme=config.get("theme", "serif"),
                split_at=config.get("split_at", "h1"),
                toc_depth=config.get("toc_depth", 2),
                hyphenate=config.get("hyphenate", True),
                justify=config.get("justify", True),
                image_quality=config.get("image_quality", 85),
                image_max_width=config.get("image_max_width", 1200),
                image_max_height=config.get("image_max_height", 1600),
                cover_path=str(cover_path) if cover_path else None
            )

            # Convert and combine all files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                combined_content = []

                # Sort files to ensure consistent order
                sorted_files = sorted(book_files, key=lambda x: (x.parent, x.name))

                for book_file in sorted_files:
                    try:
                        # Convert each file to HTML/XHTML
                        converted_content = convert_document(
                            book_file,
                            temp_path,
                            options.split_at
                        )

                        if converted_content:
                            combined_content.append(converted_content)
                            files_processed += 1
                        else:
                            files_failed += 1
                            self.logger.warning(f"Failed to convert {book_file}")

                    except Exception as e:
                        files_failed += 1
                        self.logger.error(f"Error converting {book_file}: {e}")

                # If we have any successful conversions, create the EPUB
                if combined_content:
                    # Combine all content into chapters
                    self._combine_book_content(temp_path, combined_content, sorted_files)

                    # Assemble EPUB
                    assemble_epub(
                        content_dir=temp_path,
                        output_path=output_file,
                        metadata=metadata,
                        options=options
                    )

                    return output_file.exists(), files_processed, files_failed
                else:
                    return False, files_processed, files_failed

        except Exception as e:
            self.logger.error(f"Failed to process book folder {book_folder}: {str(e)}")
            return False, 0, len(self._find_files_in_folder(book_folder))

    def _combine_book_content(self, temp_path: Path, content_list: List[str], source_files: List[Path]) -> None:
        """Combine multiple converted files into a cohesive book structure."""
        try:
            # Create a single combined HTML file
            combined_html = []
            combined_html.append('<!DOCTYPE html>')
            combined_html.append('<html xmlns="http://www.w3.org/1999/xhtml">')
            combined_html.append('<head>')
            combined_html.append('<meta charset="utf-8"/>')
            combined_html.append('<title>Combined Content</title>')
            combined_html.append('</head>')
            combined_html.append('<body>')

            for i, (content, source_file) in enumerate(zip(content_list, source_files)):
                # Add a chapter separator
                chapter_title = source_file.stem
                combined_html.append(f'<div class="chapter" id="chapter-{i+1}">')
                combined_html.append(f'<h1>{chapter_title}</h1>')

                # Extract body content from the converted HTML
                if '<body>' in content and '</body>' in content:
                    start = content.find('<body>') + 6
                    end = content.find('</body>')
                    body_content = content[start:end]
                    combined_html.append(body_content)
                else:
                    # Fallback: use the content as-is
                    combined_html.append(content)

                combined_html.append('</div>')

            combined_html.append('</body>')
            combined_html.append('</html>')

            # Save the combined file
            combined_file = temp_path / "combined.html"
            combined_file.write_text('\n'.join(combined_html), encoding='utf-8')

        except Exception as e:
            self.logger.error(f"Error combining book content: {e}")

    def _process_single_file(self, input_file: Path, output_dir: Path, config: Dict[str, Any]) -> bool:
        """Process a single file using docx2shelf."""
        try:
            from .assemble import assemble_epub
            from .convert import convert_document
            from .metadata import BuildOptions, EpubMetadata

            # Create metadata from config
            metadata = EpubMetadata(
                title=config.get("title", input_file.stem),
                author=config.get("author", "Unknown"),
                language=config.get("language", "en"),
                description=config.get("description", ""),
                publisher=config.get("publisher", ""),
                subjects=config.get("subjects", []),
                keywords=config.get("keywords", [])
            )

            # Create build options
            options = BuildOptions(
                theme=config.get("theme", "serif"),
                split_at=config.get("split_at", "h1"),
                toc_depth=config.get("toc_depth", 2),
                hyphenate=config.get("hyphenate", True),
                justify=config.get("justify", True),
                image_quality=config.get("image_quality", 85),
                image_max_width=config.get("image_max_width", 1200),
                image_max_height=config.get("image_max_height", 1600)
            )

            # Generate output filename
            output_file = output_dir / f"{input_file.stem}.epub"

            # Convert document
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Convert to HTML/XHTML
                converted_content = convert_document(
                    input_file,
                    temp_path,
                    options.split_at
                )

                # Assemble EPUB
                assemble_epub(
                    content_dir=temp_path,
                    output_path=output_file,
                    metadata=metadata,
                    options=options
                )

            return output_file.exists()

        except Exception as e:
            self.logger.error(f"Failed to process {input_file}: {str(e)}")
            return False

    def _send_webhook(self, job: BatchJob) -> None:
        """Send webhook notification for job completion."""
        if not requests or not job.webhook_url:
            return

        try:
            payload = {
                "job_id": job.id,
                "job_name": job.name,
                "status": job.status,
                "processed_files": job.processed_files,
                "failed_files": job.failed_files,
                "total_files": job.total_files,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "success_rate": (job.processed_files / job.total_files * 100) if job.total_files > 0 else 0
            }

            response = requests.post(
                job.webhook_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )

            response.raise_for_status()
            self.logger.info(f"Webhook sent successfully for job {job.id}")

        except Exception as e:
            self.logger.error(f"Failed to send webhook for job {job.id}: {str(e)}")

    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get the status of a batch job."""
        if job_id in self.running_jobs:
            return self.running_jobs[job_id]
        return None

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running batch job."""
        if job_id in self.running_jobs:
            job = self.running_jobs[job_id]
            job.status = "cancelled"

            # Cancel the future if possible
            if job_id in self.job_futures:
                future = self.job_futures[job_id]
                future.cancel()

            self.logger.info(f"Cancelled batch job {job_id}")
            return True
        return False

    def list_jobs(self, status_filter: Optional[str] = None) -> List[BatchJob]:
        """List batch jobs, optionally filtered by status."""
        jobs = list(self.running_jobs.values())

        if status_filter:
            jobs = [job for job in jobs if job.status == status_filter]

        return sorted(jobs, key=lambda x: x.created_at, reverse=True)

    def cleanup_old_jobs(self) -> int:
        """Clean up old completed jobs."""
        cutoff_date = datetime.now() - timedelta(days=self.config.auto_cleanup_days)
        cutoff_str = cutoff_date.isoformat()

        cleaned_count = 0
        jobs_to_remove = []

        for job_id, job in self.running_jobs.items():
            if (job.status in ["completed", "failed", "cancelled"] and
                job.completed_at and job.completed_at < cutoff_str):
                jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            del self.running_jobs[job_id]
            if job_id in self.job_futures:
                del self.job_futures[job_id]
            cleaned_count += 1

        self.logger.info(f"Cleaned up {cleaned_count} old jobs")
        return cleaned_count


class ConfigurationManager:
    """Manages enterprise configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> Path:
        """Get the default configuration file path."""
        if os.name == "nt":  # Windows
            base_dir = Path(os.environ.get("APPDATA", "~")).expanduser()
        else:  # Unix-like
            base_dir = Path.home()

        return base_dir / ".docx2shelf" / "enterprise" / "config.yaml"

    def _load_config(self) -> EnterpriseConfig:
        """Load configuration from file."""
        if not self.config_path.exists():
            # Create default config
            config = EnterpriseConfig()
            self.save_config(config)
            return config

        try:
            if yaml:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
            else:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            return EnterpriseConfig(**data)

        except Exception as e:
            print(f"Error loading config: {e}")
            return EnterpriseConfig()

    def save_config(self, config: EnterpriseConfig) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(config)

        try:
            if yaml:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False)
            else:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def update_config(self, **kwargs) -> None:
        """Update configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self.save_config(self.config)

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = EnterpriseConfig()
        self.save_config(self.config)


class UserManager:
    """Manages enterprise users and permissions."""

    def __init__(self, database_path: Optional[Path] = None):
        self.db_path = database_path or self._get_default_db_path()
        self._init_database()

    def _get_default_db_path(self) -> Path:
        """Get the default database path."""
        if os.name == "nt":  # Windows
            base_dir = Path(os.environ.get("APPDATA", "~")).expanduser()
        else:  # Unix-like
            base_dir = Path.home()

        return base_dir / ".docx2shelf" / "enterprise" / "users.db"

    def _init_database(self) -> None:
        """Initialize the users database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    active BOOLEAN NOT NULL DEFAULT 1,
                    api_key TEXT UNIQUE,
                    password_hash TEXT
                )
            """)

            # Create default admin user if none exists
            cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] == 0:
                self._create_default_admin(conn)

    def _create_default_admin(self, conn: sqlite3.Connection) -> None:
        """Create a default admin user."""
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@localhost",
            role="admin",
            permissions=["*"],  # All permissions
            api_key=self._generate_api_key()
        )

        self._insert_user(conn, admin_user)
        print(f"Created default admin user. API key: {admin_user.api_key}")

    def _generate_api_key(self) -> str:
        """Generate a unique API key."""
        return hashlib.sha256(f"{uuid.uuid4()}{time.time()}".encode()).hexdigest()

    def _insert_user(self, conn: sqlite3.Connection, user: User) -> None:
        """Insert a user into the database."""
        conn.execute("""
            INSERT INTO users (id, username, email, role, permissions, created_at,
                             last_login, active, api_key, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.id, user.username, user.email, user.role,
            json.dumps(user.permissions), user.created_at,
            user.last_login, user.active, user.api_key, None
        ))

    def create_user(self, username: str, email: str, role: str = "user",
                   permissions: Optional[List[str]] = None) -> User:
        """Create a new user."""
        if permissions is None:
            permissions = self._get_default_permissions(role)

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            role=role,
            permissions=permissions,
            api_key=self._generate_api_key()
        )

        with sqlite3.connect(self.db_path) as conn:
            try:
                self._insert_user(conn, user)
                return user
            except sqlite3.IntegrityError as e:
                if "username" in str(e):
                    raise ValueError("Username already exists")
                elif "email" in str(e):
                    raise ValueError("Email already exists")
                else:
                    raise ValueError("User creation failed")

    def _get_default_permissions(self, role: str) -> List[str]:
        """Get default permissions for a role."""
        permissions_map = {
            "admin": ["*"],
            "user": ["batch:create", "batch:view", "convert:use"],
            "viewer": ["batch:view", "convert:view"]
        }
        return permissions_map.get(role, ["convert:view"])

    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()

            if row:
                return User(
                    id=row[0], username=row[1], email=row[2], role=row[3],
                    permissions=json.loads(row[4]), created_at=row[5],
                    last_login=row[6], active=bool(row[7]), api_key=row[8]
                )
        return None

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get a user by API key."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM users WHERE api_key = ? AND active = 1", (api_key,))
            row = cursor.fetchone()

            if row:
                return User(
                    id=row[0], username=row[1], email=row[2], role=row[3],
                    permissions=json.loads(row[4]), created_at=row[5],
                    last_login=row[6], active=bool(row[7]), api_key=row[8]
                )
        return None

    def list_users(self, active_only: bool = True) -> List[User]:
        """List all users."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM users"
            params = []

            if active_only:
                query += " WHERE active = 1"

            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query, params)
            users = []

            for row in cursor.fetchall():
                users.append(User(
                    id=row[0], username=row[1], email=row[2], role=row[3],
                    permissions=json.loads(row[4]), created_at=row[5],
                    last_login=row[6], active=bool(row[7]), api_key=row[8]
                ))

            return users

    def update_user(self, user_id: str, **kwargs) -> bool:
        """Update user information."""
        valid_fields = ["username", "email", "role", "permissions", "active"]
        updates = []
        params = []

        for field, value in kwargs.items():
            if field in valid_fields:
                if field == "permissions":
                    value = json.dumps(value)
                updates.append(f"{field} = ?")
                params.append(value)

        if not updates:
            return False

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount > 0

    def delete_user(self, user_id: str) -> bool:
        """Delete a user (soft delete by deactivating)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))
            return cursor.rowcount > 0

    def has_permission(self, user: User, permission: str) -> bool:
        """Check if a user has a specific permission."""
        if "*" in user.permissions:  # Admin has all permissions
            return True

        return permission in user.permissions


# Global instances for enterprise features
_config_manager = None
_batch_processor = None
_user_manager = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_batch_processor() -> BatchProcessor:
    """Get the global batch processor."""
    global _batch_processor
    if _batch_processor is None:
        config = get_config_manager().config
        _batch_processor = BatchProcessor(config)
    return _batch_processor


def get_user_manager() -> UserManager:
    """Get the global user manager."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager