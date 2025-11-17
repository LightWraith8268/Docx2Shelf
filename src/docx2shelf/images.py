from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple


def check_pillow_availability() -> bool:
    """Check if Pillow is available for image processing."""
    try:
        import PIL

        return True
    except ImportError:
        return False


def get_image_info(image_path: Path) -> Optional[Tuple[int, int, str]]:
    """Get image dimensions and format.

    Returns tuple of (width, height, format) or None if failed.
    """
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            return img.width, img.height, img.format
    except Exception:
        return None


def should_resize_image(
    width: int, height: int, max_width: int = 1200, max_height: int = 1600
) -> bool:
    """Determine if image should be resized based on dimensions."""
    return width > max_width or height > max_height


def resize_image(
    image_path: Path,
    output_path: Path,
    max_width: int = 1200,
    max_height: int = 1600,
    quality: int = 85,
) -> bool:
    """Resize image while maintaining aspect ratio.

    Returns True if successful, False otherwise.
    """
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            # Convert RGBA to RGB for JPEG compatibility
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img, mask=img.split()[1])
                img = background
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            # Calculate new dimensions
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Save with optimization
            save_kwargs = {"optimize": True}
            if output_path.suffix.lower() in {".jpg", ".jpeg"}:
                save_kwargs["quality"] = quality
                save_kwargs["progressive"] = True
            elif output_path.suffix.lower() == ".png":
                save_kwargs["compress_level"] = 6
            elif output_path.suffix.lower() == ".webp":
                save_kwargs["quality"] = quality
                save_kwargs["method"] = 6

            img.save(output_path, **save_kwargs)
            return True

    except Exception as e:
        print(f"Error resizing image {image_path.name}: {e}", file=sys.stderr)
        return False


def convert_to_modern_format(
    image_path: Path, output_path: Path, target_format: str = "webp", quality: int = 85
) -> bool:
    """Convert image to modern format (WebP or AVIF).

    Returns True if successful, False otherwise.
    """
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            # Convert RGBA to RGB for better compression
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img, mask=img.split()[1])
                img = background
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            # Save with format-specific optimization
            save_kwargs = {"optimize": True, "quality": quality}

            if target_format.lower() == "webp":
                save_kwargs["method"] = 6
                save_kwargs["lossless"] = False
            elif target_format.lower() == "avif":
                # AVIF may not be available in all Pillow versions
                try:
                    save_kwargs["quality"] = quality
                    save_kwargs["speed"] = 4
                except Exception:
                    # Fall back to WebP if AVIF not supported
                    target_format = "webp"
                    save_kwargs = {"optimize": True, "quality": quality, "method": 6}

            # Update output path extension
            output_path = output_path.with_suffix(f".{target_format.lower()}")
            img.save(output_path, format=target_format.upper(), **save_kwargs)
            return True

    except Exception as e:
        print(f"Error converting image {image_path.name} to {target_format}: {e}", file=sys.stderr)
        return False


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    return file_path.stat().st_size / (1024 * 1024)


def process_image(
    image_path: Path,
    output_dir: Path,
    max_width: int = 1200,
    max_height: int = 1600,
    quality: int = 85,
    modern_format: Optional[str] = None,
    quiet: bool = False,
    enhanced_processing: bool = False,
) -> Optional[Path]:
    """Process a single image with resizing and format conversion.

    Returns path to processed image or None if processing failed.
    """
    if not image_path.exists():
        return None

    # Enhanced processing for edge cases
    if enhanced_processing:
        return process_image_enhanced(
            image_path, output_dir, max_width, max_height, quality, modern_format, quiet
        )

    # Use standard processing for regular images
    return process_image_standard(
        image_path, output_dir, max_width, max_height, quality, modern_format, quiet
    )


def process_images(
    images: List[Path],
    output_dir: Path,
    max_width: int = 1200,
    max_height: int = 1600,
    quality: int = 85,
    modern_format: Optional[str] = None,
    quiet: bool = False,
    enhanced_processing: bool = False,
) -> List[Path]:
    """Process multiple images with optimization.

    Returns list of processed image paths.
    """
    if not images:
        return []

    # Check for Pillow availability
    if not check_pillow_availability():
        if not quiet:
            print("Pillow not available. Copying images without processing.", file=sys.stderr)
            print("Install Pillow for image optimization: pip install Pillow", file=sys.stderr)

        # Copy images without processing
        processed_images = []
        for img_path in images:
            if img_path.is_file():
                output_path = output_dir / img_path.name
                output_path.write_bytes(img_path.read_bytes())
                processed_images.append(output_path)
                if not quiet:
                    print(f"Copied image: {img_path.name}")

        return processed_images

    # Process images with optimization
    processed_images = []

    if not quiet and modern_format:
        print(f"Processing images with {modern_format.upper()} conversion and resizing...")
    elif not quiet:
        print("Processing images with resizing...")

    for img_path in images:
        if img_path.is_file():
            processed_path = process_image(
                img_path,
                output_dir,
                max_width,
                max_height,
                quality,
                modern_format,
                quiet,
                enhanced_processing,
            )
            if processed_path:
                processed_images.append(processed_path)

    return processed_images


