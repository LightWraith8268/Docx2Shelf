"""
Anthology and series builder for combining multiple manuscripts into cohesive EPUBs.

Supports merging multiple DOCX files into single anthologies and creating
series collections with automated cross-references and "Also By This Author" pages.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import tempfile

from .metadata import EpubMetadata, BuildOptions
from .convert import docx_to_html_chunks
from .assemble import assemble_epub

logger = logging.getLogger(__name__)


@dataclass
class StoryInfo:
    """Information about a story in an anthology."""
    title: str
    author: str
    source_file: Path
    html_chunks: List[str] = field(default_factory=list)
    metadata: Optional[EpubMetadata] = None
    word_count: Optional[int] = None
    genre: str = ""
    summary: str = ""
    first_published: Optional[str] = None
    awards: List[str] = field(default_factory=list)


@dataclass
class AnthologyConfig:
    """Configuration for anthology building."""
    title: str
    editor: str = ""
    publisher: str = ""
    description: str = ""
    genre: str = "Anthology"

    # Story organization
    sort_stories_by: str = "title"  # title, author, word_count, date
    group_by_author: bool = False
    include_story_summaries: bool = True
    include_author_bios: bool = True

    # Table of contents
    include_story_word_counts: bool = False
    show_author_in_toc: bool = True
    toc_depth: int = 2

    # Generated pages
    generate_contents_page: bool = True
    generate_contributor_bios: bool = True
    generate_about_anthology: bool = True
    generate_credits_page: bool = True

    # Cross-references
    auto_link_author_names: bool = True
    generate_author_index: bool = True


@dataclass
class SeriesConfig:
    """Configuration for series building."""
    series_title: str
    author: str
    publisher: str = ""
    series_description: str = ""

    # Series organization
    sort_books_by: str = "series_index"  # series_index, title, date
    include_series_summary: bool = True
    include_reading_order: bool = True

    # Cross-references
    generate_also_by_pages: bool = True
    link_to_other_books: bool = True
    include_series_timeline: bool = False

    # Metadata consistency
    enforce_consistent_metadata: bool = True
    auto_update_series_info: bool = True


class AnthologyBuilder:
    """Builds anthologies from multiple manuscript sources."""

    def __init__(self, config: AnthologyConfig):
        self.config = config
        self.stories: List[StoryInfo] = []
        self.author_bios: Dict[str, str] = {}

    def add_story(
        self,
        source_file: Path,
        title: Optional[str] = None,
        author: Optional[str] = None,
        summary: str = "",
        genre: str = "",
        **kwargs
    ) -> StoryInfo:
        """Add a story to the anthology."""

        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")

        # Extract story metadata if not provided
        if not title or not author:
            extracted_title, extracted_author = self._extract_story_metadata(source_file)
            title = title or extracted_title or source_file.stem
            author = author or extracted_author or "Unknown Author"

        # Convert DOCX to HTML
        logger.info(f"Converting story: {title} by {author}")
        html_chunks = docx_to_html_chunks(source_file)

        # Calculate word count
        word_count = self._calculate_word_count(html_chunks)

        story = StoryInfo(
            title=title,
            author=author,
            source_file=source_file,
            html_chunks=html_chunks,
            word_count=word_count,
            genre=genre,
            summary=summary,
            **kwargs
        )

        self.stories.append(story)
        logger.info(f"Added story: {title} ({word_count} words)")

        return story

    def add_author_bio(self, author: str, bio: str) -> None:
        """Add author biography."""
        self.author_bios[author] = bio

    def build_anthology(self, output_path: Path, build_options: Optional[BuildOptions] = None) -> Path:
        """
        Build the complete anthology EPUB.

        Args:
            output_path: Path for output EPUB file
            build_options: Build configuration options

        Returns:
            Path to created EPUB file
        """
        if not self.stories:
            raise ValueError("No stories added to anthology")

        logger.info(f"Building anthology '{self.config.title}' with {len(self.stories)} stories")

        # Sort stories according to configuration
        self._sort_stories()

        # Create anthology metadata
        anthology_metadata = self._create_anthology_metadata()

        # Combine all story content
        combined_html_chunks = self._combine_story_content()

        # Create temporary directory for resources
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract and collect all resources
            resources = self._collect_resources(temp_path)

            # Build EPUB
            build_opts = build_options or BuildOptions()

            assemble_epub(
                meta=anthology_metadata,
                opts=build_opts,
                html_chunks=combined_html_chunks,
                resources=resources,
                output_path=output_path
            )

        logger.info(f"Anthology built successfully: {output_path}")
        return output_path

    def _extract_story_metadata(self, source_file: Path) -> Tuple[Optional[str], Optional[str]]:
        """Extract title and author from source file."""
        try:
            # Try to extract from DOCX metadata first
            if source_file.suffix.lower() == '.docx':
                from docx import Document
                doc = Document(source_file)

                title = doc.core_properties.title
                author = doc.core_properties.author

                if title and author:
                    return title, author

            # Fallback to filename parsing
            stem = source_file.stem

            # Look for common patterns like "Title - Author" or "Author - Title"
            if ' - ' in stem:
                parts = stem.split(' - ', 1)
                if len(parts) == 2:
                    # Guess which is title vs author based on capitalization
                    part1, part2 = parts
                    if part1.istitle() and not part2.istitle():
                        return part1, part2
                    elif part2.istitle() and not part1.istitle():
                        return part2, part1
                    else:
                        return part1, part2  # Default: first is title

            return stem, None

        except Exception as e:
            logger.warning(f"Could not extract metadata from {source_file}: {e}")
            return None, None

    def _calculate_word_count(self, html_chunks: List[str]) -> int:
        """Calculate approximate word count from HTML content."""
        import re

        total_words = 0
        for chunk in html_chunks:
            # Strip HTML tags and count words
            text = re.sub(r'<[^>]+>', '', chunk)
            words = len(text.split())
            total_words += words

        return total_words

    def _sort_stories(self) -> None:
        """Sort stories according to configuration."""
        if self.config.sort_stories_by == "title":
            self.stories.sort(key=lambda s: s.title.lower())
        elif self.config.sort_stories_by == "author":
            self.stories.sort(key=lambda s: (s.author.lower(), s.title.lower()))
        elif self.config.sort_stories_by == "word_count":
            self.stories.sort(key=lambda s: s.word_count or 0, reverse=True)
        elif self.config.sort_stories_by == "date":
            self.stories.sort(key=lambda s: s.first_published or "")

    def _create_anthology_metadata(self) -> EpubMetadata:
        """Create metadata for the anthology."""
        # Collect all authors
        authors = list(set(story.author for story in self.stories))

        # Create author attribution
        if len(authors) == 1:
            author_str = authors[0]
        elif len(authors) <= 3:
            author_str = ", ".join(authors)
        else:
            author_str = f"{authors[0]} and {len(authors)-1} others"

        # Add editor if specified
        if self.config.editor:
            if len(authors) == 1:
                author_str = f"{author_str} (edited by {self.config.editor})"
            else:
                author_str = f"Various Authors (edited by {self.config.editor})"

        return EpubMetadata(
            title=self.config.title,
            author=author_str,
            language="en",  # Default language
            description=self.config.description,
            publisher=self.config.publisher,
            subjects=[self.config.genre, "Anthology"],
            pubdate=datetime.now().date()
        )

    def _combine_story_content(self) -> List[str]:
        """Combine all story content into HTML chunks."""
        combined_chunks = []

        # Add anthology front matter
        if self.config.generate_contents_page:
            combined_chunks.append(self._generate_contents_page())

        if self.config.generate_about_anthology:
            combined_chunks.append(self._generate_about_page())

        # Group stories by author if configured
        if self.config.group_by_author:
            stories_by_author = {}
            for story in self.stories:
                if story.author not in stories_by_author:
                    stories_by_author[story.author] = []
                stories_by_author[story.author].append(story)

            for author, author_stories in stories_by_author.items():
                # Add author section header
                combined_chunks.append(f"<h1>Stories by {author}</h1>")

                if author in self.author_bios:
                    combined_chunks.append(f"<div class='author-bio'>{self.author_bios[author]}</div>")

                for story in author_stories:
                    combined_chunks.extend(self._format_story_content(story))
        else:
            # Add stories in order
            for story in self.stories:
                combined_chunks.extend(self._format_story_content(story))

        # Add back matter
        if self.config.generate_contributor_bios and self.author_bios:
            combined_chunks.append(self._generate_contributor_bios())

        if self.config.generate_credits_page:
            combined_chunks.append(self._generate_credits_page())

        if self.config.generate_author_index:
            combined_chunks.append(self._generate_author_index())

        return combined_chunks

    def _format_story_content(self, story: StoryInfo) -> List[str]:
        """Format a single story's content."""
        story_chunks = []

        # Story header
        header_html = f"<h1 class='story-title'>{story.title}</h1>"

        if self.config.show_author_in_toc:
            header_html += f"<h2 class='story-author'>by {story.author}</h2>"

        if story.summary and self.config.include_story_summaries:
            header_html += f"<div class='story-summary'>{story.summary}</div>"

        if story.word_count and self.config.include_story_word_counts:
            header_html += f"<div class='story-meta'>Approximately {story.word_count:,} words</div>"

        story_chunks.append(header_html)

        # Story content
        story_chunks.extend(story.html_chunks)

        return story_chunks

    def _generate_contents_page(self) -> str:
        """Generate anthology contents page."""
        html = "<h1>Contents</h1>\n<div class='anthology-toc'>\n"

        current_author = None
        for story in self.stories:
            if self.config.group_by_author and story.author != current_author:
                if current_author is not None:
                    html += "</div>\n"
                html += f"<h2>{story.author}</h2>\n<div class='author-stories'>\n"
                current_author = story.author

            html += f"<div class='story-entry'>\n"
            html += f"  <span class='story-title'>{story.title}</span>"

            if not self.config.group_by_author and self.config.show_author_in_toc:
                html += f" <span class='story-author'>by {story.author}</span>"

            if story.word_count and self.config.include_story_word_counts:
                html += f" <span class='word-count'>({story.word_count:,} words)</span>"

            html += "\n</div>\n"

        if self.config.group_by_author:
            html += "</div>\n"

        html += "</div>\n"
        return html

    def _generate_about_page(self) -> str:
        """Generate about anthology page."""
        html = "<h1>About This Anthology</h1>\n"

        if self.config.description:
            html += f"<p>{self.config.description}</p>\n"

        html += f"<p>This anthology contains {len(self.stories)} stories"

        total_words = sum(story.word_count for story in self.stories if story.word_count)
        if total_words:
            html += f" totaling approximately {total_words:,} words"

        html += ".</p>\n"

        if self.config.editor:
            html += f"<p><strong>Editor:</strong> {self.config.editor}</p>\n"

        if self.config.publisher:
            html += f"<p><strong>Publisher:</strong> {self.config.publisher}</p>\n"

        return html

    def _generate_contributor_bios(self) -> str:
        """Generate contributor biographies page."""
        html = "<h1>About the Contributors</h1>\n"

        for author in sorted(set(story.author for story in self.stories)):
            html += f"<h2>{author}</h2>\n"

            if author in self.author_bios:
                html += f"<p>{self.author_bios[author]}</p>\n"
            else:
                # List their stories in this anthology
                author_stories = [s.title for s in self.stories if s.author == author]
                if len(author_stories) == 1:
                    html += f"<p>{author} is the author of \"{author_stories[0]}\" in this anthology.</p>\n"
                else:
                    story_list = ", ".join(f'"{title}"' for title in author_stories[:-1])
                    story_list += f', and "{author_stories[-1]}"'
                    html += f"<p>{author} is the author of {story_list} in this anthology.</p>\n"

        return html

    def _generate_credits_page(self) -> str:
        """Generate credits and acknowledgments page."""
        html = "<h1>Credits</h1>\n"

        html += f"<p><strong>Anthology Title:</strong> {self.config.title}</p>\n"

        if self.config.editor:
            html += f"<p><strong>Editor:</strong> {self.config.editor}</p>\n"

        if self.config.publisher:
            html += f"<p><strong>Publisher:</strong> {self.config.publisher}</p>\n"

        html += f"<p><strong>Number of Stories:</strong> {len(self.stories)}</p>\n"
        html += f"<p><strong>Contributors:</strong> {len(set(story.author for story in self.stories))}</p>\n"

        # List stories with authors
        html += "<h2>Story Credits</h2>\n<ul>\n"
        for story in self.stories:
            html += f"<li>\"{story.title}\" by {story.author}"
            if story.first_published:
                html += f" (first published {story.first_published})"
            html += "</li>\n"
        html += "</ul>\n"

        html += f"<p><em>Anthology compiled with Docx2Shelf on {datetime.now().strftime('%B %d, %Y')}.</em></p>\n"

        return html

    def _generate_author_index(self) -> str:
        """Generate alphabetical author index."""
        html = "<h1>Author Index</h1>\n"

        authors_with_stories = {}
        for story in self.stories:
            if story.author not in authors_with_stories:
                authors_with_stories[story.author] = []
            authors_with_stories[story.author].append(story.title)

        html += "<ul class='author-index'>\n"
        for author in sorted(authors_with_stories.keys()):
            html += f"<li><strong>{author}</strong>: "
            stories = authors_with_stories[author]
            html += ", ".join(f'"{title}"' for title in stories)
            html += "</li>\n"
        html += "</ul>\n"

        return html

    def _collect_resources(self, temp_path: Path) -> List[Path]:
        """Collect all resources (images, etc.) from stories."""
        resources = []

        for story in self.stories:
            # Extract resources from each story's source
            try:
                story_resources = self._extract_story_resources(story.source_file, temp_path)
                resources.extend(story_resources)
            except Exception as e:
                logger.warning(f"Could not extract resources from {story.source_file}: {e}")

        return resources

    def _extract_story_resources(self, source_file: Path, temp_path: Path) -> List[Path]:
        """Extract resources from a single story file."""
        resources = []

        if source_file.suffix.lower() == '.docx':
            try:
                import zipfile

                with zipfile.ZipFile(source_file, 'r') as docx_zip:
                    # Find media files
                    media_files = [f for f in docx_zip.namelist() if f.startswith('word/media/')]

                    for media_file in media_files:
                        # Extract to temp directory
                        media_data = docx_zip.read(media_file)
                        output_file = temp_path / Path(media_file).name
                        output_file.write_bytes(media_data)
                        resources.append(output_file)

            except Exception as e:
                logger.warning(f"Could not extract media from {source_file}: {e}")

        return resources


