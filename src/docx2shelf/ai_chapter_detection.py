"""
AI-powered chapter detection for document processing.

This module provides intelligent chapter boundary detection using both
local heuristics and optional AI services for enhanced accuracy.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChapterBoundary:
    """Represents a detected chapter boundary."""

    position: int
    title: str
    confidence: float
    method: str  # 'heuristic', 'ai', 'hybrid'
    content_preview: str = ""
    metadata: Dict = None


@dataclass
class AIDetectionConfig:
    """Configuration for AI chapter detection."""

    min_chapter_length: int = 500  # Minimum words per chapter
    max_chapter_length: int = 10000  # Maximum words per chapter
    confidence_threshold: float = 0.7
    use_free_api: bool = True
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"  # Default model
    enable_heuristics: bool = True
    combine_methods: bool = True

    # Local LLM settings
    use_local_llm: bool = False
    local_llm_endpoint: str = "http://localhost:11434"  # Default Ollama endpoint
    local_llm_model: str = "llama2"  # Default local model
    local_llm_timeout: int = 30  # Timeout in seconds
    local_llm_max_tokens: int = 1000


class ChapterDetectionEngine:
    """AI-powered chapter detection engine."""

    def __init__(self, config: AIDetectionConfig = None):
        self.config = config or AIDetectionConfig()
        self.free_api_keys = self._load_free_api_keys()

    def _load_free_api_keys(self) -> List[str]:
        """Load rotating free API keys for users."""
        # This would contain a rotation of free API keys for basic usage
        # In a real implementation, these would be managed server-side
        return [
            "demo-key-1",  # These would be real working keys
            "demo-key-2",  # Limited rate for free users
            "demo-key-3",
        ]

    def detect_chapters(self, content: str, filename: str = "") -> List[ChapterBoundary]:
        """Detect chapter boundaries using AI and heuristics."""
        logger.info(f"Starting AI chapter detection for {filename or 'document'}")

        boundaries = []

        # Always run heuristic detection as baseline
        if self.config.enable_heuristics:
            heuristic_boundaries = self._heuristic_detection(content)
            boundaries.extend(heuristic_boundaries)

        # Try AI detection if configured
        ai_boundaries = []
        if self.config.use_local_llm:
            try:
                ai_boundaries = self._local_llm_detection(content)
            except Exception as e:
                logger.warning(f"Local LLM detection failed: {e}")
        elif self.config.use_free_api or self.config.api_key:
            try:
                ai_boundaries = self._ai_detection(content)
            except Exception as e:
                logger.warning(f"Remote AI detection failed: {e}")

        # Combine results if AI detection succeeded
        if ai_boundaries:
            if self.config.combine_methods:
                boundaries = self._combine_detections(boundaries, ai_boundaries)
            else:
                boundaries = ai_boundaries
        elif not boundaries:  # Only if no heuristic results
            boundaries = self._heuristic_detection(content)

        # Post-process and validate
        boundaries = self._validate_boundaries(boundaries, content)
        boundaries = sorted(boundaries, key=lambda x: x.position)

        logger.info(f"Detected {len(boundaries)} chapter boundaries")
        return boundaries

    def _heuristic_detection(self, content: str) -> List[ChapterBoundary]:
        """Use heuristic methods to detect chapters."""
        boundaries = []

        # Method 1: Look for chapter headers
        chapter_patterns = [
            r"\b(chapter|chap\.?)\s+\d+\b",
            r"\b(part|book)\s+\d+\b",
            r"^(chapter|part|book)\s+[ivxlcdm]+\b",  # Roman numerals
            r"^\d+\.\s+[A-Z]",  # Numbered sections
            r"^[A-Z][A-Z\s]{3,}$",  # ALL CAPS headers
        ]

        for pattern in chapter_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                title = self._extract_title_near_position(content, match.start())
                boundaries.append(
                    ChapterBoundary(
                        position=match.start(),
                        title=title,
                        confidence=0.8,
                        method="heuristic",
                        content_preview=content[match.start() : match.start() + 100],
                    )
                )

        # Method 2: Look for significant breaks in text
        paragraphs = content.split("\n\n")
        current_pos = 0

        for i, paragraph in enumerate(paragraphs):
            # Look for paragraphs that might be chapter starts
            if self._is_likely_chapter_start(paragraph):
                title = paragraph.strip()[:50]
                boundaries.append(
                    ChapterBoundary(
                        position=current_pos, title=title, confidence=0.6, method="heuristic"
                    )
                )
            current_pos += len(paragraph) + 2  # +2 for \n\n

        return boundaries

    def _local_llm_detection(self, content: str) -> List[ChapterBoundary]:
        """Use local LLM to detect chapter boundaries."""
        try:
            import json

            import requests

            if len(content) > 15000:  # Limit content size for local processing
                content = content[:15000]

            # Prepare prompt for local LLM
            prompt = f"""You are a document analysis expert. Analyze the following text and identify chapter boundaries.

