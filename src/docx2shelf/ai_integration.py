"""
AI Integration Framework for Docx2Shelf

Provides AI-powered features for metadata enhancement, genre detection,
keyword generation, and accessibility improvements.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional AI dependencies - graceful fallback if not available
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from PIL import Image

    PILLOW_AVAILABLE = True
except (ImportError, AttributeError):
    PILLOW_AVAILABLE = False

from .utils import prompt_bool


@dataclass
class AIConfig:
    """Configuration for AI features."""

    enabled: bool = True
    openai_api_key: Optional[str] = None
    use_local_models: bool = True
    cache_enabled: bool = True
    cache_dir: Optional[Path] = None
    max_retries: int = 3
    timeout: int = 30
    model_type: str = "local"  # "local", "openai", "huggingface"
    local_model: str = "gpt2"  # Default local model
    enable_caching: bool = True  # Alias for cache_enabled
    model_preferences: Dict[str, str] = field(
        default_factory=lambda: {
            "text_classification": "distilbert-base-uncased-finetuned-sst-2-english",
            "text_generation": "gpt2",
            "image_to_text": "nlpconnect/vit-gpt2-image-captioning",
        }
    )

    def __post_init__(self):
        """Ensure compatibility with different attribute names."""
        # Sync cache_enabled and enable_caching
        if hasattr(self, "cache_enabled") and hasattr(self, "enable_caching"):
            if self.cache_enabled != self.enable_caching:
                self.enable_caching = self.cache_enabled


@dataclass
class AIResult:
    """Result from an AI operation."""

    success: bool
    data: Any
    confidence: float = 0.0
    model_used: str = ""
    processing_time: float = 0.0
    error_message: str = ""
    cached: bool = False


class AIModelManager:
    """Manages AI models and provides caching."""

    def __init__(self, config: AIConfig):
        self.config = config

        # Use platformdirs for cache directory if available
        if config.cache_dir:
            self.cache_dir = config.cache_dir
        else:
            try:
                from .path_utils import get_user_cache_dir

                self.cache_dir = get_user_cache_dir("docx2shelf") / "ai_cache"
            except ImportError:
                # Fallback
                self.cache_dir = Path.home() / ".docx2shelf" / "ai_cache"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.models = {}
        self.logger = logging.getLogger(__name__)

    def get_model(self, model_type: str, model_name: Optional[str] = None) -> Optional[Any]:
        """Get or load a model.

        Args:
            model_type: Type of model (text_classification, text_generation, etc.)
            model_name: Specific model name (optional)

        Returns:
            Loaded model or None if not available
        """
        if not TRANSFORMERS_AVAILABLE:
            return None

        model_name = model_name or self.config.model_preferences.get(model_type)
        if not model_name:
            return None

        cache_key = f"{model_type}_{model_name}"

        if cache_key in self.models:
            return self.models[cache_key]

        try:
            if model_type == "text_classification":
                model = pipeline("text-classification", model=model_name)
            elif model_type == "text_generation":
                model = pipeline("text-generation", model=model_name)
            elif model_type == "image_to_text":
                model = pipeline("image-to-text", model=model_name)
            else:
                self.logger.warning(f"Unknown model type: {model_type}")
                return None

            self.models[cache_key] = model
            return model

        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            return None

    def get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        # Use hash to create safe filename
        safe_key = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.json"

    def get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached result if available."""
        if not self.config.cache_enabled:
            return None

        cache_file = self.get_cache_path(cache_key)
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load cache: {e}")

        return None

    def save_to_cache(self, cache_key: str, result: Dict):
        """Save result to cache."""
        if not self.config.cache_enabled:
            return

        cache_file = self.get_cache_path(cache_key)
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")


