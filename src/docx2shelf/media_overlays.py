"""
Media Overlays (SMIL) support for EPUB read-aloud functionality.

Enables synchronized audio narration with text highlighting for enhanced
accessibility and user experience. Supports EPUB Media Overlays 3.0 specification.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.dom import minidom
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class AudioClip:
    """Information about an audio clip."""

    src: str  # Audio file path
    clip_begin: Optional[str] = None  # Start time (e.g., "12.5s")
    clip_end: Optional[str] = None  # End time (e.g., "15.2s")
    duration: Optional[float] = None  # Duration in seconds


@dataclass
class TextFragment:
    """Information about a text fragment."""

    src: str  # XHTML file path
    fragment_id: str  # Element ID in XHTML file
    text_content: str = ""  # Actual text content


@dataclass
class SyncPoint:
    """Synchronization point between text and audio."""

    id: str
    text: TextFragment
    audio: AudioClip
    duration: Optional[float] = None


@dataclass
class MediaOverlayConfig:
    """Configuration for media overlay generation."""

    narrator: str = "TTS"  # Narrator name
    active_class: str = "epub-media-overlay-active"  # CSS class for highlighting
    playback_active_class: str = "epub-media-overlay-playing"
    audio_format: str = "mp3"  # Preferred audio format
    generate_timestamps: bool = True
    auto_generate_clips: bool = True  # Auto-segment long audio files
    max_clip_duration: float = 30.0  # Maximum clip duration in seconds
    granularity: str = "sentence"  # sentence, paragraph, or word


@dataclass
class MediaOverlay:
    """Complete media overlay for a chapter/document."""

    id: str
    title: str
    text_src: str  # XHTML file path
    audio_src: Optional[str] = None  # Audio file path (if single file)
    duration: Optional[str] = None  # Total duration
    sync_points: List[SyncPoint] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


class MediaOverlayProcessor:
    """Processes and generates EPUB Media Overlays."""

    def __init__(self, config: Optional[MediaOverlayConfig] = None):
        self.config = config or MediaOverlayConfig()
        self.overlays: List[MediaOverlay] = []

    def create_overlay_from_audio(
        self,
        xhtml_path: Path,
        audio_path: Path,
        chapter_title: str = "",
        timestamps: Optional[List[Tuple[str, float, float]]] = None,
    ) -> MediaOverlay:
        """
        Create media overlay from XHTML and audio file.

        Args:
            xhtml_path: Path to XHTML file
            audio_path: Path to audio file
            chapter_title: Title for the overlay
            timestamps: List of (element_id, start_time, end_time) tuples

        Returns:
            MediaOverlay object
        """
        overlay_id = f"overlay_{xhtml_path.stem}"

        overlay = MediaOverlay(
            id=overlay_id,
            title=chapter_title or xhtml_path.stem,
            text_src=xhtml_path.name,
            audio_src=audio_path.name,
        )

        # Parse XHTML to get text elements
        text_elements = self._parse_xhtml_for_sync(xhtml_path)

        if timestamps:
            # Use provided timestamps
            sync_points = self._create_sync_points_from_timestamps(
                text_elements, audio_path.name, timestamps
            )
        else:
            # Auto-generate sync points
            sync_points = self._auto_generate_sync_points(text_elements, audio_path.name)

        overlay.sync_points = sync_points

        # Calculate total duration
        if sync_points:
            last_point = sync_points[-1]
            if last_point.audio.clip_end:
                overlay.duration = last_point.audio.clip_end

        self.overlays.append(overlay)
        return overlay

    def _parse_xhtml_for_sync(self, xhtml_path: Path) -> List[Dict[str, Any]]:
        """Parse XHTML file to extract syncable text elements."""
        text_elements = []

        try:
            with open(xhtml_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse with BeautifulSoup for better HTML handling
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(content, "html.parser")
            except ImportError:
                logger.warning("BeautifulSoup not available, using basic parsing")
                return self._basic_parse_xhtml(content)

            # Find elements suitable for synchronization
            sync_elements = soup.find_all(
                ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]
            )

            for i, elem in enumerate(sync_elements):
                # Generate ID if not present
                elem_id = elem.get("id")
                if not elem_id:
                    elem_id = f"sync_{i:04d}"
                    elem["id"] = elem_id

                text_content = elem.get_text().strip()
                if text_content:  # Only include elements with text
                    text_elements.append(
                        {"id": elem_id, "text": text_content, "tag": elem.name, "element": elem}
                    )

            # Update XHTML file with generated IDs
            updated_content = str(soup)
            with open(xhtml_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

        except Exception as e:
            logger.error(f"Failed to parse XHTML file {xhtml_path}: {e}")

        return text_elements

    def _basic_parse_xhtml(self, content: str) -> List[Dict[str, Any]]:
        """Basic XHTML parsing fallback."""
        text_elements = []

        # Simple regex-based extraction
        element_pattern = r"<(p|h[1-6]|li|blockquote)([^>]*?)>(.*?)</\1>"
        matches = re.finditer(element_pattern, content, re.DOTALL | re.IGNORECASE)

        for i, match in enumerate(matches):
            tag, attrs, text_content = match.groups()

            # Extract or generate ID
            id_match = re.search(r'id=["\']([^"\']+)["\']', attrs)
            elem_id = id_match.group(1) if id_match else f"sync_{i:04d}"

            # Clean text content
            text_content = re.sub(r"<[^>]+>", "", text_content).strip()

            if text_content:
                text_elements.append(
                    {"id": elem_id, "text": text_content, "tag": tag.lower(), "element": None}
                )

        return text_elements

    def _create_sync_points_from_timestamps(
        self,
        text_elements: List[Dict[str, Any]],
        audio_file: str,
        timestamps: List[Tuple[str, float, float]],
    ) -> List[SyncPoint]:
        """Create sync points from provided timestamps."""
        sync_points = []
        timestamp_dict = {elem_id: (start, end) for elem_id, start, end in timestamps}

        for text_elem in text_elements:
            elem_id = text_elem["id"]

            if elem_id in timestamp_dict:
                start_time, end_time = timestamp_dict[elem_id]

                text_fragment = TextFragment(
                    src=text_elem.get("src", ""),
                    fragment_id=elem_id,
                    text_content=text_elem["text"],
                )

                audio_clip = AudioClip(
                    src=audio_file,
                    clip_begin=f"{start_time}s",
                    clip_end=f"{end_time}s",
                    duration=end_time - start_time,
                )

                sync_point = SyncPoint(
                    id=f"sync_{elem_id}",
                    text=text_fragment,
                    audio=audio_clip,
                    duration=end_time - start_time,
                )

                sync_points.append(sync_point)

        return sync_points

    def _auto_generate_sync_points(
        self, text_elements: List[Dict[str, Any]], audio_file: str
    ) -> List[SyncPoint]:
        """Auto-generate sync points based on text length."""
        sync_points = []

        if not text_elements:
            return sync_points

        # Estimate timing based on average reading speed
        # Typical reading speed: 200-250 words per minute
        words_per_second = 3.5  # Conservative estimate

        current_time = 0.0

        for text_elem in text_elements:
            text_content = text_elem["text"]
            word_count = len(text_content.split())

            # Estimate duration for this text segment
            estimated_duration = max(1.0, word_count / words_per_second)

            # Add pauses for headings and paragraph breaks
            if text_elem["tag"] in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                estimated_duration += 0.5  # Extra pause for headings

            text_fragment = TextFragment(
                src="",  # Will be set by caller
                fragment_id=text_elem["id"],
                text_content=text_content,
            )

            audio_clip = AudioClip(
                src=audio_file,
                clip_begin=f"{current_time:.1f}s",
                clip_end=f"{current_time + estimated_duration:.1f}s",
                duration=estimated_duration,
            )

            sync_point = SyncPoint(
                id=f"sync_{text_elem['id']}",
                text=text_fragment,
                audio=audio_clip,
                duration=estimated_duration,
            )

            sync_points.append(sync_point)
            current_time += estimated_duration

        return sync_points

    def generate_smil_file(self, overlay: MediaOverlay, output_path: Path) -> None:
        """Generate SMIL file for media overlay."""

        # Create SMIL XML structure
        smil = ET.Element(
            "smil",
            {
                "xmlns": "http://www.w3.org/ns/SMIL",
                "xmlns:epub": "http://www.idpf.org/2007/ops",
                "version": "3.0",
            },
        )

        # Head section
        head = ET.SubElement(smil, "head")

        # Metadata
        metadata = ET.SubElement(head, "metadata", {"xmlns:dc": "http://purl.org/dc/elements/1.1/"})

        if overlay.title:
            title = ET.SubElement(metadata, "dc:title")
            title.text = overlay.title

        if self.config.narrator:
            narrator = ET.SubElement(
                metadata, "meta", {"name": "narrator", "content": self.config.narrator}
            )

        if overlay.duration:
            duration = ET.SubElement(
                metadata, "meta", {"name": "total-duration", "content": overlay.duration}
            )

        # CSS class for highlighting
        highlight_class = ET.SubElement(
            metadata, "meta", {"name": "active-class", "content": self.config.active_class}
        )

        # Body section
        body = ET.SubElement(smil, "body")

        # Main sequence
        main_seq = ET.SubElement(
            body, "seq", {"id": "main_sequence", "epub:textref": overlay.text_src}
        )

        # Add sync points
        for sync_point in overlay.sync_points:
            par = ET.SubElement(main_seq, "par", {"id": sync_point.id})

            # Text element
            text_elem = ET.SubElement(
                par, "text", {"src": f"{overlay.text_src}#{sync_point.text.fragment_id}"}
            )

            # Audio element
            audio_attrs = {"src": sync_point.audio.src}

            if sync_point.audio.clip_begin:
                audio_attrs["clipBegin"] = sync_point.audio.clip_begin

            if sync_point.audio.clip_end:
                audio_attrs["clipEnd"] = sync_point.audio.clip_end

            audio_elem = ET.SubElement(par, "audio", audio_attrs)

        # Write SMIL file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Pretty print XML
        rough_string = ET.tostring(smil, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        # Remove extra blank lines
        lines = [line for line in pretty_xml.split("\n") if line.strip()]
        final_xml = "\n".join(lines)

        output_path.write_text(final_xml, encoding="utf-8")
        logger.info(f"Generated SMIL file: {output_path}")

    def generate_overlay_css(self) -> str:
        """Generate CSS for media overlay highlighting."""
        css = f"""
