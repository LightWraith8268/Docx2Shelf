"""
AI-Powered Accessibility Enhancement for Docx2Shelf

Provides intelligent alt-text generation, accessibility validation,
and automated accessibility improvements using AI analysis.
"""

from __future__ import annotations

import re
import json
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
import logging

# Optional dependencies for image processing
try:
    from PIL import Image, ImageStat
    PILLOW_AVAILABLE = True
except (ImportError, AttributeError):
    PILLOW_AVAILABLE = False

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

from .ai_integration import get_ai_manager, AIResult
from .utils import prompt, prompt_bool, prompt_select


@dataclass
class ImageAnalysis:
    """Analysis result for an image."""
    path: Path
    width: int
    height: int
    format: str
    file_size: int
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    brightness: float = 0.0
    contrast: float = 0.0
    is_decorative: bool = False
    has_text: bool = False
    complexity: str = "unknown"  # simple, moderate, complex
    image_type: str = "unknown"  # photo, illustration, diagram, chart, etc.


@dataclass
class AltTextSuggestion:
    """Alt-text suggestion with metadata."""
    text: str
    confidence: float
    method: str
    reasoning: str
    length_category: str = "appropriate"  # short, appropriate, long, too_long
    accessibility_score: float = 0.0


@dataclass
class AccessibilityIssue:
    """Accessibility issue found in content."""
    issue_type: str
    severity: str  # low, medium, high, critical
    element: str
    description: str
    suggestion: str
    auto_fixable: bool = False


@dataclass
class AccessibilityReport:
    """Comprehensive accessibility report."""
    images_processed: int = 0
    alt_texts_generated: int = 0
    issues_found: List[AccessibilityIssue] = field(default_factory=list)
    suggestions_applied: int = 0
    overall_score: float = 0.0
    wcag_compliance: Dict[str, bool] = field(default_factory=dict)