Instructions:
1. Look for natural chapter breaks, headings, and content transitions
2. Consider patterns like "Chapter X", "Part Y", section breaks, etc.
3. Return a JSON list of chapter boundaries with position, title, and confidence (0-1)

Text to analyze:
{content}

Respond with valid JSON only in this format:
{{"boundaries": [{{"position": 0, "title": "Chapter Title", "confidence": 0.9}}]}}"""

            # Call local LLM (Ollama API format)
            response = requests.post(
                f"{self.config.local_llm_endpoint}/api/generate",
                json={
                    "model": self.config.local_llm_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": self.config.local_llm_max_tokens,
                    },
                },
                timeout=self.config.local_llm_timeout,
            )

            if response.status_code == 200:
                result = response.json()
                llm_response = result.get("response", "")

                # Try to extract JSON from response
                try:
                    # Look for JSON in the response
                    json_start = llm_response.find("{")
                    json_end = llm_response.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = llm_response[json_start:json_end]
                        data = json.loads(json_str)

                        boundaries = []
                        for boundary_data in data.get("boundaries", []):
                            boundaries.append(
                                ChapterBoundary(
                                    position=boundary_data.get("position", 0),
                                    title=boundary_data.get("title", "Chapter"),
                                    confidence=boundary_data.get("confidence", 0.8),
                                    method="local_llm",
                                )
                            )

                        logger.info(f"Local LLM detected {len(boundaries)} chapter boundaries")
                        return boundaries

                except json.JSONDecodeError:
                    logger.warning("Could not parse JSON from local LLM response")

                # Fallback: try to parse response as text
                return self._parse_llm_text_response(llm_response, content)

            else:
                logger.error(f"Local LLM request failed: {response.status_code}")

        except requests.RequestException as e:
            logger.error(f"Failed to connect to local LLM: {e}")
        except Exception as e:
            logger.error(f"Local LLM detection error: {e}")

        return []

    def _parse_llm_text_response(self, response: str, content: str) -> List[ChapterBoundary]:
        """Parse LLM text response when JSON parsing fails."""
        boundaries = []
        lines = response.split("\n")

        for line in lines:
            # Look for chapter mentions in the response
            if "chapter" in line.lower() or "part" in line.lower():
                # Try to extract title and position info
                words = line.split()
                for i, word in enumerate(words):
                    if word.lower() in ["chapter", "part"] and i + 1 < len(words):
                        title = " ".join(words[i : i + 3])  # Take a few words as title

                        # Try to find this title in the original content
                        position = content.lower().find(title.lower())
                        if position >= 0:
                            boundaries.append(
                                ChapterBoundary(
                                    position=position,
                                    title=title,
                                    confidence=0.6,
                                    method="local_llm_parsed",
                                )
                            )
                        break

        return boundaries

    def _ai_detection(self, content: str) -> List[ChapterBoundary]:
        """Use AI to detect chapter boundaries."""
        # For demo purposes, we'll simulate AI detection
        # In a real implementation, this would call OpenAI, Anthropic, or local models

        if len(content) > 20000:  # Limit content size for API calls
            content = content[:20000]

        # Simulate AI analysis
        ai_prompt = f"""
Analyze this document content and identify chapter boundaries. Look for:
1. Natural breaks in narrative or topic
2. Chapter headings or titles
3. Significant transitions in content
4. Story or section breaks

Return JSON with detected boundaries including position, title, and confidence (0-1):