/* Media Overlay CSS */
/* Active text highlighting during narration */
.{self.config.active_class} {{
    background-color: #ffeb3b !important;
    color: #000000 !important;
    outline: 2px solid #ff9800;
    border-radius: 3px;
    padding: 0 2px;
    transition: all 0.2s ease-in-out;
}}

.{self.config.playback_active_class} {{
    background-color: #4caf50 !important;
    color: #ffffff !important;
    outline: 2px solid #2e7d32;
}}

/* Ensure text remains readable during highlighting */
.{self.config.active_class} a,
.{self.config.active_class} em,
.{self.config.active_class} strong {{
    color: inherit !important;
}}

/* Support for different reading modes */
@media (prefers-color-scheme: dark) {{
    .{self.config.active_class} {{
        background-color: #ffa726 !important;
        color: #000000 !important;
        outline-color: #ff5722;
    }}

    .{self.config.playback_active_class} {{
        background-color: #66bb6a !important;
        color: #000000 !important;
        outline-color: #388e3c;
    }}
}}

/* High contrast mode support */
@media (prefers-contrast: high) {{
    .{self.config.active_class} {{
        background-color: #ffff00 !important;
        color: #000000 !important;
        outline: 3px solid #000000;
    }}
}}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {{
    .{self.config.active_class},
    .{self.config.playback_active_class} {{
        transition: none;
    }}
}}