class SmartImageAnalyzer:
    """Advanced image analysis for accessibility enhancement."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_image(self, image_path: Path) -> ImageAnalysis:
        """Perform comprehensive image analysis.

        Args:
            image_path: Path to the image file

        Returns:
            Image analysis result
        """
        if not PILLOW_AVAILABLE:
            return self._basic_analysis(image_path)

        try:
            with Image.open(image_path) as img:
                # Basic properties
                width, height = img.size
                format_name = img.format or 'unknown'
                file_size = image_path.stat().st_size

                # Convert to RGB for analysis
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Color analysis
                dominant_colors = self._extract_dominant_colors(img)

                # Brightness and contrast
                brightness = self._calculate_brightness(img)
                contrast = self._calculate_contrast(img)

                # Content analysis
                complexity = self._analyze_complexity(img)
                image_type = self._classify_image_type(img, image_path)
                has_text = self._detect_text_presence(img)
                is_decorative = self._assess_decorative_nature(img, image_path)

                return ImageAnalysis(
                    path=image_path,
                    width=width,
                    height=height,
                    format=format_name,
                    file_size=file_size,
                    dominant_colors=dominant_colors,
                    brightness=brightness,
                    contrast=contrast,
                    is_decorative=is_decorative,
                    has_text=has_text,
                    complexity=complexity,
                    image_type=image_type
                )

        except Exception as e:
            self.logger.warning(f"Image analysis failed for {image_path}: {e}")
            return self._basic_analysis(image_path)

    def _basic_analysis(self, image_path: Path) -> ImageAnalysis:
        """Basic analysis when PIL is not available."""
        try:
            file_size = image_path.stat().st_size
            format_name = image_path.suffix.lower().replace('.', '')

            return ImageAnalysis(
                path=image_path,
                width=0,
                height=0,
                format=format_name,
                file_size=file_size,
                complexity="unknown",
                image_type="unknown"
            )
        except Exception:
            return ImageAnalysis(
                path=image_path,
                width=0,
                height=0,
                format="unknown",
                file_size=0
            )

    def _extract_dominant_colors(self, img: Image.Image) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from image."""
        try:
            # Resize for faster processing
            img_small = img.resize((50, 50))

            # Get colors and their counts
            colors = img_small.getcolors(50 * 50)
            if not colors:
                return []

            # Sort by frequency and return top colors
            colors.sort(key=lambda x: x[0], reverse=True)
            return [color[1] for color in colors[:5]]

        except Exception:
            return []

    def _calculate_brightness(self, img: Image.Image) -> float:
        """Calculate average brightness of image."""
        try:
            # Convert to grayscale and calculate mean
            grayscale = img.convert('L')
            stat = ImageStat.Stat(grayscale)
            return stat.mean[0] / 255.0  # Normalize to 0-1
        except Exception:
            return 0.5

    def _calculate_contrast(self, img: Image.Image) -> float:
        """Calculate contrast of image."""
        try:
            grayscale = img.convert('L')
            stat = ImageStat.Stat(grayscale)
            return stat.stddev[0] / 128.0  # Normalize to 0-1
        except Exception:
            return 0.5

    def _analyze_complexity(self, img: Image.Image) -> str:
        """Analyze visual complexity of image."""
        try:
            # Resize for analysis
            img_small = img.resize((100, 100))

            # Count unique colors as complexity indicator
            colors = len(img_small.getcolors(100 * 100) or [])

            # Calculate edge density if OpenCV is available
            edge_density = 0.0
            if OPENCV_AVAILABLE:
                try:
                    img_array = np.array(img_small.convert('L'))
                    edges = cv2.Canny(img_array, 50, 150)
                    edge_density = np.mean(edges) / 255.0
                except Exception:
                    pass

            # Classify complexity
            if colors < 50 and edge_density < 0.1:
                return "simple"
            elif colors < 200 and edge_density < 0.3:
                return "moderate"
            else:
                return "complex"

        except Exception:
            return "unknown"

    def _classify_image_type(self, img: Image.Image, path: Path) -> str:
        """Classify type of image based on analysis."""
        filename = path.stem.lower()

        # Check filename for clues
        if any(word in filename for word in ['chart', 'graph', 'plot', 'diagram']):
            return "chart"
        elif any(word in filename for word in ['photo', 'img', 'pic', 'jpeg', 'jpg']):
            return "photo"
        elif any(word in filename for word in ['icon', 'logo', 'symbol']):
            return "icon"
        elif any(word in filename for word in ['figure', 'fig', 'illustration']):
            return "illustration"

        # Analyze image properties
        try:
            width, height = img.size

            # Very small images are likely icons
            if max(width, height) < 100:
                return "icon"

            # Analyze color distribution
            colors = len(img.getcolors(width * height) or [])

            # Simple color palette suggests diagram/chart
            if colors < 20:
                return "diagram"
            elif colors < 100:
                return "illustration"
            else:
                return "photo"

        except Exception:
            return "unknown"

    def _detect_text_presence(self, img: Image.Image) -> bool:
        """Detect if image likely contains text."""
        # This is a simplified heuristic - real OCR would be more accurate
        try:
            # Convert to grayscale
            grayscale = img.convert('L')

            # Resize for analysis
            small_img = grayscale.resize((200, 200))

            # Calculate edge density (text has many edges)
            if OPENCV_AVAILABLE:
                img_array = np.array(small_img)
                edges = cv2.Canny(img_array, 100, 200)
                edge_density = np.mean(edges) / 255.0

                # High edge density might indicate text
                return edge_density > 0.2

        except Exception:
            pass

        return False

    def _assess_decorative_nature(self, img: Image.Image, path: Path) -> bool:
        """Assess if image is likely decorative."""
        filename = path.stem.lower()

        # Check filename for decorative indicators
        decorative_keywords = [
            'border', 'decoration', 'ornament', 'divider', 'spacer',
            'background', 'texture', 'pattern', 'frame'
        ]

        if any(keyword in filename for keyword in decorative_keywords):
            return True

        # Check image properties
        try:
            width, height = img.size

            # Very thin images might be decorative (borders, dividers)
            aspect_ratio = max(width, height) / min(width, height)
            if aspect_ratio > 10:  # Very elongated
                return True

            # Very small images might be decorative
            if max(width, height) < 50:
                return True

        except Exception:
            pass

        return False


