"""
Metadata Enhancer Plugin for Docx2Shelf

This plugin demonstrates metadata resolution capabilities.
It automatically generates and enhances metadata based on content analysis.

Author: Docx2Shelf Team
Version: 1.0.0
License: MIT
"""

import datetime
import re
from typing import Any, Dict, List

from docx2shelf.plugins import BasePlugin, MetadataResolverHook


class MetadataEnhancerPlugin(BasePlugin):
    """Plugin for automatically enhancing EPUB metadata."""

    def __init__(self):
        super().__init__(
            name="metadata_enhancer",
            version="1.0.0"
        )

    def get_hooks(self) -> Dict[str, List]:
        return {
            'metadata_resolver': [MetadataEnhancementHook()]
        }


class MetadataEnhancementHook(MetadataResolverHook):
    """Enhances metadata with auto-generated content."""

    def resolve_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance metadata with automatically generated content.

        Enhancements include:
        - Auto-generated description from content
        - Genre detection
        - Reading time estimation
        - Content warnings detection
        - Language detection
        - Publication date formatting
        """
        try:
            # Get content for analysis
            content = self._get_content_for_analysis(context)

            # Apply various enhancements
            metadata = self._generate_description(metadata, content)
            metadata = self._detect_genre(metadata, content)
            metadata = self._estimate_reading_time(metadata, content)
            metadata = self._detect_content_warnings(metadata, content)
            metadata = self._set_defaults(metadata)
            metadata = self._format_dates(metadata)
            metadata = self._add_processing_info(metadata)

            return metadata

        except Exception as e:
            print(f"Metadata Enhancer warning: {e}")
            return metadata

    def _get_content_for_analysis(self, context: Dict[str, Any]) -> str:
        """Extract content text for analysis."""
        # Try to get content from context
        content = context.get('content_preview', '')
        if not content:
            content = context.get('content', '')

        # Strip HTML tags for text analysis
        if content:
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content).strip()

        return content

    def _generate_description(self, metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Auto-generate description if not provided."""
        if 'description' in metadata and metadata['description']:
            return metadata  # Don't override existing description

        if not content:
            return metadata

        # Extract first meaningful paragraph
        sentences = re.split(r'[.!?]+', content)
        description_parts = []

        for sentence in sentences[:3]:  # Use first 3 sentences
            sentence = sentence.strip()
            if len(sentence) > 20:  # Skip very short sentences
                description_parts.append(sentence)

        if description_parts:
            description = '. '.join(description_parts)
            # Limit length
            if len(description) > 200:
                description = description[:197] + "..."
            metadata['description'] = description

        return metadata

    def _detect_genre(self, metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Detect likely genre based on content."""
        if 'genre' in metadata and metadata['genre']:
            return metadata  # Don't override existing genre

        if not content:
            return metadata

        content_lower = content.lower()

        # Define genre indicators
        genre_indicators = {
            'romance': ['love', 'heart', 'kiss', 'romance', 'relationship', 'wedding', 'marriage'],
            'mystery': ['murder', 'detective', 'clue', 'mystery', 'investigate', 'suspect', 'crime'],
            'fantasy': ['magic', 'wizard', 'dragon', 'fantasy', 'spell', 'enchant', 'kingdom'],
            'science fiction': ['space', 'alien', 'future', 'technology', 'robot', 'planet', 'galaxy'],
            'horror': ['horror', 'ghost', 'haunted', 'terror', 'nightmare', 'evil', 'demon'],
            'thriller': ['thriller', 'chase', 'escape', 'danger', 'suspense', 'pursuit'],
            'historical': ['century', 'historical', 'ancient', 'medieval', 'victorian', 'war'],
            'literary': ['literary', 'contemplat', 'philosoph', 'existential', 'meaning'],
        }

        genre_scores = {}
        for genre, keywords in genre_indicators.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                genre_scores[genre] = score

        if genre_scores:
            # Get the genre with highest score
            detected_genre = max(genre_scores, key=genre_scores.get)
            metadata['genre'] = detected_genre
            metadata['auto_detected_genre'] = True

        return metadata

    def _estimate_reading_time(self, metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Estimate reading time based on word count."""
        if not content:
            return metadata

        # Count words
        words = len(content.split())

        # Average reading speed: 200-250 words per minute
        reading_speed = 225
        minutes = max(1, round(words / reading_speed))

        metadata['estimated_reading_time'] = f"{minutes} minutes"
        metadata['word_count'] = words

        return metadata

    def _detect_content_warnings(self, metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Detect potential content warnings."""
        if not content:
            return metadata

        content_lower = content.lower()

        # Define warning indicators
        warning_indicators = {
            'violence': ['violence', 'blood', 'kill', 'murder', 'death', 'fight', 'battle'],
            'strong language': ['profanity', 'curse', 'swear', 'damn', 'hell'],
            'adult content': ['sexual', 'intimate', 'adult', 'mature'],
            'substance use': ['alcohol', 'drunk', 'drug', 'smoke', 'addiction'],
            'mental health': ['depression', 'anxiety', 'suicide', 'self-harm', 'trauma'],
        }

        detected_warnings = []
        for warning, keywords in warning_indicators.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_warnings.append(warning)

        if detected_warnings:
            metadata['content_warnings'] = detected_warnings
            metadata['auto_detected_warnings'] = True

        return metadata

    def _set_defaults(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Set sensible defaults for missing metadata."""
        defaults = {
            'language': 'en',
            'publisher': 'Self-Published',
            'rights': 'All rights reserved',
            'format': 'EPUB 3',
        }

        for key, default_value in defaults.items():
            if key not in metadata:
                metadata[key] = default_value

        return metadata

    def _format_dates(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate dates."""
        date_fields = ['published', 'created', 'modified']

        for field in date_fields:
            if field in metadata:
                date_value = metadata[field]
                if isinstance(date_value, str):
                    # Try to parse and reformat date
                    try:
                        # Handle various date formats
                        if re.match(r'\d{4}-\d{2}-\d{2}', date_value):
                            # Already in ISO format
                            continue
                        elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_value):
                            # MM/DD/YYYY format
                            from datetime import datetime
                            parsed = datetime.strptime(date_value, '%m/%d/%Y')
                            metadata[field] = parsed.strftime('%Y-%m-%d')
                        elif re.match(r'\d{1,2}-\d{1,2}-\d{4}', date_value):
                            # MM-DD-YYYY format
                            from datetime import datetime
                            parsed = datetime.strptime(date_value, '%m-%d-%Y')
                            metadata[field] = parsed.strftime('%Y-%m-%d')
                    except Exception:
                        # If parsing fails, leave as is
                        pass

        # Add current date if no publication date
        if 'published' not in metadata:
            metadata['published'] = datetime.datetime.now().strftime('%Y-%m-%d')

        return metadata

    def _add_processing_info(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Add information about processing."""
        metadata['enhanced_by'] = 'metadata_enhancer_plugin'
        metadata['enhancement_date'] = datetime.datetime.now().isoformat()

        # Track what was auto-generated
        auto_generated = []
        if 'auto_detected_genre' in metadata:
            auto_generated.append('genre')
        if 'auto_detected_warnings' in metadata:
            auto_generated.append('content_warnings')
        if 'estimated_reading_time' in metadata:
            auto_generated.append('reading_time')

        if auto_generated:
            metadata['auto_generated_fields'] = auto_generated

        return metadata


# Example of a specialized fiction metadata enhancer
class FictionMetadataPlugin(BasePlugin):
    """Specialized metadata enhancer for fiction books."""

    def __init__(self):
        super().__init__("fiction_metadata", "1.0.0")

    def get_hooks(self) -> Dict[str, List]:
        return {
            'metadata_resolver': [FictionMetadataHook()]
        }


class FictionMetadataHook(MetadataResolverHook):
    """Fiction-specific metadata enhancement."""

    def resolve_metadata(self, metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata for fiction books."""
        content = context.get('content_preview', '')

        # Detect point of view
        metadata = self._detect_pov(metadata, content)

        # Detect tense
        metadata = self._detect_tense(metadata, content)

        # Extract character names
        metadata = self._extract_characters(metadata, content)

        # Detect setting
        metadata = self._detect_setting(metadata, content)

        return metadata

    def _detect_pov(self, metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Detect point of view (first person, third person, etc.)."""
        if not content:
            return metadata

        # Count pronouns to determine POV
        first_person = len(re.findall(r'\bI\b|\bme\b|\bmy\b|\bmine\b', content, re.IGNORECASE))
        third_person = len(re.findall(r'\bhe\b|\bshe\b|\bhim\b|\bher\b|\bhis\b|\bhers\b', content, re.IGNORECASE))

        if first_person > third_person * 2:
            metadata['point_of_view'] = 'first person'
        elif third_person > first_person:
            metadata['point_of_view'] = 'third person'
        else:
            metadata['point_of_view'] = 'mixed'

        return metadata

    def _detect_tense(self, metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Detect narrative tense."""
        if not content:
            return metadata

        # Simple tense detection based on common verbs
        past_indicators = len(re.findall(r'\bwas\b|\bwere\b|\bhad\b|\bdid\b|\bsaid\b', content, re.IGNORECASE))
        present_indicators = len(re.findall(r'\bis\b|\bare\b|\bhas\b|\bdoes\b|\bsays\b', content, re.IGNORECASE))

        if past_indicators > present_indicators:
            metadata['narrative_tense'] = 'past'
        elif present_indicators > past_indicators:
            metadata['narrative_tense'] = 'present'
        else:
            metadata['narrative_tense'] = 'mixed'

        return metadata

    def _extract_characters(self, metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Extract likely character names."""
        if not content:
            return metadata

        # Find capitalized words that appear multiple times (likely names)
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        word_counts = {}
        for word in words:
            if len(word) > 2:  # Skip short words
                word_counts[word] = word_counts.get(word, 0) + 1

        # Filter for words that appear multiple times and aren't common words
        common_words = {'The', 'And', 'But', 'For', 'She', 'His', 'Her', 'Him', 'They', 'That', 'This', 'With', 'From'}
        characters = [word for word, count in word_counts.items()
                     if count >= 3 and word not in common_words]

        if characters:
            metadata['characters'] = characters[:10]  # Limit to top 10

        return metadata

    def _detect_setting(self, metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Detect setting indicators."""
        if not content:
            return metadata

        # Look for setting indicators
        setting_indicators = {
            'modern': ['computer', 'internet', 'phone', 'car', 'email'],
            'historical': ['horse', 'carriage', 'sword', 'castle', 'lord', 'lady'],
            'fantasy': ['magic', 'dragon', 'elf', 'dwarf', 'wizard', 'spell'],
            'urban': ['city', 'street', 'building', 'apartment', 'subway'],
            'rural': ['farm', 'field', 'barn', 'countryside', 'village'],
        }

        content_lower = content.lower()
        setting_scores = {}

        for setting, keywords in setting_indicators.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                setting_scores[setting] = score

        if setting_scores:
            detected_setting = max(setting_scores, key=setting_scores.get)
            metadata['setting_type'] = detected_setting

        return metadata


"""
Usage Examples:

1. Basic metadata enhancement:
   docx2shelf plugins load metadata_enhancer.py
   docx2shelf plugins enable metadata_enhancer

2. Fiction-specific enhancement:
   docx2shelf plugins enable fiction_metadata

The plugin will automatically:
- Generate descriptions from content
- Detect genre based on keywords
- Estimate reading time
- Detect content warnings
- Set sensible defaults
- Format dates properly
- Add processing metadata

For fiction books, it also:
- Detects point of view
- Detects narrative tense
- Extracts character names
- Identifies setting type
"""