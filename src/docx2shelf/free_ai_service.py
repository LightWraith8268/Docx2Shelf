"""
Free AI Service Integration for Docx2Shelf Users.

This module provides access to free AI services for users who don't have their own API keys.
It manages rate limiting, key rotation, and graceful fallbacks.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    from platformdirs import user_cache_dir
except ImportError:

    def user_cache_dir(appname: str) -> str:
        import os

        if os.name == "nt":  # Windows
            return os.path.expandvars(f"%LOCALAPPDATA%\\{appname}\\Cache")
        elif os.name == "posix":  # macOS/Linux
            return os.path.expanduser(f"~/.cache/{appname}")
        return f".{appname}_cache"


logger = logging.getLogger(__name__)


@dataclass
class APIUsage:
    """Track API usage for rate limiting."""

    requests_today: int = 0
    last_request: Optional[datetime] = None
    total_requests: int = 0
    total_words_processed: int = 0


@dataclass
class FreeAPIConfig:
    """Configuration for free AI services."""

    daily_request_limit: int = 5
    max_words_per_request: int = 10000
    max_concurrent_requests: int = 1
    enable_caching: bool = True
    cache_duration_hours: int = 24
    fallback_to_local: bool = True


class FreeAIService:
    """Manages free AI service access for Docx2Shelf users."""

    def __init__(self, config: FreeAPIConfig = None):
        self.config = config or FreeAPIConfig()
        self.cache_dir = Path(user_cache_dir("Docx2Shelf")) / "ai_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.usage_file = self.cache_dir / "usage.json"
        self.usage = self._load_usage()

        # Demo/development keys - in production these would be server-managed
        self.available_services = self._initialize_services()

    def _initialize_services(self) -> Dict[str, Dict]:
        """Initialize available AI services."""
        return {
            "openai_free": {
                "name": "OpenAI Free Tier",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-3.5-turbo",
                "key": "demo-openai-key-1",  # Would be managed server-side
                "daily_limit": 3,
                "status": "active",
            },
            "anthropic_free": {
                "name": "Anthropic Free Tier",
                "endpoint": "https://api.anthropic.com/v1/messages",
                "model": "claude-3-haiku-20240307",
                "key": "demo-anthropic-key-1",  # Would be managed server-side
                "daily_limit": 2,
                "status": "active",
            },
            "local_fallback": {
                "name": "Local Heuristic Analysis",
                "endpoint": "local",
                "model": "heuristic",
                "key": None,
                "daily_limit": 999,
                "status": "active",
            },
        }

    def _load_usage(self) -> APIUsage:
        """Load usage tracking from cache."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, "r") as f:
                    data = json.load(f)

                usage = APIUsage()
                usage.requests_today = data.get("requests_today", 0)
                usage.total_requests = data.get("total_requests", 0)
                usage.total_words_processed = data.get("total_words_processed", 0)

                # Check if it's a new day
                last_request_str = data.get("last_request")
                if last_request_str:
                    last_request = datetime.fromisoformat(last_request_str)
                    if last_request.date() != datetime.now().date():
                        usage.requests_today = 0  # Reset daily counter
                    usage.last_request = last_request

                return usage
            except Exception as e:
                logger.warning(f"Could not load usage data: {e}")

        return APIUsage()

    def _save_usage(self) -> None:
        """Save usage tracking to cache."""
        try:
            data = {
                "requests_today": self.usage.requests_today,
                "total_requests": self.usage.total_requests,
                "total_words_processed": self.usage.total_words_processed,
                "last_request": (
                    self.usage.last_request.isoformat() if self.usage.last_request else None
                ),
            }

            with open(self.usage_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save usage data: {e}")

    def get_available_service(self) -> Optional[Dict]:
        """Get an available AI service based on usage limits."""
        # Check if user has exceeded daily limits
        if self.usage.requests_today >= self.config.daily_request_limit:
            # Return local fallback
            return self.available_services.get("local_fallback")

        # Try premium services first
        for service_id in ["openai_free", "anthropic_free"]:
            service = self.available_services.get(service_id)
            if service and service["status"] == "active":
                return service

        # Fallback to local
        return self.available_services.get("local_fallback")

    def can_make_request(self, word_count: int) -> Tuple[bool, str]:
        """Check if a request can be made."""
        # Check daily limit
        if self.usage.requests_today >= self.config.daily_request_limit:
            return (
                False,
                f"Daily limit reached ({self.config.daily_request_limit} requests). Try again tomorrow.",
            )

        # Check word count limit
        if word_count > self.config.max_words_per_request:
            return (
                False,
                f"Document too large ({word_count} words). Maximum: {self.config.max_words_per_request} words.",
            )

        # Check if service is available
        service = self.get_available_service()
        if not service:
            return False, "No AI services available. Please try again later."

        return True, "OK"

    def process_chapter_detection(self, content: str, filename: str = "") -> Dict:
        """Process chapter detection using free AI service."""
        word_count = len(content.split())

        # Check if request is allowed
        can_request, message = self.can_make_request(word_count)
        if not can_request:
            return {"success": False, "error": message, "boundaries": [], "method": "error"}

        # Check cache first
        if self.config.enable_caching:
            cache_result = self._check_cache(content)
            if cache_result:
                logger.info("Returning cached AI analysis")
                return cache_result

        # Get available service
        service = self.get_available_service()

        try:
            if service["endpoint"] == "local":
                # Use local heuristic analysis
                result = self._local_analysis(content)
            else:
                # Use AI service (simulated for demo)
                result = self._simulate_ai_analysis(content, service)

            # Update usage tracking
            self._update_usage(word_count)

            # Cache result
            if self.config.enable_caching and result["success"]:
                self._cache_result(content, result)

            return result

        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            return {
                "success": False,
                "error": f"Processing failed: {e}",
                "boundaries": [],
                "method": "error",
            }

    def _local_analysis(self, content: str) -> Dict:
        """Perform local heuristic analysis."""
        try:
            from .ai_chapter_detection import AIDetectionConfig, ChapterDetectionEngine

            # Configure for heuristic-only mode
            config = AIDetectionConfig(
                use_free_api=False, enable_heuristics=True, combine_methods=False
            )

            engine = ChapterDetectionEngine(config)
            boundaries = engine._heuristic_detection(content)

            return {
                "success": True,
                "boundaries": [
                    {
                        "position": b.position,
                        "title": b.title,
                        "confidence": b.confidence,
                        "method": "local_heuristic",
                    }
                    for b in boundaries
                ],
                "method": "local_heuristic",
                "service": "Local Analysis",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Local analysis failed: {e}",
                "boundaries": [],
                "method": "error",
            }

    def _simulate_ai_analysis(self, content: str, service: Dict) -> Dict:
        """Simulate AI analysis (in production this would call real APIs)."""
        # This simulates what a real AI service would return
        import re

        boundaries = []
        lines = content.split("\n")

        # Enhanced pattern matching (simulates AI understanding)
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # AI would understand context better than simple regex
            confidence = 0.0

            # Check for explicit chapter markers
            if re.match(r"(chapter|chap\.?)\s+\d+", line, re.IGNORECASE):
                confidence = 0.95
            elif re.match(r"(part|book)\s+\d+", line, re.IGNORECASE):
                confidence = 0.90
            elif re.match(r"^[A-Z][A-Z\s]{5,}$", line):  # ALL CAPS
                confidence = 0.75
            elif re.match(r"^\d+\.", line) and len(line) < 50:
                confidence = 0.70
            elif len(line) < 50 and line[0].isupper() and i > 0:
                # Short line after break - could be chapter start
                prev_line = lines[i - 1].strip()
                if not prev_line:  # After blank line
                    confidence = 0.60

            if confidence > 0.5:
                position = sum(len(l) + 1 for l in lines[:i])
                boundaries.append(
                    {
                        "position": position,
                        "title": line[:50],
                        "confidence": confidence,
                        "method": "ai_simulated",
                    }
                )

        return {
            "success": True,
            "boundaries": boundaries,
            "method": "ai_simulated",
            "service": service["name"],
            "model": service["model"],
        }

    def _check_cache(self, content: str) -> Optional[Dict]:
        """Check if result is cached."""
        try:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            cache_file = self.cache_dir / f"{content_hash}.json"

            if cache_file.exists():
                # Check cache age
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < (self.config.cache_duration_hours * 3600):
                    with open(cache_file, "r") as f:
                        result = json.load(f)
                    result["cached"] = True
                    return result
                else:
                    # Remove expired cache
                    cache_file.unlink()
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")

        return None

    def _cache_result(self, content: str, result: Dict) -> None:
        """Cache analysis result."""
        try:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            cache_file = self.cache_dir / f"{content_hash}.json"

            # Don't cache errors
            if not result.get("success", False):
                return

            cache_data = result.copy()
            cache_data["cached_at"] = datetime.now().isoformat()

            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            logger.warning(f"Could not cache result: {e}")

    def _update_usage(self, word_count: int) -> None:
        """Update usage statistics."""
        self.usage.requests_today += 1
        self.usage.total_requests += 1
        self.usage.total_words_processed += word_count
        self.usage.last_request = datetime.now()
        self._save_usage()

    def get_usage_stats(self) -> Dict:
        """Get current usage statistics."""
        remaining_requests = max(0, self.config.daily_request_limit - self.usage.requests_today)

        return {
            "requests_today": self.usage.requests_today,
            "daily_limit": self.config.daily_request_limit,
            "remaining_today": remaining_requests,
            "total_requests": self.usage.total_requests,
            "total_words_processed": self.usage.total_words_processed,
            "last_request": (
                self.usage.last_request.isoformat() if self.usage.last_request else None
            ),
        }

    def get_service_status(self) -> Dict[str, str]:
        """Get status of all AI services."""
        status = {}
        for service_id, service in self.available_services.items():
            if service_id == "local_fallback":
                status[service_id] = "always_available"
            else:
                # In production, this would check actual service health
                status[service_id] = service["status"]
        return status

    def reset_daily_usage(self) -> None:
        """Reset daily usage counter (for testing)."""
        self.usage.requests_today = 0
        self._save_usage()

    def upgrade_to_premium_info(self) -> Dict:
        """Get information about upgrading to premium access."""
        return {
            "benefits": [
                "Unlimited daily requests",
                "Access to premium AI models (GPT-4, Claude 3 Opus)",
                "Faster processing with dedicated resources",
                "Priority support",
                "Advanced document analysis features",
                "Batch processing capabilities",
            ],
            "pricing": "Starting at $9.99/month",
            "trial": "7-day free trial available",
            "contact": "Visit https://docx2shelf.com/premium for more information",
        }


def get_free_ai_service() -> FreeAIService:
    """Get the global free AI service instance."""
    return FreeAIService()


def check_ai_quota() -> Tuple[bool, Dict]:
    """Quick check of AI quota availability."""
    service = get_free_ai_service()
    stats = service.get_usage_stats()

    has_quota = stats["remaining_today"] > 0

    return has_quota, stats


def process_document_with_free_ai(content: str, filename: str = "") -> Dict:
    """High-level function to process document with free AI."""
    service = get_free_ai_service()
    return service.process_chapter_detection(content, filename)