/* Print styles - hide highlighting */
@media print {{
    .{self.config.active_class},
    .{self.config.playback_active_class} {{
        background-color: transparent !important;
        color: inherit !important;
        outline: none !important;
    }}
}}
"""
        return css

    def get_overlay_count(self) -> int:
        """Get the number of generated overlays."""
        return len(self.overlays)

    def get_total_duration(self) -> float:
        """Get total duration of all overlays in seconds."""
        total = 0.0
        for overlay in self.overlays:
            if overlay.duration:
                # Parse duration string (e.g., "123.5s")
                duration_str = overlay.duration.rstrip("s")
                try:
                    total += float(duration_str)
                except ValueError:
                    pass
        return total

    def generate_navigation_overlay(self) -> str:
        """Generate navigation overlay for EPUB navigation document."""
        nav_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<smil xmlns="http://www.w3.org/ns/SMIL"
      xmlns:epub="http://www.idpf.org/2007/ops"
      version="3.0">
  <head>
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
      <dc:title>Media Overlay Navigation</dc:title>
      <meta name="active-class" content="{self.config.active_class}"/>
    </metadata>
  </head>
  <body>
    <seq id="nav_sequence">
"""

        for i, overlay in enumerate(self.overlays):
            nav_xml += f"""      <par id="nav_{i}">
        <text src="{overlay.text_src}"/>
        <audio src="{overlay.audio_src or 'audio/chapter.mp3'}"/>
      </par>
"""

        nav_xml += """    </seq>
  </body>
</smil>"""

        return nav_xml

    def validate_overlay(self, overlay: MediaOverlay) -> List[str]:
        """Validate media overlay for common issues."""
        issues = []

        if not overlay.sync_points:
            issues.append("No sync points defined")

        # Check for missing files
        if overlay.audio_src and not Path(overlay.audio_src).exists():
            issues.append(f"Audio file not found: {overlay.audio_src}")

        # Check sync point consistency
        for i, sync_point in enumerate(overlay.sync_points):
            if not sync_point.text.fragment_id:
                issues.append(f"Sync point {i} missing text fragment ID")

            if not sync_point.audio.src:
                issues.append(f"Sync point {i} missing audio source")

            # Check timing
            if sync_point.audio.clip_begin and sync_point.audio.clip_end:
                try:
                    begin = float(sync_point.audio.clip_begin.rstrip("s"))
                    end = float(sync_point.audio.clip_end.rstrip("s"))
                    if begin >= end:
                        issues.append(f"Sync point {i} has invalid timing: begin >= end")
                except ValueError:
                    issues.append(f"Sync point {i} has invalid time format")

        return issues


def create_media_overlay(
    xhtml_path: Path,
    audio_path: Path,
    output_path: Path,
    chapter_title: str = "",
    timestamps: Optional[List[Tuple[str, float, float]]] = None,
    config: Optional[MediaOverlayConfig] = None,
) -> MediaOverlay:
    """
    Create media overlay from XHTML and audio files.

    Args:
        xhtml_path: Path to XHTML file
        audio_path: Path to audio file
        output_path: Path for output SMIL file
        chapter_title: Title for the overlay
        timestamps: Optional list of (element_id, start_time, end_time)
        config: Media overlay configuration

    Returns:
        Generated MediaOverlay object
    """
    processor = MediaOverlayProcessor(config)
    overlay = processor.create_overlay_from_audio(xhtml_path, audio_path, chapter_title, timestamps)
    processor.generate_smil_file(overlay, output_path)
    return overlay
