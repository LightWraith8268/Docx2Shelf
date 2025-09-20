"""
Advanced Genre Detection and Keyword Generation for Docx2Shelf

Provides sophisticated AI-powered genre classification and keyword extraction
using multiple analysis techniques and machine learning models.
"""

from __future__ import annotations

import re
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import logging

from .ai_integration import get_ai_manager, AIResult
from .utils import prompt_select


@dataclass
class GenreScore:
    """Score for a detected genre."""
    genre: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    method: str = "unknown"
    sub_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class KeywordResult:
    """Result of keyword extraction."""
    keyword: str
    frequency: int
    relevance_score: float
    context_examples: List[str] = field(default_factory=list)
    category: str = "general"  # character, setting, theme, plot, etc.


@dataclass
class GenreDetectionResult:
    """Complete genre detection result."""
    primary_genre: str
    confidence: float
    secondary_genres: List[GenreScore] = field(default_factory=list)
    keywords: List[KeywordResult] = field(default_factory=list)
    content_analysis: Dict[str, Any] = field(default_factory=dict)
    bisac_suggestions: List[str] = field(default_factory=list)


class AdvancedGenreDetector:
    """Advanced genre detection using multiple analysis methods."""

    def __init__(self):
        self.ai_manager = get_ai_manager()
        self.logger = logging.getLogger(__name__)
        self._load_genre_models()

    def _load_genre_models(self):
        """Load genre detection models and data."""
        self.genre_keywords = {
            'Fantasy': {
                'primary': ['magic', 'wizard', 'dragon', 'spell', 'enchanted', 'quest', 'sword', 'kingdom'],
                'secondary': ['fairy', 'elf', 'dwarf', 'mystical', 'potion', 'crystal', 'prophecy', 'ancient'],
                'indicators': ['magical', 'mythical', 'legendary', 'supernatural', 'otherworldly'],
                'settings': ['castle', 'forest', 'mountain', 'tower', 'realm', 'dimension'],
                'characters': ['prince', 'princess', 'knight', 'sorcerer', 'oracle', 'warlock']
            },
            'Romance': {
                'primary': ['love', 'heart', 'kiss', 'passion', 'romance', 'relationship', 'wedding'],
                'secondary': ['desire', 'attraction', 'intimate', 'affection', 'devoted', 'beloved'],
                'indicators': ['romantic', 'tender', 'gentle', 'warm', 'emotional'],
                'settings': ['home', 'garden', 'beach', 'cafe', 'restaurant', 'bedroom'],
                'characters': ['lover', 'husband', 'wife', 'boyfriend', 'girlfriend', 'partner']
            },
            'Mystery': {
                'primary': ['detective', 'murder', 'crime', 'investigation', 'suspect', 'clue', 'evidence'],
                'secondary': ['mystery', 'police', 'criminal', 'victim', 'witness', 'alibi', 'motive'],
                'indicators': ['suspicious', 'hidden', 'secret', 'puzzling', 'mysterious'],
                'settings': ['office', 'library', 'alley', 'warehouse', 'station', 'courthouse'],
                'characters': ['inspector', 'sergeant', 'officer', 'lawyer', 'judge', 'criminal']
            },
            'Science Fiction': {
                'primary': ['space', 'alien', 'robot', 'technology', 'future', 'planet', 'spaceship'],
                'secondary': ['galaxy', 'laser', 'android', 'cyber', 'quantum', 'temporal', 'dimension'],
                'indicators': ['futuristic', 'advanced', 'technological', 'artificial', 'digital'],
                'settings': ['laboratory', 'station', 'colony', 'vessel', 'facility', 'base'],
                'characters': ['scientist', 'engineer', 'pilot', 'commander', 'researcher', 'android']
            },
            'Thriller': {
                'primary': ['danger', 'chase', 'escape', 'suspense', 'threat', 'victim', 'terror'],
                'secondary': ['conspiracy', 'hunt', 'survival', 'pursuit', 'betrayal', 'revenge'],
                'indicators': ['dangerous', 'intense', 'urgent', 'desperate', 'deadly'],
                'settings': ['building', 'street', 'airport', 'hotel', 'tunnel', 'bridge'],
                'characters': ['agent', 'assassin', 'target', 'operative', 'mercenary', 'spy']
            },
            'Horror': {
                'primary': ['ghost', 'monster', 'vampire', 'demon', 'haunted', 'nightmare', 'death'],
                'secondary': ['evil', 'darkness', 'shadow', 'scream', 'blood', 'terror', 'undead'],
                'indicators': ['terrifying', 'frightening', 'sinister', 'macabre', 'grotesque'],
                'settings': ['cemetery', 'mansion', 'basement', 'attic', 'woods', 'church'],
                'characters': ['witch', 'zombie', 'spirit', 'creature', 'beast', 'phantom']
            },
            'Historical Fiction': {
                'primary': ['war', 'century', 'historical', 'period', 'ancient', 'medieval'],
                'secondary': ['revolution', 'empire', 'colonial', 'dynasty', 'era', 'epoch'],
                'indicators': ['traditional', 'classical', 'vintage', 'old-fashioned', 'period'],
                'settings': ['palace', 'village', 'battlefield', 'monastery', 'court', 'estate'],
                'characters': ['king', 'queen', 'lord', 'lady', 'peasant', 'soldier']
            },
            'Literary Fiction': {
                'primary': ['life', 'character', 'society', 'human', 'emotion', 'relationship'],
                'secondary': ['experience', 'memory', 'family', 'culture', 'identity', 'meaning'],
                'indicators': ['profound', 'thoughtful', 'introspective', 'contemplative', 'philosophical'],
                'settings': ['house', 'city', 'town', 'neighborhood', 'school', 'workplace'],
                'characters': ['father', 'mother', 'child', 'friend', 'neighbor', 'teacher']
            },
            'Young Adult': {
                'primary': ['teen', 'teenager', 'school', 'college', 'friend', 'friendship'],
                'secondary': ['adolescent', 'youth', 'student', 'graduation', 'crush', 'identity'],
                'indicators': ['young', 'rebellious', 'confused', 'growing', 'discovering'],
                'settings': ['classroom', 'cafeteria', 'hallway', 'dormitory', 'campus', 'party'],
                'characters': ['student', 'teacher', 'parent', 'classmate', 'boyfriend', 'girlfriend']
            }
        }

        # BISAC code mappings
        self.bisac_codes = {
            'Fantasy': ['FIC009000', 'FIC009010', 'FIC009020', 'FIC009030'],
            'Romance': ['FIC027000', 'FIC027010', 'FIC027020', 'FIC027030'],
            'Mystery': ['FIC022000', 'FIC022010', 'FIC022020', 'FIC022030'],
            'Science Fiction': ['FIC028000', 'FIC028010', 'FIC028020', 'FIC028030'],
            'Thriller': ['FIC031000', 'FIC031010', 'FIC031020', 'FIC031030'],
            'Horror': ['FIC015000', 'FIC015010', 'FIC015020'],
            'Historical Fiction': ['FIC014000', 'FIC014010', 'FIC014020'],
            'Literary Fiction': ['FIC019000', 'FIC045000'],
            'Young Adult': ['YAF000000', 'YAF001000', 'YAF002000']
        }

    def detect_genre(self, content: str, metadata: Dict[str, Any]) -> GenreDetectionResult:
        """Perform comprehensive genre detection.

        Args:
            content: Document content
            metadata: Existing metadata

        Returns:
            Complete genre detection result
        """
        print("🔍 Performing advanced genre detection...")

        # Multiple detection methods
        results = []

        # 1. AI-powered detection
        if self.ai_manager.is_available():
            ai_result = self._detect_with_ai(content, metadata)
            if ai_result:
                results.append(('ai', ai_result))

        # 2. Advanced keyword analysis
        keyword_result = self._detect_with_advanced_keywords(content)
        results.append(('keywords', keyword_result))

        # 3. Structural analysis
        structure_result = self._detect_with_structure_analysis(content)
        results.append(('structure', structure_result))

        # 4. Metadata analysis
        metadata_result = self._detect_with_metadata(metadata)
        if metadata_result:
            results.append(('metadata', metadata_result))

        # Combine results
        final_result = self._combine_detection_results(results, content)

        print(f"✅ Genre detection complete. Primary: {final_result.primary_genre} ({final_result.confidence:.1%})")

        return final_result

    def _detect_with_ai(self, content: str, metadata: Dict[str, Any]) -> Optional[Dict]:
        """Use AI model for genre detection."""
        try:
            ai_result = self.ai_manager.detect_genre(content, metadata)
            if ai_result.success:
                return ai_result.data
        except Exception as e:
            self.logger.warning(f"AI genre detection failed: {e}")
        return None

    def _detect_with_advanced_keywords(self, content: str) -> Dict:
        """Advanced keyword-based genre detection."""
        content_lower = content.lower()
        genre_scores = {}

        for genre, keywords_dict in self.genre_keywords.items():
            total_score = 0
            evidence = []

            # Score different keyword categories with different weights
            weights = {
                'primary': 3.0,
                'secondary': 2.0,
                'indicators': 1.5,
                'settings': 1.0,
                'characters': 1.0
            }

            sub_scores = {}

            for category, keywords in keywords_dict.items():
                category_score = 0
                category_evidence = []

                for keyword in keywords:
                    count = content_lower.count(keyword)
                    if count > 0:
                        # Use logarithmic scoring to prevent single word dominance
                        keyword_score = math.log(count + 1) * weights.get(category, 1.0)
                        category_score += keyword_score
                        category_evidence.append(f"{keyword}({count})")

                sub_scores[category] = category_score
                total_score += category_score
                evidence.extend(category_evidence[:3])  # Top 3 for each category

            if total_score > 0:
                # Normalize by content length
                normalized_score = total_score / math.log(len(content.split()) + 1)
                genre_scores[genre] = {
                    'score': normalized_score,
                    'evidence': evidence[:10],  # Top 10 overall
                    'sub_scores': sub_scores
                }

        return genre_scores

    def _detect_with_structure_analysis(self, content: str) -> Dict:
        """Analyze document structure for genre clues."""
        structure_scores = {}

        # Analyze sentence and paragraph structure
        sentences = re.split(r'[.!?]+', content)
        paragraphs = content.split('\n\n')

        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / max(1, len(paragraphs))

        # Dialogue analysis
        dialogue_count = len(re.findall(r'"[^"]*"', content))
        dialogue_ratio = dialogue_count / max(1, len(sentences))

        # Action vs description ratio
        action_words = ['ran', 'jumped', 'fought', 'chased', 'escaped', 'attacked', 'struck']
        description_words = ['beautiful', 'elegant', 'peaceful', 'serene', 'gentle', 'quiet']

        action_count = sum(content.lower().count(word) for word in action_words)
        description_count = sum(content.lower().count(word) for word in description_words)

        # Genre scoring based on structure
        if dialogue_ratio > 0.3:  # High dialogue
            structure_scores['Romance'] = 0.6
            structure_scores['Young Adult'] = 0.5

        if avg_sentence_length < 15:  # Short sentences
            structure_scores['Thriller'] = 0.7
            structure_scores['Young Adult'] = 0.6

        if action_count > description_count * 2:  # Action-heavy
            structure_scores['Thriller'] = 0.8
            structure_scores['Science Fiction'] = 0.6

        if avg_paragraph_length > 100:  # Long, descriptive paragraphs
            structure_scores['Literary Fiction'] = 0.7
            structure_scores['Historical Fiction'] = 0.6

        return structure_scores

    def _detect_with_metadata(self, metadata: Dict[str, Any]) -> Optional[Dict]:
        """Analyze existing metadata for genre clues."""
        metadata_scores = {}

        # Check title for genre indicators
        title = metadata.get('title', '').lower()
        description = metadata.get('description', '').lower()
        existing_genre = metadata.get('genre', '').lower()

        combined_text = f"{title} {description}".lower()

        for genre, keywords_dict in self.genre_keywords.items():
            score = 0
            for category, keywords in keywords_dict.items():
                for keyword in keywords:
                    if keyword in combined_text:
                        score += 2.0 if keyword in title else 1.0

            if score > 0:
                metadata_scores[genre] = score

        # If genre is already specified, give it high confidence
        if existing_genre:
            for genre in self.genre_keywords.keys():
                if genre.lower() in existing_genre:
                    metadata_scores[genre] = metadata_scores.get(genre, 0) + 10

        return metadata_scores if metadata_scores else None

    def _combine_detection_results(self, results: List[Tuple[str, Dict]], content: str) -> GenreDetectionResult:
        """Combine results from different detection methods."""
        combined_scores = defaultdict(lambda: {'total': 0, 'methods': [], 'evidence': []})

        # Weights for different methods
        method_weights = {
            'ai': 0.4,
            'keywords': 0.3,
            'structure': 0.2,
            'metadata': 0.1
        }

        # Combine scores
        for method, result in results:
            weight = method_weights.get(method, 0.1)

            if method == 'ai':
                # AI results have different format
                primary = result.get('primary_genre', '')
                confidence = result.get('confidence', 0.5)
                if primary:
                    combined_scores[primary]['total'] += confidence * weight
                    combined_scores[primary]['methods'].append(method)

                for secondary in result.get('secondary_genres', []):
                    combined_scores[secondary]['total'] += 0.3 * weight
                    combined_scores[secondary]['methods'].append(method)

            elif method == 'keywords':
                # Keyword results
                for genre, data in result.items():
                    score = data['score']
                    combined_scores[genre]['total'] += score * weight
                    combined_scores[genre]['methods'].append(method)
                    combined_scores[genre]['evidence'].extend(data['evidence'])

            else:
                # Structure and metadata results
                for genre, score in result.items():
                    combined_scores[genre]['total'] += score * weight
                    combined_scores[genre]['methods'].append(method)

        # Convert to genre scores and sort
        genre_scores = []
        for genre, data in combined_scores.items():
            if data['total'] > 0:
                genre_scores.append(GenreScore(
                    genre=genre,
                    confidence=min(0.95, data['total']),
                    evidence=data['evidence'][:5],
                    method='+'.join(set(data['methods']))
                ))

        genre_scores.sort(key=lambda x: x.confidence, reverse=True)

        # Determine primary genre
        primary_genre = genre_scores[0].genre if genre_scores else 'Literary Fiction'
        primary_confidence = genre_scores[0].confidence if genre_scores else 0.3

        # Extract keywords
        keywords = self._extract_genre_keywords(content, primary_genre)

        # Generate BISAC suggestions
        bisac_suggestions = self.bisac_codes.get(primary_genre, [])

        return GenreDetectionResult(
            primary_genre=primary_genre,
            confidence=primary_confidence,
            secondary_genres=genre_scores[1:4],  # Top 3 secondary
            keywords=keywords,
            bisac_suggestions=bisac_suggestions,
            content_analysis={
                'word_count': len(content.split()),
                'methods_used': [method for method, _ in results],
                'total_genres_detected': len(genre_scores)
            }
        )

    def _extract_genre_keywords(self, content: str, primary_genre: str) -> List[KeywordResult]:
        """Extract relevant keywords for the detected genre."""
        content_lower = content.lower()
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content_lower)
        word_counts = Counter(words)

        # Get genre-specific keywords
        genre_keywords = []
        if primary_genre in self.genre_keywords:
            genre_data = self.genre_keywords[primary_genre]
            for category, keywords in genre_data.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        count = word_counts.get(keyword, 0)
                        if count > 0:
                            # Calculate relevance score
                            relevance = self._calculate_keyword_relevance(keyword, count, len(words), category)

                            # Find context examples
                            context_examples = self._find_keyword_contexts(content, keyword)

                            genre_keywords.append(KeywordResult(
                                keyword=keyword,
                                frequency=count,
                                relevance_score=relevance,
                                context_examples=context_examples[:2],
                                category=category
                            ))

        # Sort by relevance and return top keywords
        genre_keywords.sort(key=lambda x: x.relevance_score, reverse=True)
        return genre_keywords[:15]

    def _calculate_keyword_relevance(self, keyword: str, count: int, total_words: int, category: str) -> float:
        """Calculate relevance score for a keyword."""
        # Base score from frequency
        frequency_score = math.log(count + 1) / math.log(total_words + 1)

        # Category weight
        category_weights = {
            'primary': 3.0,
            'secondary': 2.0,
            'indicators': 1.5,
            'settings': 1.2,
            'characters': 1.0
        }

        category_weight = category_weights.get(category, 1.0)

        # Length bonus (longer keywords are often more specific)
        length_bonus = min(1.5, len(keyword) / 6)

        return frequency_score * category_weight * length_bonus

    def _find_keyword_contexts(self, content: str, keyword: str, context_length: int = 50) -> List[str]:
        """Find context examples for a keyword."""
        contexts = []
        content_lower = content.lower()
        keyword_lower = keyword.lower()

        start = 0
        while start < len(content_lower):
            pos = content_lower.find(keyword_lower, start)
            if pos == -1:
                break

            # Extract context
            context_start = max(0, pos - context_length)
            context_end = min(len(content), pos + len(keyword) + context_length)
            context = content[context_start:context_end].strip()

            # Clean up context
            context = re.sub(r'\s+', ' ', context)
            if len(context) > 10:
                contexts.append(f"...{context}...")

            start = pos + 1

            if len(contexts) >= 3:  # Limit context examples
                break

        return contexts