class IntelligentAltTextGenerator:
    """Advanced alt-text generation using AI and image analysis."""

    def __init__(self):
        self.ai_manager = get_ai_manager()
        self.image_analyzer = SmartImageAnalyzer()
        self.logger = logging.getLogger(__name__)

    def generate_alt_text(
        self,
        image_path: Path,
        context: str = "",
        interactive: bool = False
    ) -> List[AltTextSuggestion]:
        """Generate intelligent alt-text suggestions.

        Args:
            image_path: Path to the image
            context: Surrounding text context
            interactive: Whether to allow user interaction

        Returns:
            List of alt-text suggestions
        """
        print(f"🖼️  Generating alt-text for {image_path.name}...")

        # Analyze image
        analysis = self.image_analyzer.analyze_image(image_path)

        suggestions = []

        # 1. AI-powered generation
        if self.ai_manager.is_available():
            ai_suggestions = self._generate_ai_alt_text(image_path, context, analysis)
            suggestions.extend(ai_suggestions)

        # 2. Rule-based generation
        rule_suggestions = self._generate_rule_based_alt_text(analysis, context)
        suggestions.extend(rule_suggestions)

        # 3. Context-aware generation
        context_suggestions = self._generate_context_alt_text(analysis, context)
        suggestions.extend(context_suggestions)

        # 4. Template-based generation
        template_suggestions = self._generate_template_alt_text(analysis)
        suggestions.extend(template_suggestions)

        # Rank and filter suggestions
        final_suggestions = self._rank_suggestions(suggestions, analysis)

        if interactive and final_suggestions:
            final_suggestions = self._interactive_selection(final_suggestions, analysis)

        print(f"✅ Generated {len(final_suggestions)} alt-text suggestions")
        return final_suggestions

    def _generate_ai_alt_text(
        self,
        image_path: Path,
        context: str,
        analysis: ImageAnalysis
    ) -> List[AltTextSuggestion]:
        """Generate alt-text using AI vision models."""
        suggestions = []

        try:
            ai_result = self.ai_manager.generate_alt_text(image_path, context)

            if ai_result.success:
                alt_text = ai_result.data.get('alt_text', '')
                confidence = ai_result.data.get('confidence', 0.7)

                if alt_text:
                    accessibility_score = self._calculate_accessibility_score(alt_text, analysis)

                    suggestions.append(AltTextSuggestion(
                        text=alt_text,
                        confidence=confidence,
                        method="ai_vision",
                        reasoning="Generated using AI vision model analysis",
                        accessibility_score=accessibility_score
                    ))

        except Exception as e:
            self.logger.warning(f"AI alt-text generation failed: {e}")

        return suggestions

    def _generate_rule_based_alt_text(
        self,
        analysis: ImageAnalysis,
        context: str
    ) -> List[AltTextSuggestion]:
        """Generate alt-text using rule-based analysis."""
        suggestions = []

        # Handle decorative images
        if analysis.is_decorative:
            suggestions.append(AltTextSuggestion(
                text="",  # Empty alt for decorative images
                confidence=0.8,
                method="rule_based",
                reasoning="Image appears decorative based on analysis",
                accessibility_score=0.9
            ))
            return suggestions

        # Generate based on image type
        base_text = ""
        reasoning = ""

        if analysis.image_type == "chart":
            base_text = "Chart"
            reasoning = "Identified as chart/graph from analysis"
        elif analysis.image_type == "diagram":
            base_text = "Diagram"
            reasoning = "Identified as diagram from visual analysis"
        elif analysis.image_type == "photo":
            base_text = "Photograph"
            reasoning = "Identified as photograph from color/complexity analysis"
        elif analysis.image_type == "illustration":
            base_text = "Illustration"
            reasoning = "Identified as illustration from visual characteristics"
        elif analysis.image_type == "icon":
            base_text = "Icon"
            reasoning = "Identified as icon from size/simplicity analysis"
        else:
            base_text = "Image"
            reasoning = "Generic description based on file analysis"

        # Enhance with filename information
        filename = analysis.path.stem
        clean_filename = re.sub(r'[_\-\d]+', ' ', filename).strip()

        if clean_filename and len(clean_filename) > 2:
            enhanced_text = f"{base_text}: {clean_filename}"
        else:
            enhanced_text = base_text

        # Add descriptive details
        details = []

        if analysis.has_text:
            details.append("containing text")

        if analysis.complexity == "complex":
            details.append("with detailed content")
        elif analysis.complexity == "simple":
            details.append("with simple design")

        if details:
            enhanced_text += f" ({', '.join(details)})"

        accessibility_score = self._calculate_accessibility_score(enhanced_text, analysis)

        suggestions.append(AltTextSuggestion(
            text=enhanced_text,
            confidence=0.6,
            method="rule_based",
            reasoning=reasoning,
            accessibility_score=accessibility_score
        ))

        return suggestions

    def _generate_context_alt_text(
        self,
        analysis: ImageAnalysis,
        context: str
    ) -> List[AltTextSuggestion]:
        """Generate alt-text using surrounding context."""
        suggestions = []

        if not context or len(context) < 10:
            return suggestions

        context_lower = context.lower()

        # Look for context clues
        figure_match = re.search(r'figure\s*(\d+)', context_lower)
        if figure_match:
            figure_num = figure_match.group(1)
            alt_text = f"Figure {figure_num}"

            # Look for caption or description
            caption_patterns = [
                r'figure\s*\d+[:.]\s*([^.]+)',
                r'(?:shows?|depicts?|illustrates?)\s+([^.]+)',
                r'(?:image|photo|picture)\s+(?:of|shows?)\s+([^.]+)'
            ]

            for pattern in caption_patterns:
                match = re.search(pattern, context_lower)
                if match:
                    description = match.group(1).strip()
                    if len(description) > 5:
                        alt_text += f": {description}"
                        break

            accessibility_score = self._calculate_accessibility_score(alt_text, analysis)

            suggestions.append(AltTextSuggestion(
                text=alt_text,
                confidence=0.7,
                method="context_analysis",
                reasoning="Generated from surrounding text context",
                accessibility_score=accessibility_score
            ))

        # Look for references to charts, graphs, etc.
        chart_keywords = ['chart', 'graph', 'plot', 'diagram', 'table']
        for keyword in chart_keywords:
            if keyword in context_lower:
                # Extract description after keyword
                pattern = f'{keyword}\\s+(?:shows?|depicts?|of)?\\s*([^.]+)'
                match = re.search(pattern, context_lower)
                if match:
                    description = match.group(1).strip()
                    alt_text = f"{keyword.title()}: {description}"

                    accessibility_score = self._calculate_accessibility_score(alt_text, analysis)

                    suggestions.append(AltTextSuggestion(
                        text=alt_text,
                        confidence=0.65,
                        method="context_keywords",
                        reasoning=f"Found {keyword} reference in context",
                        accessibility_score=accessibility_score
                    ))

        return suggestions

    def _generate_template_alt_text(self, analysis: ImageAnalysis) -> List[AltTextSuggestion]:
        """Generate alt-text using templates."""
        suggestions = []

        # Template based on image properties
        templates = {
            "photo": [
                "Photograph",
                "Color photograph",
                "Black and white photograph" if analysis.brightness < 0.3 else "Bright photograph"
            ],
            "chart": [
                "Data chart",
                "Statistical chart",
                "Information chart"
            ],
            "diagram": [
                "Technical diagram",
                "Explanatory diagram",
                "Process diagram"
            ],
            "illustration": [
                "Illustration",
                "Artistic illustration",
                "Detailed illustration" if analysis.complexity == "complex" else "Simple illustration"
            ],
            "icon": [
                "Icon",
                "Symbol",
                "Graphic icon"
            ]
        }

        template_list = templates.get(analysis.image_type, ["Image"])

        for template in template_list:
            accessibility_score = self._calculate_accessibility_score(template, analysis)

            suggestions.append(AltTextSuggestion(
                text=template,
                confidence=0.4,
                method="template",
                reasoning=f"Template for {analysis.image_type} type",
                accessibility_score=accessibility_score
            ))

        return suggestions

    def _calculate_accessibility_score(self, alt_text: str, analysis: ImageAnalysis) -> float:
        """Calculate accessibility score for alt-text."""
        score = 0.5  # Base score

        # Length appropriateness
        length = len(alt_text)
        if 10 <= length <= 125:  # Ideal range
            score += 0.3
        elif 5 <= length <= 150:  # Acceptable range
            score += 0.2
        elif length > 200:  # Too long
            score -= 0.2

        # Descriptive quality
        if any(word in alt_text.lower() for word in ['shows', 'depicts', 'contains', 'illustrates']):
            score += 0.1

        # Specific vs generic
        generic_words = ['image', 'picture', 'photo', 'graphic']
        if not any(word in alt_text.lower() for word in generic_words):
            score += 0.1

        # Context appropriateness
        if analysis.is_decorative and alt_text == "":
            score += 0.2  # Correct empty alt for decorative

        # Information density
        words = alt_text.split()
        if len(words) >= 3:  # Multi-word descriptions
            score += 0.1

        return min(1.0, max(0.0, score))

    def _rank_suggestions(
        self,
        suggestions: List[AltTextSuggestion],
        analysis: ImageAnalysis
    ) -> List[AltTextSuggestion]:
        """Rank and filter suggestions by quality."""
        if not suggestions:
            return []

        # Remove duplicates
        seen_texts = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.text not in seen_texts:
                unique_suggestions.append(suggestion)
                seen_texts.add(suggestion.text)

        # Calculate combined score
        for suggestion in unique_suggestions:
            # Combine confidence, accessibility, and method preference
            method_weights = {
                'ai_vision': 1.0,
                'context_analysis': 0.9,
                'rule_based': 0.7,
                'context_keywords': 0.6,
                'template': 0.3
            }

            method_weight = method_weights.get(suggestion.method, 0.5)
            combined_score = (
                suggestion.confidence * 0.4 +
                suggestion.accessibility_score * 0.4 +
                method_weight * 0.2
            )

            suggestion.confidence = combined_score

        # Sort by combined score
        unique_suggestions.sort(key=lambda x: x.confidence, reverse=True)

        # Return top suggestions
        return unique_suggestions[:5]

    def _interactive_selection(
        self,
        suggestions: List[AltTextSuggestion],
        analysis: ImageAnalysis
    ) -> List[AltTextSuggestion]:
        """Allow user to interactively select/modify suggestions."""
        print(f"\n🖼️  Alt-text suggestions for {analysis.path.name}:")
        print(f"   Type: {analysis.image_type} | Size: {analysis.width}x{analysis.height}")

        if analysis.is_decorative:
            print("   Note: Image appears decorative (empty alt-text recommended)")

        options = []
        for i, suggestion in enumerate(suggestions):
            confidence_icon = "🟢" if suggestion.confidence >= 0.8 else "🟡" if suggestion.confidence >= 0.6 else "🔴"
            print(f"   {i+1}. {confidence_icon} \"{suggestion.text}\"")
            print(f"      Method: {suggestion.method} | Score: {suggestion.accessibility_score:.2f}")
            options.append(suggestion.text[:50] + "..." if len(suggestion.text) > 50 else suggestion.text)

        options.extend(["Enter custom alt-text", "Skip this image"])

        choice = prompt_select("Choose alt-text", options)

        if choice < len(suggestions):
            return [suggestions[choice]]
        elif choice == len(suggestions):
            # Custom alt-text
            custom_text = prompt("Enter custom alt-text").strip()
            if custom_text:
                custom_suggestion = AltTextSuggestion(
                    text=custom_text,
                    confidence=1.0,
                    method="user_input",
                    reasoning="User-provided alt-text",
                    accessibility_score=self._calculate_accessibility_score(custom_text, analysis)
                )
                return [custom_suggestion]

        return []


