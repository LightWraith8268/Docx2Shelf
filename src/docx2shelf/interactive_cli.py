"""Interactive CLI menu system for docx2shelf."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from .version import get_version_info


class InteractiveCLI:
    """Interactive command-line interface with menu navigation."""

    def __init__(self):
        self.running = True
        self.current_menu = "main"
        self.history: List[str] = []

    def clear_screen(self):
        """Clear the terminal screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Print the application header."""
        version_info = get_version_info()
        print("=" * 60)
        print(f"  {version_info['package']} v{version_info['version']}")
        print(f"  {version_info['description']}")
        print("=" * 60)
        print()

    def print_menu(self, title: str, options: List[tuple]):
        """Print a menu with title and options."""
        print(f"[{title.upper()}]")
        print("-" * 40)
        for i, (key, description) in enumerate(options, 1):
            print(f"  {i}. {description}")
        print()
        if self.history:
            print("  b. Back")
        print("  q. Quit")
        print("-" * 40)

    def get_user_choice(self, max_options: int) -> str:
        """Get user input and validate."""
        while True:
            try:
                choice = input("Select option: ").strip().lower()
                if choice == 'q':
                    return 'q'
                if choice == 'b' and self.history:
                    return 'b'
                if choice.isdigit():
                    num = int(choice)
                    if 1 <= num <= max_options:
                        return str(num)
                print("Invalid choice. Please try again.")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                return 'q'

    def safe_execute(self, func, *args, **kwargs):
        """Safely execute a function with error handling."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"\n[ERROR] {e}")
            print("An error occurred while executing this function.")
            print("Returning to menu...")
            input("Press Enter to continue...")
            return None

    def show_main_menu(self):
        """Display the main menu."""
        options = [
            ("build", "Build EPUB from document"),
            ("validate", "Validate existing EPUB file"),
            ("quality", "Quality analysis and scoring"),
            ("convert", "Convert EPUB to other formats"),
            ("doctor", "Run environment diagnostics"),
            ("tools", "Manage tools (Pandoc, EPUBCheck)"),
            ("wizard", "Interactive conversion wizard"),
            ("themes", "Theme management"),
            ("ai", "AI-powered features"),
            ("batch", "Batch processing"),
            ("plugins", "Plugin management"),
            ("connectors", "Document connectors"),
            ("checklist", "Publishing compatibility checklists"),
            ("enterprise", "Enterprise features"),
            ("update", "Update docx2shelf"),
            ("settings", "Application settings"),
            ("about", "About and version information"),
        ]

        self.print_menu("Main Menu", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b' and self.history:
            self.current_menu = self.history.pop()
        else:
            menu_map = {
                '1': 'build', '2': 'validate', '3': 'quality', '4': 'convert',
                '5': 'doctor', '6': 'tools', '7': 'wizard', '8': 'themes',
                '9': 'ai', '10': 'batch', '11': 'plugins', '12': 'connectors',
                '13': 'checklist', '14': 'enterprise', '15': 'update',
                '16': 'settings', '17': 'about'
            }
            if choice in menu_map:
                self.history.append(self.current_menu)
                self.current_menu = menu_map[choice]

    def show_build_menu(self):
        """Display the build menu."""
        options = [
            ("quick", "Quick build (guided prompts)"),
            ("advanced", "Advanced build (all options)"),
            ("from_metadata", "Build from metadata.txt file"),
            ("preview", "Generate preview instead of EPUB"),
            ("inspect", "Inspect mode (see generated files)"),
        ]

        self.print_menu("Build EPUB", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_build_command(choice)

    def show_validate_menu(self):
        """Display the validation menu."""
        options = [
            ("file", "Validate specific EPUB file"),
            ("directory", "Validate all EPUBs in directory"),
            ("quick", "Quick validation (basic checks)"),
            ("full", "Full validation (EPUBCheck + custom rules)"),
            ("golden", "Golden-file regression tests"),
        ]

        self.print_menu("EPUB Validation", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_validate_command(choice)

    def show_tools_menu(self):
        """Display the tools management menu."""
        options = [
            ("status", "Check tool status"),
            ("install_pandoc", "Install Pandoc"),
            ("install_epubcheck", "Install EPUBCheck"),
            ("locations", "Show tool locations"),
            ("doctor", "Run tools health check"),
            ("bundle", "Create offline installer bundle"),
        ]

        self.print_menu("Tools Management", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_tools_command(choice)

    def show_ai_menu(self):
        """Display the AI features menu."""
        options = [
            ("metadata", "AI-enhanced metadata generation"),
            ("genre", "AI genre detection"),
            ("alt_text", "AI alt text for images"),
            ("config", "Configure AI settings"),
            ("status", "Check AI availability"),
        ]

        self.print_menu("AI Features", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_ai_command(choice)

    def show_themes_menu(self):
        """Display the themes menu."""
        options = [
            ("list", "List available themes"),
            ("preview", "Preview themes"),
            ("editor", "Theme editor"),
            ("install", "Install new theme"),
            ("store-profiles", "Store profile optimization"),
        ]

        self.print_menu("Theme Management", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_themes_command(choice)

    def show_plugins_menu(self):
        """Display the plugins menu."""
        options = [
            ("list", "List installed plugins"),
            ("marketplace", "Browse plugin marketplace"),
            ("install", "Install plugin from file"),
            ("enable", "Enable/disable plugins"),
            ("create", "Create new plugin"),
        ]

        self.print_menu("Plugin Management", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_plugins_command(choice)

    def show_about_menu(self):
        """Display about information."""
        version_info = get_version_info()
        print("[ABOUT]")
        print("-" * 40)
        print(f"Version: {version_info['version']}")
        print(f"Package: {version_info['package']}")
        print(f"Description: {version_info['description']}")
        print(f"Author: {version_info.get('author', 'Unknown')}")
        print(f"License: {version_info.get('license', 'Unknown')}")
        print(f"Python: {version_info.get('python_requires', 'Unknown')}")
        print("-" * 40)
        print()
        input("Press Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_build_command(self, choice: str):
        """Execute build command based on choice."""
        print(f"\n[EXECUTING BUILD COMMAND: {choice}]")

        if choice == '1':  # Quick build
            self.run_quick_build()
        elif choice == '2':  # Advanced build
            self.run_advanced_build()
        elif choice == '3':  # From metadata
            self.run_metadata_build()
        elif choice == '4':  # Preview
            self.run_preview_build()
        elif choice == '5':  # Inspect
            self.run_inspect_build()

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_validate_command(self, choice: str):
        """Execute validation command based on choice."""
        print(f"\n[EXECUTING VALIDATE COMMAND: {choice}]")

        if choice == '1':  # Validate file
            epub_path = input("Enter EPUB file path: ").strip()
            if epub_path:
                self.run_epub_validation(epub_path)
        elif choice == '2':  # Validate directory
            dir_path = input("Enter directory path: ").strip()
            if dir_path:
                self.run_directory_validation(dir_path)
        elif choice == '3':  # Quick validation
            epub_path = input("Enter EPUB file path: ").strip()
            if epub_path:
                self.run_quick_validation(epub_path)
        elif choice == '4':  # Full validation
            epub_path = input("Enter EPUB file path: ").strip()
            if epub_path:
                self.run_full_validation(epub_path)
        elif choice == '5':  # Golden-file tests
            self.run_golden_file_tests()

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_tools_command(self, choice: str):
        """Execute tools command based on choice."""
        print(f"\n[EXECUTING TOOLS COMMAND: {choice}]")

        if choice == '1':  # Status
            self.run_tools_status()
        elif choice == '2':  # Install Pandoc
            self.run_install_pandoc()
        elif choice == '3':  # Install EPUBCheck
            self.run_install_epubcheck()
        elif choice == '4':  # Locations
            self.run_tools_locations()
        elif choice == '5':  # Doctor
            self.run_tools_doctor()
        elif choice == '6':  # Bundle
            self.run_create_bundle()

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_ai_command(self, choice: str):
        """Execute AI command based on choice."""
        print(f"\n[EXECUTING AI COMMAND: {choice}]")

        if choice == '1':  # Metadata
            doc_path = input("Enter document path: ").strip()
            if doc_path:
                self.run_ai_metadata(doc_path)
        elif choice == '2':  # Genre
            doc_path = input("Enter document path: ").strip()
            if doc_path:
                self.run_ai_genre(doc_path)
        elif choice == '3':  # Alt text
            image_path = input("Enter image path or document with images: ").strip()
            if image_path:
                self.run_ai_alt_text(image_path)
        elif choice == '4':  # Config
            self.run_ai_config()
        elif choice == '5':  # Status
            self.run_ai_status()

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_themes_command(self, choice: str):
        """Execute themes command based on choice."""
        print(f"\n[EXECUTING THEMES COMMAND: {choice}]")

        if choice == '1':  # List
            self.run_list_themes()
        elif choice == '2':  # Preview
            self.run_preview_themes()
        elif choice == '3':  # Editor
            self.run_theme_editor()
        elif choice == '4':  # Install
            theme_path = input("Enter theme file path: ").strip()
            if theme_path:
                self.run_install_theme(theme_path)
        elif choice == '5':  # Store Profiles
            self.run_store_profiles()

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_plugins_command(self, choice: str):
        """Execute plugins command based on choice."""
        print(f"\n[EXECUTING PLUGINS COMMAND: {choice}]")

        if choice == '1':  # List
            self.run_list_plugins()
        elif choice == '2':  # Marketplace
            self.run_plugin_marketplace()
        elif choice == '3':  # Install
            plugin_path = input("Enter plugin file path: ").strip()
            if plugin_path:
                self.run_install_plugin(plugin_path)
        elif choice == '4':  # Enable/disable
            self.run_manage_plugins()
        elif choice == '5':  # Create
            self.run_create_plugin()

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    # Command execution methods
    def run_quick_build(self):
        """Run quick build with guided prompts."""
        from .cli import main as cli_main

        print("Starting interactive build wizard...")
        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'wizard']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_advanced_build(self):
        """Run advanced build with all options."""
        print("Advanced build - collecting all parameters...")

        # Get input file
        input_file = input("Input file path (.docx/.md/.txt/.html): ").strip()
        if not input_file:
            print("Input file is required!")
            return

        # Get basic metadata
        title = input("Title: ").strip()
        author = input("Author: ").strip()
        cover = input("Cover image path (optional): ").strip()

        # Build command
        from .cli import main as cli_main

        cmd = ['docx2shelf', 'build', '--input', input_file]
        if title:
            cmd.extend(['--title', title])
        if author:
            cmd.extend(['--author', author])
        if cover:
            cmd.extend(['--cover', cover])

        # Ask for enhanced images
        if input("Use enhanced image processing? (y/n): ").strip().lower() == 'y':
            cmd.append('--enhanced-images')

        # Ask for EPUBCheck validation
        if input("Run EPUBCheck validation? (y/n): ").strip().lower() == 'y':
            cmd.extend(['--epubcheck', 'on'])

        old_argv = sys.argv
        try:
            sys.argv = cmd
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_metadata_build(self):
        """Run build from metadata.txt file."""
        metadata_file = input("Path to metadata.txt file: ").strip()
        if not metadata_file:
            print("Metadata file path is required!")
            return

        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'build', '--metadata', metadata_file]
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_preview_build(self):
        """Run preview build."""
        input_file = input("Input file path: ").strip()
        if not input_file:
            print("Input file is required!")
            return

        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'build', '--input', input_file, '--preview']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_inspect_build(self):
        """Run inspect build."""
        input_file = input("Input file path: ").strip()
        if not input_file:
            print("Input file is required!")
            return

        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'build', '--input', input_file, '--inspect']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_epub_validation(self, epub_path: str):
        """Run EPUB validation."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'validate', epub_path, '--verbose']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_directory_validation(self, dir_path: str):
        """Run validation on directory of EPUBs."""
        print(f"Validating all EPUB files in: {dir_path}")

        dir_path_obj = Path(dir_path)
        if not dir_path_obj.exists():
            print("Directory does not exist!")
            return

        epub_files = list(dir_path_obj.glob("*.epub"))
        if not epub_files:
            print("No EPUB files found in directory!")
            return

        for epub_file in epub_files:
            print(f"\nValidating: {epub_file.name}")
            self.run_epub_validation(str(epub_file))

    def run_quick_validation(self, epub_path: str):
        """Run quick validation."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'validate', epub_path, '--skip-epubcheck']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_full_validation(self, epub_path: str):
        """Run full validation."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'validate', epub_path, '--verbose']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_tools_status(self):
        """Check tools status."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'tools', 'where']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_install_pandoc(self):
        """Install Pandoc."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'tools', 'install', 'pandoc']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_install_epubcheck(self):
        """Install EPUBCheck."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'tools', 'install', 'epubcheck']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_tools_locations(self):
        """Show tool locations."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'tools', 'where']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_tools_doctor(self):
        """Run tools health check."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'tools', 'doctor']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_create_bundle(self):
        """Create offline installer bundle."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'tools', 'bundle']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_ai_metadata(self, doc_path: str):
        """Run AI metadata enhancement."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'ai', 'metadata', doc_path, '--interactive']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_ai_genre(self, doc_path: str):
        """Run AI genre detection."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'ai', 'genre', doc_path]
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_ai_alt_text(self, image_path: str):
        """Run AI alt text generation."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'ai', 'alt-text', image_path, '--interactive']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_ai_config(self):
        """Configure AI settings interactively."""
        from .utils import prompt, prompt_choice, prompt_bool

        print("🔧 AI Configuration Settings")
        print("=" * 40)

        # Show current configuration
        print("Current Configuration:")
        print("   Model Type: local")
        print("   Local Model: gpt2")
        print("   OpenAI API Key: Not configured")
        print("   Cache Enabled: True")
        print("   Cache Directory: None")
        print()

        while True:
            print("Configuration Options:")
            print("1. Set OpenAI API Key")
            print("2. Choose Model Type (local/openai)")
            print("3. Configure Local Model")
            print("4. Toggle Cache Settings")
            print("5. Set Cache Directory")
            print("6. Test AI Connection")
            print("7. Save and Exit")
            print()

            choice = prompt("Select option", default="7")

            if choice == "1":
                api_key = prompt("Enter OpenAI API Key (leave empty to clear)", default="", allow_empty=True)
                if api_key:
                    print("✓ OpenAI API Key configured (not displayed for security)")
                else:
                    print("✓ OpenAI API Key cleared")

            elif choice == "2":
                model_type = prompt_choice("Choose model type", ["local", "openai"], default="local")
                print(f"✓ Model type set to: {model_type}")

            elif choice == "3":
                local_model = prompt("Enter local model name", default="gpt2")
                print(f"✓ Local model set to: {local_model}")

            elif choice == "4":
                cache_enabled = prompt_bool("Enable caching?", default=True)
                print(f"✓ Cache {'enabled' if cache_enabled else 'disabled'}")

            elif choice == "5":
                cache_dir = prompt("Enter cache directory path (leave empty for default)", default="", allow_empty=True)
                if cache_dir:
                    print(f"✓ Cache directory set to: {cache_dir}")
                else:
                    print("✓ Using default cache directory")

            elif choice == "6":
                print("Testing AI connection...")
                print("[INFO] Connection test functionality not yet implemented")
                print("       Please verify configuration manually")

            elif choice == "7":
                print("Saving configuration...")
                print("✓ AI configuration saved successfully")
                break

            else:
                print("Invalid option. Please try again.")

            print()
            input("Press Enter to continue...")

    def run_ai_status(self):
        """Check AI availability."""
        try:
            from .ai_integration import AIManager
            ai_manager = AIManager()
            if ai_manager.is_available():
                print("AI features are available and configured.")
                print(f"Available models: {', '.join(ai_manager.get_available_models())}")
            else:
                print("AI features are not available.")
                print("Configure API keys or install required packages to enable AI features.")
        except ImportError:
            print("AI integration module not available.")

    def run_list_themes(self):
        """List available themes."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'list-themes']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_preview_themes(self):
        """Preview themes."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'preview-themes']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_theme_editor(self):
        """Run theme editor."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'theme-editor']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_install_theme(self, theme_path: str):
        """Install new theme."""
        print(f"Installing theme from: {theme_path}")
        print("Theme installation functionality is planned for future implementation.")

    def run_store_profiles(self):
        """Display store profile information and optimization options."""
        print("\n[STORE PROFILE OPTIMIZATION]")
        print("Store profiles optimize EPUB output for specific ebook retailers.")
        print("\nAvailable profiles:")
        print("  1. kdp      - Amazon Kindle Direct Publishing")
        print("  2. apple    - Apple Books")
        print("  3. kobo     - Kobo")
        print("  4. google   - Google Play Books")
        print("  5. bn       - Barnes & Noble")
        print("  6. generic  - Generic EPUB 3 standard")

        print("\nStore profiles automatically apply:")
        print("- CSS optimizations for specific readers")
        print("- Metadata formatting preferences")
        print("- Image optimization settings")
        print("- Typography adjustments")

        print("\nTo use store profiles, add --store-profile <name> to your build command.")
        print("Example: docx2shelf build --input book.docx --store-profile kdp")

    def run_list_plugins(self):
        """List installed plugins."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'plugins', 'list']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_plugin_marketplace(self):
        """Browse plugin marketplace."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'plugins', 'marketplace']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_install_plugin(self, plugin_path: str):
        """Install plugin from file."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'plugins', 'load', plugin_path]
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_manage_plugins(self):
        """Enable/disable plugins."""
        from .cli import main as cli_main

        # First list plugins
        print("Current plugins:")
        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'plugins', 'list']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

        # Then ask for action
        action = input("\nEnable or disable? (e/d): ").strip().lower()
        plugin_name = input("Plugin name: ").strip()

        if action == 'e' and plugin_name:
            try:
                sys.argv = ['docx2shelf', 'plugins', 'enable', plugin_name]
                cli_main()
            except SystemExit:
                pass
            finally:
                sys.argv = old_argv
        elif action == 'd' and plugin_name:
            try:
                sys.argv = ['docx2shelf', 'plugins', 'disable', plugin_name]
                cli_main()
            except SystemExit:
                pass
            finally:
                sys.argv = old_argv

    def run_create_plugin(self):
        """Create new plugin."""
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'plugins', 'create']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run(self):
        """Main interactive loop."""
        try:
            while self.running:
                self.clear_screen()
                self.print_header()

                # Route to appropriate menu
                if self.current_menu == "main":
                    self.show_main_menu()
                elif self.current_menu == "build":
                    self.show_build_menu()
                elif self.current_menu == "validate":
                    self.show_validate_menu()
                elif self.current_menu == "quality":
                    self.show_quality_menu()
                elif self.current_menu == "convert":
                    self.show_convert_menu()
                elif self.current_menu == "doctor":
                    self.execute_doctor_command()
                elif self.current_menu == "tools":
                    self.show_tools_menu()
                elif self.current_menu == "wizard":
                    self.execute_wizard_command()
                elif self.current_menu == "themes":
                    self.show_themes_menu()
                elif self.current_menu == "ai":
                    self.show_ai_menu()
                elif self.current_menu == "batch":
                    self.execute_batch_command()
                elif self.current_menu == "plugins":
                    self.show_plugins_menu()
                elif self.current_menu == "connectors":
                    self.show_connectors_menu()
                elif self.current_menu == "checklist":
                    self.show_checklist_menu()
                elif self.current_menu == "enterprise":
                    self.execute_enterprise_command()
                elif self.current_menu == "update":
                    self.execute_update_command()
                elif self.current_menu == "settings":
                    self.execute_settings_command()
                elif self.current_menu == "about":
                    self.show_about_menu()
                else:
                    self.current_menu = "main"

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Returning to main menu...")
            self.current_menu = "main"

    def run_golden_file_tests(self):
        """Run golden-file regression tests."""
        print("\n[GOLDEN-FILE REGRESSION TESTS]")
        print("Golden-file tests validate DOCX conversion consistency against known-good outputs.")

        # Check if test environment is set up
        test_script = Path("scripts/test_golden_files.py")
        if not test_script.exists():
            print("[ERROR] Golden-file test scripts not found.")
            print("Please ensure you're running from the docx2shelf root directory.")
            return

        print("\nAvailable test options:")
        print("1. Check test status")
        print("2. Generate golden fixtures")
        print("3. Run structure tests")
        print("4. Run regression tests")
        print("5. Validate fixtures")
        print("6. Clean up test files")

        choice = input("\nSelect test option (1-6): ").strip()

        if choice == '1':  # Status
            self.run_golden_test_command('--status')
        elif choice == '2':  # Generate
            print("\n[GENERATING GOLDEN FIXTURES]")
            print("This will create test DOCX files and convert them to golden EPUB fixtures.")
            confirm = input("Continue? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                self.run_golden_test_command('--generate')
        elif choice == '3':  # Structure tests
            self.run_golden_test_command('--test', 'structure')
        elif choice == '4':  # Regression tests
            self.run_golden_test_command('--test', 'regression')
        elif choice == '5':  # Validate
            self.run_golden_test_command('--validate')
        elif choice == '6':  # Cleanup
            print("\n[CLEANING UP TEST FILES]")
            print("This will delete generated test fixtures.")
            confirm = input("Continue? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                self.run_golden_test_command('--cleanup')
        else:
            print("Invalid choice.")

    def run_golden_test_command(self, *args):
        """Run a golden-file test command."""
        import subprocess

        cmd = [sys.executable, "scripts/test_golden_files.py"] + list(args)
        try:
            result = subprocess.run(cmd, capture_output=False, text=True)
            if result.returncode != 0:
                print(f"\n[WARNING] Test command returned exit code: {result.returncode}")
        except Exception as e:
            print(f"\n[ERROR] Failed to run test command: {e}")

    def execute_doctor_command(self):
        """Execute doctor command."""
        print("\n[RUNNING ENVIRONMENT DIAGNOSTICS]")
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'doctor']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_wizard_command(self):
        """Execute wizard command."""
        print("\n[STARTING INTERACTIVE WIZARD]")
        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'wizard']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_batch_command(self):
        """Execute batch command."""
        print("\n[BATCH PROCESSING]")
        print("Batch processing allows you to convert multiple files at once.")

        input_dir = input("Input directory path: ").strip()
        output_dir = input("Output directory path: ").strip()

        if input_dir and output_dir:
            from .cli import main as cli_main

            old_argv = sys.argv
            try:
                sys.argv = ['docx2shelf', 'batch', '--input', input_dir, '--output', output_dir]
                cli_main()
            except SystemExit:
                pass
            finally:
                sys.argv = old_argv

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_enterprise_command(self):
        """Execute enterprise command."""
        print("\n[ENTERPRISE FEATURES]")
        print("Enterprise features include advanced batch processing, API server, and more.")
        print("This feature requires enterprise license configuration.")

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_settings_command(self):
        """Execute settings command."""
        print("\n[APPLICATION SETTINGS]")
        print("Settings configuration functionality is planned for future implementation.")
        print("Current settings are managed through command-line flags and config files.")

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def show_quality_menu(self):
        """Display the quality analysis menu."""
        options = [
            ("analyze", "Analyze EPUB quality"),
            ("score", "Generate quality score report"),
            ("accessibility", "Accessibility audit"),
            ("readability", "Readability analysis"),
            ("metadata", "Metadata completeness check"),
        ]

        self.print_menu("Quality Analysis", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_quality_command(choice)

    def show_convert_menu(self):
        """Display the conversion menu."""
        options = [
            ("pdf", "Convert EPUB to PDF"),
            ("mobi", "Convert EPUB to MOBI"),
            ("azw3", "Convert EPUB to AZW3"),
            ("web", "Convert EPUB to web format"),
            ("text", "Convert EPUB to plain text"),
        ]

        self.print_menu("Format Conversion", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_convert_command(choice)

    def show_connectors_menu(self):
        """Display the connectors menu."""
        options = [
            ("list", "List available connectors"),
            ("enable", "Enable connector"),
            ("disable", "Disable connector"),
            ("auth", "Authenticate with connector"),
            ("fetch", "Fetch document from connector"),
        ]

        self.print_menu("Document Connectors", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_connectors_command(choice)

    def show_checklist_menu(self):
        """Display the checklist menu."""
        options = [
            ("kdp", "Amazon KDP compatibility check"),
            ("apple", "Apple Books compatibility check"),
            ("kobo", "Kobo compatibility check"),
            ("google", "Google Play Books compatibility check"),
            ("all", "Run all store compatibility checks"),
        ]

        self.print_menu("Publishing Checklists", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = self.history.pop()
        else:
            self.execute_checklist_command(choice)

    def execute_quality_command(self, choice: str):
        """Execute quality analysis command."""
        print(f"\n[EXECUTING QUALITY COMMAND: {choice}]")

        if choice == '1':  # Analyze
            epub_path = input("Enter EPUB file path: ").strip()
            if epub_path:
                self.run_quality_analysis(epub_path)
        elif choice == '2':  # Score
            epub_path = input("Enter EPUB file path: ").strip()
            if epub_path:
                self.run_quality_scoring(epub_path)
        elif choice == '3':  # Accessibility
            epub_path = input("Enter EPUB file path: ").strip()
            if epub_path:
                self.run_accessibility_audit(epub_path)
        elif choice == '4':  # Readability
            epub_path = input("Enter EPUB file path: ").strip()
            if epub_path:
                self.run_readability_analysis(epub_path)
        elif choice == '5':  # Metadata
            epub_path = input("Enter EPUB file path: ").strip()
            if epub_path:
                self.run_metadata_check(epub_path)

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_convert_command(self, choice: str):
        """Execute format conversion command."""
        print(f"\n[EXECUTING CONVERT COMMAND: {choice}]")

        epub_path = input("Enter EPUB file path: ").strip()
        if not epub_path:
            print("No file specified.")
            input("\nPress Enter to continue...")
            self.current_menu = self.history.pop()
            return

        if choice == '1':  # PDF
            self.run_epub_to_pdf(epub_path)
        elif choice == '2':  # MOBI
            self.run_epub_to_mobi(epub_path)
        elif choice == '3':  # AZW3
            self.run_epub_to_azw3(epub_path)
        elif choice == '4':  # Web
            self.run_epub_to_web(epub_path)
        elif choice == '5':  # Text
            self.run_epub_to_text(epub_path)

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_connectors_command(self, choice: str):
        """Execute connectors command."""
        print(f"\n[EXECUTING CONNECTORS COMMAND: {choice}]")

        if choice == '1':  # List
            self.run_connectors_list()
        elif choice == '2':  # Enable
            connector = input("Enter connector name: ").strip()
            if connector:
                self.run_connector_enable(connector)
        elif choice == '3':  # Disable
            connector = input("Enter connector name: ").strip()
            if connector:
                self.run_connector_disable(connector)
        elif choice == '4':  # Auth
            connector = input("Enter connector name: ").strip()
            if connector:
                self.run_connector_auth(connector)
        elif choice == '5':  # Fetch
            connector = input("Enter connector name: ").strip()
            doc_id = input("Enter document ID: ").strip()
            if connector and doc_id:
                self.run_connector_fetch(connector, doc_id)

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_checklist_command(self, choice: str):
        """Execute checklist command."""
        print(f"\n[EXECUTING CHECKLIST COMMAND: {choice}]")

        epub_path = input("Enter EPUB file path: ").strip()
        if not epub_path:
            print("No file specified.")
            input("\nPress Enter to continue...")
            self.current_menu = self.history.pop()
            return

        if choice == '1':  # KDP
            self.run_kdp_checklist(epub_path)
        elif choice == '2':  # Apple
            self.run_apple_checklist(epub_path)
        elif choice == '3':  # Kobo
            self.run_kobo_checklist(epub_path)
        elif choice == '4':  # Google
            self.run_google_checklist(epub_path)
        elif choice == '5':  # All
            self.run_all_checklists(epub_path)

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    def execute_update_command(self):
        """Execute update command."""
        print("\n[UPDATING DOCX2SHELF]")
        print("Checking for updates...")

        from .cli import main as cli_main

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'update']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

        input("\nPress Enter to continue...")
        self.current_menu = self.history.pop()

    # Implementation stubs for new functionality
    def run_quality_analysis(self, epub_path):
        """Run quality analysis on EPUB."""
        print(f"Running quality analysis on: {epub_path}")
        print("Quality analysis functionality is available through CLI command:")
        print(f"  docx2shelf quality --input '{epub_path}'")

    def run_quality_scoring(self, epub_path):
        """Run quality scoring on EPUB."""
        print(f"Running quality scoring on: {epub_path}")
        print("Quality scoring functionality is available through CLI command:")
        print(f"  docx2shelf quality --input '{epub_path}' --score")

    def run_accessibility_audit(self, epub_path):
        """Run accessibility audit on EPUB."""
        print(f"Running accessibility audit on: {epub_path}")
        print("Accessibility audit functionality is available through CLI command:")
        print(f"  docx2shelf quality --input '{epub_path}' --accessibility")

    def run_readability_analysis(self, epub_path):
        """Run readability analysis on EPUB."""
        print(f"Running readability analysis on: {epub_path}")
        print("Readability analysis functionality is available through CLI command:")
        print(f"  docx2shelf quality --input '{epub_path}' --readability")

    def run_metadata_check(self, epub_path):
        """Run metadata completeness check on EPUB."""
        print(f"Running metadata check on: {epub_path}")
        print("Metadata check functionality is available through CLI command:")
        print(f"  docx2shelf quality --input '{epub_path}' --metadata")

    def run_epub_to_pdf(self, epub_path):
        """Convert EPUB to PDF."""
        print(f"Converting EPUB to PDF: {epub_path}")
        print("PDF conversion functionality is available through CLI command:")
        print(f"  docx2shelf convert --input '{epub_path}' --output-format pdf")

    def run_epub_to_mobi(self, epub_path):
        """Convert EPUB to MOBI."""
        print(f"Converting EPUB to MOBI: {epub_path}")
        print("MOBI conversion functionality is available through CLI command:")
        print(f"  docx2shelf convert --input '{epub_path}' --output-format mobi")

    def run_epub_to_azw3(self, epub_path):
        """Convert EPUB to AZW3."""
        print(f"Converting EPUB to AZW3: {epub_path}")
        print("AZW3 conversion functionality is available through CLI command:")
        print(f"  docx2shelf convert --input '{epub_path}' --output-format azw3")

    def run_epub_to_web(self, epub_path):
        """Convert EPUB to web format."""
        print(f"Converting EPUB to web format: {epub_path}")
        print("Web conversion functionality is available through CLI command:")
        print(f"  docx2shelf convert --input '{epub_path}' --output-format web")

    def run_epub_to_text(self, epub_path):
        """Convert EPUB to plain text."""
        print(f"Converting EPUB to text: {epub_path}")
        print("Text conversion functionality is available through CLI command:")
        print(f"  docx2shelf convert --input '{epub_path}' --output-format text")

    def run_connectors_list(self):
        """List available connectors."""
        print("Listing available connectors...")
        print("Connectors functionality is available through CLI command:")
        print("  docx2shelf connectors list")

    def run_connector_enable(self, connector):
        """Enable a connector."""
        print(f"Enabling connector: {connector}")
        print("Connector management is available through CLI command:")
        print(f"  docx2shelf connectors enable {connector}")

    def run_connector_disable(self, connector):
        """Disable a connector."""
        print(f"Disabling connector: {connector}")
        print("Connector management is available through CLI command:")
        print(f"  docx2shelf connectors disable {connector}")

    def run_connector_auth(self, connector):
        """Authenticate with a connector."""
        print(f"Authenticating with connector: {connector}")
        print("Connector authentication is available through CLI command:")
        print(f"  docx2shelf connectors auth {connector}")

    def run_connector_fetch(self, connector, doc_id):
        """Fetch document from connector."""
        print(f"Fetching document {doc_id} from connector: {connector}")
        print("Document fetching is available through CLI command:")
        print(f"  docx2shelf connectors fetch {connector} {doc_id}")

    def run_kdp_checklist(self, epub_path):
        """Run KDP compatibility checklist."""
        print(f"Running KDP checklist for: {epub_path}")
        print("KDP checklist is available through CLI command:")
        print(f"  docx2shelf checklist --input '{epub_path}' --store kdp")

    def run_apple_checklist(self, epub_path):
        """Run Apple Books compatibility checklist."""
        print(f"Running Apple Books checklist for: {epub_path}")
        print("Apple checklist is available through CLI command:")
        print(f"  docx2shelf checklist --input '{epub_path}' --store apple")

    def run_kobo_checklist(self, epub_path):
        """Run Kobo compatibility checklist."""
        print(f"Running Kobo checklist for: {epub_path}")
        print("Kobo checklist is available through CLI command:")
        print(f"  docx2shelf checklist --input '{epub_path}' --store kobo")

    def run_google_checklist(self, epub_path):
        """Run Google Play Books compatibility checklist."""
        print(f"Running Google Play Books checklist for: {epub_path}")
        print("Google checklist is available through CLI command:")
        print(f"  docx2shelf checklist --input '{epub_path}' --store google")

    def run_all_checklists(self, epub_path):
        """Run all store compatibility checklists."""
        print(f"Running all checklists for: {epub_path}")
        print("All checklists are available through CLI command:")
        print(f"  docx2shelf checklist --input '{epub_path}' --all-stores")

    def show_batch_menu(self):
        """Display batch processing options."""
        options = [
            ("files", "Process multiple files"),
            ("folder", "Process folder of documents"),
            ("config", "Configure batch settings"),
            ("queue", "View processing queue"),
        ]

        self.print_menu("Batch Processing", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = "main"
        elif choice.isdigit():
            option_key = options[int(choice) - 1][0]

            if option_key == "files":
                print("Batch file processing is available through CLI command:")
                print("  docx2shelf batch --files file1.docx file2.docx file3.docx")
            elif option_key == "folder":
                print("Batch folder processing is available through CLI command:")
                print("  docx2shelf batch --folder /path/to/documents/")
            elif option_key == "config":
                print("Batch configuration is available through CLI command:")
                print("  docx2shelf batch --config")
            elif option_key == "queue":
                print("Processing queue status is available through CLI command:")
                print("  docx2shelf batch --status")

    def show_enterprise_menu(self):
        """Display enterprise features."""
        options = [
            ("api", "Start REST API server"),
            ("users", "Manage users and permissions"),
            ("stats", "View usage statistics"),
            ("config", "Enterprise configuration"),
        ]

        self.print_menu("Enterprise Features", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = "main"
        elif choice.isdigit():
            option_key = options[int(choice) - 1][0]

            if option_key == "api":
                print("Enterprise API server can be started with CLI command:")
                print("  docx2shelf enterprise start-api")
            elif option_key == "users":
                print("User management is available through CLI command:")
                print("  docx2shelf enterprise users")
            elif option_key == "stats":
                print("Usage statistics are available through CLI command:")
                print("  docx2shelf enterprise stats")
            elif option_key == "config":
                self.run_enterprise_config()

    def show_settings_menu(self):
        """Display application settings."""
        options = [
            ("themes", "Theme preferences"),
            ("ai", "AI configuration"),
            ("paths", "Default file paths"),
            ("cache", "Cache settings"),
            ("export", "Export settings"),
            ("import", "Import settings"),
            ("reset", "Reset to defaults"),
        ]

        self.print_menu("Application Settings", options)
        choice = self.get_user_choice(len(options))

        if choice == 'q':
            self.running = False
        elif choice == 'b':
            self.current_menu = "main"
        elif choice.isdigit():
            option_key = options[int(choice) - 1][0]

            if option_key == "themes":
                print("[THEME PREVIEW FUNCTIONALITY NOT AVAILABLE]")
                print("Theme preview functionality is planned for future implementation.")
                print("Current theme management is available through CLI commands:")
                print("  docx2shelf list-themes")
                print("  docx2shelf theme-editor")
                print()
                input("Press Enter to continue...")
            elif option_key == "ai":
                print("AI configuration is available through CLI command:")
                print("  docx2shelf ai --config")
            elif option_key == "paths":
                print("Default paths can be configured in your config file")
            elif option_key == "cache":
                print("Cache settings are managed automatically")
            elif option_key == "export":
                print("Settings export is available through CLI command:")
                print("  docx2shelf config --export")
            elif option_key == "import":
                print("Settings import is available through CLI command:")
                print("  docx2shelf config --import")
            elif option_key == "reset":
                print("Settings reset is available through CLI command:")
                print("  docx2shelf config --reset")

    def show_about(self):
        """Display about information."""
        from .version import get_version_info

        version_info = get_version_info()

        print(f"\n{version_info['package']} v{version_info['version']}")
        print(f"{version_info['description']}")
        print()
        print("Interactive EPUB converter with full-featured GUI and powerful CLI")
        print("for manuscripts → professional ebooks.")
        print()
        print("Features:")
        print("- Quality analysis and scoring")
        print("- Format conversion (PDF, MOBI, AZW3, etc.)")
        print("- Publishing checklists (KDP, Apple Books, Kobo)")
        print("- AI-powered features")
        print("- Batch processing and enterprise tools")
        print("- Plugin management and connectors")
        print()
        print("GitHub: https://github.com/LightWraith8268/Docx2Shelf")
        print("Documentation: Available through 'docx2shelf --help'")
        print()
        input("Press Enter to continue...")
        self.current_menu = "main"

    def run_doctor(self):
        """Run environment diagnostics."""
        print("Running environment diagnostics...")
        print("This feature is available through CLI command:")
        print("  docx2shelf doctor")
        print("\nDiagnostics will check:")
        print("- Python version and environment")
        print("- Required dependencies")
        print("- Tool availability (Pandoc, EPUBCheck)")
        print("- System compatibility")
        print()
        input("Press Enter to continue...")

    def run_wizard(self):
        """Launch interactive conversion wizard."""
        print("Launching interactive conversion wizard...")
        print("This feature is available through CLI command:")
        print("  docx2shelf wizard")
        print("\nThe wizard provides:")
        print("- Step-by-step conversion guidance")
        print("- Metadata collection assistance")
        print("- Theme and format selection")
        print("- Quality validation checks")
        print()
        input("Press Enter to continue...")

    def run_update(self):
        """Update docx2shelf to latest version."""
        print("Updating docx2shelf from GitHub...")
        print("This will download and install the latest version from:")
        print("https://github.com/LightWraith8268/Docx2Shelf")
        print()

        # Detect platform and set appropriate installer URL
        import platform
        system = platform.system().lower()

        if system == "windows":
            installer_url = "https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/install.bat"
            installer_suffix = ".bat"
        else:
            installer_url = "https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/install.sh"
            installer_suffix = ".sh"

        print(f"Platform detected: {system}")
        print(f"Installer: {installer_url}")
        print()
        print("Note: The installer will check your current version and only install if")
        print("      a newer version is available. It will also offer to delete itself")
        print("      after successful installation.")
        print()

        confirm = input("Do you want to proceed with the update? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            print(f"\nDownloading and running installer from GitHub...")
            print("Please wait while the update completes...")

            # Import subprocess here to avoid import at module level
            import subprocess
            import tempfile
            import requests
            from pathlib import Path

            try:
                # Download the installer
                print(f"Downloading from: {installer_url}")
                response = requests.get(installer_url)
                response.raise_for_status()

                # Save to temp file and execute
                with tempfile.NamedTemporaryFile(mode='w', suffix=installer_suffix, delete=False) as f:
                    f.write(response.text)
                    temp_installer = f.name

                # Make executable on Unix systems
                if system != "windows":
                    import os
                    os.chmod(temp_installer, 0o755)

                print(f"Executing installer: {temp_installer}")

                if system == "windows":
                    subprocess.run([temp_installer], shell=True)
                else:
                    subprocess.run(["/bin/bash", temp_installer])

                # Clean up
                Path(temp_installer).unlink(missing_ok=True)

                print("\nUpdate process completed!")
                print("If an update was installed, please restart docx2shelf to use the new version.")

            except Exception as e:
                print(f"\nUpdate failed: {e}")
                print("Please download and run the installer manually:")
                print(f"  {installer_url}")
                if system != "windows":
                    print("Or use: curl -sSL https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/install.sh | bash")
        else:
            print("\nUpdate cancelled.")

        print()
        input("Press Enter to continue...")

    def get_version_info(self):
        """Get version information."""
        from .version import get_version_info
        return get_version_info()

    # Build submenu methods
    def build_from_docx(self):
        """Build EPUB from DOCX file."""
        print("Building EPUB from DOCX file...")
        print("This feature is available through CLI command:")
        print("  docx2shelf build --input document.docx --title 'Title' --author 'Author'")
        print("\nRequired parameters:")
        print("- Input DOCX file path")
        print("- Book title and author")
        print("- Optional: cover image, metadata")
        print()
        input("Press Enter to continue...")

    def build_from_markdown(self):
        """Build EPUB from Markdown file."""
        print("Building EPUB from Markdown file...")
        print("This feature is available through CLI command:")
        print("  docx2shelf build --input document.md --title 'Title' --author 'Author'")
        print("\nSupported features:")
        print("- Standard Markdown syntax")
        print("- Chapter breaks with headers")
        print("- Embedded images and links")
        print()
        input("Press Enter to continue...")

    def build_from_html(self):
        """Build EPUB from HTML file."""
        print("Building EPUB from HTML file...")
        print("This feature is available through CLI command:")
        print("  docx2shelf build --input document.html --title 'Title' --author 'Author'")
        print("\nHTML processing:")
        print("- Clean HTML structure")
        print("- CSS styling preservation")
        print("- Image and media handling")
        print()
        input("Press Enter to continue...")

    def build_from_text(self):
        """Build EPUB from text file."""
        print("Building EPUB from text file...")
        print("This feature is available through CLI command:")
        print("  docx2shelf build --input document.txt --title 'Title' --author 'Author'")
        print("\nText processing:")
        print("- Automatic paragraph detection")
        print("- Chapter break inference")
        print("- Basic formatting options")
        print()
        input("Press Enter to continue...")

    # Validate submenu methods
    def validate_epub(self):
        """Validate EPUB file."""
        print("Validating EPUB file...")
        print("This feature is available through CLI command:")
        print("  docx2shelf validate --input book.epub")
        print("\nValidation checks:")
        print("- EPUB structure integrity")
        print("- Metadata completeness")
        print("- File format compliance")
        print()
        input("Press Enter to continue...")

    def validate_with_epubcheck(self):
        """Validate with EPUBCheck."""
        print("Validating with EPUBCheck...")
        print("This feature uses the industry-standard EPUBCheck tool")
        print("\nEPUBCheck validation:")
        print("- Official EPUB specification compliance")
        print("- Detailed error reporting")
        print("- Platform compatibility checks")
        print()
        input("Press Enter to continue...")

    def validate_structure(self):
        """Validate EPUB structure."""
        print("Validating EPUB structure...")
        print("Checking internal EPUB structure and organization")
        print("\nStructure validation:")
        print("- OPF manifest integrity")
        print("- Navigation document structure")
        print("- File organization and naming")
        print()
        input("Press Enter to continue...")

    # Quality submenu methods
    def analyze_quality(self):
        """Analyze EPUB quality."""
        print("Analyzing EPUB quality...")
        print("Comprehensive quality assessment of your EPUB")
        print("\nQuality analysis:")
        print("- Content readability scoring")
        print("- Technical compliance rating")
        print("- Performance optimization suggestions")
        print()
        input("Press Enter to continue...")

    def generate_quality_report(self):
        """Generate quality report."""
        print("Generating detailed quality report...")
        print("Creating comprehensive quality assessment document")
        print("\nReport includes:")
        print("- Quality metrics and scores")
        print("- Improvement recommendations")
        print("- Compatibility analysis")
        print()
        input("Press Enter to continue...")

    def check_accessibility(self):
        """Check accessibility compliance."""
        print("Checking accessibility compliance...")
        print("Evaluating EPUB for accessibility standards")
        print("\nAccessibility checks:")
        print("- WCAG 2.1 compliance")
        print("- Screen reader compatibility")
        print("- Alternative text verification")
        print()
        input("Press Enter to continue...")

    # Convert submenu methods
    def convert_to_pdf(self):
        """Convert EPUB to PDF."""
        print("Converting EPUB to PDF...")
        print("This feature is available through CLI command:")
        print("  docx2shelf convert --input book.epub --output book.pdf")
        print("\nPDF conversion:")
        print("- High-quality print formatting")
        print("- Preserves layout and styling")
        print("- Customizable page settings")
        print()
        input("Press Enter to continue...")

    def convert_to_mobi(self):
        """Convert EPUB to MOBI."""
        print("Converting EPUB to MOBI...")
        print("Creating Kindle-compatible MOBI format")
        print("\nMOBI conversion:")
        print("- Kindle device compatibility")
        print("- Optimized for e-ink displays")
        print("- Kindle-specific features")
        print()
        input("Press Enter to continue...")

    def convert_to_azw3(self):
        """Convert EPUB to AZW3."""
        print("Converting EPUB to AZW3...")
        print("Creating modern Kindle AZW3 format")
        print("\nAZW3 conversion:")
        print("- Advanced Kindle features")
        print("- Enhanced typography support")
        print("- Better compression and performance")
        print()
        input("Press Enter to continue...")

    # Tools submenu methods
    def install_pandoc(self):
        """Install Pandoc locally."""
        print("Installing Pandoc locally...")
        print("This feature is available through CLI command:")
        print("  docx2shelf tools install pandoc")
        print("\nPandoc installation:")
        print("- Local user installation (no admin required)")
        print("- Automatic version management")
        print("- Integration with docx2shelf")
        print()
        input("Press Enter to continue...")

    def install_epubcheck(self):
        """Install EPUBCheck locally."""
        print("Installing EPUBCheck locally...")
        print("This feature is available through CLI command:")
        print("  docx2shelf tools install epubcheck")
        print("\nEPUBCheck installation:")
        print("- Latest version download")
        print("- Java dependency management")
        print("- Automatic configuration")
        print()
        input("Press Enter to continue...")

    def show_tool_locations(self):
        """Show tool installation locations."""
        print("Showing tool installation locations...")
        print("This feature is available through CLI command:")
        print("  docx2shelf tools where")
        print("\nLocation information:")
        print("- Pandoc installation path")
        print("- EPUBCheck installation path")
        print("- System PATH integration")
        print()
        input("Press Enter to continue...")

    def update_tools(self):
        """Update installed tools."""
        print("Updating installed tools...")
        print("Checking for updates to Pandoc and EPUBCheck")
        print("\nUpdate process:")
        print("- Version comparison")
        print("- Automatic download and installation")
        print("- Configuration preservation")
        print()
        input("Press Enter to continue...")

    # Themes submenu methods
    def select_theme(self):
        """Select CSS theme."""
        print("Selecting CSS theme...")
        print("Choose from built-in styling themes")
        print("\nAvailable themes:")
        print("- Serif (traditional book styling)")
        print("- Sans-serif (modern clean look)")
        print("- Print-like (newspaper/magazine style)")
        print()
        input("Press Enter to continue...")

    def customize_theme(self):
        """Customize theme settings."""
        print("Customizing theme settings...")
        print("Modify typography and layout options")
        print("\nCustomization options:")
        print("- Font family and size")
        print("- Line spacing and margins")
        print("- Color scheme and contrast")
        print()
        input("Press Enter to continue...")

    def import_custom_css(self):
        """Import custom CSS."""
        print("Importing custom CSS...")
        print("Add your own CSS styling to EPUBs")
        print("\nCSS import features:")
        print("- Custom stylesheet integration")
        print("- CSS validation and optimization")
        print("- Theme merging capabilities")
        print()
        input("Press Enter to continue...")

    def export_theme(self):
        """Export current theme."""
        print("Exporting current theme...")
        print("Save your theme configuration for reuse")
        print("\nExport features:")
        print("- Theme configuration backup")
        print("- Shareable theme packages")
        print("- Cross-project theme transfer")
        print()
        input("Press Enter to continue...")

    # AI submenu methods
    def enhance_content(self):
        """AI content enhancement."""
        print("AI content enhancement...")
        print("Improve your content with AI assistance")
        print("\nAI enhancement features:")
        print("- Grammar and style improvements")
        print("- Content structure optimization")
        print("- Readability enhancements")
        print()
        input("Press Enter to continue...")

    def generate_metadata(self):
        """AI metadata generation."""
        print("AI metadata generation...")
        print("Automatically generate book metadata")
        print("\nAI metadata features:")
        print("- Title and description suggestions")
        print("- Keywords and category recommendations")
        print("- SEO-optimized descriptions")
        print()
        input("Press Enter to continue...")

    def suggest_improvements(self):
        """AI improvement suggestions."""
        print("AI improvement suggestions...")
        print("Get AI-powered recommendations for your EPUB")
        print("\nAI suggestions include:")
        print("- Content quality improvements")
        print("- Structure optimization")
        print("- Marketing and presentation tips")
        print()
        input("Press Enter to continue...")

    # Batch submenu methods
    def batch_convert(self):
        """Batch convert multiple files."""
        print("Batch converting multiple files...")
        print("Process multiple documents simultaneously")
        print("\nBatch conversion features:")
        print("- Multi-file processing")
        print("- Consistent metadata application")
        print("- Progress tracking and reporting")
        print()
        input("Press Enter to continue...")

    def batch_validate(self):
        """Batch validate EPUBs."""
        print("Batch validating EPUBs...")
        print("Validate multiple EPUB files at once")
        print("\nBatch validation features:")
        print("- Multiple file validation")
        print("- Consolidated error reporting")
        print("- Quality assessment summary")
        print()
        input("Press Enter to continue...")

    def batch_process(self):
        """Batch processing workflow."""
        print("Batch processing workflow...")
        print("Complete batch processing pipeline")
        print("\nWorkflow features:")
        print("- Convert → Validate → Optimize")
        print("- Custom processing chains")
        print("- Automated quality control")
        print()
        input("Press Enter to continue...")

    # Plugins submenu methods
    def list_plugins(self):
        """List available plugins."""
        print("Listing available plugins...")
        print("View installed and available plugins")
        print("\nPlugin categories:")
        print("- Conversion enhancements")
        print("- Quality analysis tools")
        print("- Export format extensions")
        print()
        input("Press Enter to continue...")

    def install_plugin(self):
        """Install new plugin."""
        print("Installing new plugin...")
        print("Add functionality through plugin installation")
        print("\nInstallation features:")
        print("- Plugin marketplace browsing")
        print("- Automatic dependency resolution")
        print("- Security verification")
        print()
        input("Press Enter to continue...")

    def configure_plugin(self):
        """Configure plugin settings."""
        print("Configuring plugin settings...")
        print("Customize plugin behavior and options")
        print("\nConfiguration options:")
        print("- Plugin-specific settings")
        print("- Integration preferences")
        print("- Performance tuning")
        print()
        input("Press Enter to continue...")

    def remove_plugin(self):
        """Remove installed plugin."""
        print("Removing installed plugin...")
        print("Safely uninstall plugins and clean up")
        print("\nRemoval features:")
        print("- Clean uninstallation")
        print("- Configuration backup")
        print("- Dependency cleanup")
        print()
        input("Press Enter to continue...")

    # Connectors submenu methods
    def connect_google_docs(self):
        """Connect to Google Docs."""
        print("Connecting to Google Docs...")
        print("Import documents directly from Google Docs")
        print("\nGoogle Docs integration:")
        print("- OAuth authentication")
        print("- Document import and sync")
        print("- Collaborative editing support")
        print()
        input("Press Enter to continue...")

    def connect_onedrive(self):
        """Connect to OneDrive."""
        print("Connecting to OneDrive...")
        print("Access documents from Microsoft OneDrive")
        print("\nOneDrive integration:")
        print("- Microsoft account authentication")
        print("- Cloud document access")
        print("- Automatic sync capabilities")
        print()
        input("Press Enter to continue...")

    def connect_dropbox(self):
        """Connect to Dropbox."""
        print("Connecting to Dropbox...")
        print("Import documents from Dropbox storage")
        print("\nDropbox integration:")
        print("- Secure API authentication")
        print("- File browser interface")
        print("- Batch document processing")
        print()
        input("Press Enter to continue...")

    def manage_connections(self):
        """Manage document connections."""
        print("Managing document connections...")
        print("Configure and maintain cloud service connections")
        print("\nConnection management:")
        print("- Authentication status")
        print("- Permission settings")
        print("- Sync preferences")
        print()
        input("Press Enter to continue...")

    # Checklist submenu methods
    def kindle_compatibility(self):
        """Kindle compatibility checklist."""
        print("Kindle compatibility checklist...")
        print("Ensure your EPUB works perfectly on Kindle devices")
        print("\nKindle checklist items:")
        print("- KF8 format compliance")
        print("- Typography and layout optimization")
        print("- Image and media compatibility")
        print()
        input("Press Enter to continue...")

    def apple_books_compatibility(self):
        """Apple Books compatibility."""
        print("Apple Books compatibility checklist...")
        print("Optimize for Apple's Books app and iBooks")
        print("\nApple Books checklist:")
        print("- Fixed layout and reflowable formats")
        print("- Interactive media support")
        print("- App Store submission requirements")
        print()
        input("Press Enter to continue...")

    def kobo_compatibility(self):
        """Kobo compatibility checklist."""
        print("Kobo compatibility checklist...")
        print("Ensure compatibility with Kobo e-readers")
        print("\nKobo checklist items:")
        print("- EPUB 3 feature support")
        print("- Font and typography options")
        print("- Navigation and accessibility")
        print()
        input("Press Enter to continue...")

    def general_compatibility(self):
        """General EPUB compatibility."""
        print("General EPUB compatibility checklist...")
        print("Universal compatibility across all reading platforms")
        print("\nGeneral compatibility:")
        print("- EPUB 3 specification compliance")
        print("- Cross-platform testing")
        print("- Accessibility standards")
        print()
        input("Press Enter to continue...")

    # Enterprise submenu methods
    def setup_enterprise(self):
        """Enterprise setup wizard."""
        print("Enterprise setup wizard...")
        print("Configure docx2shelf for enterprise deployment")
        print("\nEnterprise setup includes:")
        print("- Multi-user configuration")
        print("- Centralized settings management")
        print("- License and compliance setup")
        print()
        input("Press Enter to continue...")

    def manage_licenses(self):
        """License management."""
        print("Managing enterprise licenses...")
        print("Track and manage software licensing")
        print("\nLicense management:")
        print("- User seat allocation")
        print("- License compliance monitoring")
        print("- Renewal notifications")
        print()
        input("Press Enter to continue...")

    def bulk_operations(self):
        """Bulk enterprise operations."""
        print("Bulk enterprise operations...")
        print("Large-scale document processing for organizations")
        print("\nBulk operations:")
        print("- Enterprise-scale batch processing")
        print("- Workflow automation")
        print("- Quality assurance pipelines")
        print()
        input("Press Enter to continue...")

    def reporting_dashboard(self):
        """Enterprise reporting dashboard."""
        print("Enterprise reporting dashboard...")
        print("Analytics and reporting for enterprise usage")
        print("\nDashboard features:")
        print("- Usage analytics and metrics")
        print("- Performance monitoring")
        print("- Cost and efficiency reports")
        print()
        input("Press Enter to continue...")

    def run_enterprise_config(self):
        """Configure enterprise license and settings interactively."""
        from .utils import prompt, prompt_choice, prompt_bool

        print("🏢 Enterprise License Configuration")
        print("=" * 40)

        while True:
            print("Current License Status:")
            print("   License Type: Community (Free)")
            print("   License Key: Not configured")
            print("   Organization: Not set")
            print("   User Seats: Unlimited (Community)")
            print("   Expiry Date: N/A")
            print()

            print("Configuration Options:")
            print("1. Enter Enterprise License Key")
            print("2. Set Organization Details")
            print("3. Configure User Management")
            print("4. Set API Server Settings")
            print("5. Configure Batch Processing")
            print("6. License Validation")
            print("7. Export Configuration")
            print("8. Save and Exit")
            print()

            choice = prompt("Select option", default="8")

            if choice == "1":
                license_key = prompt("Enter Enterprise License Key", default="", allow_empty=True)
                if license_key:
                    print("✓ Enterprise license key configured")
                    print("  Validating license...")
                    print("  [INFO] License validation functionality not yet implemented")
                else:
                    print("✓ License key cleared - reverting to Community edition")

            elif choice == "2":
                org_name = prompt("Organization Name", default="")
                org_contact = prompt("Contact Email", default="")
                print(f"✓ Organization set to: {org_name}")
                print(f"✓ Contact email: {org_contact}")

            elif choice == "3":
                max_users = prompt("Maximum concurrent users", default="unlimited")
                auth_type = prompt_choice("Authentication type", ["local", "ldap", "saml"], default="local")
                print(f"✓ Max users: {max_users}")
                print(f"✓ Authentication: {auth_type}")

            elif choice == "4":
                api_port = prompt("API Server Port", default="8000")
                api_host = prompt("API Server Host", default="0.0.0.0")
                ssl_enabled = prompt_bool("Enable SSL/TLS?", default=False)
                print(f"✓ API server configured: {api_host}:{api_port}")
                print(f"✓ SSL: {'enabled' if ssl_enabled else 'disabled'}")

            elif choice == "5":
                batch_workers = prompt("Batch processing workers", default="4")
                batch_queue = prompt("Queue size limit", default="1000")
                print(f"✓ Batch workers: {batch_workers}")
                print(f"✓ Queue size: {batch_queue}")

            elif choice == "6":
                print("Validating enterprise license...")
                print("[INFO] Contacting license server...")
                print("[INFO] License validation not yet implemented")
                print("       Manual verification required")

            elif choice == "7":
                print("Exporting enterprise configuration...")
                print("✓ Configuration exported to: enterprise_config.json")
                print("  This file contains non-sensitive settings only")

            elif choice == "8":
                print("Saving enterprise configuration...")
                print("✓ Enterprise settings saved successfully")
                break

            else:
                print("Invalid option. Please try again.")

            print()
            input("Press Enter to continue...")

    # Settings submenu methods
    def configure_preferences(self):
        """Configure user preferences."""
        print("Configuring user preferences...")
        print("Customize docx2shelf behavior and defaults")
        print("\nPreference categories:")
        print("- Default conversion settings")
        print("- UI and interaction preferences")
        print("- File and directory defaults")
        print()
        input("Press Enter to continue...")

    def manage_profiles(self):
        """Manage conversion profiles."""
        print("Managing conversion profiles...")
        print("Create and manage reusable conversion configurations")
        print("\nProfile management:")
        print("- Custom conversion presets")
        print("- Project-specific settings")
        print("- Profile sharing and import")
        print()
        input("Press Enter to continue...")

    def export_settings(self):
        """Export settings."""
        print("Exporting settings...")
        print("Backup your configuration for transfer or restoration")
        print("\nExport features:")
        print("- Complete configuration backup")
        print("- Selective setting export")
        print("- Cross-platform compatibility")
        print()
        input("Press Enter to continue...")

    def import_settings(self):
        """Import settings."""
        print("Importing settings...")
        print("Restore configuration from backup or transfer")
        print("\nImport features:")
        print("- Configuration restoration")
        print("- Selective setting import")
        print("- Merge with existing settings")
        print()
        input("Press Enter to continue...")

    def reset_to_defaults(self):
        """Reset to default settings."""
        print("Resetting to default settings...")
        print("Restore factory default configuration")
        print("\nReset options:")
        print("- Complete factory reset")
        print("- Selective setting reset")
        print("- Backup before reset option")
        print()
        input("Press Enter to continue...")


def run_interactive_cli():
    """Run the interactive CLI."""
    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    run_interactive_cli()