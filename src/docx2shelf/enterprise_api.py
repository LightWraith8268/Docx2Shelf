"""
Enterprise integration and advanced REST API for Docx2Shelf.

Provides webhook integration, OpenAPI specification, rate limiting,
and database integration for enterprise workflows.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

import requests


@dataclass
class ConversionJob:
    """Represents a conversion job in the system."""

    job_id: str
    input_file_path: str
    output_file_path: Optional[str] = None
    input_format: str = "docx"
    output_format: str = "epub"
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    priority: int = 5  # 1-10, higher is more priority
    progress_percent: float = 0.0
    file_size_bytes: int = 0
    estimated_duration_seconds: Optional[float] = None


@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration."""

    url: str
    secret: Optional[str] = None
    events: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    retry_count: int = 3
    timeout_seconds: int = 30


@dataclass
class APIKey:
    """API key for authentication."""

    key_id: str
    key_hash: str
    name: str
    user_id: str
    permissions: List[str] = field(default_factory=list)
    rate_limit_per_minute: int = 60
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None
    enabled: bool = True


@dataclass
class RateLimitInfo:
    """Rate limiting information."""

    requests_made: int = 0
    window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    requests_per_minute: int = 60
    burst_size: int = 10


class DatabaseManager:
    """Manages database operations for enterprise features."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection_lock = Lock()
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversion_jobs (
                    job_id TEXT PRIMARY KEY,
                    input_file_path TEXT NOT NULL,
                    output_file_path TEXT,
                    input_format TEXT DEFAULT 'docx',
                    output_format TEXT DEFAULT 'epub',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    metadata TEXT,
                    user_id TEXT,
                    priority INTEGER DEFAULT 5,
                    progress_percent REAL DEFAULT 0.0,
                    file_size_bytes INTEGER DEFAULT 0,
                    estimated_duration_seconds REAL
                );

                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    key_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    permissions TEXT,
                    rate_limit_per_minute INTEGER DEFAULT 60,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    enabled BOOLEAN DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS webhook_endpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    secret TEXT,
                    events TEXT,
                    headers TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    retry_count INTEGER DEFAULT 3,
                    timeout_seconds INTEGER DEFAULT 30
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_status ON conversion_jobs(status);
                CREATE INDEX IF NOT EXISTS idx_jobs_user ON conversion_jobs(user_id);
                CREATE INDEX IF NOT EXISTS idx_jobs_created ON conversion_jobs(created_at);
                CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
            """
            )

    def _get_connection(self):
        """Get database connection."""
        return sqlite3.connect(
            self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )

    def create_conversion_job(self, job: ConversionJob) -> str:
        """Create a new conversion job."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversion_jobs (
                    job_id, input_file_path, output_file_path, input_format,
                    output_format, status, created_at, started_at, completed_at,
                    error_message, metadata, user_id, priority, progress_percent,
                    file_size_bytes, estimated_duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    job.job_id,
                    job.input_file_path,
                    job.output_file_path,
                    job.input_format,
                    job.output_format,
                    job.status,
                    job.created_at,
                    job.started_at,
                    job.completed_at,
                    job.error_message,
                    json.dumps(job.metadata),
                    job.user_id,
                    job.priority,
                    job.progress_percent,
                    job.file_size_bytes,
                    job.estimated_duration_seconds,
                ),
            )
        return job.job_id

    def get_conversion_job(self, job_id: str) -> Optional[ConversionJob]:
        """Get conversion job by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM conversion_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_conversion_job(row)
        return None

    def update_conversion_job(self, job: ConversionJob):
        """Update conversion job."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE conversion_jobs SET
                    output_file_path = ?, status = ?, started_at = ?,
                    completed_at = ?, error_message = ?, metadata = ?,
                    progress_percent = ?, estimated_duration_seconds = ?
                WHERE job_id = ?
            """,
                (
                    job.output_file_path,
                    job.status,
                    job.started_at,
                    job.completed_at,
                    job.error_message,
                    json.dumps(job.metadata),
                    job.progress_percent,
                    job.estimated_duration_seconds,
                    job.job_id,
                ),
            )

    def list_conversion_jobs(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ConversionJob]:
        """List conversion jobs with filtering."""
        query = "SELECT * FROM conversion_jobs WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [self._row_to_conversion_job(row) for row in cursor.fetchall()]

    def _row_to_conversion_job(self, row) -> ConversionJob:
        """Convert database row to ConversionJob."""
        return ConversionJob(
            job_id=row[0],
            input_file_path=row[1],
            output_file_path=row[2],
            input_format=row[3],
            output_format=row[4],
            status=row[5],
            created_at=row[6],
            started_at=row[7],
            completed_at=row[8],
            error_message=row[9],
            metadata=json.loads(row[10]) if row[10] else {},
            user_id=row[11],
            priority=row[12],
            progress_percent=row[13],
            file_size_bytes=row[14],
            estimated_duration_seconds=row[15],
        )

    def create_api_key(self, api_key: APIKey):
        """Create a new API key."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO api_keys (
                    key_id, key_hash, name, user_id, permissions,
                    rate_limit_per_minute, created_at, last_used_at, enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    api_key.key_id,
                    api_key.key_hash,
                    api_key.name,
                    api_key.user_id,
                    json.dumps(api_key.permissions),
                    api_key.rate_limit_per_minute,
                    api_key.created_at,
                    api_key.last_used_at,
                    api_key.enabled,
                ),
            )

    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM api_keys WHERE key_id = ? AND enabled = 1", (key_id,)
            )
            row = cursor.fetchone()
            if row:
                return APIKey(
                    key_id=row[0],
                    key_hash=row[1],
                    name=row[2],
                    user_id=row[3],
                    permissions=json.loads(row[4]) if row[4] else [],
                    rate_limit_per_minute=row[5],
                    created_at=row[6],
                    last_used_at=row[7],
                    enabled=bool(row[8]),
                )
        return None

    def update_api_key_usage(self, key_id: str):
        """Update API key last used timestamp."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE key_id = ?",
                (datetime.now(timezone.utc), key_id),
            )

    def log_audit_event(
        self,
        user_id: Optional[str],
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
    ):
        """Log audit event."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (
                    user_id, action, resource_type, resource_id,
                    details, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    action,
                    resource_type,
                    resource_id,
                    json.dumps(details) if details else None,
                    ip_address,
                    user_agent,
                ),
            )


class WebhookManager:
    """Manages webhook endpoints and notifications."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.endpoints: List[WebhookEndpoint] = []
        self._load_endpoints()

    def _load_endpoints(self):
        """Load webhook endpoints from database."""
        with self.db_manager._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM webhook_endpoints WHERE enabled = 1")
            for row in cursor.fetchall():
                endpoint = WebhookEndpoint(
                    url=row[1],
                    secret=row[2],
                    events=json.loads(row[3]) if row[3] else [],
                    headers=json.loads(row[4]) if row[4] else {},
                    enabled=bool(row[5]),
                    retry_count=row[6],
                    timeout_seconds=row[7],
                )
                self.endpoints.append(endpoint)

    def add_endpoint(self, endpoint: WebhookEndpoint):
        """Add webhook endpoint."""
        with self.db_manager._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO webhook_endpoints (
                    url, secret, events, headers, enabled, retry_count, timeout_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    endpoint.url,
                    endpoint.secret,
                    json.dumps(endpoint.events),
                    json.dumps(endpoint.headers),
                    endpoint.enabled,
                    endpoint.retry_count,
                    endpoint.timeout_seconds,
                ),
            )
        self.endpoints.append(endpoint)

    def send_webhook(self, event: str, data: Dict[str, Any]):
        """Send webhook notification to all relevant endpoints."""
        for endpoint in self.endpoints:
            if endpoint.enabled and (not endpoint.events or event in endpoint.events):
                self._send_to_endpoint(endpoint, event, data)

    def _send_to_endpoint(self, endpoint: WebhookEndpoint, event: str, data: Dict[str, Any]):
        """Send webhook to specific endpoint with retries."""
        payload = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Docx2Shelf-Webhook/1.2.6",
            **endpoint.headers,
        }

        # Add signature if secret is configured
        if endpoint.secret:
            payload_json = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                endpoint.secret.encode(), payload_json.encode(), hashlib.sha256
            ).hexdigest()
            headers["X-Docx2Shelf-Signature"] = f"sha256={signature}"

        # Send with retries
        for attempt in range(endpoint.retry_count + 1):
            try:
                response = requests.post(
                    endpoint.url, json=payload, headers=headers, timeout=endpoint.timeout_seconds
                )
                response.raise_for_status()
                break  # Success

            except requests.RequestException as e:
                if attempt == endpoint.retry_count:
                    print(
                        f"Failed to send webhook to {endpoint.url} after {endpoint.retry_count + 1} attempts: {e}"
                    )
                else:
                    time.sleep(2**attempt)  # Exponential backoff