class AccessibilityAuditor:
    """Comprehensive accessibility auditing for EPUB content."""

    def __init__(self):
        self.alt_text_generator = IntelligentAltTextGenerator()
        self.logger = logging.getLogger(__name__)

    def audit_content_accessibility(
        self,
        content: str,
        images: List[Path],
        interactive: bool = False
    ) -> AccessibilityReport:
        """Perform comprehensive accessibility audit.

        Args:
            content: Document content
            images: List of image paths
            interactive: Whether to use interactive mode

        Returns:
            Accessibility report with issues and suggestions
        """
        print("♿ Performing comprehensive accessibility audit...")

        report = AccessibilityReport()

        # Audit images
        self._audit_images(images, content, report, interactive)

        # Audit content structure
        self._audit_content_structure(content, report)

        # Audit language and readability
        self._audit_language_accessibility(content, report)

        # Calculate overall score
        report.overall_score = self._calculate_overall_score(report)

        # WCAG compliance check
        report.wcag_compliance = self._check_wcag_compliance(report)

        print(f"✅ Accessibility audit complete. Score: {report.overall_score:.1%}")

        return report

    def _audit_images(
        self,
        images: List[Path],
        content: str,
        report: AccessibilityReport,
        interactive: bool
    ):
        """Audit image accessibility."""
        report.images_processed = len(images)

        for image_path in images:
            # Check if image has context in content
            image_name = image_path.stem
            context = self._extract_image_context(content, image_name)

            # Generate alt-text suggestions
            suggestions = self.alt_text_generator.generate_alt_text(
                image_path, context, interactive
            )

            if suggestions:
                report.alt_texts_generated += 1

                # Check for accessibility issues
                best_suggestion = suggestions[0]

                if not best_suggestion.text and not self.alt_text_generator.image_analyzer.analyze_image(image_path).is_decorative:
                    report.issues_found.append(AccessibilityIssue(
                        issue_type="missing_alt_text",
                        severity="high",
                        element=f"Image: {image_path.name}",
                        description="Image lacks descriptive alt-text",
                        suggestion=f"Add alt-text: \"{best_suggestion.text}\"",
                        auto_fixable=True
                    ))

                elif len(best_suggestion.text) > 200:
                    report.issues_found.append(AccessibilityIssue(
                        issue_type="alt_text_too_long",
                        severity="medium",
                        element=f"Image: {image_path.name}",
                        description="Alt-text is too long (>200 characters)",
                        suggestion="Consider shortening the description or using longdesc",
                        auto_fixable=False
                    ))

    def _audit_content_structure(self, content: str, report: AccessibilityReport):
        """Audit content structure for accessibility."""
        # Check heading structure
        headings = re.findall(r'<h([1-6])[^>]*>(.*?)</h[1-6]>', content, re.IGNORECASE | re.DOTALL)

        if headings:
            # Check for proper heading hierarchy
            heading_levels = [int(match[0]) for match in headings]

            for i, level in enumerate(heading_levels[1:], 1):
                prev_level = heading_levels[i-1]
                if level > prev_level + 1:
                    report.issues_found.append(AccessibilityIssue(
                        issue_type="heading_hierarchy",
                        severity="medium",
                        element=f"Heading {i+1}",
                        description=f"Heading jumps from h{prev_level} to h{level}",
                        suggestion="Use sequential heading levels (h1, h2, h3, etc.)",
                        auto_fixable=False
                    ))
        else:
            # No headings found
            if len(content) > 1000:  # Only flag for substantial content
                report.issues_found.append(AccessibilityIssue(
                    issue_type="no_headings",
                    severity="high",
                    element="Document structure",
                    description="Document lacks heading structure",
                    suggestion="Add headings to organize content",
                    auto_fixable=False
                ))

        # Check for tables without headers
        tables = re.findall(r'<table[^>]*>.*?</table>', content, re.IGNORECASE | re.DOTALL)
        for i, table in enumerate(tables):
            if '<th' not in table.lower() and 'scope=' not in table.lower():
                report.issues_found.append(AccessibilityIssue(
                    issue_type="table_headers",
                    severity="medium",
                    element=f"Table {i+1}",
                    description="Table lacks proper headers",
                    suggestion="Add <th> elements or scope attributes",
                    auto_fixable=False
                ))

    def _audit_language_accessibility(self, content: str, report: AccessibilityReport):
        """Audit language and readability for accessibility."""
        # Check for language attribute
        if 'lang=' not in content.lower():
            report.issues_found.append(AccessibilityIssue(
                issue_type="missing_language",
                severity="medium",
                element="Document",
                description="Document language not specified",
                suggestion="Add lang attribute to document",
                auto_fixable=True
            ))

        # Basic readability check
        sentences = re.split(r'[.!?]+', content)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

            if avg_sentence_length > 25:
                report.issues_found.append(AccessibilityIssue(
                    issue_type="complex_sentences",
                    severity="low",
                    element="Text content",
                    description=f"Average sentence length is high ({avg_sentence_length:.1f} words)",
                    suggestion="Consider breaking up long sentences for better readability",
                    auto_fixable=False
                ))

        # Check for color-only information
        color_words = ['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'brown']
        color_references = sum(content.lower().count(color) for color in color_words)

        if color_references > 5:  # Arbitrary threshold
            report.issues_found.append(AccessibilityIssue(
                issue_type="color_dependency",
                severity="medium",
                element="Text content",
                description="Content may rely on color for information",
                suggestion="Ensure information is conveyed through text as well as color",
                auto_fixable=False
            ))

    def _extract_image_context(self, content: str, image_name: str) -> str:
        """Extract context around image references."""
        # Look for image references in content
        image_patterns = [
            rf'{re.escape(image_name)}',
            rf'figure\s*\d*',
            rf'image\s*\d*'
        ]

        for pattern in image_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            if matches:
                # Get context around first match
                match = matches[0]
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                return content[start:end]

        return ""

    def _calculate_overall_score(self, report: AccessibilityReport) -> float:
        """Calculate overall accessibility score."""
        base_score = 1.0

        # Deduct points for issues
        severity_weights = {
            'critical': 0.2,
            'high': 0.1,
            'medium': 0.05,
            'low': 0.02
        }

        for issue in report.issues_found:
            weight = severity_weights.get(issue.severity, 0.02)
            base_score -= weight

        # Bonus for alt-text coverage
        if report.images_processed > 0:
            alt_text_coverage = report.alt_texts_generated / report.images_processed
            base_score += (alt_text_coverage - 0.5) * 0.1  # Bonus/penalty based on coverage

        return max(0.0, min(1.0, base_score))

    def _check_wcag_compliance(self, report: AccessibilityReport) -> Dict[str, bool]:
        """Check WCAG 2.1 compliance levels."""
        compliance = {
            'A': True,
            'AA': True,
            'AAA': True
        }

        # Check for critical issues that break WCAG compliance
        for issue in report.issues_found:
            if issue.severity == 'critical':
                compliance['A'] = False
                compliance['AA'] = False
                compliance['AAA'] = False
            elif issue.severity == 'high':
                compliance['AA'] = False
                compliance['AAA'] = False
            elif issue.severity == 'medium':
                compliance['AAA'] = False

        return compliance


def generate_image_alt_texts(
    images: List[Path],
    content: str = "",
    interactive: bool = False
) -> Dict[Path, str]:
    """Convenience function to generate alt-texts for multiple images.

    Args:
        images: List of image paths
        content: Document content for context
        interactive: Whether to use interactive mode

    Returns:
        Dictionary mapping image paths to alt-texts
    """
    generator = IntelligentAltTextGenerator()
    alt_texts = {}

    for image_path in images:
        # Extract context for this image
        image_name = image_path.stem
        context = ""
        if content:
            # Simple context extraction
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if image_name.lower() in line.lower():
                    # Get surrounding lines
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context = ' '.join(lines[start:end])
                    break

        suggestions = generator.generate_alt_text(image_path, context, interactive)
        if suggestions:
            alt_texts[image_path] = suggestions[0].text

    return alt_texts


def audit_accessibility(
    content: str,
    images: List[Path],
    interactive: bool = False
) -> AccessibilityReport:
    """Convenience function for accessibility auditing.

    Args:
        content: Document content
        images: List of image paths
        interactive: Whether to use interactive mode

    Returns:
        Accessibility audit report
    """
    auditor = AccessibilityAuditor()
    return auditor.audit_content_accessibility(content, images, interactive)