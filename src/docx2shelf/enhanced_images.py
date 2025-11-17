"""
Enhanced Image Processing for Edge Cases

This module extends the basic image handling with support for:
- CMYK color space conversion
- Advanced transparency handling
- Large image progressive optimization
- Corrupted image detection and recovery
- Color profile management
- Advanced format detection and conversion
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .images import check_pillow_availability


class ColorSpace(Enum):
    """Supported color spaces."""

    RGB = "RGB"
    RGBA = "RGBA"
    CMYK = "CMYK"
    LAB = "LAB"
    GRAYSCALE = "L"
    PALETTE = "P"


class TransparencyHandling(Enum):
    """Transparency handling strategies."""

    PRESERVE = "preserve"  # Keep transparency when possible
    FLATTEN_WHITE = "flatten_white"  # Flatten to white background
    FLATTEN_BLACK = "flatten_black"  # Flatten to black background
    FLATTEN_CUSTOM = "flatten_custom"  # Flatten to custom color
    AUTO = "auto"  # Choose best strategy based on image content


@dataclass
class ImageProcessingConfig:
    """Configuration for enhanced image processing."""

    # Color space handling
    target_color_space: ColorSpace = ColorSpace.RGB
    preserve_color_profiles: bool = False
    convert_cmyk_to_rgb: bool = True

    # Transparency handling
    transparency_strategy: TransparencyHandling = TransparencyHandling.AUTO
    background_color: Tuple[int, int, int] = (255, 255, 255)  # White background

    # Large image handling
    max_dimension: int = 4000  # Maximum width or height
    progressive_threshold_kb: int = 500  # Enable progressive for files > 500KB
    chunk_size_mb: int = 50  # Process large images in chunks

    # Quality and compression
    jpeg_progressive: bool = True
    jpeg_optimize: bool = True
    png_compress_level: int = 6
    webp_lossless_threshold: int = 64  # Use lossless WebP for small images

    # Error handling
    strict_mode: bool = False  # Fail on any error vs. graceful degradation
    auto_fix_corruption: bool = True
    preserve_animation: bool = True  # For GIF/WebP animations


class EnhancedImageProcessor:
    """Enhanced image processor for edge cases."""

    def __init__(self, config: ImageProcessingConfig):
        self.config = config
        self._pillow_available = check_pillow_availability()

    def process_image_with_edge_case_handling(
        self, input_path: Path, output_path: Path, target_format: Optional[str] = None
    ) -> Tuple[bool, List[str], Dict[str, any]]:
        """
        Process image with comprehensive edge case handling.

        Returns:
            (success, warnings, metadata)
        """
        warnings_list = []
        metadata = {}

        if not self._pillow_available:
            if not self.config.strict_mode:
                # Graceful fallback - just copy file
                output_path.write_bytes(input_path.read_bytes())
                warnings_list.append("Pillow not available, copied image without processing")
                return True, warnings_list, metadata
            else:
                return False, ["Pillow required for enhanced image processing"], metadata

        try:
            from PIL import Image

            # Step 1: Analyze image and detect issues
            analysis = self._analyze_image_advanced(input_path)
            metadata.update(analysis)

            if analysis.get("corrupted", False):
                if self.config.auto_fix_corruption:
                    success, warnings = self._attempt_corruption_fix(input_path, output_path)
                    if success:
                        warnings_list.extend(warnings)
                        return True, warnings_list, metadata

                if self.config.strict_mode:
                    return False, ["Image appears corrupted and auto-fix failed"], metadata
                else:
                    # Copy as-is with warning
                    output_path.write_bytes(input_path.read_bytes())
                    warnings_list.append("Image may be corrupted, copied without processing")
                    return True, warnings_list, metadata

            # Step 2: Open and process image
            with Image.open(input_path) as img:
                # Handle large images
                if self._is_large_image(img):
                    img, large_warnings = self._handle_large_image(img)
                    warnings_list.extend(large_warnings)

                # Handle CMYK color space
                if img.mode == "CMYK":
                    img, cmyk_warnings = self._handle_cmyk_image(img)
                    warnings_list.extend(cmyk_warnings)

                # Handle transparency
                if self._has_transparency(img):
                    img, transparency_warnings = self._handle_transparency(img)
                    warnings_list.extend(transparency_warnings)

                # Color profile handling
                if self.config.preserve_color_profiles and hasattr(img, "info"):
                    profile_warnings = self._handle_color_profiles(img)
                    warnings_list.extend(profile_warnings)

                # Format-specific optimization
                save_kwargs = self._get_save_parameters(img, target_format, output_path)

                # Save with optimization
                img.save(output_path, **save_kwargs)

                # Post-processing metadata
                metadata["processed_size"] = output_path.stat().st_size
                metadata["final_format"] = save_kwargs.get("format", target_format)

                return True, warnings_list, metadata

        except Exception as e:
            error_msg = f"Error processing image {input_path.name}: {str(e)}"

            if self.config.strict_mode:
                return False, [error_msg], metadata
            else:
                # Fallback: copy original
                try:
                    output_path.write_bytes(input_path.read_bytes())
                    warnings_list.append(f"{error_msg} (copied original)")
                    return True, warnings_list, metadata
                except Exception as copy_error:
                    return False, [f"{error_msg}, copy failed: {str(copy_error)}"], metadata

    def _analyze_image_advanced(self, image_path: Path) -> Dict[str, any]:
        """Perform advanced image analysis."""
        analysis = {
            "file_size": image_path.stat().st_size,
            "corrupted": False,
            "color_space": "unknown",
            "has_transparency": False,
            "has_animation": False,
            "has_color_profile": False,
            "estimated_complexity": "unknown",
        }

        try:
            from PIL import Image

            with Image.open(image_path) as img:
                analysis["width"] = img.width
                analysis["height"] = img.height
                analysis["color_space"] = img.mode
                analysis["format"] = img.format

                # Check for transparency
                analysis["has_transparency"] = self._has_transparency(img)

                # Check for animation
                analysis["has_animation"] = getattr(img, "is_animated", False)

                # Check for color profile
                analysis["has_color_profile"] = "icc_profile" in img.info

                # Estimate complexity (for quality decisions)
                if hasattr(img, "histogram"):
                    # Simple complexity estimation based on color diversity
                    hist = img.histogram()
                    unique_colors = len([x for x in hist if x > 0])
                    if unique_colors < 16:
                        analysis["estimated_complexity"] = "simple"
                    elif unique_colors < 256:
                        analysis["estimated_complexity"] = "moderate"
                    else:
                        analysis["estimated_complexity"] = "complex"

        except Exception as e:
            analysis["corrupted"] = True
            analysis["corruption_reason"] = str(e)

        return analysis

    def _is_large_image(self, img) -> bool:
        """Check if image is considered large."""
        return img.width > self.config.max_dimension or img.height > self.config.max_dimension

    def _handle_large_image(self, img) -> Tuple[any, List[str]]:
        """Handle large images with special processing."""
        warnings = []

        if img.width > self.config.max_dimension or img.height > self.config.max_dimension:
            # Calculate new dimensions maintaining aspect ratio
            ratio = min(
                self.config.max_dimension / img.width, self.config.max_dimension / img.height
            )
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)

            # Use high-quality resampling for large images
            from PIL import Image

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            warnings.append(
                f"Large image resized from {img.width}x{img.height} to {new_width}x{new_height}"
            )

        return img, warnings

    def _handle_cmyk_image(self, img) -> Tuple[any, List[str]]:
        """Handle CMYK color space conversion."""
        warnings = []

        if img.mode == "CMYK" and self.config.convert_cmyk_to_rgb:
            try:
                from PIL import ImageCms

                # Try to use color profile for accurate conversion
                if "icc_profile" in img.info:
                    # Professional CMYK to RGB conversion using ICC profiles
                    cmyk_profile = ImageCms.ImageCmsProfile(io.BytesIO(img.info["icc_profile"]))
                    rgb_profile = ImageCms.createProfile("sRGB")
                    transform = ImageCms.buildTransformFromOpenProfiles(
                        cmyk_profile, rgb_profile, "CMYK", "RGB"
                    )
                    img = ImageCms.applyTransform(img, transform)
                    warnings.append("CMYK image converted to RGB using ICC profile")
                else:
                    # Fallback to basic conversion
                    img = img.convert("RGB")
                    warnings.append(
                        "CMYK image converted to RGB (no ICC profile, may have color shifts)"
                    )

            except ImportError:
                # PIL without ICC support
                img = img.convert("RGB")
                warnings.append(
                    "CMYK image converted to RGB (no ICC support, may have color shifts)"
                )
            except Exception as e:
                # Fallback to basic conversion
                img = img.convert("RGB")
                warnings.append(f"CMYK conversion warning: {str(e)}, used basic conversion")

        return img, warnings

    def _has_transparency(self, img) -> bool:
        """Check if image has transparency."""
        return (
            img.mode in ("RGBA", "LA")
            or "transparency" in img.info
            or (img.mode == "P" and "transparency" in img.info)
        )

    def _handle_transparency(self, img) -> Tuple[any, List[str]]:
        """Handle transparency based on configuration."""
        warnings = []

        if not self._has_transparency(img):
            return img, warnings

        strategy = self.config.transparency_strategy

        if strategy == TransparencyHandling.PRESERVE:
            # Try to preserve transparency
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            warnings.append("Transparency preserved")

        elif strategy == TransparencyHandling.FLATTEN_WHITE:
            img = self._flatten_transparency(img, (255, 255, 255))
            warnings.append("Transparency flattened to white background")

        elif strategy == TransparencyHandling.FLATTEN_BLACK:
            img = self._flatten_transparency(img, (0, 0, 0))
            warnings.append("Transparency flattened to black background")

        elif strategy == TransparencyHandling.FLATTEN_CUSTOM:
            img = self._flatten_transparency(img, self.config.background_color)
            warnings.append(
                f"Transparency flattened to custom background {self.config.background_color}"
            )

        elif strategy == TransparencyHandling.AUTO:
            # Analyze image to determine best strategy
            if self._should_preserve_transparency(img):
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                warnings.append("Transparency preserved (auto-detected as beneficial)")
            else:
                img = self._flatten_transparency(img, (255, 255, 255))
                warnings.append(
                    "Transparency flattened to white background (auto-detected as beneficial)"
                )

        return img, warnings

    def _flatten_transparency(self, img, background_color: Tuple[int, int, int]):
        """Flatten transparency to solid background."""
        from PIL import Image

        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, background_color)
            background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            return background
        elif img.mode == "LA":
            background = Image.new(
                "L", img.size, background_color[0]
            )  # Use first value for grayscale
            background.paste(img, mask=img.split()[-1])
            return background
        elif img.mode == "P" and "transparency" in img.info:
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, background_color)
            background.paste(img, mask=img.split()[-1])
            return background
        else:
            return img.convert("RGB")

    def _should_preserve_transparency(self, img) -> bool:
        """Determine if transparency should be preserved based on image analysis."""
        # Simple heuristic: preserve transparency if it's used significantly
        if img.mode == "RGBA":
            alpha_channel = img.split()[-1]
            alpha_histogram = alpha_channel.histogram()

            # If more than 10% of pixels are partially transparent, preserve it
            total_pixels = img.width * img.height
            fully_opaque_pixels = alpha_histogram[255] if len(alpha_histogram) > 255 else 0
            transparent_pixels = total_pixels - fully_opaque_pixels

            return (transparent_pixels / total_pixels) > 0.1

        return True  # Default to preserving for other transparency types

    def _handle_color_profiles(self, img) -> List[str]:
        """Handle color profile preservation/conversion."""
        warnings = []

        if "icc_profile" in img.info:
            if self.config.preserve_color_profiles:
                warnings.append("Color profile preserved")
            else:
                # Remove color profile to reduce file size
                if hasattr(img, "info"):
                    img.info.pop("icc_profile", None)
                warnings.append("Color profile removed to reduce file size")

        return warnings

    def _get_save_parameters(
        self, img, target_format: Optional[str], output_path: Path
    ) -> Dict[str, any]:
        """Get optimized save parameters for the image."""
        save_kwargs = {"optimize": True}

        # Determine format
        if target_format:
            format_name = target_format.upper()
            if format_name == "JPG":
                format_name = "JPEG"
        else:
            format_name = output_path.suffix.upper().lstrip(".")
            if format_name == "JPG":
                format_name = "JPEG"

        save_kwargs["format"] = format_name

        # Format-specific parameters
        if format_name == "JPEG":
            save_kwargs["quality"] = 85
            save_kwargs["progressive"] = self.config.jpeg_progressive
            if self.config.jpeg_optimize:
                save_kwargs["optimize"] = True

            # Use progressive for larger files
            file_size_kb = img.width * img.height * 3 // 1024  # Rough estimate
            if file_size_kb > self.config.progressive_threshold_kb:
                save_kwargs["progressive"] = True

        elif format_name == "PNG":
            save_kwargs["compress_level"] = self.config.png_compress_level
            if img.mode == "P":  # Palette mode
                save_kwargs["optimize"] = True

        elif format_name == "WEBP":
            # Use lossless for small or simple images
            file_size_kb = img.width * img.height * 3 // 1024
            if file_size_kb < self.config.webp_lossless_threshold:
                save_kwargs["lossless"] = True
            else:
                save_kwargs["quality"] = 80
                save_kwargs["method"] = 6  # Best compression

        return save_kwargs

    def _attempt_corruption_fix(
        self, input_path: Path, output_path: Path
    ) -> Tuple[bool, List[str]]:
        """Attempt to fix corrupted images."""
        warnings = []

        try:
            from PIL import Image

            # Try opening with different decoders
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                # Try forcing RGB conversion
                with Image.open(input_path) as img:
                    # Convert to RGB to handle mode issues
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    # Save with basic JPEG to fix corruption
                    img.save(output_path, "JPEG", quality=85)
                    warnings.append("Corruption detected and fixed by converting to JPEG")
                    return True, warnings

        except Exception as e:
            warnings.append(f"Could not fix corruption: {str(e)}")
            return False, warnings


def create_epub_optimized_config() -> ImageProcessingConfig:
    """Create configuration optimized for EPUB processing."""
    return ImageProcessingConfig(
        target_color_space=ColorSpace.RGB,
        preserve_color_profiles=False,  # Reduce file size
        convert_cmyk_to_rgb=True,
        transparency_strategy=TransparencyHandling.AUTO,
        max_dimension=1600,  # EPUB-friendly max size
        progressive_threshold_kb=200,  # Lower threshold for EPUB
        strict_mode=False,  # Graceful degradation for EPUB
        auto_fix_corruption=True,
        preserve_animation=False,  # Convert GIF to static for EPUB
    )


def create_high_fidelity_config() -> ImageProcessingConfig:
    """Create configuration for high-fidelity image preservation."""
    return ImageProcessingConfig(
        target_color_space=ColorSpace.RGB,
        preserve_color_profiles=True,
        convert_cmyk_to_rgb=True,
        transparency_strategy=TransparencyHandling.PRESERVE,
        max_dimension=4000,
        progressive_threshold_kb=1000,
        strict_mode=True,  # Fail on errors for quality control
        auto_fix_corruption=False,
        preserve_animation=True,
    )


def validate_image_integrity(image_path: Path) -> Tuple[bool, List[str], Dict[str, any]]:
    """
    Validate image integrity and detect potential issues.

    Returns:
        (is_valid, issues, analysis)
    """
    issues = []
    analysis = {}

    if not image_path.exists():
        return False, ["File does not exist"], analysis

    try:
        from PIL import Image

        with Image.open(image_path) as img:
            analysis["format"] = img.format
            analysis["mode"] = img.mode
            analysis["size"] = (img.width, img.height)
            analysis["file_size"] = image_path.stat().st_size

            # Check for CMYK without conversion capability
            if img.mode == "CMYK":
                try:
                    from PIL import ImageCms

                    analysis["icc_support"] = True
                except ImportError:
                    issues.append("CMYK image detected but no ICC profile support available")
                    analysis["icc_support"] = False

            # Check for extremely large dimensions
            if img.width > 10000 or img.height > 10000:
                issues.append(
                    f"Very large dimensions: {img.width}x{img.height} may cause memory issues"
                )

            # Check file size
            size_mb = analysis["file_size"] / (1024 * 1024)
            if size_mb > 50:
                issues.append(f"Large file size: {size_mb:.1f}MB may cause processing delays")

            # Try to access image data to detect corruption
            try:
                img.load()
            except Exception as e:
                issues.append(f"Image data corruption detected: {str(e)}")

            # Check for unsupported modes
            if img.mode not in ["RGB", "RGBA", "L", "LA", "P", "CMYK"]:
                issues.append(f"Unsupported color mode: {img.mode}")

    except Exception as e:
        issues.append(f"Cannot open image: {str(e)}")
        return False, issues, analysis

    return len(issues) == 0, issues, analysis
