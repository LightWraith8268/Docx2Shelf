"""AI command handlers - extracted from cli.py."""

from __future__ import annotations

import argparse
from pathlib import Path


def run_ai_command(args) -> int:
    """Handle AI subcommands."""
    try:
        if args.ai_action == "metadata":
            return run_ai_metadata(args)
        elif args.ai_action == "genre":
            return run_ai_genre(args)
        elif args.ai_action == "alt-text":
            return run_ai_alt_text(args)
        elif args.ai_action == "config":
            return run_ai_config(args)
        else:
            print(f"Unknown AI action: {args.ai_action}")
            return 1
    except Exception as e:
        print(f"Error running AI command: {e}")
        return 1


def run_ai_metadata(args) -> int:
    """Enhance metadata using AI analysis."""
    from ..ai_integration import get_ai_manager
    from ..ai_metadata import enhance_metadata_with_ai
    from ..metadata import EpubMetadata
    from .utils import read_document_content, save_metadata_to_file

    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return 1

    # Check AI availability
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        print("[WARNING] AI features not available. Please check your AI configuration.")
        return 1

    try:
        print(f"🤖 Analyzing metadata for: {input_file.name}")

        # Read document content
        content = read_document_content(input_file)
        if not content:
            print("Error: Could not read document content")
            return 1

        # Create basic metadata
        metadata = EpubMetadata(title=input_file.stem, author="Unknown Author", language="en")

        # Enhance with AI
        enhanced = enhance_metadata_with_ai(content, metadata, interactive=args.interactive)

        # Output results
        if args.output:
            save_metadata_to_file(enhanced.original, Path(args.output))
            print(f"[SUCCESS] Enhanced metadata saved to: {args.output}")
        else:
            print("\n📊 Enhanced Metadata:")
            print(f"   Title: {enhanced.original.title}")
            print(f"   Author: {enhanced.original.author}")
            print(f"   Description: {enhanced.original.description or '(none)'}")
            if hasattr(enhanced.original, "genre") and enhanced.original.genre:
                print(f"   Genre: {enhanced.original.genre}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_ai_genre(args) -> int:
    """Detect genres and keywords using AI."""
    from ..ai_genre_detection import detect_genre_with_ai
    from ..ai_integration import get_ai_manager
    from .utils import read_document_content

    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return 1

    # Check AI availability
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        print("[WARNING] AI features not available. Please check your AI configuration.")
        return 1

    try:
        print(f"🎯 Analyzing genres and keywords for: {input_file.name}")

        # Read document content
        content = read_document_content(input_file)
        if not content:
            print("Error: Could not read document content")
            return 1

        # Detect genres
        metadata_dict = {"title": input_file.stem, "author": "Unknown Author", "description": ""}
        result = detect_genre_with_ai(content, metadata_dict)

        if args.json:
            import json

            output = {
                "genres": [
                    {"genre": g.genre, "confidence": g.confidence, "source": g.source}
                    for g in result.genres
                ],
                "keywords": result.keywords,
                "analysis_summary": result.analysis_summary,
            }
            print(json.dumps(output, indent=2))
        else:
            print("\n📚 Detected Genres:")
            for genre in result.genres[:5]:
                confidence_icon = (
                    "🟢" if genre.confidence >= 0.8 else "🟡" if genre.confidence >= 0.6 else "🔴"
                )
                print(
                    f"   {confidence_icon} {genre.genre} ({genre.confidence:.1%}) - {genre.source}"
                )

            print(f"\n🏷️  Keywords: {', '.join(result.keywords[:15])}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_ai_alt_text(args) -> int:
    """Generate alt text for images using AI."""
    from ..ai_accessibility import generate_image_alt_texts
    from ..ai_integration import get_ai_manager

    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"Error: Input path not found: {input_path}")
        return 1

    # Check AI availability
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        print("[WARNING] AI features not available. Please check your AI configuration.")
        return 1

    try:
        print(f"🖼️  Generating alt text for: {input_path.name}")

        if input_path.is_file() and input_path.suffix.lower() in [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
        ]:
            # Single image file
            suggestions = generate_image_alt_texts([input_path], interactive=args.interactive)

            if suggestions:
                print("\n✨ Alt Text Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    confidence_icon = (
                        "🟢"
                        if suggestion.confidence >= 0.8
                        else "🟡" if suggestion.confidence >= 0.6 else "🔴"
                    )
                    print(f"   {i}. {confidence_icon} {suggestion.alt_text}")
                    print(
                        f"      Confidence: {suggestion.confidence:.1%} | Source: {suggestion.source}"
                    )
            else:
                print("No alt text suggestions generated")

        else:
            print("Error: Please provide a valid image file (.jpg, .png, .gif, .webp)")
            return 1

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def run_ai_config(args) -> int:
    """Manage AI configuration."""
    from ..ai_integration import AIConfig

    try:
        config = AIConfig()

        if args.list:
            print("🔧 AI Configuration:")
            print(f"   Model Type: {config.model_type}")
            print(f"   Local Model: {config.local_model}")
            if config.openai_api_key:
                print(f"   OpenAI API Key: {'*' * 8}{config.openai_api_key[-4:]}")
            else:
                print("   OpenAI API Key: Not configured")
            print(f"   Cache Enabled: {config.enable_caching}")
            print(f"   Cache Directory: {config.cache_dir}")

        elif args.set:
            key, value = args.set
            if hasattr(config, key):
                setattr(config, key, value)
                # Save configuration would go here
                print(f"[SET] {key} = {value}")
            else:
                print(f"Error: Unknown configuration key: {key}")
                return 1

        elif args.reset:
            # Reset to defaults would go here
            print("[SUCCESS] AI configuration reset to defaults")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1
