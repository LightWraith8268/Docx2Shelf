"""
Interactive Conversion Wizard for Docx2Shelf.

Provides step-by-step guidance with real-time preview capabilities for
streamlined EPUB conversion workflows with enhanced user experience.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ai_genre_detection import detect_genre_with_ai
from .ai_integration import get_ai_manager
from .ai_metadata import enhance_metadata_with_ai
from .error_handler import handle_error, wrap_with_error_handling
from .metadata import BuildOptions, EpubMetadata


@dataclass
class WizardStep:
    """Individual step in the conversion wizard."""

    step_id: str
    title: str
    description: str
    is_required: bool = True
    is_completed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    help_text: Optional[str] = None


@dataclass
class WizardState:
    """Current state of the conversion wizard."""

    current_step: int = 0
    input_file: Optional[Path] = None
    metadata: Optional[EpubMetadata] = None
    build_options: Optional[BuildOptions] = None
    preview_enabled: bool = True
    auto_save_enabled: bool = True
    session_file: Optional[Path] = None
    steps: List[WizardStep] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


class ConversionWizard:
    """Interactive conversion wizard with step-by-step guidance."""

    def __init__(self, session_dir: Optional[Path] = None):
        """Initialize the conversion wizard.

        Args:
            session_dir: Directory to store wizard session files
        """
        self.session_dir = session_dir or Path.home() / ".docx2shelf" / "wizard"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state = WizardState()
        self.preview_process = None
        self._initialize_steps()

    def _initialize_steps(self):
        """Initialize the wizard steps."""
        self.state.steps = [
            WizardStep(
                step_id="welcome",
                title="Welcome to Docx2Shelf",
                description="Get started with converting your document to EPUB",
                is_required=False,
                help_text="This wizard will guide you through the conversion process step by step.",
            ),
            WizardStep(
                step_id="input_file",
                title="Select Input File",
                description="Choose the DOCX file you want to convert",
                help_text="Supported formats: .docx, .md, .txt, .html",
            ),
            WizardStep(
                step_id="metadata",
                title="Book Metadata",
                description="Enter title, author, and other book information",
                help_text="This information will appear in e-readers and bookstores",
            ),
            WizardStep(
                step_id="theme_style",
                title="Theme & Styling",
                description="Choose visual appearance and formatting options",
                is_required=False,
                help_text="Select from built-in themes or customize your own",
            ),
            WizardStep(
                step_id="structure",
                title="Book Structure",
                description="Configure chapters and table of contents",
                is_required=False,
                help_text="Define how your content should be organized",
            ),
            WizardStep(
                step_id="preview",
                title="Preview & Review",
                description="Review your settings and preview the result",
                is_required=False,
                help_text="Make final adjustments before conversion",
            ),
            WizardStep(
                step_id="conversion",
                title="Convert to EPUB",
                description="Generate your EPUB file",
                help_text="The conversion process will create your final EPUB",
            ),
        ]

    def start_wizard(self, input_file: Optional[Path] = None) -> int:
        """Start the interactive wizard.

        Args:
            input_file: Optional pre-selected input file

        Returns:
            Exit code (0 for success)
        """
        print("📖 Welcome to the Docx2Shelf Conversion Wizard!")
        print("=" * 60)

        # Load or create session
        if input_file:
            self.state.input_file = input_file
            self._skip_to_step("metadata")
        else:
            self._load_session()

        # Main wizard loop
        while self.state.current_step < len(self.state.steps):
            step = self.state.steps[self.state.current_step]

            if not self._run_step(step):
                print("\n❌ Wizard cancelled by user.")
                return 1

            self.state.current_step += 1

            # Auto-save session
            if self.state.auto_save_enabled:
                self._save_session()

        print("\n🎉 Conversion wizard completed successfully!")
        return 0

    def _run_step(self, step: WizardStep) -> bool:
        """Run a single wizard step.

        Args:
            step: The step to execute

        Returns:
            True if step completed successfully, False if cancelled
        """
        self._display_step_header(step)

        # Execute step-specific logic
        if step.step_id == "welcome":
            return self._step_welcome()
        elif step.step_id == "input_file":
            return self._step_input_file()
        elif step.step_id == "metadata":
            return self._step_metadata()
        elif step.step_id == "theme_style":
            return self._step_theme_style()
        elif step.step_id == "structure":
            return self._step_structure()
        elif step.step_id == "preview":
            return self._step_preview()
        elif step.step_id == "conversion":
            return self._step_conversion()
        else:
            print(f"Unknown step: {step.step_id}")
            return True

    def _display_step_header(self, step: WizardStep):
        """Display the header for a wizard step."""
        step_num = self.state.current_step + 1
        total_steps = len(self.state.steps)

        print(f"\n📋 Step {step_num}/{total_steps}: {step.title}")
        print("-" * 40)
        print(step.description)

        if step.help_text:
            print(f"\n💡 {step.help_text}")

        if step.validation_errors:
            print("\n⚠️  Issues to resolve:")
            for error in step.validation_errors:
                print(f"   • {error}")

        print()

    def _step_welcome(self) -> bool:
        """Welcome step."""
        print("This wizard will help you convert your document to EPUB format.")
        print("You can navigate using:")
        print("  • [Enter] - Continue to next step")
        print("  • 'back' - Go to previous step")
        print("  • 'quit' - Exit wizard")
        print("  • 'help' - Show help for current step")

        response = self._get_user_input("Press Enter to continue")
        return self._handle_navigation(response)

    def _step_input_file(self) -> bool:
        """Input file selection step."""
        if self.state.input_file:
            print(f"Current file: {self.state.input_file}")
            if self._confirm("Use this file?"):
                return True

        while True:
            file_path = self._get_user_input("Enter path to your document file")

            if not self._handle_navigation(file_path):
                return False

            if file_path in ["", "skip"]:
                continue

            path = Path(file_path.strip("\"'"))

            if not path.exists():
                print(f"❌ File not found: {path}")
                continue

            if path.suffix.lower() not in [".docx", ".md", ".txt", ".html", ".htm"]:
                print(f"❌ Unsupported file type: {path.suffix}")
                print("Supported formats: .docx, .md, .txt, .html")
                continue

            self.state.input_file = path
            print(f"✅ File selected: {path.name}")
            return True

    def _step_metadata(self) -> bool:
        """Metadata entry step with AI enhancement."""

        if not self.state.metadata:
            # Try to extract metadata from file
            self.state.metadata = self._extract_metadata_from_file()

        metadata = self.state.metadata

        # Offer AI enhancement if available
        ai_manager = get_ai_manager()
        if ai_manager.is_available() and self.state.input_file:
            print("\n🤖 AI-Powered Metadata Enhancement Available!")
            if self._prompt_bool(
                "Would you like AI to analyze your document and suggest metadata?"
            ):
                self._enhance_metadata_with_ai(metadata)

        # Interactive metadata entry
        print("\nEnter book metadata (press Enter to keep current value):")

        title = self._get_user_input(f"Title [{metadata.title}]") or metadata.title
        author = self._get_user_input(f"Author [{metadata.author}]") or metadata.author
        description = (
            self._get_user_input(f"Description [{metadata.description or 'None'}]")
            or metadata.description
        )
        language = self._get_user_input(f"Language [{metadata.language}]") or metadata.language

        # AI Genre Detection
        if ai_manager.is_available() and self._prompt_bool(
            "Would you like AI to suggest genres and keywords?"
        ):
            self._suggest_genre_and_keywords(metadata)

        # Update metadata
        metadata.title = title
        metadata.author = author
        metadata.description = description
        metadata.language = language

        print("\n✅ Metadata configured:")
        print(f"   Title: {metadata.title}")
        print(f"   Author: {metadata.author}")
        print(f"   Language: {metadata.language}")
        if hasattr(metadata, "genre") and metadata.genre:
            print(f"   Genre: {metadata.genre}")

        return True

    def _step_theme_style(self) -> bool:
        """Theme and styling step."""
        print("Available themes:")
        themes = self._get_available_themes()

        for i, theme in enumerate(themes, 1):
            print(f"  {i}. {theme['name']} - {theme['description']}")

        print(f"  {len(themes) + 1}. Custom theme editor")

        while True:
            choice = self._get_user_input("Select theme (number)")

            if not self._handle_navigation(choice):
                return False

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(themes):
                    selected_theme = themes[choice_num - 1]
                    self.state.custom_settings["theme"] = selected_theme["id"]
                    print(f"✅ Theme selected: {selected_theme['name']}")
                    break
                elif choice_num == len(themes) + 1:
                    return self._run_theme_editor()
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Please enter a number")

        return True

    def _step_structure(self) -> bool:
        """Book structure configuration step."""
        print("Configure book structure:")

        # Chapter detection
        print("\n1. Chapter Detection:")
        print("   a) Auto-detect from headings (recommended)")
        print("   b) Manual page breaks")
        print("   c) Custom configuration")

        structure_choice = self._get_user_input("Choose option (a/b/c)") or "a"

        if not self._handle_navigation(structure_choice):
            return False

        self.state.custom_settings["chapter_detection"] = structure_choice

        # Table of contents depth
        toc_depth = self._get_user_input("Table of contents depth (1-6) [2]") or "2"

        try:
            self.state.custom_settings["toc_depth"] = int(toc_depth)
        except ValueError:
            self.state.custom_settings["toc_depth"] = 2

        print(f"✅ Structure configured with TOC depth {self.state.custom_settings['toc_depth']}")
        return True

    def _step_preview(self) -> bool:
        """Preview and review step."""
        print("📖 Generating preview...")

        if self.state.preview_enabled:
            success = self._generate_preview()
            if success:
                print("✅ Preview generated successfully!")
                print("   Preview will open in your default browser")

                if self._confirm("Open preview now?"):
                    self._open_preview()
            else:
                print("❌ Preview generation failed")

        print("\n📋 Review your settings:")
        self._display_configuration_summary()

        if not self._confirm("Proceed with conversion?"):
            print("You can go back to modify settings")
            self.state.current_step -= 2  # Go back to previous step
            return True

        return True

    def _step_conversion(self) -> bool:
        """Final conversion step."""
        print("🚀 Starting EPUB conversion...")

        try:
            output_path = self._run_conversion()
            print("✅ Conversion completed successfully!")
            print(f"📖 EPUB saved to: {output_path}")

            if self._confirm("Open output folder?"):
                self._open_output_folder(output_path)

            return True

        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            print("Check the error details above and try again")
            return False

    def _extract_metadata_from_file(self) -> EpubMetadata:
        """Extract metadata from the input file."""
        from .metadata import EpubMetadata

        # Try to extract from DOCX core properties
        metadata = EpubMetadata(
            title=self.state.input_file.stem if self.state.input_file else "Untitled",
            author="Unknown Author",
            language="en",
        )

        if self.state.input_file and self.state.input_file.suffix.lower() == ".docx":
            try:
                from docx import Document

                doc = Document(self.state.input_file)
                core = getattr(doc, "core_properties", None)

                if core:
                    if getattr(core, "title", None):
                        metadata.title = core.title
                    if getattr(core, "author", None):
                        metadata.author = core.author

            except Exception:
                pass  # Use defaults

        return metadata

    def _get_available_themes(self) -> List[Dict[str, str]]:
        """Get list of available themes."""
        return [
            {"id": "serif", "name": "Serif", "description": "Classic book style with serif fonts"},
            {
                "id": "sans",
                "name": "Sans-serif",
                "description": "Modern clean style with sans-serif fonts",
            },
            {
                "id": "printlike",
                "name": "Print-like",
                "description": "Traditional print book appearance",
            },
            {"id": "minimal", "name": "Minimal", "description": "Clean minimal design"},
        ]

    def _run_theme_editor(self) -> bool:
        """Run the interactive theme editor."""
        try:
            from .theme_editor import ThemeEditor

            print("\n🎨 Advanced Theme Editor")
            print("Create and customize your own theme with live preview")

            editor = ThemeEditor()
            result = editor.run_interactive_editor()

            if result and result.get("theme_id"):
                # Save the custom theme ID to wizard state
                self.state.custom_settings["theme"] = result["theme_id"]
                self.state.custom_settings["custom_theme_path"] = result.get("theme_path")
                print(f"✅ Custom theme created: {result['theme_id']}")
                return True
            else:
                print("🔄 Returning to theme selection...")
                return False  # Return to theme selection

        except ImportError:
            print("❌ Theme editor module not available")
            print("🔄 Returning to theme selection...")
            return False
        except Exception as e:
            # Use enhanced error handling for theme editor issues
            handled = handle_error(
                error=e, operation="theme editor", step="theme_selection", interactive=True
            )
            if not handled:
                print(f"❌ Theme editor error: {e}")
            print("🔄 Returning to theme selection...")
            return False

    def _generate_preview(self) -> bool:
        """Generate a preview of the EPUB."""
        import argparse
        import tempfile

        from .cli import run_build

        try:
            if not self.state.input_file or not self.state.metadata:
                print("❌ Cannot generate preview: input file or metadata missing")
                return False

            print("\n🔄 Generating preview...")

            # Create temporary output directory for preview
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Create args namespace for preview conversion
                args = argparse.Namespace()
                args.input = str(self.state.input_file)
                args.title = self.state.metadata.title
                args.author = self.state.metadata.author
                args.language = self.state.metadata.language
                args.theme = self.state.custom_settings.get("theme", "serif")
                args.toc_depth = self.state.custom_settings.get("toc_depth", 2)
                args.output = str(temp_path)
                args.no_prompt = True
                args.quiet = False
                args.preview = True  # Enable preview mode
                args.preview_port = 8000
                args.inspect = False  # Don't need inspect mode in preview

                # Run conversion with preview enabled
                result = run_build(args)

                if result != 0:
                    print("❌ Preview generation failed")
                    return False

                print("✅ Preview generated successfully")
                return True

        except Exception as e:
            print(f"❌ Preview generation error: {e}")
            return False

    def _open_preview(self):
        """Open the preview in browser.

        Note: Preview is automatically opened when preview mode is enabled.
        This method is included for explicit user-triggered preview opening.
        """
        import webbrowser

        try:
            port = self.state.custom_settings.get("preview_port", 8000)
            url = f"http://localhost:{port}"

            if webbrowser.open(url):
                print(f"✅ Opened preview in browser: {url}")
            else:
                print(f"⚠️  Could not open browser. Visit manually: {url}")

        except Exception as e:
            print(f"❌ Could not open preview: {e}")

    def _display_configuration_summary(self):
        """Display a summary of current configuration."""
        print(f"Input file: {self.state.input_file}")
        if self.state.metadata:
            print(f"Title: {self.state.metadata.title}")
            print(f"Author: {self.state.metadata.author}")

        theme = self.state.custom_settings.get("theme", "serif")
        print(f"Theme: {theme}")

        toc_depth = self.state.custom_settings.get("toc_depth", 2)
        print(f"TOC Depth: {toc_depth}")

    @wrap_with_error_handling("EPUB conversion", "conversion")
    def _run_conversion(self) -> Path:
        """Run the actual conversion process."""
        import argparse

        from .cli import run_build

        try:
            # Create args namespace
            args = argparse.Namespace()
            args.input = str(self.state.input_file)
            args.title = self.state.metadata.title
            args.author = self.state.metadata.author
            args.language = self.state.metadata.language
            args.theme = self.state.custom_settings.get("theme", "serif")
            args.toc_depth = self.state.custom_settings.get("toc_depth", 2)

            # Set default values for other required arguments
            args.output = None  # Let system generate name
            args.no_prompt = True
            args.quiet = False

            # Run conversion
            result = run_build(args)

            if result != 0:
                raise RuntimeError("Conversion failed - check the output above for details")

            # Return the output path (would need to be captured from run_build)
            output_name = f"{self.state.metadata.title.replace(' ', '_')}.epub"
            return Path(output_name)

        except Exception as e:
            # Enhanced error handling will provide contextual help
            handled = handle_error(
                error=e,
                operation="EPUB conversion",
                file_path=self.state.input_file,
                step="conversion",
                interactive=True,
            )
            if not handled:
                raise

    def _open_output_folder(self, output_path: Path):
        """Open the folder containing the output file."""
        import os
        import subprocess

        folder = output_path.parent

        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", folder])
            else:  # Linux
                subprocess.run(["xdg-open", folder])
        except Exception as e:
            print(f"Could not open folder: {e}")
            print(f"Output location: {folder}")

    def _save_session(self):
        """Save the current wizard session."""
        if not self.state.session_file:
            self.state.session_file = self.session_dir / f"session_{int(time.time())}.json"

        session_data = {
            "current_step": self.state.current_step,
            "input_file": str(self.state.input_file) if self.state.input_file else None,
            "metadata": self.state.metadata.__dict__ if self.state.metadata else None,
            "custom_settings": self.state.custom_settings,
            "preview_enabled": self.state.preview_enabled,
        }

        try:
            with open(self.state.session_file, "w") as f:
                json.dump(session_data, f, indent=2, default=str)
        except Exception:
            pass  # Ignore save errors

    def _load_session(self):
        """Load the most recent wizard session."""
        try:
            session_files = list(self.session_dir.glob("session_*.json"))
            if not session_files:
                return

            latest_session = max(session_files, key=lambda p: p.stat().st_mtime)

            with open(latest_session, "r") as f:
                session_data = json.load(f)

            if self._confirm(f"Resume previous session from {latest_session.stem}?"):
                self.state.current_step = session_data.get("current_step", 0)
                if session_data.get("input_file"):
                    self.state.input_file = Path(session_data["input_file"])
                self.state.custom_settings = session_data.get("custom_settings", {})
                # Restore metadata would need more complex deserialization

        except Exception:
            pass  # Ignore load errors

    def _skip_to_step(self, step_id: str):
        """Skip to a specific step by ID."""
        for i, step in enumerate(self.state.steps):
            if step.step_id == step_id:
                self.state.current_step = i
                break

    def _get_user_input(self, prompt: str) -> str:
        """Get user input with prompt."""
        try:
            return input(f"{prompt}: ").strip()
        except (KeyboardInterrupt, EOFError):
            return "quit"

    def _confirm(self, question: str) -> bool:
        """Ask user for yes/no confirmation."""
        while True:
            response = self._get_user_input(f"{question} (y/n)").lower()
            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no"]:
                return False
            elif response in ["quit", "exit"]:
                return False
            else:
                print("Please enter 'y' or 'n'")

    def _handle_navigation(self, response: str) -> bool:
        """Handle navigation commands."""
        response = response.lower().strip()

        if response in ["quit", "exit", "q"]:
            return False
        elif response in ["back", "b"]:
            if self.state.current_step > 0:
                self.state.current_step -= 2  # Will be incremented in main loop
                return True
            else:
                print("Already at first step")
                return True
        elif response in ["help", "h"]:
            self._show_step_help()
            return True

        return True

    def _show_step_help(self):
        """Show help for the current step."""
        step = self.state.steps[self.state.current_step]
        print(f"\n📚 Help for {step.title}:")
        print(f"   {step.help_text or 'No additional help available'}")

        print("\nNavigation commands:")
        print("   'back' - Go to previous step")
        print("   'quit' - Exit wizard")
        print("   'help' - Show this help")

    def _enhance_metadata_with_ai(self, metadata: EpubMetadata):
        """Enhance metadata using AI analysis."""
        try:
            print("🤖 Analyzing document content...")

            # Read document content
            content = self._read_document_content()
            if not content:
                print("⚠️  Could not read document content for AI analysis")
                return

            # Get AI enhancement
            enhanced = enhance_metadata_with_ai(content, metadata, interactive=True)

            # Apply enhancements
            if enhanced.applied_suggestions:
                print(f"✅ Applied {len(enhanced.applied_suggestions)} AI suggestions")
            else:
                print("ℹ️  No automatic suggestions applied")

        except Exception as e:
            print(f"⚠️  AI metadata enhancement failed: {e}")

    def _suggest_genre_and_keywords(self, metadata: EpubMetadata):
        """Suggest genres and keywords using AI."""
        try:
            print("🎯 Analyzing content for genres and keywords...")

            content = self._read_document_content()
            if not content:
                print("⚠️  Could not read document content for analysis")
                return

            # Detect genres
            genre_result = detect_genre_with_ai(
                content,
                {
                    "title": metadata.title,
                    "author": metadata.author,
                    "description": metadata.description or "",
                },
            )

            if genre_result.genres:
                print("\n📚 Suggested Genres:")
                for i, genre in enumerate(genre_result.genres[:5], 1):
                    confidence_icon = (
                        "🟢"
                        if genre.confidence >= 0.8
                        else "🟡" if genre.confidence >= 0.6 else "🔴"
                    )
                    print(f"   {i}. {confidence_icon} {genre.genre} ({genre.confidence:.1%})")

                choice = self._get_user_input("Select genre number (or Enter to skip)")
                if choice.isdigit() and 1 <= int(choice) <= len(genre_result.genres[:5]):
                    selected_genre = genre_result.genres[int(choice) - 1]
                    metadata.genre = selected_genre.genre
                    print(f"✅ Set genre to: {selected_genre.genre}")

            if genre_result.keywords:
                print(f"\n🏷️  Suggested Keywords: {', '.join(genre_result.keywords[:10])}")
                if self._prompt_bool("Apply these keywords?"):
                    metadata.keywords = genre_result.keywords[:10]
                    print("✅ Keywords applied")

        except Exception as e:
            print(f"⚠️  Genre detection failed: {e}")

    def _read_document_content(self) -> str:
        """Read document content for AI analysis."""
        if not self.state.input_file:
            return ""

        try:
            if self.state.input_file.suffix.lower() == ".docx":
                # Use docx2txt or similar to extract text
                from .convert import extract_text_from_docx

                return extract_text_from_docx(self.state.input_file)
            else:
                # Read as text file
                return self.state.input_file.read_text(encoding="utf-8")
        except Exception:
            return ""

    def _prompt_bool(self, question: str) -> bool:
        """Prompt user with yes/no question."""
        while True:
            response = self._get_user_input(f"{question} (y/n)").lower()
            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no", "quit", "exit"]:
                return False
            else:
                print("Please enter 'y' or 'n'")


def run_wizard_mode(input_file: Optional[Path] = None) -> int:
    """Run the conversion wizard.

    Args:
        input_file: Optional pre-selected input file

    Returns:
        Exit code (0 for success)
    """
    wizard = ConversionWizard()
    return wizard.start_wizard(input_file)
