"""
AI-Powered Metadata Enhancement for Docx2Shelf

Provides intelligent metadata suggestion, enhancement, and validation
using AI analysis of document content.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .ai_integration import get_ai_manager
from .metadata import EpubMetadata
from .utils import prompt_select


@dataclass
class MetadataSuggestion:
    """A single metadata suggestion from AI analysis."""
    field: str
    value: str
    confidence: float
    reasoning: str
    source: str = "ai"  # ai, rule-based, user, existing


@dataclass
class EnhancedMetadata:
    """Enhanced metadata with AI suggestions."""
    original: EpubMetadata
    suggestions: List[MetadataSuggestion] = field(default_factory=list)
    ai_analysis: Dict[str, Any] = field(default_factory=dict)
    applied_suggestions: Set[str] = field(default_factory=set)

    def get_suggestions_for_field(self, field: str) -> List[MetadataSuggestion]:
        """Get all suggestions for a specific field."""
        return [s for s in self.suggestions if s.field == field]

    def get_best_suggestion(self, field: str) -> Optional[MetadataSuggestion]:
        """Get the best suggestion for a field (highest confidence)."""
        field_suggestions = self.get_suggestions_for_field(field)
        if not field_suggestions:
            return None
        return max(field_suggestions, key=lambda s: s.confidence)

    def apply_suggestion(self, suggestion: MetadataSuggestion) -> bool:
        """Apply a suggestion to the metadata."""
        try:
            if hasattr(self.original, suggestion.field):
                setattr(self.original, suggestion.field, suggestion.value)
                self.applied_suggestions.add(suggestion.field)
                return True
        except Exception:
            pass
        return False


class AIMetadataEnhancer:
    """AI-powered metadata enhancement system."""

    def __init__(self):
        self.ai_manager = get_ai_manager()
        self.logger = logging.getLogger(__name__)

    def enhance_metadata(
        self,
        content: str,
        original_metadata: EpubMetadata,
        interactive: bool = False
    ) -> EnhancedMetadata:
        """Enhance metadata using AI analysis.

        Args:
            content: Document content for analysis
            original_metadata: Original metadata
            interactive: Whether to prompt user for selections

        Returns:
            Enhanced metadata with suggestions
        """
        print("🤖 Analyzing content for metadata enhancement...")

        enhanced = EnhancedMetadata(original=original_metadata)

        if not self.ai_manager.is_available():
            print("⚠️  AI features not available - using basic analysis")
            return self._enhance_basic(content, enhanced)

        try:
            # Get AI analysis
            ai_result = self.ai_manager.enhance_metadata(
                content,
                self._metadata_to_dict(original_metadata)
            )

            if ai_result.success:
                enhanced.ai_analysis = ai_result.data
                self._process_ai_results(enhanced, ai_result.data)

                if interactive:
                    self._interactive_enhancement(enhanced)
                else:
                    self._auto_apply_high_confidence(enhanced)

                print(f"✅ Metadata enhanced with {len(enhanced.suggestions)} suggestions")
            else:
                print(f"⚠️  AI analysis failed: {ai_result.error_message}")
                enhanced = self._enhance_basic(content, enhanced)

        except Exception as e:
            self.logger.error(f"Metadata enhancement error: {e}")
            enhanced = self._enhance_basic(content, enhanced)

        return enhanced

    def _metadata_to_dict(self, metadata: EpubMetadata) -> Dict[str, Any]:
        """Convert metadata to dictionary for AI analysis."""
        return {
            'title': metadata.title,
            'author': metadata.author,
            'description': metadata.description,
            'language': metadata.language,
            'keywords': getattr(metadata, 'keywords', []),
            'genre': getattr(metadata, 'genre', ''),
            'series_name': getattr(metadata, 'series_name', ''),
            'publication_date': getattr(metadata, 'publication_date', ''),
        }

    def _process_ai_results(self, enhanced: EnhancedMetadata, ai_data: Dict[str, Any]):
        """Process AI analysis results into suggestions."""
        # Title suggestions
        for title in ai_data.get('title_suggestions', []):
            if title and title != enhanced.original.title:
                enhanced.suggestions.append(MetadataSuggestion(
                    field='title',
                    value=title,
                    confidence=0.7,
                    reasoning="AI analysis of content structure and narrative",
                    source='ai'
                ))

        # Description suggestions
        for desc in ai_data.get('description_suggestions', []):
            if desc and desc != enhanced.original.description:
                enhanced.suggestions.append(MetadataSuggestion(
                    field='description',
                    value=desc,
                    confidence=0.8,
                    reasoning="Generated from content analysis",
                    source='ai'
                ))

        # Genre suggestions
        for genre in ai_data.get('genre_suggestions', []):
            if genre:
                enhanced.suggestions.append(MetadataSuggestion(
                    field='genre',
                    value=genre,
                    confidence=0.6,
                    reasoning="Detected from content themes and keywords",
                    source='ai'
                ))

        # Keyword suggestions
        keywords = ai_data.get('keyword_suggestions', [])
        if keywords:
            # Combine keywords into a comma-separated string
            keyword_str = ', '.join(keywords[:10])  # Top 10 keywords
            enhanced.suggestions.append(MetadataSuggestion(
                field='keywords',
                value=keyword_str,
                confidence=0.7,
                reasoning="Extracted from content analysis",
                source='ai'
            ))

        # Reading level and additional metadata
        reading_level = ai_data.get('reading_level')
        if reading_level and reading_level != 'unknown':
            enhanced.suggestions.append(MetadataSuggestion(
                field='reading_level',
                value=reading_level,
                confidence=0.8,
                reasoning="Calculated from text complexity metrics",
                source='ai'
            ))

        # Word count and reading time
        word_count = ai_data.get('word_count', 0)
        if word_count > 0:
            enhanced.suggestions.append(MetadataSuggestion(
                field='word_count',
                value=str(word_count),
                confidence=0.9,
                reasoning="Counted from document content",
                source='ai'
            ))

        reading_time = ai_data.get('estimated_reading_time', 0)
        if reading_time > 0:
            enhanced.suggestions.append(MetadataSuggestion(
                field='estimated_reading_time',
                value=f"{reading_time} minutes",
                confidence=0.9,
                reasoning="Estimated based on word count",
                source='ai'
            ))

    def _interactive_enhancement(self, enhanced: EnhancedMetadata):
        """Interactive metadata enhancement with user choices."""
        print("\n📝 AI Metadata Suggestions")
        print("=" * 30)

        # Group suggestions by field
        fields_with_suggestions = {}
        for suggestion in enhanced.suggestions:
            if suggestion.field not in fields_with_suggestions:
                fields_with_suggestions[suggestion.field] = []
            fields_with_suggestions[suggestion.field].append(suggestion)

        for field, suggestions in fields_with_suggestions.items():
            print(f"\n📋 {field.replace('_', ' ').title()}:")

            current_value = getattr(enhanced.original, field, '')
            if current_value:
                print(f"   Current: {current_value}")

            # Show suggestions
            options = []
            for i, suggestion in enumerate(suggestions):
                confidence_icon = "🟢" if suggestion.confidence >= 0.8 else "🟡" if suggestion.confidence >= 0.6 else "🔴"
                print(f"   {i+1}. {confidence_icon} {suggestion.value}")
                print(f"      Confidence: {suggestion.confidence:.1%}")
                print(f"      Reason: {suggestion.reasoning}")
                options.append(f"{suggestion.value[:50]}...")

            # Add keep current option
            options.append("Keep current value")
            options.append("Skip this field")

            print()
            choice = prompt_select(f"Choose {field}", options)

            if choice < len(suggestions):
                # Apply selected suggestion
                enhanced.apply_suggestion(suggestions[choice])
                print(f"✅ Applied: {suggestions[choice].value}")
            elif choice == len(suggestions):
                print("Keeping current value")
            else:
                print("Skipping field")

    def _auto_apply_high_confidence(self, enhanced: EnhancedMetadata):
        """Automatically apply high-confidence suggestions."""
        auto_applied = 0

        for suggestion in enhanced.suggestions:
            # Only auto-apply very high confidence suggestions
            if suggestion.confidence >= 0.9:
                current_value = getattr(enhanced.original, suggestion.field, '')

                # Don't overwrite existing values unless they're empty
                if not current_value:
                    if enhanced.apply_suggestion(suggestion):
                        auto_applied += 1
                        print(f"✅ Auto-applied: {suggestion.field} = {suggestion.value}")

        if auto_applied > 0:
            print(f"📊 Auto-applied {auto_applied} high-confidence suggestions")

    def _enhance_basic(self, content: str, enhanced: EnhancedMetadata) -> EnhancedMetadata:
        """Basic metadata enhancement without AI."""
        print("📊 Performing basic content analysis...")

        # Basic statistics
        words = content.split()
        word_count = len(words)
        estimated_reading_time = max(1, word_count // 250)

        # Add basic suggestions
        enhanced.suggestions.append(MetadataSuggestion(
            field='word_count',
            value=str(word_count),
            confidence=1.0,
            reasoning="Counted from document content",
            source='basic'
        ))

        enhanced.suggestions.append(MetadataSuggestion(
            field='estimated_reading_time',
            value=f"{estimated_reading_time} minutes",
            confidence=1.0,
            reasoning="Estimated based on average reading speed",
            source='basic'
        ))

        # Basic keyword extraction
        keywords = self._extract_basic_keywords(content)
        if keywords:
            enhanced.suggestions.append(MetadataSuggestion(
                field='keywords',
                value=', '.join(keywords[:10]),
                confidence=0.6,
                reasoning="Extracted using frequency analysis",
                source='basic'
            ))

        # Basic genre detection
        genres = self._detect_basic_genre(content)
        for genre in genres[:2]:  # Top 2 genres
            enhanced.suggestions.append(MetadataSuggestion(
                field='genre',
                value=genre,
                confidence=0.5,
                reasoning="Detected using keyword patterns",
                source='basic'
            ))

        return enhanced

    def _extract_basic_keywords(self, content: str) -> List[str]:
        """Basic keyword extraction using frequency analysis."""
        # Simple word frequency analysis
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())

        # Common stop words to filter out
        stop_words = {
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'know', 'want',
            'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here',
            'would', 'there', 'could', 'other', 'make', 'what', 'only', 'over',
            'think', 'also', 'back', 'after', 'first', 'well', 'year', 'work',
            'such', 'where', 'most', 'take', 'than', 'many', 'even', 'more'
        }

        # Count word frequencies
        word_counts = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_counts[word] = word_counts.get(word, 0) + 1

        # Filter and sort
        min_frequency = max(2, len(words) // 1000)  # Minimum frequency based on content length
        keywords = [word for word, count in word_counts.items() if count >= min_frequency]
        keywords.sort(key=lambda w: word_counts[w], reverse=True)

        return keywords[:20]

    def _detect_basic_genre(self, content: str) -> List[str]:
        """Basic genre detection using keyword patterns."""
        genre_keywords = {
            'Fantasy': ['magic', 'wizard', 'dragon', 'spell', 'enchanted', 'kingdom', 'quest'],
            'Romance': ['love', 'heart', 'kiss', 'passion', 'romance', 'relationship'],
            'Mystery': ['detective', 'murder', 'crime', 'investigation', 'suspect', 'clue'],
            'Science Fiction': ['space', 'alien', 'robot', 'technology', 'future', 'planet'],
            'Thriller': ['danger', 'chase', 'escape', 'suspense', 'threat', 'victim'],
            'Horror': ['ghost', 'monster', 'vampire', 'demon', 'haunted', 'nightmare'],
            'Historical': ['war', 'century', 'historical', 'period', 'ancient', 'medieval'],
            'Literary Fiction': ['life', 'character', 'society', 'human', 'emotion', 'family']
        }

        content_lower = content.lower()
        genre_scores = {}

        for genre, keywords in genre_keywords.items():
            score = sum(content_lower.count(keyword) for keyword in keywords)
            if score > 0:
                genre_scores[genre] = score

        # Sort by score and return top genres
        sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
        return [genre for genre, score in sorted_genres if score > 1]

    def generate_metadata_report(self, enhanced: EnhancedMetadata) -> str:
        """Generate a detailed metadata enhancement report."""
        report = []
        report.append("📊 Metadata Enhancement Report")
        report.append("=" * 40)
        report.append("")

        # Original metadata summary
        report.append("📝 Original Metadata:")
        report.append(f"   Title: {enhanced.original.title}")
        report.append(f"   Author: {enhanced.original.author}")
        report.append(f"   Description: {enhanced.original.description or '(none)'}")
        report.append("")

        # AI analysis results
        if enhanced.ai_analysis:
            ai_data = enhanced.ai_analysis
            report.append("🤖 AI Analysis Results:")
            report.append(f"   Word Count: {ai_data.get('word_count', 'N/A')}")
            report.append(f"   Reading Time: {ai_data.get('estimated_reading_time', 'N/A')} minutes")
            report.append(f"   Reading Level: {ai_data.get('reading_level', 'N/A')}")
            report.append(f"   Model Used: {ai_data.get('model_used', 'N/A')}")
            report.append("")

        # Suggestions summary
        report.append("💡 Suggestions Summary:")
        suggestions_by_field = {}
        for suggestion in enhanced.suggestions:
            if suggestion.field not in suggestions_by_field:
                suggestions_by_field[suggestion.field] = []
            suggestions_by_field[suggestion.field].append(suggestion)

        for field, suggestions in suggestions_by_field.items():
            report.append(f"   {field.replace('_', ' ').title()}:")
            for suggestion in suggestions:
                status = "✅ Applied" if field in enhanced.applied_suggestions else "⏳ Suggested"
                confidence_icon = "🟢" if suggestion.confidence >= 0.8 else "🟡" if suggestion.confidence >= 0.6 else "🔴"
                report.append(f"     {status} {confidence_icon} {suggestion.value[:50]}...")
                report.append(f"       Confidence: {suggestion.confidence:.1%} | Source: {suggestion.source}")

        report.append("")
        report.append(f"📈 Total Suggestions: {len(enhanced.suggestions)}")
        report.append(f"📋 Applied: {len(enhanced.applied_suggestions)}")

        return "\n".join(report)


def enhance_metadata_with_ai(
    content: str,
    metadata: EpubMetadata,
    interactive: bool = False
) -> EnhancedMetadata:
    """Convenience function to enhance metadata with AI.

    Args:
        content: Document content
        metadata: Original metadata
        interactive: Whether to use interactive mode

    Returns:
        Enhanced metadata with AI suggestions
    """
    enhancer = AIMetadataEnhancer()
    return enhancer.enhance_metadata(content, metadata, interactive)


def suggest_metadata_improvements(
    content: str,
    metadata: EpubMetadata
) -> List[MetadataSuggestion]:
    """Get metadata improvement suggestions.

    Args:
        content: Document content
        metadata: Current metadata

    Returns:
        List of metadata suggestions
    """
    enhanced = enhance_metadata_with_ai(content, metadata, interactive=False)
    return enhanced.suggestions