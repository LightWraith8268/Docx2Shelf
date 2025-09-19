"""
Figure and table processing for EPUB semantic markup.

This module handles the conversion of images and tables into proper semantic HTML5
markup with figcaption elements and generates Lists of Figures/Tables pages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote

from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)


@dataclass
class FigureConfig:
    """Configuration for figure processing."""
    auto_number: bool = True
    number_format: str = "Figure {number}"
    caption_class: str = "figure-caption"
    figure_class: str = "figure"
    list_of_figures_title: str = "List of Figures"
    list_of_tables_title: str = "List of Tables"
    generate_lists: bool = True


@dataclass
class FigureInfo:
    """Information about a figure or table."""
    id: str
    number: int
    caption: str
    alt_text: str
    src: str
    chapter_title: str
    chapter_id: str
    type: str  # 'figure' or 'table'


class FigureProcessor:
    """Processes figures and tables in EPUB content."""

    def __init__(self, config: Optional[FigureConfig] = None):
        self.config = config or FigureConfig()
        self.figures: List[FigureInfo] = []
        self.tables: List[FigureInfo] = []
        self.figure_counter = 0
        self.table_counter = 0

    def process_content(self, html_content: str, chapter_title: str = "", chapter_id: str = "") -> str:
        """Process HTML content to wrap images and tables in semantic markup."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Process images
        self._process_images(soup, chapter_title, chapter_id)

        # Process tables
        self._process_tables(soup, chapter_title, chapter_id)

        return str(soup)

    def _process_images(self, soup: BeautifulSoup, chapter_title: str, chapter_id: str) -> None:
        """Convert img tags to semantic figure elements."""
        images = soup.find_all('img')

        for img in images:
            # Skip if already wrapped in figure
            if img.find_parent('figure'):
                continue

            # Generate figure info
            self.figure_counter += 1
            figure_id = f"figure-{self.figure_counter}"

            # Extract or generate caption
            caption = self._extract_image_caption(img)
            if not caption and self.config.auto_number:
                caption = self.config.number_format.format(number=self.figure_counter)

            # Create figure element
            figure = soup.new_tag('figure', **{
                'class': self.config.figure_class,
                'id': figure_id
            })

            # Move img into figure
            img_parent = img.parent
            img.extract()
            figure.append(img)

            # Add figcaption if we have a caption
            if caption:
                figcaption = soup.new_tag('figcaption', **{
                    'class': self.config.caption_class
                })
                figcaption.string = caption
                figure.append(figcaption)

            # Insert figure where img was
            if img_parent:
                img_parent.append(figure)

            # Store figure info
            self.figures.append(FigureInfo(
                id=figure_id,
                number=self.figure_counter,
                caption=caption,
                alt_text=img.get('alt', ''),
                src=img.get('src', ''),
                chapter_title=chapter_title,
                chapter_id=chapter_id,
                type='figure'
            ))

    def _process_tables(self, soup: BeautifulSoup, chapter_title: str, chapter_id: str) -> None:
        """Wrap tables in semantic figure elements."""
        tables = soup.find_all('table')

        for table in tables:
            # Skip if already wrapped in figure
            if table.find_parent('figure'):
                continue

            # Generate table info
            self.table_counter += 1
            table_id = f"table-{self.table_counter}"

            # Extract or generate caption
            caption = self._extract_table_caption(table)
            if not caption and self.config.auto_number:
                caption = f"Table {self.table_counter}"

            # Create figure element (tables use figure too in HTML5)
            figure = soup.new_tag('figure', **{
                'class': 'table-figure',
                'id': table_id
            })

            # Move table into figure
            table_parent = table.parent
            table.extract()

            # Add figcaption if we have a caption (before table for tables)
            if caption:
                figcaption = soup.new_tag('figcaption', **{
                    'class': 'table-caption'
                })
                figcaption.string = caption
                figure.append(figcaption)

            figure.append(table)

            # Insert figure where table was
            if table_parent:
                table_parent.append(figure)

            # Store table info
            self.tables.append(FigureInfo(
                id=table_id,
                number=self.table_counter,
                caption=caption,
                alt_text='',  # Tables don't have alt text
                src='',       # Tables don't have src
                chapter_title=chapter_title,
                chapter_id=chapter_id,
                type='table'
            ))

    def _extract_image_caption(self, img: Tag) -> str:
        """Extract caption text from image context."""
        # Check for title attribute
        if img.get('title'):
            return img['title']

        # Check for alt attribute as fallback
        if img.get('alt'):
            return img['alt']

        # Look for caption in surrounding elements
        parent = img.parent
        if parent:
            # Check for caption class nearby
            caption_elem = parent.find(class_=re.compile(r'caption|figure-caption'))
            if caption_elem:
                return caption_elem.get_text().strip()

            # Check for em/i elements that might be captions
            next_sibling = img.find_next_sibling(['em', 'i', 'p'])
            if next_sibling and len(next_sibling.get_text().strip()) < 200:
                text = next_sibling.get_text().strip()
                if text.startswith(('Figure', 'Fig.', 'Image')):
                    return text

        return ""

    def _extract_table_caption(self, table: Tag) -> str:
        """Extract caption text from table context."""
        # Check for existing caption element
        caption_elem = table.find('caption')
        if caption_elem:
            return caption_elem.get_text().strip()

        # Look for preceding paragraph that might be a caption
        prev_sibling = table.find_previous_sibling('p')
        if prev_sibling:
            text = prev_sibling.get_text().strip()
            if text.startswith(('Table', 'Tab.')):
                return text

        return ""

    def generate_list_of_figures(self) -> str:
        """Generate HTML for List of Figures page."""
        if not self.figures:
            return ""

        html = f'<h1>{self.config.list_of_figures_title}</h1>\n<ol class="list-of-figures">\n'

        for figure in self.figures:
            chapter_link = f"../{figure.chapter_id}.xhtml" if figure.chapter_id else ""
            figure_link = f"{chapter_link}#{figure.id}" if chapter_link else f"#{figure.id}"

            html += f'  <li><a href="{figure_link}">'
            if figure.caption:
                html += f'{figure.caption}'
            else:
                html += f'Figure {figure.number}'
            html += '</a>'

            if figure.chapter_title:
                html += f' <span class="chapter-ref">({figure.chapter_title})</span>'

            html += '</li>\n'

        html += '</ol>\n'
        return html

    def generate_list_of_tables(self) -> str:
        """Generate HTML for List of Tables page."""
        if not self.tables:
            return ""

        html = f'<h1>{self.config.list_of_tables_title}</h1>\n<ol class="list-of-tables">\n'

        for table in self.tables:
            chapter_link = f"../{table.chapter_id}.xhtml" if table.chapter_id else ""
            table_link = f"{chapter_link}#{table.id}" if chapter_link else f"#{table.id}"

            html += f'  <li><a href="{table_link}">'
            if table.caption:
                html += f'{table.caption}'
            else:
                html += f'Table {table.number}'
            html += '</a>'

            if table.chapter_title:
                html += f' <span class="chapter-ref">({table.chapter_title})</span>'

            html += '</li>\n'

        html += '</ol>\n'
        return html

    def get_figure_count(self) -> int:
        """Get total number of figures processed."""
        return len(self.figures)

    def get_table_count(self) -> int:
        """Get total number of tables processed."""
        return len(self.tables)

    def reset_counters(self) -> None:
        """Reset figure and table counters."""
        self.figure_counter = 0
        self.table_counter = 0
        self.figures.clear()
        self.tables.clear()


def process_figures_and_tables(
    html_content: str,
    chapter_title: str = "",
    chapter_id: str = "",
    config: Optional[FigureConfig] = None
) -> Tuple[str, FigureProcessor]:
    """
    Process HTML content to add semantic figure markup.

    Args:
        html_content: The HTML content to process
        chapter_title: Title of the current chapter
        chapter_id: ID of the current chapter
        config: Configuration for figure processing

    Returns:
        Tuple of (processed_html, figure_processor)
    """
    processor = FigureProcessor(config)
    processed_html = processor.process_content(html_content, chapter_title, chapter_id)
    return processed_html, processor