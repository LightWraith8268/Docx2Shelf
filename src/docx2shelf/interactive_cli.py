"""Enhanced interactive CLI with rich terminal UI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional

from rich.prompt import Prompt

from .terminal_ui import TerminalUI
from .version import get_version_info


class EnhancedInteractiveCLI:
    """Enhanced interactive CLI with beautiful terminal UI and improved UX."""

    def __init__(self):
        """Initialize the enhanced interactive CLI."""
        self.ui = TerminalUI()
        self.running = True
        self.current_menu = "main"
        self.navigation_stack: list[str] = []
        self.version_info = get_version_info()

        # Menu definitions with emojis and help text
        self.menus = self._define_menus()

    def _define_menus(self) -> dict:
        """Define all menu structures."""
        return {
            "main": {
                "title": "Main Menu",
                "options": [
                    ("build", "📖", "Build EPUB from document"),
                    ("validate", "✓", "Validate existing EPUB file"),
                    ("quality", "⭐", "Quality analysis and scoring"),
                    ("convert", "🔄", "Convert EPUB to other formats"),
                    ("doctor", "🩺", "Run environment diagnostics"),
                    ("tools", "🔧", "Manage tools (Pandoc, EPUBCheck)"),
                    ("wizard", "🧙", "Interactive conversion wizard"),
                    ("themes", "🎨", "Theme management"),
                    ("ai", "🤖", "AI-powered features"),
                    ("batch", "📚", "Batch processing"),
                    ("plugins", "🔌", "Plugin management"),
                    ("connectors", "🔗", "Document connectors"),
                    ("checklist", "📋", "Publishing compatibility checklists"),
                    ("enterprise", "🏢", "Enterprise features"),
                    ("update", "⬆️", "Update docx2shelf"),
                    ("settings", "⚙️", "Application settings"),
                    ("about", "ℹ️", "About and version information"),
                ],
                "help": (
                    "Welcome to Docx2Shelf Interactive CLI!\n\n"
                    "Use number keys to select options, [b] to go back, [q] to quit, [h] for help.\n"
                    "Keyboard shortcuts: Ctrl+C to cancel current operation."
                ),
            },
            "build": {
                "title": "Build EPUB",
                "options": [
                    ("quick", "⚡", "Quick build (guided prompts)"),
                    ("advanced", "🔧", "Advanced build (all options)"),
                    ("from_metadata", "📄", "Build from metadata.txt file"),
                    ("preview", "👁️", "Generate preview instead of EPUB"),
                    ("inspect", "🔍", "Inspect mode (see generated files)"),
                ],
                "help": (
                    "Build Options:\n\n"
                    "• Quick Build: Fastest way to create an EPUB with guided prompts\n"
                    "• Advanced Build: Full control over all conversion options\n"
                    "• From Metadata: Use pre-configured metadata.txt file\n"
                    "• Preview: Generate a preview without creating full EPUB\n"
                    "• Inspect: See all generated files before packaging"
                ),
            },
            "validate": {
                "title": "EPUB Validation",
                "options": [
                    ("file", "📄", "Validate specific EPUB file"),
                    ("directory", "📁", "Validate all EPUBs in directory"),
                    ("quick", "⚡", "Quick validation (basic checks)"),
                    ("full", "🔍", "Full validation (EPUBCheck + custom rules)"),
                    ("golden", "🥇", "Golden-file regression tests"),
                ],
                "help": (
                    "Validation Options:\n\n"
                    "• File: Validate a single EPUB file\n"
                    "• Directory: Batch validate multiple files\n"
                    "• Quick: Fast basic validation\n"
                    "• Full: Comprehensive validation with EPUBCheck\n"
                    "• Golden: Compare against reference files"
                ),
            },
            "tools": {
                "title": "Tools Management",
                "options": [
                    ("status", "📊", "Check tool status"),
                    ("install_pandoc", "📥", "Install Pandoc"),
                    ("install_epubcheck", "📥", "Install EPUBCheck"),
                    ("update_all", "⬆️", "Update all tools"),
                    ("locations", "📍", "Show tool locations"),
                    ("doctor", "🩺", "Run tools health check"),
                    ("bundle", "📦", "Create offline installer bundle"),
                ],
                "help": (
                    "Tool Management:\n\n"
                    "• Status: Check which tools are installed and their versions\n"
                    "• Install: Download and install Pandoc or EPUBCheck\n"
                    "• Update: Get the latest versions of installed tools\n"
                    "• Locations: See where tools are installed\n"
                    "• Doctor: Diagnose tool configuration issues\n"
                    "• Bundle: Create offline installer for air-gapped systems"
                ),
            },
            "ai": {
                "title": "AI Features",
                "options": [
                    ("metadata", "📝", "AI-enhanced metadata generation"),
                    ("genre", "🎭", "AI genre detection"),
                    ("alt_text", "🖼️", "AI alt text for images"),
                    ("tags", "🏷️", "Generate keywords and tags"),
                    ("config", "⚙️", "Configure AI settings"),
                    ("status", "📊", "Check AI availability"),
                ],
                "help": (
                    "AI-Powered Features:\n\n"
                    "• Metadata: Auto-generate professional metadata\n"
                    "• Genre: Automatically detect book genre\n"
                    "• Alt Text: Generate accessibility descriptions for images\n"
                    "• Tags: Create SEO-friendly keywords\n"
                    "• Config: Set API keys and AI preferences\n"
                    "• Status: Check if AI features are available"
                ),
            },
            "themes": {
                "title": "Theme Management",
                "options": [
                    ("list", "📋", "List available themes"),
                    ("preview", "👁️", "Preview themes"),
                    ("editor", "✏️", "Theme editor"),
                    ("create", "➕", "Create custom theme"),
                    ("import", "📥", "Import theme"),
                    ("export", "📤", "Export theme"),
                ],
                "help": (
                    "Theme Management:\n\n"
                    "• List: See all available CSS themes\n"
                    "• Preview: View how themes look\n"
                    "• Editor: Customize theme settings\n"
                    "• Create: Build a new theme from scratch\n"
                    "• Import/Export: Share themes between projects"
                ),
            },
            "quality": {
                "title": "Quality Analysis",
                "options": [
                    ("score", "⭐", "Overall quality scoring"),
                    ("accessibility", "♿", "Accessibility audit"),
                    ("content", "📝", "Content validation"),
                    ("metadata", "📋", "Metadata completeness"),
                    ("report", "📊", "Generate full report"),
                ],
                "help": (
                    "Quality Assessment:\n\n"
                    "• Score: Get an overall quality rating\n"
                    "• Accessibility: Check WCAG compliance\n"
                    "• Content: Validate structure and formatting\n"
                    "• Metadata: Ensure complete metadata\n"
                    "• Report: Comprehensive quality report"
                ),
            },
            "convert": {
                "title": "Format Conversion",
                "options": [
                    ("to_mobi", "📱", "Convert EPUB to MOBI"),
                    ("to_pdf", "📄", "Convert EPUB to PDF"),
                    ("to_html", "🌐", "Convert EPUB to HTML"),
                    ("from_md", "📝", "Convert Markdown to EPUB"),
                ],
                "help": (
                    "Format Conversion:\n\n"
                    "• MOBI: Convert for Kindle devices\n"
                    "• PDF: Create PDF version\n"
                    "• HTML: Export as web page\n"
                    "• From Markdown: Build EPUB from Markdown files"
                ),
            },
            "batch": {
                "title": "Batch Processing",
                "options": [
                    ("convert", "📚", "Batch convert multiple files"),
                    ("validate", "✓", "Batch validate EPUBs"),
                    ("update_metadata", "📝", "Batch update metadata"),
                    ("status", "📊", "Check batch job status"),
                ],
                "help": (
                    "Batch Processing:\n\n"
                    "• Convert: Process multiple documents at once\n"
                    "• Validate: Validate multiple EPUB files\n"
                    "• Update Metadata: Apply metadata changes to multiple files\n"
                    "• Status: Monitor running batch jobs"
                ),
            },
            "plugins": {
                "title": "Plugin Management",
                "options": [
                    ("list", "📋", "List installed plugins"),
                    ("available", "🔍", "Browse available plugins"),
                    ("install", "📥", "Install plugin"),
                    ("remove", "🗑️", "Remove plugin"),
                    ("configure", "⚙️", "Configure plugins"),
                ],
                "help": (
                    "Plugin System:\n\n"
                    "• List: See installed plugins\n"
                    "• Available: Browse plugin directory\n"
                    "• Install: Add new plugins\n"
                    "• Remove: Uninstall plugins\n"
                    "• Configure: Manage plugin settings"
                ),
            },
            "connectors": {
                "title": "Document Connectors",
                "options": [
                    ("google_docs", "📄", "Google Docs integration"),
                    ("onedrive", "☁️", "OneDrive connector"),
                    ("dropbox", "📦", "Dropbox integration"),
                    ("ftp", "🌐", "FTP/SFTP connection"),
                ],
                "help": (
                    "Cloud Connectors:\n\n"
                    "• Google Docs: Import from Google Drive\n"
                    "• OneDrive: Access Microsoft OneDrive files\n"
                    "• Dropbox: Sync with Dropbox\n"
                    "• FTP: Download from FTP servers"
                ),
            },
            "checklist": {
                "title": "Publishing Checklists",
                "options": [
                    ("kindle", "📱", "Amazon Kindle checklist"),
                    ("apple", "🍎", "Apple Books checklist"),
                    ("kobo", "📖", "Kobo checklist"),
                    ("generic", "📋", "Generic EPUB3 checklist"),
                    ("all", "🎯", "Run all checklists"),
                ],
                "help": (
                    "Publishing Compatibility:\n\n"
                    "• Kindle: Check KDP requirements\n"
                    "• Apple: Verify Apple Books compliance\n"
                    "• Kobo: Ensure Kobo compatibility\n"
                    "• Generic: Standard EPUB3 validation\n"
                    "• All: Comprehensive check for all platforms"
                ),
            },
            "enterprise": {
                "title": "Enterprise Features",
                "options": [
                    ("batch_api", "🌐", "Batch API server"),
                    ("workflow", "🔄", "Workflow automation"),
                    ("reporting", "📊", "Analytics and reporting"),
                    ("team", "👥", "Team collaboration"),
                ],
                "help": (
                    "Enterprise Tools:\n\n"
                    "• Batch API: REST API for automation\n"
                    "• Workflow: Custom workflow definitions\n"
                    "• Reporting: Track conversion metrics\n"
                    "• Team: Multi-user collaboration features"
                ),
            },
            "settings": {
                "title": "Application Settings",
                "options": [
                    ("defaults", "⚙️", "Default build options"),
                    ("paths", "📁", "File paths and locations"),
                    ("appearance", "🎨", "UI preferences"),
                    ("advanced", "🔧", "Advanced settings"),
                    ("reset", "🔄", "Reset to defaults"),
                ],
                "help": (
                    "Settings:\n\n"
                    "• Defaults: Set default conversion options\n"
                    "• Paths: Configure file locations\n"
                    "• Appearance: Customize UI appearance\n"
                    "• Advanced: Expert configuration options\n"
                    "• Reset: Restore factory settings"
                ),
            },
        }

    def run(self):
        """Main interactive loop with enhanced UI."""
        try:
            # Show welcome screen
            self._show_welcome()

            while self.running:
                self.ui.clear()
                self._show_header()
                self._show_breadcrumb()

                # Get menu status if available
                status = self._get_menu_status()

                # Route to appropriate menu
                if self.current_menu in self.menus:
                    self._show_menu(self.current_menu, status)
                elif self.current_menu == "doctor":
                    self._execute_doctor()
                elif self.current_menu == "wizard":
                    self._execute_wizard()
                elif self.current_menu == "update":
                    self._execute_update()
                elif self.current_menu == "about":
                    self._show_about()
                else:
                    self.ui.print_error(f"Unknown menu: {self.current_menu}")
                    self.ui.pause()
                    self.current_menu = "main"

        except KeyboardInterrupt:
            self.ui.console.print("\n[dim]Interrupted by user[/dim]")
        finally:
            self._show_goodbye()

    def _show_welcome(self):
        """Show welcome screen on first launch."""
        self.ui.clear()
        self.ui.print_header(
            self.version_info["package"],
            self.version_info["version"],
            self.version_info["description"],
        )
        self.ui.print_info("Welcome to the Interactive CLI!")
        self.ui.console.print()
        self.ui.print_list(
            [
                "Use number keys to select menu options",
                "Press [h] at any menu for help",
                "Press [b] to go back, [q] to quit",
                "Use Ctrl+C to cancel long operations",
            ],
            style="dim",
            bullet="→",
        )
        self.ui.console.print()
        self.ui.pause("Press Enter to continue")

    def _show_header(self):
        """Show application header."""
        self.ui.print_header(
            self.version_info["package"],
            self.version_info["version"],
        )

    def _show_breadcrumb(self):
        """Show breadcrumb navigation."""
        if not self.navigation_stack and self.current_menu == "main":
            return

        path = ["Home"]
        if self.navigation_stack:
            for menu_id in self.navigation_stack:
                if menu_id in self.menus:
                    path.append(self.menus[menu_id]["title"])
        if self.current_menu != "main" and self.current_menu in self.menus:
            path.append(self.menus[self.current_menu]["title"])

        if len(path) > 1:
            self.ui.print_breadcrumb(path)

    def _get_menu_status(self) -> Optional[dict]:
        """Get status information for current menu."""
        if self.current_menu == "tools":
            return self._get_tools_status()
        elif self.current_menu == "ai":
            return self._get_ai_status()
        return None

    def _get_tools_status(self) -> dict:
        """Get tools installation status."""
        try:
            from .tools import pandoc_path, epubcheck_cmd

            status = {}
            try:
                pandoc = pandoc_path()
                status["Pandoc"] = "✓ Installed" if pandoc else "✗ Not installed"
            except:
                status["Pandoc"] = "✗ Not installed"

            try:
                epubcheck = epubcheck_cmd()
                status["EPUBCheck"] = "✓ Installed" if epubcheck else "✗ Not installed"
            except:
                status["EPUBCheck"] = "✗ Not installed"

            return status
        except:
            return {}

    def _get_ai_status(self) -> dict:
        """Get AI features status."""
        try:
            from .ai_integration import get_ai_manager

            ai_mgr = get_ai_manager()
            status = {"AI Status": "✓ Available" if ai_mgr.is_available() else "✗ Not configured"}
            return status
        except:
            return {"AI Status": "✗ Not available"}

    def _show_menu(self, menu_id: str, status: Optional[dict] = None):
        """Show a menu and handle user selection."""
        menu = self.menus[menu_id]

        # Print menu
        self.ui.print_menu(
            menu["title"],
            menu["options"],
            show_back=bool(self.navigation_stack),
            status_info=status,
        )

        # Get valid options
        valid_options = [str(i) for i in range(1, len(menu["options"]) + 1)]
        valid_options.extend(["q", "h"])
        if self.navigation_stack:
            valid_options.append("b")

        # Get user choice
        choice = self.ui.get_input("Select option", valid_options)

        # Handle choice
        if choice == "q":
            if self.ui.confirm("Are you sure you want to quit?"):
                self.running = False
        elif choice == "h":
            self.ui.print_help(menu.get("help", "No help available"))
            self.ui.pause()
        elif choice == "b" and self.navigation_stack:
            self.current_menu = self.navigation_stack.pop()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(menu["options"]):
                action_id, _, _ = menu["options"][idx]
                self._handle_menu_action(menu_id, action_id)

    def _handle_menu_action(self, menu_id: str, action_id: str):
        """Handle a menu action selection."""
        # Check if action is a submenu
        if action_id in self.menus:
            self.navigation_stack.append(self.current_menu)
            self.current_menu = action_id
        else:
            # Execute command
            self._execute_command(menu_id, action_id)

    def _execute_command(self, menu_id: str, action_id: str):
        """Execute a command from a menu."""
        try:
            # Map commands to their handlers
            handler_map = {
                # Build commands
                ("build", "quick"): self._build_quick,
                ("build", "advanced"): self._build_advanced,
                ("build", "from_metadata"): self._build_from_metadata,
                ("build", "preview"): self._build_preview,
                ("build", "inspect"): self._build_inspect,
                # Validate commands
                ("validate", "file"): self._validate_file,
                ("validate", "directory"): self._validate_directory,
                ("validate", "quick"): self._validate_quick,
                ("validate", "full"): self._validate_full,
                ("validate", "golden"): self._validate_golden,
                # Tools commands
                ("tools", "status"): self._tools_status,
                ("tools", "install_pandoc"): self._tools_install_pandoc,
                ("tools", "install_epubcheck"): self._tools_install_epubcheck,
                ("tools", "update_all"): self._tools_update_all,
                ("tools", "locations"): self._tools_locations,
                ("tools", "doctor"): self._tools_doctor,
                ("tools", "bundle"): self._tools_bundle,
                # AI commands
                ("ai", "metadata"): self._ai_metadata,
                ("ai", "genre"): self._ai_genre,
                ("ai", "alt_text"): self._ai_alt_text,
                ("ai", "tags"): self._ai_tags,
                ("ai", "config"): self._ai_config,
                ("ai", "status"): self._ai_status,
                # Theme commands
                ("themes", "list"): self._themes_list,
                ("themes", "preview"): self._themes_preview,
                ("themes", "editor"): self._themes_editor,
                ("themes", "create"): self._themes_create,
                ("themes", "import"): self._themes_import,
                ("themes", "export"): self._themes_export,
                # Quality commands
                ("quality", "score"): self._quality_score,
                ("quality", "accessibility"): self._quality_accessibility,
                ("quality", "content"): self._quality_content,
                ("quality", "metadata"): self._quality_metadata,
                ("quality", "report"): self._quality_report,
                # Convert commands
                ("convert", "to_mobi"): self._convert_to_mobi,
                ("convert", "to_pdf"): self._convert_to_pdf,
                ("convert", "to_html"): self._convert_to_html,
                ("convert", "from_md"): self._convert_from_md,
                # Batch commands
                ("batch", "convert"): self._batch_convert,
                ("batch", "validate"): self._batch_validate,
                ("batch", "update_metadata"): self._batch_update_metadata,
                ("batch", "status"): self._batch_status,
                # Plugin commands
                ("plugins", "list"): self._plugins_list,
                ("plugins", "available"): self._plugins_available,
                ("plugins", "install"): self._plugins_install,
                ("plugins", "remove"): self._plugins_remove,
                ("plugins", "configure"): self._plugins_configure,
                # Connector commands
                ("connectors", "google_docs"): self._connectors_google_docs,
                ("connectors", "onedrive"): self._connectors_onedrive,
                ("connectors", "dropbox"): self._connectors_dropbox,
                ("connectors", "ftp"): self._connectors_ftp,
                # Checklist commands
                ("checklist", "kindle"): self._checklist_kindle,
                ("checklist", "apple"): self._checklist_apple,
                ("checklist", "kobo"): self._checklist_kobo,
                ("checklist", "generic"): self._checklist_generic,
                ("checklist", "all"): self._checklist_all,
                # Enterprise commands
                ("enterprise", "batch_api"): self._enterprise_batch_api,
                ("enterprise", "workflow"): self._enterprise_workflow,
                ("enterprise", "reporting"): self._enterprise_reporting,
                ("enterprise", "team"): self._enterprise_team,
                # Settings commands
                ("settings", "defaults"): self._settings_defaults,
                ("settings", "paths"): self._settings_paths,
                ("settings", "appearance"): self._settings_appearance,
                ("settings", "advanced"): self._settings_advanced,
                ("settings", "reset"): self._settings_reset,
            }

            key = (menu_id, action_id)
            if key in handler_map:
                handler_map[key]()
            else:
                self.ui.print_warning(f"Command not implemented: {menu_id}.{action_id}")
                self.ui.pause()

        except Exception as e:
            self.ui.print_error(f"Error executing command: {e}")
            import traceback

            self.ui.console.print(f"[dim]{traceback.format_exc()}[/dim]")
            self.ui.pause()

    # ============================================================================
    # Command Implementations
    # ============================================================================

    # Build Commands
    def _build_quick(self):
        """Quick build with guided prompts."""
        from .cli_handlers import run_build
        import argparse

        self.ui.print_section("Quick Build", "Building EPUB with guided prompts...")
        args = argparse.Namespace(
            command="build",
            input=None,
            title=None,
            author=None,
            output=None,
            lang="en",
            theme="serif",
            cover=None,
        )
        try:
            run_build(args)
            self.ui.print_success("Build completed!")
        except Exception as e:
            self.ui.print_error(f"Build failed: {e}")
        self.ui.pause()

    def _build_advanced(self):
        """Advanced build with all options."""
        self.ui.print_info("Advanced build: Use command line for full control")
        self.ui.console.print("[dim]Run: docx2shelf build --help[/dim]")
        self.ui.pause()

    def _build_from_metadata(self):
        """Build from metadata.txt file."""
        self.ui.print_info("Build from metadata.txt")
        self.ui.console.print("[dim]Place metadata.txt in same directory as your document[/dim]")
        self.ui.pause()

    def _build_preview(self):
        """Generate preview."""
        self.ui.print_info("Preview generation not yet implemented in interactive mode")
        self.ui.pause()

    def _build_inspect(self):
        """Inspect mode."""
        self.ui.print_info("Inspect mode: Use --inspect flag from command line")
        self.ui.pause()

    # Validate Commands
    def _validate_file(self):
        """Validate specific EPUB file."""
        from .cli_handlers import run_validate
        import argparse

        file_path = Prompt.ask("[bold yellow]Enter EPUB file path[/bold yellow]")
        args = argparse.Namespace(
            command="validate", epub=file_path, quick=False, golden_file=None
        )
        try:
            run_validate(args)
            self.ui.print_success("Validation completed!")
        except Exception as e:
            self.ui.print_error(f"Validation failed: {e}")
        self.ui.pause()

    def _validate_directory(self):
        """Validate all EPUBs in directory."""
        self.ui.print_info("Directory validation: Use batch validate command")
        self.ui.pause()

    def _validate_quick(self):
        """Quick validation."""
        self.ui.print_info("Quick validation mode")
        self.ui.pause()

    def _validate_full(self):
        """Full validation."""
        self.ui.print_info("Full validation with EPUBCheck")
        self.ui.pause()

    def _validate_golden(self):
        """Golden file regression tests."""
        self.ui.print_info("Golden file testing not yet implemented")
        self.ui.pause()

    # Tools Commands
    def _tools_status(self):
        """Check tool status."""
        from .tools import pandoc_path, epubcheck_cmd

        self.ui.print_section("Tool Status", "Checking installed tools...")

        try:
            pandoc = pandoc_path()
            if pandoc:
                self.ui.print_status("Pandoc", str(pandoc), True)
            else:
                self.ui.print_status("Pandoc", "Not installed", False)
        except Exception as e:
            self.ui.print_status("Pandoc", f"Error: {e}", False)

        try:
            epubcheck = epubcheck_cmd()
            if epubcheck:
                self.ui.print_status("EPUBCheck", "Installed", True)
            else:
                self.ui.print_status("EPUBCheck", "Not installed", False)
        except Exception as e:
            self.ui.print_status("EPUBCheck", f"Error: {e}", False)

        self.ui.pause()

    def _tools_install_pandoc(self):
        """Install Pandoc."""
        from .tools import install_pandoc

        if self.ui.confirm("Install Pandoc?"):
            with self.ui.create_progress("Installing Pandoc") as progress:
                task = progress.add_task("Downloading...", total=100)
                try:
                    install_pandoc()
                    progress.update(task, completed=100)
                    self.ui.print_success("Pandoc installed successfully!")
                except Exception as e:
                    self.ui.print_error(f"Installation failed: {e}")
        self.ui.pause()

    def _tools_install_epubcheck(self):
        """Install EPUBCheck."""
        from .tools import install_epubcheck

        if self.ui.confirm("Install EPUBCheck?"):
            with self.ui.create_progress("Installing EPUBCheck") as progress:
                task = progress.add_task("Downloading...", total=100)
                try:
                    install_epubcheck()
                    progress.update(task, completed=100)
                    self.ui.print_success("EPUBCheck installed successfully!")
                except Exception as e:
                    self.ui.print_error(f"Installation failed: {e}")
        self.ui.pause()

    def _tools_update_all(self):
        """Update all tools."""
        self.ui.print_info("Updating all tools...")
        self._tools_install_pandoc()
        self._tools_install_epubcheck()

    def _tools_locations(self):
        """Show tool locations."""
        from .tools import tools_dir, pandoc_path

        self.ui.print_section("Tool Locations", "Showing installation paths...")
        self.ui.print_key_value_pairs(
            {
                "Tools Directory": str(tools_dir()),
                "Pandoc": str(pandoc_path()) if pandoc_path() else "Not installed",
            }
        )
        self.ui.pause()

    def _tools_doctor(self):
        """Run tools health check."""
        self._execute_doctor()

    def _tools_bundle(self):
        """Create offline installer bundle."""
        self.ui.print_info("Offline bundle creation not yet implemented")
        self.ui.pause()

    # AI Commands
    def _ai_metadata(self):
        """AI metadata generation."""
        self.ui.print_info("AI metadata generation requires API key configuration")
        self.ui.pause()

    def _ai_genre(self):
        """AI genre detection."""
        self.ui.print_info("AI genre detection requires API key configuration")
        self.ui.pause()

    def _ai_alt_text(self):
        """AI alt text generation."""
        self.ui.print_info("AI alt text generation requires API key configuration")
        self.ui.pause()

    def _ai_tags(self):
        """AI tag generation."""
        self.ui.print_info("AI tag generation requires API key configuration")
        self.ui.pause()

    def _ai_config(self):
        """Configure AI settings."""
        self.ui.print_section("AI Configuration", "Configure AI API settings...")
        self.ui.console.print("[dim]Set API keys in environment or config file[/dim]")
        self.ui.pause()

    def _ai_status(self):
        """Check AI status."""
        status = self._get_ai_status()
        self.ui.print_section("AI Status", "Checking AI availability...")
        self.ui.print_key_value_pairs(status)
        self.ui.pause()

    # Theme Commands
    def _themes_list(self):
        """List themes."""
        from .cli_handlers import run_list_themes
        import argparse

        args = argparse.Namespace(command="list-themes")
        try:
            run_list_themes(args)
        except Exception as e:
            self.ui.print_error(f"Error listing themes: {e}")
        self.ui.pause()

    def _themes_preview(self):
        """Preview themes."""
        from .cli_handlers import run_preview_themes
        import argparse

        args = argparse.Namespace(command="preview-themes")
        try:
            run_preview_themes(args)
        except Exception as e:
            self.ui.print_error(f"Error previewing themes: {e}")
        self.ui.pause()

    def _themes_editor(self):
        """Theme editor."""
        from .cli_handlers import run_theme_editor
        import argparse

        args = argparse.Namespace(command="theme-editor")
        try:
            run_theme_editor(args)
        except Exception as e:
            self.ui.print_error(f"Error launching theme editor: {e}")
        self.ui.pause()

    def _themes_create(self):
        """Create theme."""
        self.ui.print_info("Theme creation: Use theme editor")
        self.ui.pause()

    def _themes_import(self):
        """Import theme."""
        self.ui.print_info("Theme import not yet implemented")
        self.ui.pause()

    def _themes_export(self):
        """Export theme."""
        self.ui.print_info("Theme export not yet implemented")
        self.ui.pause()

    # Quality Commands
    def _quality_score(self):
        """Quality scoring."""
        from .cli_handlers import run_quality_assessment
        import argparse

        file_path = Prompt.ask("[bold yellow]Enter EPUB file path[/bold yellow]")
        args = argparse.Namespace(command="quality", epub=file_path)
        try:
            run_quality_assessment(args)
        except Exception as e:
            self.ui.print_error(f"Quality assessment failed: {e}")
        self.ui.pause()

    def _quality_accessibility(self):
        """Accessibility audit."""
        self.ui.print_info("Accessibility audit")
        self.ui.pause()

    def _quality_content(self):
        """Content validation."""
        self.ui.print_info("Content validation")
        self.ui.pause()

    def _quality_metadata(self):
        """Metadata completeness."""
        self.ui.print_info("Metadata validation")
        self.ui.pause()

    def _quality_report(self):
        """Generate full report."""
        self.ui.print_info("Full quality report generation")
        self.ui.pause()

    # Convert Commands
    def _convert_to_mobi(self):
        """Convert to MOBI."""
        self.ui.print_info("MOBI conversion requires Kindle tools")
        self.ui.pause()

    def _convert_to_pdf(self):
        """Convert to PDF."""
        self.ui.print_info("PDF conversion")
        self.ui.pause()

    def _convert_to_html(self):
        """Convert to HTML."""
        self.ui.print_info("HTML export")
        self.ui.pause()

    def _convert_from_md(self):
        """Convert from Markdown."""
        self.ui.print_info("Markdown conversion: Use build command with .md file")
        self.ui.pause()

    # Batch Commands
    def _batch_convert(self):
        """Batch convert."""
        from .cli_handlers import run_batch_mode
        import argparse

        args = argparse.Namespace(command="batch")
        try:
            run_batch_mode(args)
        except Exception as e:
            self.ui.print_error(f"Batch conversion failed: {e}")
        self.ui.pause()

    def _batch_validate(self):
        """Batch validate."""
        self.ui.print_info("Batch validation")
        self.ui.pause()

    def _batch_update_metadata(self):
        """Batch update metadata."""
        self.ui.print_info("Batch metadata update")
        self.ui.pause()

    def _batch_status(self):
        """Batch job status."""
        self.ui.print_info("Batch job status monitoring")
        self.ui.pause()

    # Plugin Commands
    def _plugins_list(self):
        """List plugins."""
        self.ui.print_info("Plugin system not yet implemented")
        self.ui.pause()

    def _plugins_available(self):
        """Browse available plugins."""
        self.ui.print_info("Plugin directory not yet implemented")
        self.ui.pause()

    def _plugins_install(self):
        """Install plugin."""
        self.ui.print_info("Plugin installation not yet implemented")
        self.ui.pause()

    def _plugins_remove(self):
        """Remove plugin."""
        self.ui.print_info("Plugin removal not yet implemented")
        self.ui.pause()

    def _plugins_configure(self):
        """Configure plugins."""
        self.ui.print_info("Plugin configuration not yet implemented")
        self.ui.pause()

    # Connector Commands
    def _connectors_google_docs(self):
        """Google Docs connector."""
        self.ui.print_info("Google Docs integration not yet implemented")
        self.ui.pause()

    def _connectors_onedrive(self):
        """OneDrive connector."""
        self.ui.print_info("OneDrive integration not yet implemented")
        self.ui.pause()

    def _connectors_dropbox(self):
        """Dropbox connector."""
        self.ui.print_info("Dropbox integration not yet implemented")
        self.ui.pause()

    def _connectors_ftp(self):
        """FTP connector."""
        self.ui.print_info("FTP integration not yet implemented")
        self.ui.pause()

    # Checklist Commands
    def _checklist_kindle(self):
        """Kindle checklist."""
        from .cli_handlers import run_checklist
        import argparse

        args = argparse.Namespace(command="checklist", epub=None, platform="kindle")
        try:
            run_checklist(args)
        except Exception as e:
            self.ui.print_error(f"Checklist failed: {e}")
        self.ui.pause()

    def _checklist_apple(self):
        """Apple Books checklist."""
        from .cli_handlers import run_checklist
        import argparse

        args = argparse.Namespace(command="checklist", epub=None, platform="apple")
        try:
            run_checklist(args)
        except Exception as e:
            self.ui.print_error(f"Checklist failed: {e}")
        self.ui.pause()

    def _checklist_kobo(self):
        """Kobo checklist."""
        from .cli_handlers import run_checklist
        import argparse

        args = argparse.Namespace(command="checklist", epub=None, platform="kobo")
        try:
            run_checklist(args)
        except Exception as e:
            self.ui.print_error(f"Checklist failed: {e}")
        self.ui.pause()

    def _checklist_generic(self):
        """Generic checklist."""
        from .cli_handlers import run_checklist
        import argparse

        args = argparse.Namespace(command="checklist", epub=None, platform="epub3")
        try:
            run_checklist(args)
        except Exception as e:
            self.ui.print_error(f"Checklist failed: {e}")
        self.ui.pause()

    def _checklist_all(self):
        """Run all checklists."""
        from .cli_handlers import run_checklist
        import argparse

        args = argparse.Namespace(command="checklist", epub=None, platform="all")
        try:
            run_checklist(args)
        except Exception as e:
            self.ui.print_error(f"Checklist failed: {e}")
        self.ui.pause()

    # Enterprise Commands
    def _enterprise_batch_api(self):
        """Batch API server."""
        self.ui.print_info("Enterprise batch API")
        self.ui.pause()

    def _enterprise_workflow(self):
        """Workflow automation."""
        self.ui.print_info("Workflow automation")
        self.ui.pause()

    def _enterprise_reporting(self):
        """Analytics and reporting."""
        self.ui.print_info("Analytics and reporting")
        self.ui.pause()

    def _enterprise_team(self):
        """Team collaboration."""
        self.ui.print_info("Team collaboration features")
        self.ui.pause()

    # Settings Commands
    def _settings_defaults(self):
        """Default settings."""
        self.ui.print_info("Default build options configuration")
        self.ui.pause()

    def _settings_paths(self):
        """Path settings."""
        self.ui.print_info("File paths and locations")
        self.ui.pause()

    def _settings_appearance(self):
        """Appearance settings."""
        self.ui.print_info("UI preferences")
        self.ui.pause()

    def _settings_advanced(self):
        """Advanced settings."""
        self.ui.print_info("Advanced configuration options")
        self.ui.pause()

    def _settings_reset(self):
        """Reset settings."""
        if self.ui.confirm("Reset all settings to defaults?"):
            self.ui.print_success("Settings reset (not yet implemented)")
        self.ui.pause()

    # Special Commands
    def _execute_doctor(self):
        """Run environment diagnostics."""
        from .cli_handlers import run_doctor
        import argparse

        self.ui.print_section("Environment Diagnostics", "Running system health check...")
        args = argparse.Namespace(command="doctor")
        try:
            run_doctor(args)
        except Exception as e:
            self.ui.print_error(f"Diagnostic failed: {e}")
        self.ui.pause()
        if self.navigation_stack:
            self.current_menu = self.navigation_stack.pop()
        else:
            self.current_menu = "main"

    def _execute_wizard(self):
        """Run interactive wizard."""
        from .cli_handlers import run_wizard
        import argparse

        self.ui.print_section("Conversion Wizard", "Starting interactive wizard...")
        args = argparse.Namespace(command="wizard")
        try:
            run_wizard(args)
        except Exception as e:
            self.ui.print_error(f"Wizard failed: {e}")
        self.ui.pause()
        if self.navigation_stack:
            self.current_menu = self.navigation_stack.pop()
        else:
            self.current_menu = "main"

    def _execute_update(self):
        """Check for updates."""
        from .cli_handlers import run_update
        import argparse

        self.ui.print_section("Update Check", "Checking for updates...")
        args = argparse.Namespace(command="update")
        try:
            run_update(args)
        except Exception as e:
            self.ui.print_error(f"Update check failed: {e}")
        self.ui.pause()
        if self.navigation_stack:
            self.current_menu = self.navigation_stack.pop()
        else:
            self.current_menu = "main"

    def _show_about(self):
        """Show about information."""
        self.ui.console.print()
        self.ui.print_section(
            f"{self.version_info['package']} v{self.version_info['version']}",
            self.version_info["description"],
        )

        self.ui.console.print()
        self.ui.print_list(
            [
                "License: MIT",
                "Repository: https://github.com/LightWraith8268/Docx2Shelf",
                "Documentation: https://github.com/LightWraith8268/Docx2Shelf/wiki",
            ],
            style="cyan",
            bullet="→",
        )

        self.ui.console.print()
        self.ui.pause()

        if self.navigation_stack:
            self.current_menu = self.navigation_stack.pop()
        else:
            self.current_menu = "main"

    def _show_goodbye(self):
        """Show goodbye message."""
        self.ui.console.print()
        self.ui.print_success("Thank you for using Docx2Shelf!")
        self.ui.console.print("[dim]Happy publishing! 📚[/dim]")
        self.ui.console.print()


def run_interactive_cli():
    """Run the enhanced interactive CLI."""
    cli = EnhancedInteractiveCLI()
    cli.run()


if __name__ == "__main__":
    run_interactive_cli()
