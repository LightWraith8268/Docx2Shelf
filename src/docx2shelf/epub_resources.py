"""EPUB resource processing (images and fonts).

This module handles processing and embedding of resources in EPUB files:
- Image validation, optimization, and format conversion
- Font embedding with subsetting
- Resource path security validation
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from .content_security import validate_resource_path
from .fonts import process_embedded_fonts, warn_about_font_licensing
from .images import get_media_type_for_image, process_images
from .metadata import BuildOptions


def process_and_add_images(book, resources: list[Path], opts: BuildOptions) -> None:
    """Process and add images to EPUB book with security validation and optimization.

    This function:
    1. Validates resource paths for security
    2. Filters and processes image files
    3. Applies optimization (resize, format conversion)
    4. Adds processed images to the EPUB book
    5. Handles non-image resources

    Args:
        book: EpubBook instance from ebooklib
        resources: List of resource file paths (images and other media)
        opts: BuildOptions with image processing settings
    """
    if not resources:
        return

    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError("ebooklib is required to assemble EPUB. Install 'ebooklib'.") from e

    # Validate resource paths for security
    safe_resources = []
    unsafe_resources = []
    base_dir = Path.cwd()  # Use current directory as base for validation

    for res in resources:
        if validate_resource_path(res, base_dir):
            safe_resources.append(res)
        else:
            unsafe_resources.append(res)

    # Report unsafe resources
    if unsafe_resources and not opts.quiet:
        print(f"⚠️  Skipped {len(unsafe_resources)} unsafe resource paths:")
        for unsafe_res in unsafe_resources[:3]:
            print(f"   {unsafe_res}")
        if len(unsafe_resources) > 3:
            print(f"   ... and {len(unsafe_resources) - 3} more")

    # Use only safe resources
    resources = safe_resources

    # Process images with optimization
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Filter image files
        image_files = [
            res
            for res in resources
            if res.suffix.lower()
            in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp", ".tiff", ".tif"}
        ]

        if image_files:
            # Process images with auto-resize and optional format conversion
            modern_format = None if opts.image_format == "original" else opts.image_format
            processed_images = process_images(
                image_files,
                temp_path,
                max_width=opts.image_max_width,
                max_height=opts.image_max_height,
                quality=opts.image_quality,
                modern_format=modern_format,
                quiet=opts.quiet,
                enhanced_processing=opts.enhanced_images,
            )

            # Add processed images to EPUB
            for img_path in processed_images:
                mt = get_media_type_for_image(img_path)
                item = epub.EpubItem(
                    uid=f"img_{img_path.stem}",
                    file_name=f"images/{img_path.name}",
                    media_type=mt,
                    content=img_path.read_bytes(),
                )
                book.add_item(item)

        # Handle non-image resources
        for res in resources:
            if res.suffix.lower() not in {
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".webp",
                ".avif",
                ".bmp",
                ".tiff",
                ".tif",
            }:
                # Keep non-image resources as-is
                item = epub.EpubItem(
                    uid=f"res_{res.stem}",
                    file_name=f"images/{res.name}",
                    media_type="application/octet-stream",
                    content=res.read_bytes(),
                )
                book.add_item(item)


def process_and_add_fonts(book, opts: BuildOptions, html_content: str) -> None:
    """Process and embed fonts in EPUB book with subsetting.

    Font subsetting reduces file size by including only the characters
    actually used in the HTML content.

    Args:
        book: EpubBook instance from ebooklib
        opts: BuildOptions with embed_fonts_dir path
        html_content: Combined HTML content from all chapters (for character analysis)
    """
    if not opts.embed_fonts_dir or not opts.embed_fonts_dir.exists():
        return

    try:
        from ebooklib import epub  # type: ignore
    except Exception as e:
        raise RuntimeError("ebooklib is required to assemble EPUB. Install 'ebooklib'.") from e

    # Display font licensing warning
    warn_about_font_licensing(opts.embed_fonts_dir, opts.quiet)

    # Process fonts with subsetting
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Collect all HTML content for character analysis
        html_chunks = []
        for item in book.items:
            if (
                hasattr(item, "content")
                and hasattr(item, "file_name")
                and item.file_name.endswith(".xhtml")
            ):
                if isinstance(item.content, bytes):
                    html_chunks.append(item.content.decode("utf-8"))
                else:
                    html_chunks.append(str(item.content))

        # Process and subset fonts
        processed_fonts = process_embedded_fonts(
            opts.embed_fonts_dir, html_chunks, temp_path, opts.quiet
        )

        # Add processed fonts to EPUB
        for font_path in processed_fonts:
            data = font_path.read_bytes()
            item = epub.EpubItem(
                uid=f"font_{font_path.stem}",
                file_name=f"fonts/{font_path.name}",
                media_type="font/otf" if font_path.suffix.lower() == ".otf" else "font/ttf",
                content=data,
            )
            book.add_item(item)
