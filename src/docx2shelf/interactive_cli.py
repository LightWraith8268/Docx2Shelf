"""Interactive CLI menu system for docx2shelf."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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

    def show_main_menu(self):
        """Display the main menu."""
        options = [
            ("build", "Build EPUB from document"),
            ("validate", "Validate existing EPUB file"),
            ("doctor", "Run environment diagnostics"),
            ("tools", "Manage tools (Pandoc, EPUBCheck)"),
            ("wizard", "Interactive conversion wizard"),
            ("themes", "Theme management"),
            ("ai", "AI-powered features"),
            ("batch", "Batch processing"),
            ("plugins", "Plugin management"),
            ("enterprise", "Enterprise features"),
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
                '1': 'build', '2': 'validate', '3': 'doctor', '4': 'tools',
                '5': 'wizard', '6': 'themes', '7': 'ai', '8': 'batch',
                '9': 'plugins', '10': 'enterprise', '11': 'settings', '12': 'about'
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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        from pathlib import Path

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'ai', 'alt-text', image_path, '--interactive']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def run_ai_config(self):
        """Configure AI settings."""
        from .cli import main as cli_main
        import sys

        old_argv = sys.argv
        try:
            sys.argv = ['docx2shelf', 'ai', 'config', '--list']
            cli_main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

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
        import sys

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
        print("Theme preview functionality would open a browser with theme samples.")
        print("This feature is planned for future implementation.")

    def run_theme_editor(self):
        """Run theme editor."""
        from .cli import main as cli_main
        import sys

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

    def run_list_plugins(self):
        """List installed plugins."""
        from .cli import main as cli_main
        import sys

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
        import sys

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
        import sys

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
        import sys

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
        import sys

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
                elif self.current_menu == "enterprise":
                    self.execute_enterprise_command()
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

    def execute_doctor_command(self):
        """Execute doctor command."""
        print("\n[RUNNING ENVIRONMENT DIAGNOSTICS]")
        from .cli import main as cli_main
        import sys

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
        import sys

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
            import sys

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


def run_interactive_cli():
    """Run the interactive CLI."""
    cli = InteractiveCLI()
    cli.run()


if __name__ == "__main__":
    run_interactive_cli()