class RateLimiter:
    """Rate limiting for API endpoints."""

    def __init__(self):
        self.clients: Dict[str, RateLimitInfo] = {}
        self.lock = Lock()

    def is_allowed(
        self, client_id: str, requests_per_minute: int = 60, burst_size: int = 10
    ) -> bool:
        """Check if client is allowed to make request."""
        with self.lock:
            now = datetime.now(timezone.utc)

            if client_id not in self.clients:
                self.clients[client_id] = RateLimitInfo(requests_per_minute=requests_per_minute)

            client_info = self.clients[client_id]

            # Reset window if needed
            window_duration = timedelta(minutes=1)
            if now - client_info.window_start > window_duration:
                client_info.requests_made = 0
                client_info.window_start = now

            # Check rate limit
            if client_info.requests_made >= requests_per_minute:
                return False

            # Check burst limit
            if client_info.requests_made >= burst_size:
                time_since_window_start = (now - client_info.window_start).total_seconds()
                expected_requests = (time_since_window_start / 60.0) * requests_per_minute
                if client_info.requests_made >= expected_requests:
                    return False

            client_info.requests_made += 1
            return True

    def get_rate_limit_info(self, client_id: str) -> Optional[RateLimitInfo]:
        """Get current rate limit info for client."""
        return self.clients.get(client_id)