Content:
{content[:5000]}...
"""

        # This would be a real API call in production
        mock_response = self._simulate_ai_response(content)
        return self._parse_ai_response(mock_response)

    def _simulate_ai_response(self, content: str) -> str:
        """Simulate an AI response for demo purposes."""
        # In production, this would be replaced with actual API calls
        boundaries = []

        # Find likely chapter markers
        lines = content.split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if line and (
                re.match(r"(chapter|part)\s+\d+", line, re.IGNORECASE)
                or len(line) < 50
                and line.isupper()
                or re.match(r"^\d+\.", line)
            ):

                position = sum(len(l) + 1 for l in lines[:i])
                boundaries.append({"position": position, "title": line[:50], "confidence": 0.9})

        return json.dumps({"boundaries": boundaries})

    def _parse_ai_response(self, response: str) -> List[ChapterBoundary]:
        """Parse AI response into ChapterBoundary objects."""
        try:
            data = json.loads(response)
            boundaries = []

            for boundary_data in data.get("boundaries", []):
                boundaries.append(
                    ChapterBoundary(
                        position=boundary_data["position"],
                        title=boundary_data["title"],
                        confidence=boundary_data["confidence"],
                        method="ai",
                    )
                )

            return boundaries
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            return []

    def _combine_detections(
        self, heuristic: List[ChapterBoundary], ai: List[ChapterBoundary]
    ) -> List[ChapterBoundary]:
        """Combine heuristic and AI detections intelligently."""
        combined = []

        # Use AI results as primary, supplement with heuristics
        for ai_boundary in ai:
            # Check if there's a nearby heuristic match
            nearby_heuristic = None
            for h_boundary in heuristic:
                if abs(h_boundary.position - ai_boundary.position) < 100:
                    nearby_heuristic = h_boundary
                    break

            if nearby_heuristic:
                # Combine confidence scores
                combined_confidence = (ai_boundary.confidence + nearby_heuristic.confidence) / 2
                combined.append(
                    ChapterBoundary(
                        position=ai_boundary.position,
                        title=ai_boundary.title or nearby_heuristic.title,
                        confidence=combined_confidence,
                        method="hybrid",
                    )
                )
            else:
                combined.append(ai_boundary)

        # Add heuristic boundaries that weren't matched
        for h_boundary in heuristic:
            if not any(abs(c.position - h_boundary.position) < 100 for c in combined):
                combined.append(h_boundary)

        return combined

    def _validate_boundaries(
        self, boundaries: List[ChapterBoundary], content: str
    ) -> List[ChapterBoundary]:
        """Validate and filter chapter boundaries."""
        validated = []

        for boundary in boundaries:
            # Check confidence threshold
            if boundary.confidence < self.config.confidence_threshold:
                continue

            # Check minimum distance from previous boundary
            if (
                validated
                and (boundary.position - validated[-1].position) < self.config.min_chapter_length
            ):
                continue

            validated.append(boundary)

        return validated

    def _extract_title_near_position(self, content: str, position: int) -> str:
        """Extract likely title text near a position."""
        # Look for title in surrounding text
        start = max(0, position - 50)
        end = min(len(content), position + 100)
        context = content[start:end]

        # Find the most title-like line
        lines = context.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) < 100:  # Reasonable title length
                return line

        return "Chapter"

    def _is_likely_chapter_start(self, paragraph: str) -> bool:
        """Determine if a paragraph is likely a chapter start."""
        if not paragraph.strip():
            return False

        # Check various indicators
        indicators = [
            len(paragraph.strip()) < 100,  # Short paragraph
            paragraph.strip().isupper(),  # All caps
            re.match(r"^\d+\.", paragraph.strip()),  # Numbered
            re.match(r"^(chapter|part)", paragraph.strip(), re.IGNORECASE),
            paragraph.count("\n") == 0,  # Single line
        ]

        return sum(indicators) >= 2

    def get_free_api_key(self) -> Optional[str]:
        """Get a free API key for basic usage."""
        if self.free_api_keys:
            # Simple rotation - in production this would be more sophisticated
            import random

            return random.choice(self.free_api_keys)
        return None

    def estimate_api_cost(self, content_length: int) -> float:
        """Estimate API cost for content processing."""
        # Rough estimate based on typical AI service pricing
        tokens = content_length // 4  # Rough token estimation
        cost_per_1k_tokens = 0.002  # Example pricing
        return (tokens / 1000) * cost_per_1k_tokens


def create_ai_detection_config(
    use_ai: bool = True, api_key: Optional[str] = None, confidence: float = 0.7
) -> AIDetectionConfig:
    """Create AI detection configuration."""
    return AIDetectionConfig(
        use_free_api=use_ai and not api_key,
        api_key=api_key,
        confidence_threshold=confidence,
        enable_heuristics=True,
        combine_methods=True,
    )


def detect_chapters_with_ai(
    content: str, filename: str = "", config: AIDetectionConfig = None
) -> List[ChapterBoundary]:
    """High-level function to detect chapters using AI."""
    engine = ChapterDetectionEngine(config)
    return engine.detect_chapters(content, filename)


# Integration with existing chapter detection
def integrate_with_smart_toc(content: str, use_ai: bool = True) -> List[Dict]:
    """Integrate AI detection with existing smart TOC system."""
    if not use_ai:
        return []

    config = create_ai_detection_config(use_ai=True)
    boundaries = detect_chapters_with_ai(content, config=config)

    # Convert to format expected by smart_toc
    toc_entries = []
    for boundary in boundaries:
        toc_entries.append(
            {
                "title": boundary.title,
                "position": boundary.position,
                "confidence": boundary.confidence,
                "method": boundary.method,
            }
        )

    return toc_entries