class IntelligentKeywordExtractor:
    """Advanced keyword extraction with semantic analysis."""

    def __init__(self):
        self.ai_manager = get_ai_manager()
        self.logger = logging.getLogger(__name__)

    def extract_keywords(self, content: str, max_keywords: int = 20) -> List[KeywordResult]:
        """Extract intelligent keywords from content.

        Args:
            content: Document content
            max_keywords: Maximum number of keywords to return

        Returns:
            List of extracted keywords with relevance scores
        """
        print("🔤 Extracting intelligent keywords...")

        # Multiple extraction methods
        results = []

        # 1. Frequency-based extraction
        freq_keywords = self._extract_frequency_keywords(content)
        results.extend(freq_keywords)

        # 2. TF-IDF style extraction
        tfidf_keywords = self._extract_tfidf_keywords(content)
        results.extend(tfidf_keywords)

        # 3. Named entity recognition (basic)
        entity_keywords = self._extract_entity_keywords(content)
        results.extend(entity_keywords)

        # 4. Semantic clustering
        cluster_keywords = self._extract_cluster_keywords(content)
        results.extend(cluster_keywords)

        # Combine and deduplicate
        final_keywords = self._combine_keyword_results(results, max_keywords)

        print(f"✅ Extracted {len(final_keywords)} relevant keywords")
        return final_keywords

    def _extract_frequency_keywords(self, content: str) -> List[KeywordResult]:
        """Extract keywords based on frequency analysis."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())

        # Filter stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one',
            'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see',
            'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'with',
            'have', 'this', 'will', 'your', 'they', 'said', 'each', 'which', 'their', 'time', 'would',
            'there', 'could', 'other', 'after', 'first', 'never', 'these', 'think', 'where', 'being'
        }

        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        word_counts = Counter(filtered_words)

        keywords = []
        for word, count in word_counts.most_common(50):
            if count >= 2:  # Minimum frequency
                relevance = math.log(count + 1) / math.log(len(filtered_words) + 1)
                keywords.append(KeywordResult(
                    keyword=word,
                    frequency=count,
                    relevance_score=relevance,
                    category='frequency'
                ))

        return keywords

    def _extract_tfidf_keywords(self, content: str) -> List[KeywordResult]:
        """Extract keywords using TF-IDF-like scoring."""
        # Simple TF-IDF implementation
        sentences = re.split(r'[.!?]+', content)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())

        if not sentences or not words:
            return []

        # Calculate term frequency
        tf = Counter(words)
        total_words = len(words)

        # Calculate document frequency (sentence-level)
        df = {}
        for word in set(words):
            df[word] = sum(1 for sentence in sentences if word in sentence.lower())

        # Calculate TF-IDF scores
        keywords = []
        for word, freq in tf.items():
            if freq >= 2 and len(word) > 3:
                tf_score = freq / total_words
                idf_score = math.log(len(sentences) / (df[word] + 1))
                tfidf_score = tf_score * idf_score

                keywords.append(KeywordResult(
                    keyword=word,
                    frequency=freq,
                    relevance_score=tfidf_score,
                    category='tfidf'
                ))

        return sorted(keywords, key=lambda x: x.relevance_score, reverse=True)[:20]

    def _extract_entity_keywords(self, content: str) -> List[KeywordResult]:
        """Extract named entities as keywords."""
        # Basic named entity recognition using patterns
        entities = []

        # Proper nouns (capitalized words not at sentence start)
        proper_nouns = re.findall(r'(?<!\.)\s+([A-Z][a-z]{2,})', content)
        proper_noun_counts = Counter(proper_nouns)

        for noun, count in proper_noun_counts.items():
            if count >= 2:
                entities.append(KeywordResult(
                    keyword=noun,
                    frequency=count,
                    relevance_score=count * 1.5,  # Boost for proper nouns
                    category='entity'
                ))

        # Place names (patterns like "in X", "at X", "from X")
        places = re.findall(r'\b(?:in|at|from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', content)
        place_counts = Counter(places)

        for place, count in place_counts.items():
            if count >= 2:
                entities.append(KeywordResult(
                    keyword=place,
                    frequency=count,
                    relevance_score=count * 1.3,
                    category='place'
                ))

        return entities

    def _extract_cluster_keywords(self, content: str) -> List[KeywordResult]:
        """Extract keywords using semantic clustering."""
        # Simple clustering based on co-occurrence
        sentences = re.split(r'[.!?]+', content)
        words = []

        for sentence in sentences:
            sentence_words = re.findall(r'\b[a-zA-Z]{4,}\b', sentence.lower())
            words.extend(sentence_words)

        if len(words) < 10:
            return []

        # Find word co-occurrences
        cooccurrence = defaultdict(lambda: defaultdict(int))
        word_counts = Counter(words)

        for sentence in sentences:
            sentence_words = list(set(re.findall(r'\b[a-zA-Z]{4,}\b', sentence.lower())))
            for i, word1 in enumerate(sentence_words):
                for word2 in sentence_words[i+1:]:
                    cooccurrence[word1][word2] += 1
                    cooccurrence[word2][word1] += 1

        # Score words based on their connections
        cluster_scores = {}
        for word, count in word_counts.items():
            if count >= 2:
                # Score based on connections to other frequent words
                connection_score = sum(
                    cooccurrence[word][other] * math.log(word_counts[other] + 1)
                    for other in cooccurrence[word]
                    if word_counts[other] >= 2
                )
                cluster_scores[word] = connection_score / (count + 1)

        # Convert to keyword results
        keywords = []
        for word, score in sorted(cluster_scores.items(), key=lambda x: x[1], reverse=True)[:15]:
            keywords.append(KeywordResult(
                keyword=word,
                frequency=word_counts[word],
                relevance_score=score,
                category='cluster'
            ))

        return keywords

    def _combine_keyword_results(self, all_results: List[KeywordResult], max_keywords: int) -> List[KeywordResult]:
        """Combine and deduplicate keyword results."""
        # Group by keyword
        keyword_groups = defaultdict(list)
        for result in all_results:
            keyword_groups[result.keyword].append(result)

        # Combine scores for each keyword
        final_keywords = []
        for keyword, results in keyword_groups.items():
            if len(keyword) <= 3:  # Skip very short keywords
                continue

            # Combine scores with method weighting
            method_weights = {
                'frequency': 0.3,
                'tfidf': 0.4,
                'entity': 0.2,
                'cluster': 0.1
            }

            total_score = 0
            total_frequency = 0
            categories = set()

            for result in results:
                weight = method_weights.get(result.category, 0.1)
                total_score += result.relevance_score * weight
                total_frequency = max(total_frequency, result.frequency)
                categories.add(result.category)

            # Boost score if detected by multiple methods
            if len(categories) > 1:
                total_score *= 1.2

            final_keywords.append(KeywordResult(
                keyword=keyword,
                frequency=total_frequency,
                relevance_score=total_score,
                category='+'.join(sorted(categories))
            ))

        # Sort by relevance and return top keywords
        final_keywords.sort(key=lambda x: x.relevance_score, reverse=True)
        return final_keywords[:max_keywords]


def detect_genre_with_ai(content: str, metadata: Dict[str, Any] = None) -> GenreDetectionResult:
    """Convenience function for genre detection.

    Args:
        content: Document content
        metadata: Optional metadata

    Returns:
        Genre detection result
    """
    detector = AdvancedGenreDetector()
    return detector.detect_genre(content, metadata or {})


def extract_intelligent_keywords(content: str, max_keywords: int = 20) -> List[KeywordResult]:
    """Convenience function for keyword extraction.

    Args:
        content: Document content
        max_keywords: Maximum keywords to extract

    Returns:
        List of extracted keywords
    """
    extractor = IntelligentKeywordExtractor()
    return extractor.extract_keywords(content, max_keywords)