def process_image_enhanced(
    image_path: Path,
    output_dir: Path,
    max_width: int = 1200,
    max_height: int = 1600,
    quality: int = 85,
    modern_format: Optional[str] = None,
    quiet: bool = False,
) -> Optional[Path]:
    """Process image with enhanced edge case handling."""
    try:
        from .enhanced_images import (
            EnhancedImageProcessor,
            TransparencyHandling,
            create_epub_optimized_config,
        )

        # Create enhanced config based on parameters
        config = create_epub_optimized_config()
        config.max_dimension = max(max_width, max_height)
        config.jpeg_quality = quality

        # Adjust transparency handling for different formats
        if modern_format and modern_format.lower() in ["webp", "png"]:
            config.transparency_strategy = TransparencyHandling.PRESERVE
        else:
            config.transparency_strategy = TransparencyHandling.AUTO

        processor = EnhancedImageProcessor(config)

        # Determine output path and format
        if modern_format:
            output_name = f"{image_path.stem}.{modern_format.lower()}"
        else:
            output_name = image_path.name

        output_path = output_dir / output_name

        # Process with enhanced handling
        success, warnings, metadata = processor.process_image_with_edge_case_handling(
            image_path, output_path, modern_format
        )

        if success:
            if not quiet:
                # Report processing results
                original_size = metadata.get("file_size", 0) / (1024 * 1024)  # MB
                processed_size = metadata.get("processed_size", 0) / (1024 * 1024)  # MB

                if processed_size > 0 and original_size > 0:
                    savings = ((original_size - processed_size) / original_size) * 100
                    print(
                        f"Enhanced processing: {image_path.name} "
                        f"({original_size:.2f} -> {processed_size:.2f} MB, {savings:.1f}% reduction)"
                    )

                # Report any warnings
                for warning in warnings:
                    print(f"  Warning: {warning}", file=sys.stderr)

            return output_path
        else:
            # Fall back to regular processing
            if not quiet:
                print(
                    f"Enhanced processing failed for {image_path.name}, falling back to standard processing"
                )
            return process_image_standard(
                image_path, output_dir, max_width, max_height, quality, modern_format, quiet
            )

    except ImportError:
        # Enhanced processing not available, fall back to standard
        if not quiet:
            print(
                f"Enhanced image processing not available for {image_path.name}, using standard processing"
            )
        return process_image_standard(
            image_path, output_dir, max_width, max_height, quality, modern_format, quiet
        )
    except Exception as e:
        if not quiet:
            print(
                f"Enhanced processing error for {image_path.name}: {e}, falling back to standard",
                file=sys.stderr,
            )
        return process_image_standard(
            image_path, output_dir, max_width, max_height, quality, modern_format, quiet
        )


def process_image_standard(
    image_path: Path,
    output_dir: Path,
    max_width: int = 1200,
    max_height: int = 1600,
    quality: int = 85,
    modern_format: Optional[str] = None,
    quiet: bool = False,
) -> Optional[Path]:
    """Standard image processing (original implementation)."""
    # Get image info
    img_info = get_image_info(image_path)
    if not img_info:
        if not quiet:
            print(f"Could not read image: {image_path.name}", file=sys.stderr)
        return None

    width, height, format_name = img_info
    original_size = get_file_size_mb(image_path)

    # Determine processing needed
    needs_resize = should_resize_image(width, height, max_width, max_height)
    needs_format_conversion = modern_format and format_name.lower() not in {"webp", "avif"}

    if not needs_resize and not needs_format_conversion:
        # Copy original if no processing needed
        output_path = output_dir / image_path.name
        output_path.write_bytes(image_path.read_bytes())
        if not quiet:
            print(f"Copied image: {image_path.name} ({original_size:.2f} MB)")
        return output_path

    # Determine output filename and format
    if modern_format:
        output_name = f"{image_path.stem}.{modern_format.lower()}"
    else:
        output_name = image_path.name

    output_path = output_dir / output_name

    # Process image
    if modern_format and needs_format_conversion:
        success = convert_to_modern_format(image_path, output_path, modern_format, quality)
    elif needs_resize:
        success = resize_image(image_path, output_path, max_width, max_height, quality)
    else:
        # Just copy
        output_path.write_bytes(image_path.read_bytes())
        success = True

    if success:
        new_size = get_file_size_mb(output_path)
        if not quiet:
            reduction = (
                ((original_size - new_size) / original_size) * 100 if original_size > 0 else 0
            )
            action_desc = []
            if needs_resize:
                action_desc.append("resized")
            if needs_format_conversion:
                action_desc.append(f"converted to {modern_format}")

            action_str = ", ".join(action_desc) if action_desc else "processed"
            print(
                f"Image {action_str}: {image_path.name} ({original_size:.2f} → {new_size:.2f} MB, {reduction:.1f}% reduction)"
            )

        return output_path
    else:
        # Fall back to copying original
        fallback_path = output_dir / image_path.name
        fallback_path.write_bytes(image_path.read_bytes())
        if not quiet:
            print(f"Image processing failed, copied original: {image_path.name}")
        return fallback_path


def get_media_type_for_image(image_path: Path) -> str:
    """Get MIME type for image file."""
    suffix = image_path.suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".avif": "image/avif",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }

    return mime_types.get(suffix, "image/jpeg")  # Default to JPEG