class EnterpriseAPIManager:
    """Main manager for enterprise API features."""

    def __init__(self, db_path: Path):
        self.db_manager = DatabaseManager(db_path)
        self.webhook_manager = WebhookManager(self.db_manager)
        self.rate_limiter = RateLimiter()
        self.conversion_queue: List[ConversionJob] = []
        self.queue_lock = Lock()

    def authenticate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Authenticate API key."""
        if not api_key or len(api_key) < 32:
            return None

        # Extract key ID (first 8 characters)
        key_id = api_key[:8]

        # Get stored key
        stored_key = self.db_manager.get_api_key(key_id)
        if not stored_key:
            return None

        # Verify key hash
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if not hmac.compare_digest(stored_key.key_hash, key_hash):
            return None

        # Update usage
        self.db_manager.update_api_key_usage(key_id)
        return stored_key

    def create_conversion_job(
        self, input_file_path: str, user_id: str = None, metadata: Dict[str, Any] = None
    ) -> ConversionJob:
        """Create new conversion job."""
        job = ConversionJob(
            job_id=str(uuid.uuid4()),
            input_file_path=input_file_path,
            user_id=user_id,
            metadata=metadata or {},
            file_size_bytes=(
                Path(input_file_path).stat().st_size if Path(input_file_path).exists() else 0
            ),
        )

        job_id = self.db_manager.create_conversion_job(job)

        # Add to queue
        with self.queue_lock:
            self.conversion_queue.append(job)
            self.conversion_queue.sort(key=lambda x: (-x.priority, x.created_at))

        # Send webhook
        self.webhook_manager.send_webhook("job.created", asdict(job))

        # Log audit event
        self.db_manager.log_audit_event(
            user_id=user_id,
            action="job.created",
            resource_type="conversion_job",
            resource_id=job_id,
            details={"input_file": input_file_path},
        )

        return job

    def get_next_job(self) -> Optional[ConversionJob]:
        """Get next job from queue."""
        with self.queue_lock:
            if self.conversion_queue:
                return self.conversion_queue.pop(0)
        return None

    def update_job_status(
        self, job_id: str, status: str, progress_percent: float = None, error_message: str = None
    ):
        """Update job status."""
        job = self.db_manager.get_conversion_job(job_id)
        if not job:
            return

        job.status = status
        if progress_percent is not None:
            job.progress_percent = progress_percent
        if error_message:
            job.error_message = error_message

        if status == "running" and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        elif status in ["completed", "failed"]:
            job.completed_at = datetime.now(timezone.utc)

        self.db_manager.update_conversion_job(job)

        # Send webhook
        event = f"job.{status}"
        self.webhook_manager.send_webhook(event, asdict(job))

        # Log audit event
        self.db_manager.log_audit_event(
            user_id=job.user_id,
            action=event,
            resource_type="conversion_job",
            resource_id=job_id,
            details={"status": status, "progress": progress_percent},
        )

    def generate_api_key(
        self, name: str, user_id: str, permissions: List[str] | None = None
    ) -> str:
        """Generate new API key."""
        key_id = str(uuid.uuid4())[:8]
        key_secret = str(uuid.uuid4()).replace("-", "")
        api_key = f"{key_id}{key_secret}"

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            permissions=permissions or [],
        )

        self.db_manager.create_api_key(api_key_obj)

        # Log audit event
        self.db_manager.log_audit_event(
            user_id=user_id,
            action="api_key.created",
            resource_type="api_key",
            resource_id=key_id,
            details={"name": name, "permissions": permissions},
        )

        return api_key

    def get_job_queue_status(self) -> Dict[str, Any]:
        """Get current job queue status."""
        with self.queue_lock:
            pending_jobs = len(self.conversion_queue)

        running_jobs = len(self.db_manager.list_conversion_jobs(status="running"))

        return {
            "pending_jobs": pending_jobs,
            "running_jobs": running_jobs,
            "queue_size": pending_jobs + running_jobs,
        }


# FastAPI application for REST endpoints
try:
    import uvicorn
    from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from pydantic import BaseModel, Field

    app = FastAPI(
        title="Docx2Shelf Enterprise API",
        description="Enterprise-grade document conversion API with batch processing",
        version="1.2.8",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security
    security = HTTPBearer()

    # Global manager instance
    api_manager: Optional[EnterpriseAPIManager] = None

    # Request/Response models
    class ConversionRequest(BaseModel):
        input_file_path: str = Field(..., description="Path to input file")
        output_directory: Optional[str] = Field(None, description="Output directory")
        title: Optional[str] = Field(None, description="Book title")
        author: Optional[str] = Field(None, description="Book author")
        theme: str = Field("serif", description="EPUB theme")
        processing_mode: str = Field("files", description="Processing mode: 'files' or 'books'")
        split_at: str = Field("h1", description="Chapter split level")
        toc_depth: int = Field(2, description="Table of contents depth")
        hyphenate: bool = Field(True, description="Enable hyphenation")
        justify: bool = Field(True, description="Enable text justification")
        webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")

    class BatchJobRequest(BaseModel):
        name: str = Field(..., description="Job name")
        input_pattern: str = Field(..., description="Input pattern or directory")
        output_directory: str = Field(..., description="Output directory")
        processing_mode: str = Field("books", description="Processing mode: 'files' or 'books'")
        config: Dict[str, Any] = Field(default_factory=dict, description="Job configuration")
        webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")

    class JobResponse(BaseModel):
        job_id: str
        status: str
        progress: Optional[int] = None
        message: Optional[str] = None

    class APIKeyRequest(BaseModel):
        name: str = Field(..., description="API key name")
        permissions: List[str] = Field(default_factory=list, description="API key permissions")

    class APIKeyResponse(BaseModel):
        api_key: str
        key_id: str
        message: str

    def get_api_manager() -> EnterpriseAPIManager:
        """Get the global API manager."""
        global api_manager
        if api_manager is None:
            import os
            from pathlib import Path

            # Default database path
            if os.name == "nt":  # Windows
                base_dir = Path(os.environ.get("APPDATA", "~")).expanduser()
            else:  # Unix-like
                base_dir = Path.home()

            db_path = base_dir / ".docx2shelf" / "enterprise" / "api.db"
            api_manager = EnterpriseAPIManager(db_path)

        return api_manager

    async def verify_api_key(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> APIKey:
        """Verify API key and return user info."""
        manager = get_api_manager()

        api_key_obj = manager.authenticate_api_key(credentials.credentials)
        if not api_key_obj:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Check rate limiting
        if not manager.rate_limiter.is_allowed(
            api_key_obj.key_id, api_key_obj.rate_limit_per_minute
        ):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        return api_key_obj

    @app.get("/", response_model=Dict[str, str])
    async def root():
        """API root endpoint."""
        return {
            "name": "Docx2Shelf Enterprise API",
            "version": "1.2.8",
            "description": "Enterprise document conversion API",
            "docs": "/docs",
        }

    @app.get("/health", response_model=Dict[str, str])
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

    @app.post("/api/v1/jobs/batch", response_model=JobResponse)
    async def create_batch_job(
        request: BatchJobRequest,
        background_tasks: BackgroundTasks,
        api_key: APIKey = Depends(verify_api_key),
    ):
        """Create a new batch processing job."""
        try:
            import uuid

            from .enterprise import BatchJob, get_batch_processor

            # Create batch job
            job = BatchJob(
                id=str(uuid.uuid4()),
                name=request.name,
                input_pattern=request.input_pattern,
                output_directory=request.output_directory,
                config=request.config,
                processing_mode=request.processing_mode,
                user_id=api_key.user_id,
                webhook_url=request.webhook_url,
            )

            # Submit to batch processor
            processor = get_batch_processor()
            job_id = processor.submit_batch_job(job)

            # Log audit event
            manager = get_api_manager()
            manager.db_manager.log_audit_event(
                user_id=api_key.user_id,
                action="batch_job.created",
                resource_type="batch_job",
                resource_id=job_id,
                details={"name": request.name, "mode": request.processing_mode},
            )

            return JobResponse(
                job_id=job_id,
                status="pending",
                message="Batch job created and queued for processing",
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    @app.get("/api/v1/jobs/batch/{job_id}", response_model=Dict[str, Any])
    async def get_batch_job(job_id: str, api_key: APIKey = Depends(verify_api_key)):
        """Get batch job status and details."""
        try:
            from .enterprise import get_batch_processor

            processor = get_batch_processor()
            job = processor.get_job_status(job_id)

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            # Check permissions (users can only see their own jobs unless admin)
            if job.user_id != api_key.user_id and "*" not in api_key.permissions:
                raise HTTPException(status_code=403, detail="Access denied")

            return {
                "job_id": job.id,
                "name": job.name,
                "status": job.status,
                "processing_mode": job.processing_mode,
                "progress": job.progress,
                "total_items": job.total_items,
                "processed_items": job.processed_items,
                "failed_items": job.failed_items,
                "total_files": job.total_files,
                "processed_files": job.processed_files,
                "failed_files": job.failed_files,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "book_results": job.book_results,
                "success_log": job.success_log[-10:],  # Last 10 successes
                "error_log": job.error_log[-10:],  # Last 10 errors
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    @app.get("/api/v1/jobs/batch", response_model=List[Dict[str, Any]])
    async def list_batch_jobs(
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        api_key: APIKey = Depends(verify_api_key),
    ):
        """List batch jobs."""
        try:
            from .enterprise import get_batch_processor

            processor = get_batch_processor()
            jobs = processor.list_jobs(status_filter=status)

            # Filter by user permissions
            if "*" not in api_key.permissions:
                jobs = [job for job in jobs if job.user_id == api_key.user_id]

            # Apply pagination
            jobs = jobs[offset : offset + limit]

            return [
                {
                    "job_id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "processing_mode": job.processing_mode,
                    "progress": job.progress,
                    "total_items": job.total_items,
                    "processed_items": job.processed_items,
                    "failed_items": job.failed_items,
                    "created_at": job.created_at,
                    "completed_at": job.completed_at,
                }
                for job in jobs
            ]

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    @app.delete("/api/v1/jobs/batch/{job_id}", response_model=Dict[str, str])
    async def cancel_batch_job(job_id: str, api_key: APIKey = Depends(verify_api_key)):
        """Cancel a batch job."""
        try:
            from .enterprise import get_batch_processor

            processor = get_batch_processor()
            job = processor.get_job_status(job_id)

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            # Check permissions
            if job.user_id != api_key.user_id and "*" not in api_key.permissions:
                raise HTTPException(status_code=403, detail="Access denied")

            success = processor.cancel_job(job_id)

            if success:
                # Log audit event
                manager = get_api_manager()
                manager.db_manager.log_audit_event(
                    user_id=api_key.user_id,
                    action="batch_job.cancelled",
                    resource_type="batch_job",
                    resource_id=job_id,
                )

                return {"message": "Job cancelled successfully"}
            else:
                return {"message": "Job could not be cancelled (may have already completed)"}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    @app.post("/api/v1/convert", response_model=JobResponse)
    async def convert_document(
        request: ConversionRequest,
        background_tasks: BackgroundTasks,
        api_key: APIKey = Depends(verify_api_key),
    ):
        """Convert a single document."""
        try:
            manager = get_api_manager()

            # Create conversion job
            job = manager.create_conversion_job(
                input_file_path=request.input_file_path,
                user_id=api_key.user_id,
                metadata={
                    "title": request.title,
                    "author": request.author,
                    "theme": request.theme,
                    "split_at": request.split_at,
                    "toc_depth": request.toc_depth,
                    "hyphenate": request.hyphenate,
                    "justify": request.justify,
                    "output_directory": request.output_directory,
                    "webhook_url": request.webhook_url,
                },
            )

            # Start processing in background
            background_tasks.add_task(process_conversion_job, job.job_id)

            return JobResponse(
                job_id=job.job_id,
                status="pending",
                message="Conversion job created and queued for processing",
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    @app.get("/api/v1/convert/{job_id}", response_model=Dict[str, Any])
    async def get_conversion_job(job_id: str, api_key: APIKey = Depends(verify_api_key)):
        """Get conversion job status."""
        try:
            manager = get_api_manager()
            job = manager.db_manager.get_conversion_job(job_id)

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            # Check permissions
            if job.user_id != api_key.user_id and "*" not in api_key.permissions:
                raise HTTPException(status_code=403, detail="Access denied")

            return {
                "job_id": job.job_id,
                "input_file_path": job.input_file_path,
                "output_file_path": job.output_file_path,
                "status": job.status,
                "progress_percent": job.progress_percent,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "metadata": job.metadata,
                "file_size_bytes": job.file_size_bytes,
                "estimated_duration_seconds": job.estimated_duration_seconds,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    @app.post("/api/v1/auth/keys", response_model=APIKeyResponse)
    async def create_api_key(request: APIKeyRequest, api_key: APIKey = Depends(verify_api_key)):
        """Create a new API key (admin only)."""
        if "*" not in api_key.permissions and "admin" not in api_key.permissions:
            raise HTTPException(status_code=403, detail="Admin access required")

        try:
            manager = get_api_manager()
            new_key = manager.generate_api_key(
                name=request.name, user_id=api_key.user_id, permissions=request.permissions
            )

            return APIKeyResponse(
                api_key=new_key, key_id=new_key[:8], message="API key created successfully"
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    @app.get("/api/v1/stats", response_model=Dict[str, Any])
    async def get_statistics(api_key: APIKey = Depends(verify_api_key)):
        """Get API usage statistics."""
        try:
            manager = get_api_manager()

            # Get job queue status
            queue_status = manager.get_job_queue_status()

            # Get batch processor stats
            from .enterprise import get_batch_processor

            processor = get_batch_processor()

            # Get job statistics (user-filtered)
            if "*" in api_key.permissions:
                # Admin can see all stats
                all_jobs = manager.db_manager.list_conversion_jobs(limit=1000)
                batch_jobs = processor.list_jobs()
            else:
                # Users see only their own stats
                all_jobs = manager.db_manager.list_conversion_jobs(
                    user_id=api_key.user_id, limit=1000
                )
                batch_jobs = [
                    job for job in processor.list_jobs() if job.user_id == api_key.user_id
                ]

            job_stats = {
                "total_jobs": len(all_jobs),
                "completed_jobs": len([j for j in all_jobs if j.status == "completed"]),
                "failed_jobs": len([j for j in all_jobs if j.status == "failed"]),
                "running_jobs": len([j for j in all_jobs if j.status == "running"]),
                "pending_jobs": len([j for j in all_jobs if j.status == "pending"]),
            }

            batch_stats = {
                "total_batch_jobs": len(batch_jobs),
                "completed_batch_jobs": len([j for j in batch_jobs if j.status == "completed"]),
                "failed_batch_jobs": len([j for j in batch_jobs if j.status == "failed"]),
                "running_batch_jobs": len([j for j in batch_jobs if j.status == "running"]),
                "pending_batch_jobs": len([j for j in batch_jobs if j.status == "pending"]),
            }

            return {
                "conversion_jobs": job_stats,
                "batch_jobs": batch_stats,
                "queue_status": queue_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def process_conversion_job(job_id: str):
        """Background task to process a conversion job."""
        try:
            manager = get_api_manager()
            job = manager.db_manager.get_conversion_job(job_id)

            if not job:
                return

            # Update status to running
            manager.update_job_status(job_id, "running", 0)

            # Process the file
            import tempfile
            from pathlib import Path

            from .assemble import assemble_epub
            from .convert import convert_document
            from .metadata import BuildOptions, EpubMetadata

            input_path = Path(job.input_file_path)
            if not input_path.exists():
                manager.update_job_status(job_id, "failed", error_message="Input file not found")
                return

            # Create metadata from job metadata
            metadata = EpubMetadata(
                title=job.metadata.get("title", input_path.stem),
                author=job.metadata.get("author", "Unknown"),
                language=job.metadata.get("language", "en"),
                description=job.metadata.get("description", ""),
                publisher=job.metadata.get("publisher", ""),
                subjects=job.metadata.get("subjects", []),
                keywords=job.metadata.get("keywords", []),
            )

            # Create build options
            options = BuildOptions(
                theme=job.metadata.get("theme", "serif"),
                split_at=job.metadata.get("split_at", "h1"),
                toc_depth=job.metadata.get("toc_depth", 2),
                hyphenate=job.metadata.get("hyphenate", True),
                justify=job.metadata.get("justify", True),
                image_quality=job.metadata.get("image_quality", 85),
                image_max_width=job.metadata.get("image_max_width", 1200),
                image_max_height=job.metadata.get("image_max_height", 1600),
            )

            # Determine output path
            output_dir = Path(job.metadata.get("output_directory", input_path.parent))
            output_file = output_dir / f"{input_path.stem}.epub"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Update job with output path
            job.output_file_path = str(output_file)
            manager.db_manager.update_conversion_job(job)

            # Convert document
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Update progress
                manager.update_job_status(job_id, "running", 25)

                # Convert to HTML/XHTML
                convert_document(input_path, temp_path, options.split_at)

                # Update progress
                manager.update_job_status(job_id, "running", 75)

                # Assemble EPUB
                assemble_epub(
                    content_dir=temp_path,
                    output_path=output_file,
                    metadata=metadata,
                    options=options,
                )

                # Update progress
                manager.update_job_status(job_id, "running", 100)

            # Mark as completed
            if output_file.exists():
                manager.update_job_status(job_id, "completed", 100)
            else:
                manager.update_job_status(
                    job_id, "failed", error_message="Output file was not created"
                )

        except Exception as e:
            manager = get_api_manager()
            manager.update_job_status(job_id, "failed", error_message=str(e))

    def start_api_server(host: str = "localhost", port: int = 8080, debug: bool = False):
        """Start the FastAPI server."""
        uvicorn.run(app, host=host, port=port, debug=debug, reload=debug)

except ImportError:
    # FastAPI not available
    app = None
    start_api_server = None