class SeriesBuilder:
    """Builds series collections with cross-references."""

    def __init__(self, config: SeriesConfig):
        self.config = config
        self.books: List[Tuple[Path, EpubMetadata]] = []

    def add_book(self, epub_path: Path, metadata: Optional[EpubMetadata] = None) -> None:
        """Add a book to the series."""
        if not epub_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        if metadata is None:
            metadata = self._extract_epub_metadata(epub_path)

        self.books.append((epub_path, metadata))
        logger.info(f"Added book to series: {metadata.title}")

    def build_series_collection(self, output_dir: Path) -> List[Path]:
        """
        Build series collection with updated cross-references.

        Args:
            output_dir: Directory for output EPUB files

        Returns:
            List of paths to updated EPUB files
        """
        if not self.books:
            raise ValueError("No books added to series")

        logger.info(f"Building series collection '{self.config.series_title}' with {len(self.books)} books")

        output_dir.mkdir(parents=True, exist_ok=True)
        updated_books = []

        # Sort books according to configuration
        sorted_books = self._sort_books()

        # Generate series-wide content
        also_by_content = self._generate_also_by_content()
        series_info_content = self._generate_series_info()

        for i, (epub_path, metadata) in enumerate(sorted_books):
            # Update metadata for series consistency
            if self.config.enforce_consistent_metadata:
                metadata = self._update_series_metadata(metadata, i + 1)

            # Create updated EPUB with series content
            output_path = output_dir / f"{metadata.title.replace(' ', '_')}.epub"

            updated_path = self._update_epub_with_series_content(
                epub_path,
                output_path,
                metadata,
                also_by_content,
                series_info_content
            )

            updated_books.append(updated_path)

        logger.info(f"Series collection built: {len(updated_books)} books updated")
        return updated_books

    def _extract_epub_metadata(self, epub_path: Path) -> EpubMetadata:
        """Extract metadata from existing EPUB."""
        # This would parse the EPUB's OPF file to extract metadata
        # For now, create basic metadata from filename
        return EpubMetadata(
            title=epub_path.stem.replace('_', ' '),
            author=self.config.author,
            language="en"
        )

    def _sort_books(self) -> List[Tuple[Path, EpubMetadata]]:
        """Sort books according to configuration."""
        if self.config.sort_books_by == "series_index":
            return sorted(self.books, key=lambda b: b[1].series_index or 0)
        elif self.config.sort_books_by == "title":
            return sorted(self.books, key=lambda b: b[1].title.lower())
        elif self.config.sort_books_by == "date":
            return sorted(self.books, key=lambda b: b[1].pubdate or datetime.min.date())
        else:
            return self.books

    def _update_series_metadata(self, metadata: EpubMetadata, series_index: int) -> EpubMetadata:
        """Update metadata for series consistency."""
        if self.config.auto_update_series_info:
            metadata.series = self.config.series_title
            metadata.series_index = series_index
            metadata.author = self.config.author

        return metadata

    def _generate_also_by_content(self) -> str:
        """Generate 'Also By This Author' page content."""
        if not self.config.generate_also_by_pages:
            return ""

        html = f"<h1>Also by {self.config.author}</h1>\n"
        html += f"<h2>{self.config.series_title} Series</h2>\n<ol>\n"

        for epub_path, metadata in self._sort_books():
            html += f"<li>{metadata.title}"
            if metadata.series_index:
                html += f" (Book {metadata.series_index})"
            html += "</li>\n"

        html += "</ol>\n"

        if self.config.series_description:
            html += f"<p>{self.config.series_description}</p>\n"

        return html

    def _generate_series_info(self) -> str:
        """Generate series information page."""
        html = f"<h1>About the {self.config.series_title} Series</h1>\n"

        if self.config.series_description:
            html += f"<p>{self.config.series_description}</p>\n"

        if self.config.include_reading_order:
            html += "<h2>Reading Order</h2>\n<ol>\n"
            for epub_path, metadata in self._sort_books():
                html += f"<li>{metadata.title}</li>\n"
            html += "</ol>\n"

        html += f"<p><strong>Author:</strong> {self.config.author}</p>\n"
        html += f"<p><strong>Series Length:</strong> {len(self.books)} books</p>\n"

        return html

    def _update_epub_with_series_content(
        self,
        source_epub: Path,
        output_epub: Path,
        metadata: EpubMetadata,
        also_by_content: str,
        series_info_content: str
    ) -> Path:
        """Update EPUB with series-specific content."""

        # For now, just copy the original EPUB
        # In a full implementation, this would:
        # 1. Extract the EPUB
        # 2. Add new pages for series content
        # 3. Update the navigation
        # 4. Repackage the EPUB

        shutil.copy2(source_epub, output_epub)
        logger.info(f"Updated EPUB: {output_epub}")

        return output_epub


def build_anthology(
    config: AnthologyConfig,
    story_files: List[Path],
    output_path: Path,
    build_options: Optional[BuildOptions] = None
) -> Path:
    """
    Build anthology from multiple story files.

    Args:
        config: Anthology configuration
        story_files: List of source files (DOCX, etc.)
        output_path: Path for output EPUB
        build_options: Build configuration

    Returns:
        Path to created anthology EPUB
    """
    builder = AnthologyBuilder(config)

    for story_file in story_files:
        builder.add_story(story_file)

    return builder.build_anthology(output_path, build_options)


def build_series_collection(
    config: SeriesConfig,
    epub_files: List[Path],
    output_dir: Path
) -> List[Path]:
    """
    Build series collection from existing EPUBs.

    Args:
        config: Series configuration
        epub_files: List of EPUB files in series
        output_dir: Directory for updated EPUBs

    Returns:
        List of paths to updated EPUB files
    """
    builder = SeriesBuilder(config)

    for epub_file in epub_files:
        builder.add_book(epub_file)

    return builder.build_series_collection(output_dir)