class MetadataEnhancer:
    """AI-powered metadata enhancement."""

    def __init__(self, model_manager: AIModelManager):
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)

    def enhance_metadata(self, content: str, existing_metadata: Dict[str, Any]) -> AIResult:
        """Enhance metadata using AI analysis.

        Args:
            content: Document content for analysis
            existing_metadata: Current metadata

        Returns:
            AIResult with enhanced metadata suggestions
        """
        import time

        start_time = time.time()

        # Create cache key
        content_hash = hashlib.md5(content.encode()).hexdigest()
        cache_key = f"metadata_enhancement_{content_hash}"

        # Check cache first
        cached = self.model_manager.get_cached_result(cache_key)
        if cached:
            return AIResult(
                success=True,
                data=cached,
                confidence=cached.get("confidence", 0.8),
                model_used=cached.get("model_used", "cached"),
                processing_time=time.time() - start_time,
                cached=True,
            )

        try:
            # Extract key information from content
            enhanced = self._analyze_content_for_metadata(content, existing_metadata)

            result_data = {
                "title_suggestions": enhanced.get("title_suggestions", []),
                "description_suggestions": enhanced.get("description_suggestions", []),
                "keyword_suggestions": enhanced.get("keyword_suggestions", []),
                "genre_suggestions": enhanced.get("genre_suggestions", []),
                "reading_level": enhanced.get("reading_level", "unknown"),
                "word_count": enhanced.get("word_count", 0),
                "estimated_reading_time": enhanced.get("estimated_reading_time", 0),
                "confidence": enhanced.get("confidence", 0.7),
                "model_used": enhanced.get("model_used", "rule-based"),
            }

            # Save to cache
            self.model_manager.save_to_cache(cache_key, result_data)

            return AIResult(
                success=True,
                data=result_data,
                confidence=result_data["confidence"],
                model_used=result_data["model_used"],
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            self.logger.error(f"Metadata enhancement failed: {e}")
            return AIResult(
                success=False,
                data={},
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def _analyze_content_for_metadata(self, content: str, existing_metadata: Dict) -> Dict:
        """Analyze content to extract metadata insights."""
        # Basic text analysis
        words = content.split()
        word_count = len(words)
        estimated_reading_time = max(1, word_count // 250)  # ~250 words per minute

        # Extract potential titles from first paragraphs
        title_suggestions = self._extract_title_suggestions(
            content, existing_metadata.get("title", "")
        )

        # Generate description from content
        description_suggestions = self._generate_description_suggestions(content)

        # Extract keywords
        keyword_suggestions = self._extract_keywords(content)

        # Basic genre detection
        genre_suggestions = self._detect_genre_basic(content)

        # Estimate reading level
        reading_level = self._estimate_reading_level(content)

        return {
            "title_suggestions": title_suggestions,
            "description_suggestions": description_suggestions,
            "keyword_suggestions": keyword_suggestions,
            "genre_suggestions": genre_suggestions,
            "reading_level": reading_level,
            "word_count": word_count,
            "estimated_reading_time": estimated_reading_time,
            "confidence": 0.7,
            "model_used": "rule-based-analysis",
        }

    def _extract_title_suggestions(self, content: str, current_title: str) -> List[str]:
        """Extract potential title suggestions from content."""
        suggestions = []

        # Look for chapter titles or headings
        lines = content.split("\n")
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if line and len(line) < 100:
                # Check if it looks like a title
                if (
                    line.isupper()
                    or line.startswith("Chapter")
                    or line.startswith("Part")
                    or (len(line.split()) <= 8 and not line.endswith("."))
                ):

                    cleaned = re.sub(r"^(Chapter|Part)\s*\d+:?\s*", "", line, flags=re.IGNORECASE)
                    if cleaned and cleaned != current_title:
                        suggestions.append(cleaned.strip())

        # Add current title variations
        if current_title:
            # Remove common suffixes/prefixes
            clean_title = re.sub(r"^(The|A|An)\s+", "", current_title)
            if clean_title != current_title:
                suggestions.append(clean_title)

        return suggestions[:5]  # Return top 5 suggestions

    def _generate_description_suggestions(self, content: str) -> List[str]:
        """Generate description suggestions from content."""
        # Extract first few sentences as potential description
        sentences = re.split(r"[.!?]+", content)
        clean_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

        suggestions = []

        if clean_sentences:
            # First sentence
            if len(clean_sentences[0]) <= 200:
                suggestions.append(clean_sentences[0])

            # First two sentences
            if len(clean_sentences) > 1:
                two_sentences = f"{clean_sentences[0]}. {clean_sentences[1]}"
                if len(two_sentences) <= 300:
                    suggestions.append(two_sentences)

            # First paragraph summary
            first_paragraph = content.split("\n\n")[0] if "\n\n" in content else content[:500]
            if len(first_paragraph) <= 400 and first_paragraph not in suggestions:
                suggestions.append(first_paragraph)

        return suggestions[:3]

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords from content."""
        # Simple keyword extraction using frequency and relevance
        words = re.findall(r"\b[a-zA-Z]{3,}\b", content.lower())

        # Filter out common words
        stop_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "man",
            "new",
            "now",
            "old",
            "see",
            "two",
            "way",
            "who",
            "boy",
            "did",
            "its",
            "let",
            "put",
            "say",
            "she",
            "too",
            "use",
            "with",
            "have",
            "this",
            "will",
            "your",
            "they",
            "said",
            "each",
            "which",
            "their",
            "time",
            "would",
            "there",
            "could",
            "other",
            "after",
            "first",
            "never",
            "these",
            "think",
            "where",
            "being",
            "every",
            "great",
            "might",
            "shall",
            "still",
            "those",
            "under",
            "while",
            "should",
            "through",
        }

        # Count word frequencies
        word_counts = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency and return top keywords
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:20] if count > 2]

    def _detect_genre_basic(self, content: str) -> List[str]:
        """Basic genre detection using keyword patterns."""
        genre_keywords = {
            "fantasy": [
                "magic",
                "wizard",
                "dragon",
                "spell",
                "enchanted",
                "kingdom",
                "quest",
                "sword",
                "mystical",
            ],
            "romance": [
                "love",
                "heart",
                "kiss",
                "passion",
                "romance",
                "relationship",
                "wedding",
                "marriage",
            ],
            "mystery": [
                "detective",
                "murder",
                "crime",
                "investigation",
                "suspect",
                "clue",
                "mystery",
                "police",
            ],
            "science_fiction": [
                "space",
                "alien",
                "robot",
                "technology",
                "future",
                "planet",
                "spaceship",
                "galaxy",
            ],
            "thriller": [
                "danger",
                "chase",
                "escape",
                "suspense",
                "threat",
                "victim",
                "conspiracy",
                "terror",
            ],
            "horror": [
                "ghost",
                "monster",
                "vampire",
                "demon",
                "haunted",
                "nightmare",
                "death",
                "evil",
            ],
            "historical": [
                "war",
                "century",
                "historical",
                "period",
                "ancient",
                "medieval",
                "revolution",
            ],
            "literary": [
                "life",
                "character",
                "society",
                "human",
                "emotion",
                "relationship",
                "experience",
            ],
        }

        content_lower = content.lower()
        genre_scores = {}

        for genre, keywords in genre_keywords.items():
            score = sum(content_lower.count(keyword) for keyword in keywords)
            if score > 0:
                genre_scores[genre] = score

        # Sort by score and return top genres
        sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
        return [genre.replace("_", " ").title() for genre, score in sorted_genres[:3]]

    def _estimate_reading_level(self, content: str) -> str:
        """Estimate reading level using basic text metrics."""
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return "unknown"

        # Calculate averages
        total_words = 0
        total_syllables = 0

        for sentence in sentences:
            words = sentence.split()
            total_words += len(words)
            for word in words:
                total_syllables += self._count_syllables(word)

        if len(sentences) == 0 or total_words == 0:
            return "unknown"

        avg_sentence_length = total_words / len(sentences)
        avg_syllables_per_word = total_syllables / total_words

        # Simple reading level estimation
        if avg_sentence_length < 15 and avg_syllables_per_word < 1.5:
            return "elementary"
        elif avg_sentence_length < 20 and avg_syllables_per_word < 1.7:
            return "middle_school"
        elif avg_sentence_length < 25 and avg_syllables_per_word < 2.0:
            return "high_school"
        else:
            return "college"

    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count for a word."""
        word = word.lower().strip()
        if not word:
            return 0

        # Simple syllable counting heuristic
        vowels = "aeiouy"
        syllable_count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel

        # Handle silent e
        if word.endswith("e") and syllable_count > 1:
            syllable_count -= 1

        return max(1, syllable_count)


class GenreDetector:
    """Advanced genre detection using AI models."""

    def __init__(self, model_manager: AIModelManager):
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)

    def detect_genre(self, content: str, metadata: Dict[str, Any]) -> AIResult:
        """Detect genre using AI analysis.

        Args:
            content: Document content
            metadata: Existing metadata

        Returns:
            AIResult with genre detection results
        """
        import time

        start_time = time.time()

        # Create cache key
        content_hash = hashlib.md5(content.encode()).hexdigest()
        cache_key = f"genre_detection_{content_hash}"

        # Check cache
        cached = self.model_manager.get_cached_result(cache_key)
        if cached:
            return AIResult(
                success=True,
                data=cached,
                confidence=cached.get("confidence", 0.8),
                model_used=cached.get("model_used", "cached"),
                processing_time=time.time() - start_time,
                cached=True,
            )

        try:
            # Try AI model first
            ai_result = self._detect_with_ai_model(content)

            if not ai_result["success"]:
                # Fallback to rule-based detection
                ai_result = self._detect_with_rules(content)

            # Save to cache
            self.model_manager.save_to_cache(cache_key, ai_result)

            return AIResult(
                success=ai_result["success"],
                data=ai_result,
                confidence=ai_result.get("confidence", 0.7),
                model_used=ai_result.get("model_used", "unknown"),
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            self.logger.error(f"Genre detection failed: {e}")
            return AIResult(
                success=False,
                data={},
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def _detect_with_ai_model(self, content: str) -> Dict:
        """Use AI model for genre detection."""
        model = self.model_manager.get_model("text_classification")

        if not model:
            return {"success": False, "reason": "model_unavailable"}

        try:
            # Take a sample of the content for analysis
            sample = content[:2000]  # First 2000 characters

            # Note: This is a simplified example - in practice, you'd want
            # a model specifically trained for genre classification
            result = model(sample)

            if result:
                # Map classification results to genres
                # This is a simplified mapping - real implementation would need
                # proper genre classification model
                confidence = result[0].get("score", 0.5)
                label = result[0].get("label", "unknown")

                # Map generic sentiment labels to potential genres
                genre_mapping = {
                    "POSITIVE": "romance",
                    "NEGATIVE": "thriller",
                    "NEUTRAL": "literary",
                }

                detected_genre = genre_mapping.get(label, "general")

                return {
                    "success": True,
                    "primary_genre": detected_genre,
                    "confidence": confidence,
                    "secondary_genres": [],
                    "model_used": "transformers_classification",
                }

        except Exception as e:
            self.logger.warning(f"AI model detection failed: {e}")

        return {"success": False, "reason": "model_error"}

    def _detect_with_rules(self, content: str) -> Dict:
        """Fallback rule-based genre detection."""
        # Enhanced rule-based detection
        genre_patterns = {
            "fantasy": {
                "keywords": [
                    "magic",
                    "wizard",
                    "dragon",
                    "spell",
                    "enchanted",
                    "kingdom",
                    "quest",
                    "sword",
                    "mystical",
                    "fairy",
                    "elf",
                    "dwarf",
                ],
                "weight": 1.0,
            },
            "romance": {
                "keywords": [
                    "love",
                    "heart",
                    "kiss",
                    "passion",
                    "romance",
                    "relationship",
                    "wedding",
                    "marriage",
                    "beloved",
                    "darling",
                ],
                "weight": 1.0,
            },
            "mystery": {
                "keywords": [
                    "detective",
                    "murder",
                    "crime",
                    "investigation",
                    "suspect",
                    "clue",
                    "mystery",
                    "police",
                    "evidence",
                    "witness",
                ],
                "weight": 1.0,
            },
            "science_fiction": {
                "keywords": [
                    "space",
                    "alien",
                    "robot",
                    "technology",
                    "future",
                    "planet",
                    "spaceship",
                    "galaxy",
                    "laser",
                    "android",
                ],
                "weight": 1.0,
            },
            "thriller": {
                "keywords": [
                    "danger",
                    "chase",
                    "escape",
                    "suspense",
                    "threat",
                    "victim",
                    "conspiracy",
                    "terror",
                    "hunt",
                    "survival",
                ],
                "weight": 1.0,
            },
            "horror": {
                "keywords": [
                    "ghost",
                    "monster",
                    "vampire",
                    "demon",
                    "haunted",
                    "nightmare",
                    "death",
                    "evil",
                    "scream",
                    "blood",
                ],
                "weight": 1.0,
            },
            "historical": {
                "keywords": [
                    "war",
                    "century",
                    "historical",
                    "period",
                    "ancient",
                    "medieval",
                    "revolution",
                    "empire",
                    "colonial",
                ],
                "weight": 1.0,
            },
            "literary": {
                "keywords": [
                    "life",
                    "character",
                    "society",
                    "human",
                    "emotion",
                    "relationship",
                    "experience",
                    "memory",
                    "family",
                ],
                "weight": 0.8,
            },
        }

        content_lower = content.lower()
        genre_scores = {}

        for genre, pattern in genre_patterns.items():
            score = 0
            for keyword in pattern["keywords"]:
                count = content_lower.count(keyword)
                score += count * pattern["weight"]

            if score > 0:
                genre_scores[genre] = score

        if not genre_scores:
            return {
                "success": True,
                "primary_genre": "general",
                "confidence": 0.3,
                "secondary_genres": [],
                "model_used": "rule-based-fallback",
            }

        # Sort and get top genres
        sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)

        primary_genre = sorted_genres[0][0]
        primary_score = sorted_genres[0][1]

        # Calculate confidence based on score relative to content length
        max_possible_score = len(content.split()) * 0.1  # Rough estimate
        confidence = min(0.9, primary_score / max_possible_score)

        secondary_genres = [genre for genre, score in sorted_genres[1:3]]

        return {
            "success": True,
            "primary_genre": primary_genre,
            "confidence": confidence,
            "secondary_genres": secondary_genres,
            "model_used": "rule-based",
        }


class ImageAltTextGenerator:
    """AI-powered alt-text generation for images."""

    def __init__(self, model_manager: AIModelManager):
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)

    def generate_alt_text(self, image_path: Path, context: str = "") -> AIResult:
        """Generate alt-text for an image.

        Args:
            image_path: Path to the image file
            context: Surrounding text context for better descriptions

        Returns:
            AIResult with generated alt-text
        """
        import time

        start_time = time.time()

        if not PILLOW_AVAILABLE:
            return AIResult(
                success=False, data={}, error_message="PIL not available for image processing"
            )

        # Create cache key
        image_hash = self._get_image_hash(image_path)
        context_hash = hashlib.md5(context.encode()).hexdigest()[:8]
        cache_key = f"alt_text_{image_hash}_{context_hash}"

        # Check cache
        cached = self.model_manager.get_cached_result(cache_key)
        if cached:
            return AIResult(
                success=True,
                data=cached,
                confidence=cached.get("confidence", 0.8),
                model_used=cached.get("model_used", "cached"),
                processing_time=time.time() - start_time,
                cached=True,
            )

        try:
            # Try AI model first
            ai_result = self._generate_with_ai_model(image_path, context)

            if not ai_result["success"]:
                # Fallback to rule-based generation
                ai_result = self._generate_with_rules(image_path, context)

            # Save to cache
            self.model_manager.save_to_cache(cache_key, ai_result)

            return AIResult(
                success=ai_result["success"],
                data=ai_result,
                confidence=ai_result.get("confidence", 0.7),
                model_used=ai_result.get("model_used", "unknown"),
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            self.logger.error(f"Alt-text generation failed: {e}")
            return AIResult(
                success=False,
                data={},
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def _get_image_hash(self, image_path: Path) -> str:
        """Get hash of image file for caching."""
        try:
            with open(image_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return hashlib.md5(str(image_path).encode()).hexdigest()

    def _generate_with_ai_model(self, image_path: Path, context: str) -> Dict:
        """Generate alt-text using AI vision model."""
        model = self.model_manager.get_model("image_to_text")

        if not model:
            return {"success": False, "reason": "model_unavailable"}

        try:
            # Load and process image
            image = Image.open(image_path)

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Generate caption
            result = model(image)

            if result and len(result) > 0:
                generated_text = result[0].get("generated_text", "").strip()

                if generated_text:
                    # Enhance with context if available
                    enhanced_text = self._enhance_with_context(generated_text, context)

                    return {
                        "success": True,
                        "alt_text": enhanced_text,
                        "raw_generated": generated_text,
                        "confidence": 0.8,
                        "model_used": "vision_transformer",
                    }

        except Exception as e:
            self.logger.warning(f"AI vision model failed: {e}")

        return {"success": False, "reason": "model_error"}

    def _generate_with_rules(self, image_path: Path, context: str) -> Dict:
        """Fallback rule-based alt-text generation."""
        try:
            # Analyze image properties
            image = Image.open(image_path)
            width, height = image.size
            format_name = image.format or "unknown"

            # Generate basic description based on filename and properties
            filename = image_path.stem

            # Clean filename for description
            clean_name = re.sub(r"[_-]", " ", filename)
            clean_name = re.sub(r"\d+", "", clean_name).strip()

            # Basic description
            if clean_name:
                alt_text = f"Image: {clean_name}"
            else:
                alt_text = "Image"

            # Add context if available
            if context:
                # Look for relevant keywords in context
                context_words = context.lower().split()
                image_keywords = ["figure", "chart", "graph", "photo", "illustration", "diagram"]

                for keyword in image_keywords:
                    if keyword in context_words:
                        alt_text = (
                            f"{keyword.title()}: {clean_name}" if clean_name else keyword.title()
                        )
                        break

            # Add basic image properties for accessibility
            orientation = (
                "landscape" if width > height else "portrait" if height > width else "square"
            )
            size_desc = (
                "large"
                if max(width, height) > 1000
                else "medium" if max(width, height) > 500 else "small"
            )

            enhanced_alt = f"{alt_text} ({size_desc} {orientation} {format_name.lower()} image)"

            return {
                "success": True,
                "alt_text": enhanced_alt,
                "confidence": 0.4,
                "model_used": "rule-based",
                "image_properties": {
                    "width": width,
                    "height": height,
                    "format": format_name,
                    "orientation": orientation,
                    "size_category": size_desc,
                },
            }

        except Exception as e:
            self.logger.error(f"Rule-based alt-text generation failed: {e}")
            return {
                "success": True,
                "alt_text": f"Image: {image_path.name}",
                "confidence": 0.2,
                "model_used": "filename-fallback",
            }

    def _enhance_with_context(self, generated_text: str, context: str) -> str:
        """Enhance generated alt-text with context information."""
        if not context or len(context) < 10:
            return generated_text

        # Look for contextual clues
        context_lower = context.lower()

        # Check if it's a figure, chart, etc.
        if "figure" in context_lower:
            return f"Figure: {generated_text}"
        elif "chart" in context_lower or "graph" in context_lower:
            return f"Chart: {generated_text}"
        elif "diagram" in context_lower:
            return f"Diagram: {generated_text}"
        elif "photo" in context_lower or "photograph" in context_lower:
            return f"Photograph: {generated_text}"

        return generated_text


class AIIntegrationManager:
    """Main manager for all AI integration features."""

    def __init__(self, config: Optional[AIConfig] = None):
        """Initialize the AI integration manager.

        Args:
            config: AI configuration (uses defaults if None)
        """
        self.config = config or AIConfig()
        self.model_manager = AIModelManager(self.config)
        self.metadata_enhancer = MetadataEnhancer(self.model_manager)
        self.genre_detector = GenreDetector(self.model_manager)
        self.alt_text_generator = ImageAltTextGenerator(self.model_manager)
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """Check if AI features are available."""
        return self.config.enabled and (TRANSFORMERS_AVAILABLE or OPENAI_AVAILABLE)

    def get_capabilities(self) -> Dict[str, bool]:
        """Get available AI capabilities."""
        return {
            "metadata_enhancement": self.config.enabled,
            "genre_detection": self.config.enabled,
            "alt_text_generation": self.config.enabled and PILLOW_AVAILABLE,
            "local_models": TRANSFORMERS_AVAILABLE,
            "openai_api": OPENAI_AVAILABLE and bool(self.config.openai_api_key),
            "caching": self.config.cache_enabled,
        }

    def enhance_metadata(self, content: str, metadata: Dict[str, Any]) -> AIResult:
        """Enhance metadata using AI."""
        if not self.config.enabled:
            return AIResult(success=False, data={}, error_message="AI features disabled")

        return self.metadata_enhancer.enhance_metadata(content, metadata)

    def detect_genre(self, content: str, metadata: Dict[str, Any]) -> AIResult:
        """Detect genre using AI."""
        if not self.config.enabled:
            return AIResult(success=False, data={}, error_message="AI features disabled")

        return self.genre_detector.detect_genre(content, metadata)

    def generate_alt_text(self, image_path: Path, context: str = "") -> AIResult:
        """Generate alt-text for images."""
        if not self.config.enabled:
            return AIResult(success=False, data={}, error_message="AI features disabled")

        return self.alt_text_generator.generate_alt_text(image_path, context)

    def configure_interactive(self) -> bool:
        """Interactive configuration of AI features."""
        print("🤖 AI Features Configuration")
        print("=" * 30)

        # Check availability
        capabilities = self.get_capabilities()

        print("Available AI capabilities:")
        for feature, available in capabilities.items():
            status = "✅" if available else "❌"
            print(f"  {status} {feature.replace('_', ' ').title()}")

        print()

        # Enable/disable AI features
        if prompt_bool("Enable AI features?", default=True):
            self.config.enabled = True

            # Configure caching
            if prompt_bool("Enable result caching for faster performance?", default=True):
                self.config.cache_enabled = True

            # Configure models
            if TRANSFORMERS_AVAILABLE:
                if prompt_bool("Use local AI models (recommended for privacy)?", default=True):
                    self.config.use_local_models = True

            # OpenAI configuration
            if OPENAI_AVAILABLE:
                if prompt_bool("Configure OpenAI API for enhanced features?", default=False):
                    api_key = input("Enter OpenAI API key (or press Enter to skip): ").strip()
                    if api_key:
                        self.config.openai_api_key = api_key

            print("✅ AI features configured successfully!")
            return True
        else:
            self.config.enabled = False
            print("AI features disabled.")
            return False


# Global AI manager instance
_ai_manager: Optional[AIIntegrationManager] = None


def get_ai_manager(config: Optional[AIConfig] = None) -> AIIntegrationManager:
    """Get or create the global AI manager instance."""
    global _ai_manager
    if _ai_manager is None:
        _ai_manager = AIIntegrationManager(config)
    return _ai_manager


def is_ai_available() -> bool:
    """Check if AI features are available."""
    return get_ai_manager().is_available()


def configure_ai_interactive() -> bool:
    """Interactive AI configuration."""
    return get_ai_manager().configure_interactive()
