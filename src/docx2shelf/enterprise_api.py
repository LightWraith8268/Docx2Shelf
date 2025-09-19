"""
Enterprise integration and advanced REST API for Docx2Shelf.

Provides webhook integration, OpenAPI specification, rate limiting,
and database integration for enterprise workflows.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
from urllib.parse import urlparse
import requests
from threading import Lock


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
            conn.executescript("""
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
            """)

    def _get_connection(self):
        """Get database connection."""
        return sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )

    def create_conversion_job(self, job: ConversionJob) -> str:
        """Create a new conversion job."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO conversion_jobs (
                    job_id, input_file_path, output_file_path, input_format,
                    output_format, status, created_at, started_at, completed_at,
                    error_message, metadata, user_id, priority, progress_percent,
                    file_size_bytes, estimated_duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, job.input_file_path, job.output_file_path,
                job.input_format, job.output_format, job.status,
                job.created_at, job.started_at, job.completed_at,
                job.error_message, json.dumps(job.metadata), job.user_id,
                job.priority, job.progress_percent, job.file_size_bytes,
                job.estimated_duration_seconds
            ))
        return job.job_id

    def get_conversion_job(self, job_id: str) -> Optional[ConversionJob]:
        """Get conversion job by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM conversion_jobs WHERE job_id = ?",
                (job_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_conversion_job(row)
        return None

    def update_conversion_job(self, job: ConversionJob):
        """Update conversion job."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE conversion_jobs SET
                    output_file_path = ?, status = ?, started_at = ?,
                    completed_at = ?, error_message = ?, metadata = ?,
                    progress_percent = ?, estimated_duration_seconds = ?
                WHERE job_id = ?
            """, (
                job.output_file_path, job.status, job.started_at,
                job.completed_at, job.error_message,
                json.dumps(job.metadata), job.progress_percent,
                job.estimated_duration_seconds, job.job_id
            ))

    def list_conversion_jobs(self, user_id: Optional[str] = None,
                           status: Optional[str] = None,
                           limit: int = 100, offset: int = 0) -> List[ConversionJob]:
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
            estimated_duration_seconds=row[15]
        )

    def create_api_key(self, api_key: APIKey):
        """Create a new API key."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO api_keys (
                    key_id, key_hash, name, user_id, permissions,
                    rate_limit_per_minute, created_at, last_used_at, enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                api_key.key_id, api_key.key_hash, api_key.name,
                api_key.user_id, json.dumps(api_key.permissions),
                api_key.rate_limit_per_minute, api_key.created_at,
                api_key.last_used_at, api_key.enabled
            ))

    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM api_keys WHERE key_id = ? AND enabled = 1",
                (key_id,)
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
                    enabled=bool(row[8])
                )
        return None

    def update_api_key_usage(self, key_id: str):
        """Update API key last used timestamp."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE key_id = ?",
                (datetime.now(timezone.utc), key_id)
            )

    def log_audit_event(self, user_id: Optional[str], action: str,
                       resource_type: str = None, resource_id: str = None,
                       details: Dict[str, Any] = None, ip_address: str = None,
                       user_agent: str = None):
        """Log audit event."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_log (
                    user_id, action, resource_type, resource_id,
                    details, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, action, resource_type, resource_id,
                json.dumps(details) if details else None,
                ip_address, user_agent
            ))


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
                    timeout_seconds=row[7]
                )
                self.endpoints.append(endpoint)

    def add_endpoint(self, endpoint: WebhookEndpoint):
        """Add webhook endpoint."""
        with self.db_manager._get_connection() as conn:
            conn.execute("""
                INSERT INTO webhook_endpoints (
                    url, secret, events, headers, enabled, retry_count, timeout_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                endpoint.url, endpoint.secret,
                json.dumps(endpoint.events), json.dumps(endpoint.headers),
                endpoint.enabled, endpoint.retry_count, endpoint.timeout_seconds
            ))
        self.endpoints.append(endpoint)

    def send_webhook(self, event: str, data: Dict[str, Any]):
        """Send webhook notification to all relevant endpoints."""
        for endpoint in self.endpoints:
            if endpoint.enabled and (not endpoint.events or event in endpoint.events):
                self._send_to_endpoint(endpoint, event, data)

    def _send_to_endpoint(self, endpoint: WebhookEndpoint, event: str, data: Dict[str, Any]):
        """Send webhook to specific endpoint with retries."""
        payload = {
            'event': event,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': data
        }

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Docx2Shelf-Webhook/1.2.6',
            **endpoint.headers
        }

        # Add signature if secret is configured
        if endpoint.secret:
            payload_json = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                endpoint.secret.encode(),
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Docx2Shelf-Signature'] = f'sha256={signature}'

        # Send with retries
        for attempt in range(endpoint.retry_count + 1):
            try:
                response = requests.post(
                    endpoint.url,
                    json=payload,
                    headers=headers,
                    timeout=endpoint.timeout_seconds
                )
                response.raise_for_status()
                break  # Success

            except requests.RequestException as e:
                if attempt == endpoint.retry_count:
                    print(f"Failed to send webhook to {endpoint.url} after {endpoint.retry_count + 1} attempts: {e}")
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff


class RateLimiter:
    """Rate limiting for API endpoints."""

    def __init__(self):
        self.clients: Dict[str, RateLimitInfo] = {}
        self.lock = Lock()

    def is_allowed(self, client_id: str, requests_per_minute: int = 60,
                   burst_size: int = 10) -> bool:
        """Check if client is allowed to make request."""
        with self.lock:
            now = datetime.now(timezone.utc)

            if client_id not in self.clients:
                self.clients[client_id] = RateLimitInfo(
                    requests_per_minute=requests_per_minute
                )

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

    def create_conversion_job(self, input_file_path: str, user_id: str = None,
                            metadata: Dict[str, Any] = None) -> ConversionJob:
        """Create new conversion job."""
        job = ConversionJob(
            job_id=str(uuid.uuid4()),
            input_file_path=input_file_path,
            user_id=user_id,
            metadata=metadata or {},
            file_size_bytes=Path(input_file_path).stat().st_size if Path(input_file_path).exists() else 0
        )

        job_id = self.db_manager.create_conversion_job(job)

        # Add to queue
        with self.queue_lock:
            self.conversion_queue.append(job)
            self.conversion_queue.sort(key=lambda x: (-x.priority, x.created_at))

        # Send webhook
        self.webhook_manager.send_webhook('job.created', asdict(job))

        # Log audit event
        self.db_manager.log_audit_event(
            user_id=user_id,
            action='job.created',
            resource_type='conversion_job',
            resource_id=job_id,
            details={'input_file': input_file_path}
        )

        return job

    def get_next_job(self) -> Optional[ConversionJob]:
        """Get next job from queue."""
        with self.queue_lock:
            if self.conversion_queue:
                return self.conversion_queue.pop(0)
        return None

    def update_job_status(self, job_id: str, status: str,
                         progress_percent: float = None,
                         error_message: str = None):
        """Update job status."""
        job = self.db_manager.get_conversion_job(job_id)
        if not job:
            return

        job.status = status
        if progress_percent is not None:
            job.progress_percent = progress_percent
        if error_message:
            job.error_message = error_message

        if status == 'running' and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        elif status in ['completed', 'failed']:
            job.completed_at = datetime.now(timezone.utc)

        self.db_manager.update_conversion_job(job)

        # Send webhook
        event = f'job.{status}'
        self.webhook_manager.send_webhook(event, asdict(job))

        # Log audit event
        self.db_manager.log_audit_event(
            user_id=job.user_id,
            action=event,
            resource_type='conversion_job',
            resource_id=job_id,
            details={'status': status, 'progress': progress_percent}
        )

    def generate_api_key(self, name: str, user_id: str,
                        permissions: List[str] = None) -> str:
        """Generate new API key."""
        key_id = str(uuid.uuid4())[:8]
        key_secret = str(uuid.uuid4()).replace('-', '')
        api_key = f"{key_id}{key_secret}"

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            permissions=permissions or []
        )

        self.db_manager.create_api_key(api_key_obj)

        # Log audit event
        self.db_manager.log_audit_event(
            user_id=user_id,
            action='api_key.created',
            resource_type='api_key',
            resource_id=key_id,
            details={'name': name, 'permissions': permissions}
        )

        return api_key

    def get_job_queue_status(self) -> Dict[str, Any]:
        """Get current job queue status."""
        with self.queue_lock:
            pending_jobs = len(self.conversion_queue)

        running_jobs = len(self.db_manager.list_conversion_jobs(status='running'))

        return {
            'pending_jobs': pending_jobs,
            'running_jobs': running_jobs,
            'queue_size': pending_jobs + running_jobs
        }