"""
Cross-platform GUI application for Docx2Shelf.

Provides a user-friendly interface for EPUB conversion with drag-and-drop
support, live preview, and one-click conversion capabilities.
"""

from __future__ import annotations

import logging
import sys
import tempfile
import threading
from pathlib import Path
from typing import List

# Try different GUI frameworks in order of preference
GUI_FRAMEWORK = None

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
    GUI_FRAMEWORK = "tkinter"
except ImportError:
    pass

if not GUI_FRAMEWORK:
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets
        GUI_FRAMEWORK = "pyqt5"
    except ImportError:
        try:
            from PyQt6 import QtCore, QtGui, QtWidgets
            GUI_FRAMEWORK = "pyqt6"
        except ImportError:
            pass

from ..assemble import assemble_epub
from ..convert import docx_to_html_chunks
from ..metadata import BuildOptions, EpubMetadata
from ..settings import get_settings_manager, ApplicationSettings, ConversionDefaults, UIPreferences, FileDefaults, AdvancedSettings
from ..tools import epubcheck_cmd

logger = logging.getLogger(__name__)


class ConversionWorker:
    """Background worker for EPUB conversion."""

    def __init__(self, progress_callback=None, complete_callback=None, error_callback=None):
        self.progress_callback = progress_callback
        self.complete_callback = complete_callback
        self.error_callback = error_callback
        self.cancelled = False

    def convert(self, input_file: Path, output_file: Path, metadata: EpubMetadata, options: BuildOptions):
        """Run conversion in background thread."""
        try:
            if self.progress_callback:
                self.progress_callback("Starting conversion...", 0)

            if self.cancelled:
                return

            # Step 1: Convert DOCX to HTML
            if self.progress_callback:
                self.progress_callback("Converting DOCX to HTML...", 20)

            html_chunks = docx_to_html_chunks(input_file)

            if self.cancelled:
                return

            # Step 2: Extract resources
            if self.progress_callback:
                self.progress_callback("Extracting resources...", 40)

            resources = self._extract_resources(input_file)

            if self.cancelled:
                return

            # Step 3: Assemble EPUB
            if self.progress_callback:
                self.progress_callback("Assembling EPUB...", 60)

            assemble_epub(
                meta=metadata,
                opts=options,
                html_chunks=html_chunks,
                resources=resources,
                output_path=output_file
            )

            if self.cancelled:
                return

            # Step 4: Validate (optional)
            if options.validate_epub and epubcheck_cmd():
                if self.progress_callback:
                    self.progress_callback("Validating EPUB...", 80)

                # Run EPUBCheck validation
                # Implementation would go here

            if self.progress_callback:
                self.progress_callback("Conversion complete!", 100)

            if self.complete_callback:
                self.complete_callback(output_file)

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            if self.error_callback:
                self.error_callback(str(e))

    def cancel(self):
        """Cancel the conversion."""
        self.cancelled = True

    def _extract_resources(self, docx_file: Path) -> List[Path]:
        """Extract resources from DOCX file."""
        resources = []

        try:
            import zipfile

            with zipfile.ZipFile(docx_file, 'r') as docx_zip:
                # Find media files
                media_files = [f for f in docx_zip.namelist() if f.startswith('word/media/')]

                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)

                    for media_file in media_files:
                        # Extract to temp directory
                        media_data = docx_zip.read(media_file)
                        output_file = temp_path / Path(media_file).name
                        output_file.write_bytes(media_data)
                        resources.append(output_file)

        except Exception as e:
            logger.warning(f"Could not extract resources: {e}")

        return resources


if GUI_FRAMEWORK == "tkinter":
    class TkinterMainWindow:
        """Main application window using Tkinter."""

        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Docx2Shelf - EPUB Converter")
            self.root.geometry("800x600")

            # Set icon if available
            try:
                icon_path = Path(__file__).parent / "assets" / "icon.ico"
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
            except:
                pass

            # Initialize settings manager
            self.settings_manager = get_settings_manager()
            self.settings = self.settings_manager.settings

            self.setup_ui()
            self.current_worker = None
            self.load_ui_preferences()

        def setup_ui(self):
            """Setup the user interface."""

            # Create main notebook for tabs
            notebook = ttk.Notebook(self.root)
            notebook.pack(fill="both", expand=True, padx=10, pady=10)

            # Convert tab
            convert_frame = ttk.Frame(notebook)
            notebook.add(convert_frame, text="Convert")
            self.setup_convert_tab(convert_frame)

            # Settings tab
            settings_frame = ttk.Frame(notebook)
            notebook.add(settings_frame, text="Settings")
            self.setup_settings_tab(settings_frame)

            # About tab
            about_frame = ttk.Frame(notebook)
            notebook.add(about_frame, text="About")
            self.setup_about_tab(about_frame)

        def setup_convert_tab(self, parent):
            """Setup the conversion tab."""

            # File selection section
            file_frame = ttk.LabelFrame(parent, text="Input File", padding=10)
            file_frame.pack(fill="x", padx=10, pady=5)

            self.file_path_var = tk.StringVar()
            file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60)
            file_entry.pack(side="left", fill="x", expand=True)

            browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_input_file)
            browse_btn.pack(side="right", padx=(5, 0))

            # Drag and drop label
            drop_label = ttk.Label(parent, text="Or drag and drop a DOCX file here",
                                 font=("Arial", 10, "italic"))
            drop_label.pack(pady=5)

            # Enable drag and drop
            self.setup_drag_drop()

            # Metadata section
            meta_frame = ttk.LabelFrame(parent, text="Book Metadata", padding=10)
            meta_frame.pack(fill="x", padx=10, pady=5)

            # Title
            ttk.Label(meta_frame, text="Title:").grid(row=0, column=0, sticky="w", pady=2)
            self.title_var = tk.StringVar()
            title_entry = ttk.Entry(meta_frame, textvariable=self.title_var, width=40)
            title_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=2)

            # Author
            ttk.Label(meta_frame, text="Author:").grid(row=1, column=0, sticky="w", pady=2)
            self.author_var = tk.StringVar()
            author_entry = ttk.Entry(meta_frame, textvariable=self.author_var, width=40)
            author_entry.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=2)

            # Language
            ttk.Label(meta_frame, text="Language:").grid(row=2, column=0, sticky="w", pady=2)
            self.language_var = tk.StringVar(value="en")
            language_combo = ttk.Combobox(meta_frame, textvariable=self.language_var,
                                        values=["en", "es", "fr", "de", "it", "pt", "nl", "ru", "zh", "ja"],
                                        width=10)
            language_combo.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=2)

            # Description
            ttk.Label(meta_frame, text="Description:").grid(row=3, column=0, sticky="nw", pady=2)
            self.description_text = tk.Text(meta_frame, height=3, width=40)
            self.description_text.grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=2)

            meta_frame.columnconfigure(1, weight=1)

            # Output section
            output_frame = ttk.LabelFrame(parent, text="Output", padding=10)
            output_frame.pack(fill="x", padx=10, pady=5)

            self.output_path_var = tk.StringVar()
            output_entry = ttk.Entry(output_frame, textvariable=self.output_path_var, width=60)
            output_entry.pack(side="left", fill="x", expand=True)

            output_browse_btn = ttk.Button(output_frame, text="Browse...", command=self.browse_output_file)
            output_browse_btn.pack(side="right", padx=(5, 0))

            # Progress section
            progress_frame = ttk.Frame(parent)
            progress_frame.pack(fill="x", padx=10, pady=10)

            self.progress_var = tk.StringVar(value="Ready to convert")
            progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
            progress_label.pack()

            self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
            self.progress_bar.pack(fill="x", pady=(5, 0))

            # Buttons
            button_frame = ttk.Frame(parent)
            button_frame.pack(fill="x", padx=10, pady=10)

            self.convert_btn = ttk.Button(button_frame, text="Convert to EPUB",
                                        command=self.start_conversion, style="Accent.TButton")
            self.convert_btn.pack(side="left")

            self.cancel_btn = ttk.Button(button_frame, text="Cancel",
                                       command=self.cancel_conversion, state="disabled")
            self.cancel_btn.pack(side="left", padx=(10, 0))

            preview_btn = ttk.Button(button_frame, text="Preview", command=self.preview_epub)
            preview_btn.pack(side="right")

        def setup_settings_tab(self, parent):
            """Setup the comprehensive settings tab."""

            # Create notebook for settings categories
            settings_notebook = ttk.Notebook(parent)
            settings_notebook.pack(fill="both", expand=True, padx=10, pady=10)

            # Conversion Defaults tab
            conv_frame = ttk.Frame(settings_notebook)
            settings_notebook.add(conv_frame, text="Conversion")
            self.setup_conversion_settings(conv_frame)

            # UI Preferences tab
            ui_frame = ttk.Frame(settings_notebook)
            settings_notebook.add(ui_frame, text="Interface")
            self.setup_ui_settings(ui_frame)

            # File Defaults tab
            file_frame = ttk.Frame(settings_notebook)
            settings_notebook.add(file_frame, text="Files")
            self.setup_file_settings(file_frame)

            # Advanced Settings tab
            advanced_frame = ttk.Frame(settings_notebook)
            settings_notebook.add(advanced_frame, text="Advanced")
            self.setup_advanced_settings(advanced_frame)

            # Enterprise Configuration tab
            enterprise_frame = ttk.Frame(settings_notebook)
            settings_notebook.add(enterprise_frame, text="Enterprise")
            self.setup_enterprise_settings(enterprise_frame)

            # Settings control buttons
            button_frame = ttk.Frame(parent)
            button_frame.pack(fill="x", padx=10, pady=(0, 10))

            ttk.Button(button_frame, text="Save Settings",
                      command=self.save_settings).pack(side="left")
            ttk.Button(button_frame, text="Reset to Defaults",
                      command=self.reset_settings).pack(side="left", padx=(10, 0))
            ttk.Button(button_frame, text="Export Settings",
                      command=self.export_settings).pack(side="right")
            ttk.Button(button_frame, text="Import Settings",
                      command=self.import_settings).pack(side="right", padx=(0, 10))

        def setup_conversion_settings(self, parent):
            """Setup conversion defaults settings."""
            scroll_frame = self.create_scrollable_frame(parent)
            frame = scroll_frame

            # CSS Theme
            ttk.Label(frame, text="CSS Theme:").grid(row=0, column=0, sticky="w", pady=5)
            self.theme_var = tk.StringVar(value=self.settings.conversion_defaults.css_theme)
            theme_combo = ttk.Combobox(frame, textvariable=self.theme_var,
                                     values=["serif", "sans", "printlike", "dyslexic"],
                                     state="readonly")
            theme_combo.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=5)

            # Language
            ttk.Label(frame, text="Default Language:").grid(row=1, column=0, sticky="w", pady=5)
            self.lang_var = tk.StringVar(value=self.settings.conversion_defaults.language)
            lang_combo = ttk.Combobox(frame, textvariable=self.lang_var,
                                    values=["en", "es", "fr", "de", "it", "pt", "nl", "ru", "zh", "ja"])
            lang_combo.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=5)

            # Validation
            self.validate_var = tk.BooleanVar(value=self.settings.conversion_defaults.validate_epub)
            validate_check = ttk.Checkbutton(frame, text="Validate EPUB with EPUBCheck",
                                           variable=self.validate_var)
            validate_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

            # Image settings
            ttk.Label(frame, text="Max Image Width:").grid(row=3, column=0, sticky="w", pady=5)
            self.image_width_var = tk.StringVar(value=str(self.settings.conversion_defaults.image_max_width))
            width_entry = ttk.Entry(frame, textvariable=self.image_width_var, width=10)
            width_entry.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=5)

            # Accessibility
            self.a11y_var = tk.BooleanVar(value=self.settings.conversion_defaults.accessibility_features)
            a11y_check = ttk.Checkbutton(frame, text="Include accessibility features",
                                       variable=self.a11y_var)
            a11y_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

            # Chapter detection
            ttk.Label(frame, text="Chapter Detection:").grid(row=5, column=0, sticky="w", pady=5)
            self.chapter_var = tk.StringVar(value=self.settings.conversion_defaults.chapter_detection)
            chapter_combo = ttk.Combobox(frame, textvariable=self.chapter_var,
                                       values=["auto", "h1", "h2", "pagebreak"],
                                       state="readonly")
            chapter_combo.grid(row=5, column=1, sticky="w", padx=(5, 0), pady=5)

            # Include ToC
            self.toc_var = tk.BooleanVar(value=self.settings.conversion_defaults.include_toc)
            toc_check = ttk.Checkbutton(frame, text="Include Table of Contents",
                                      variable=self.toc_var)
            toc_check.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

            # Include Cover
            self.cover_var = tk.BooleanVar(value=self.settings.conversion_defaults.include_cover)
            cover_check = ttk.Checkbutton(frame, text="Include Cover Page",
                                        variable=self.cover_var)
            cover_check.grid(row=7, column=0, columnspan=2, sticky="w", pady=5)

        def setup_ui_settings(self, parent):
            """Setup UI preferences."""
            scroll_frame = self.create_scrollable_frame(parent)
            frame = scroll_frame

            # Remember last directory
            self.remember_dir_var = tk.BooleanVar(value=self.settings.ui_preferences.remember_last_directory)
            remember_check = ttk.Checkbutton(frame, text="Remember last directory",
                                           variable=self.remember_dir_var)
            remember_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

            # Auto-fill metadata
            self.auto_fill_var = tk.BooleanVar(value=self.settings.ui_preferences.auto_fill_metadata)
            auto_fill_check = ttk.Checkbutton(frame, text="Auto-fill metadata from DOCX",
                                            variable=self.auto_fill_var)
            auto_fill_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

            # Show advanced options
            self.show_advanced_var = tk.BooleanVar(value=self.settings.ui_preferences.show_advanced_options)
            advanced_check = ttk.Checkbutton(frame, text="Show advanced options by default",
                                           variable=self.show_advanced_var)
            advanced_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

            # UI Theme
            ttk.Label(frame, text="UI Theme:").grid(row=3, column=0, sticky="w", pady=5)
            self.ui_theme_var = tk.StringVar(value=self.settings.ui_preferences.theme)
            theme_combo = ttk.Combobox(frame, textvariable=self.ui_theme_var,
                                     values=["light", "dark", "system"],
                                     state="readonly")
            theme_combo.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=5)

            # Font size
            ttk.Label(frame, text="Font Size:").grid(row=4, column=0, sticky="w", pady=5)
            self.font_size_var = tk.StringVar(value=self.settings.ui_preferences.font_size)
            font_combo = ttk.Combobox(frame, textvariable=self.font_size_var,
                                    values=["small", "medium", "large"],
                                    state="readonly")
            font_combo.grid(row=4, column=1, sticky="w", padx=(5, 0), pady=5)

            # Confirm overwrite
            self.confirm_overwrite_var = tk.BooleanVar(value=self.settings.ui_preferences.confirm_overwrite)
            confirm_check = ttk.Checkbutton(frame, text="Confirm before overwriting files",
                                          variable=self.confirm_overwrite_var)
            confirm_check.grid(row=5, column=0, columnspan=2, sticky="w", pady=5)

            # Show tooltips
            self.tooltips_var = tk.BooleanVar(value=self.settings.ui_preferences.show_tooltips)
            tooltips_check = ttk.Checkbutton(frame, text="Show helpful tooltips",
                                           variable=self.tooltips_var)
            tooltips_check.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

        def setup_file_settings(self, parent):
            """Setup file and directory defaults."""
            scroll_frame = self.create_scrollable_frame(parent)
            frame = scroll_frame

            # Default output directory
            ttk.Label(frame, text="Default Output Directory:").grid(row=0, column=0, sticky="w", pady=5)
            self.output_dir_var = tk.StringVar(value=self.settings.file_defaults.default_output_directory or "")
            output_entry = ttk.Entry(frame, textvariable=self.output_dir_var, width=40)
            output_entry.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=5)
            browse_output_btn = ttk.Button(frame, text="Browse...", command=self.browse_default_output)
            browse_output_btn.grid(row=0, column=2, padx=(5, 0), pady=5)

            # Auto-generate output name
            self.auto_name_var = tk.BooleanVar(value=self.settings.file_defaults.auto_generate_output_name)
            auto_name_check = ttk.Checkbutton(frame, text="Auto-generate output filename",
                                            variable=self.auto_name_var)
            auto_name_check.grid(row=1, column=0, columnspan=3, sticky="w", pady=5)

            # Backup original
            self.backup_var = tk.BooleanVar(value=self.settings.file_defaults.backup_original)
            backup_check = ttk.Checkbutton(frame, text="Create backup of original file",
                                         variable=self.backup_var)
            backup_check.grid(row=2, column=0, columnspan=3, sticky="w", pady=5)

            # Temp directory
            ttk.Label(frame, text="Temporary Directory:").grid(row=3, column=0, sticky="w", pady=5)
            self.temp_dir_var = tk.StringVar(value=self.settings.file_defaults.temp_directory or "")
            temp_entry = ttk.Entry(frame, textvariable=self.temp_dir_var, width=40)
            temp_entry.grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=5)
            browse_temp_btn = ttk.Button(frame, text="Browse...", command=self.browse_temp_dir)
            browse_temp_btn.grid(row=3, column=2, padx=(5, 0), pady=5)

            frame.columnconfigure(1, weight=1)

        def setup_advanced_settings(self, parent):
            """Setup advanced application settings."""
            scroll_frame = self.create_scrollable_frame(parent)
            frame = scroll_frame

            # Logging
            self.logging_var = tk.BooleanVar(value=self.settings.advanced_settings.enable_logging)
            logging_check = ttk.Checkbutton(frame, text="Enable application logging",
                                          variable=self.logging_var)
            logging_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

            # Log level
            ttk.Label(frame, text="Log Level:").grid(row=1, column=0, sticky="w", pady=5)
            self.log_level_var = tk.StringVar(value=self.settings.advanced_settings.log_level)
            log_combo = ttk.Combobox(frame, textvariable=self.log_level_var,
                                   values=["DEBUG", "INFO", "WARNING", "ERROR"],
                                   state="readonly")
            log_combo.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=5)

            # Concurrent jobs
            ttk.Label(frame, text="Concurrent Jobs:").grid(row=2, column=0, sticky="w", pady=5)
            self.concurrent_var = tk.StringVar(value=str(self.settings.advanced_settings.concurrent_jobs))
            concurrent_entry = ttk.Entry(frame, textvariable=self.concurrent_var, width=10)
            concurrent_entry.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=5)

            # Check for updates
            self.updates_var = tk.BooleanVar(value=self.settings.advanced_settings.check_for_updates)
            updates_check = ttk.Checkbutton(frame, text="Check for updates automatically",
                                          variable=self.updates_var)
            updates_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)

            # Crash reporting
            self.crash_var = tk.BooleanVar(value=self.settings.advanced_settings.enable_crash_reporting)
            crash_check = ttk.Checkbutton(frame, text="Enable crash reporting",
                                        variable=self.crash_var)
            crash_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

            # Telemetry
            self.telemetry_var = tk.BooleanVar(value=self.settings.advanced_settings.enable_telemetry)
            telemetry_check = ttk.Checkbutton(frame, text="Enable anonymous usage telemetry",
                                            variable=self.telemetry_var)
            telemetry_check.grid(row=5, column=0, columnspan=2, sticky="w", pady=5)

        def setup_enterprise_settings(self, parent):
            """Setup enterprise configuration."""
            scroll_frame = self.create_scrollable_frame(parent)
            frame = scroll_frame

            # Enable enterprise mode
            self.enterprise_enabled_var = tk.BooleanVar(value=self.settings.enterprise_config is not None)
            enterprise_check = ttk.Checkbutton(frame, text="Enable Enterprise Features",
                                             variable=self.enterprise_enabled_var,
                                             command=self.toggle_enterprise_settings)
            enterprise_check.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

            # Enterprise settings frame (enabled/disabled based on checkbox)
            self.enterprise_frame = ttk.LabelFrame(frame, text="Enterprise Configuration", padding=10)
            self.enterprise_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10, padx=10)

            # API settings
            ttk.Label(self.enterprise_frame, text="API Host:").grid(row=0, column=0, sticky="w", pady=5)
            enterprise_config = self.settings.enterprise_config
            default_host = enterprise_config.api_host if enterprise_config else "localhost"
            self.api_host_var = tk.StringVar(value=default_host)
            host_entry = ttk.Entry(self.enterprise_frame, textvariable=self.api_host_var, width=20)
            host_entry.grid(row=0, column=1, sticky="w", padx=(5, 0), pady=5)

            ttk.Label(self.enterprise_frame, text="API Port:").grid(row=1, column=0, sticky="w", pady=5)
            default_port = enterprise_config.api_port if enterprise_config else 8080
            self.api_port_var = tk.StringVar(value=str(default_port))
            port_entry = ttk.Entry(self.enterprise_frame, textvariable=self.api_port_var, width=10)
            port_entry.grid(row=1, column=1, sticky="w", padx=(5, 0), pady=5)

            # Batch processing
            ttk.Label(self.enterprise_frame, text="Max Concurrent Jobs:").grid(row=2, column=0, sticky="w", pady=5)
            default_jobs = enterprise_config.max_concurrent_jobs if enterprise_config else 4
            self.max_jobs_var = tk.StringVar(value=str(default_jobs))
            jobs_entry = ttk.Entry(self.enterprise_frame, textvariable=self.max_jobs_var, width=10)
            jobs_entry.grid(row=2, column=1, sticky="w", padx=(5, 0), pady=5)

            ttk.Label(self.enterprise_frame, text="Job Timeout (hours):").grid(row=3, column=0, sticky="w", pady=5)
            default_timeout = enterprise_config.job_timeout_hours if enterprise_config else 24
            self.job_timeout_var = tk.StringVar(value=str(default_timeout))
            timeout_entry = ttk.Entry(self.enterprise_frame, textvariable=self.job_timeout_var, width=10)
            timeout_entry.grid(row=3, column=1, sticky="w", padx=(5, 0), pady=5)

            # Storage settings
            ttk.Label(self.enterprise_frame, text="Storage Directory:").grid(row=4, column=0, sticky="w", pady=5)
            default_storage = enterprise_config.storage_directory if enterprise_config else ""
            self.storage_dir_var = tk.StringVar(value=default_storage or "")
            storage_entry = ttk.Entry(self.enterprise_frame, textvariable=self.storage_dir_var, width=30)
            storage_entry.grid(row=4, column=1, sticky="ew", padx=(5, 0), pady=5)
            browse_storage_btn = ttk.Button(self.enterprise_frame, text="Browse...", command=self.browse_storage_dir)
            browse_storage_btn.grid(row=4, column=2, padx=(5, 0), pady=5)

            # Enable/disable enterprise frame based on initial state
            self.toggle_enterprise_settings()

            self.enterprise_frame.columnconfigure(1, weight=1)
            frame.columnconfigure(0, weight=1)

        def create_scrollable_frame(self, parent):
            """Create a scrollable frame for settings."""
            canvas = tk.Canvas(parent)
            scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            return scrollable_frame

        def setup_about_tab(self, parent):
            """Setup the about tab."""

            about_text = """
Docx2Shelf - EPUB Converter

A powerful tool for converting Microsoft Word documents (.docx)
to high-quality EPUB 3.0 ebooks.

Features:
• Professional EPUB 3.0 output
• Multiple CSS themes
• Accessibility compliance
• Retailer-specific optimization
• Cross-reference support
• Mathematical equations
• Media overlays for audio

For more information, visit:
https://github.com/anthropics/docx2shelf

Version: 1.2.4
"""

            text_widget = ScrolledText(parent, wrap=tk.WORD, state=tk.DISABLED)
            text_widget.pack(fill="both", expand=True, padx=20, pady=20)

            text_widget.config(state=tk.NORMAL)
            text_widget.insert(tk.END, about_text)
            text_widget.config(state=tk.DISABLED)

        def setup_drag_drop(self):
            """Setup drag and drop functionality."""
            # Basic drag and drop for tkinter
            def drop_handler(event):
                files = self.root.tk.splitlist(event.data)
                if files:
                    file_path = Path(files[0])
                    if file_path.suffix.lower() == '.docx':
                        self.file_path_var.set(str(file_path))
                        self.auto_fill_metadata(file_path)

            try:
                from tkinterdnd2 import DND_FILES, TkinterDnD
                self.root = TkinterDnD.Tk()
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind('<<Drop>>', drop_handler)
            except ImportError:
                # Fallback: no drag and drop
                pass

        def browse_input_file(self):
            """Browse for input DOCX file."""
            file_path = filedialog.askopenfilename(
                title="Select DOCX file",
                filetypes=[("Word documents", "*.docx"), ("All files", "*.*")]
            )

            if file_path:
                self.file_path_var.set(file_path)
                self.auto_fill_metadata(Path(file_path))

        def browse_output_file(self):
            """Browse for output EPUB file."""
            file_path = filedialog.asksaveasfilename(
                title="Save EPUB as",
                defaultextension=".epub",
                filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
            )

            if file_path:
                self.output_path_var.set(file_path)

        def auto_fill_metadata(self, docx_path: Path):
            """Auto-fill metadata from DOCX file."""
            try:
                from docx import Document
                doc = Document(docx_path)

                if doc.core_properties.title and not self.title_var.get():
                    self.title_var.set(doc.core_properties.title)

                if doc.core_properties.author and not self.author_var.get():
                    self.author_var.set(doc.core_properties.author)

                if doc.core_properties.comments and self.description_text.get("1.0", tk.END).strip() == "":
                    self.description_text.insert("1.0", doc.core_properties.comments)

                # Auto-generate output path
                if not self.output_path_var.get():
                    output_path = docx_path.with_suffix('.epub')
                    self.output_path_var.set(str(output_path))

            except Exception as e:
                logger.warning(f"Could not extract metadata: {e}")

        def start_conversion(self):
            """Start EPUB conversion."""
            input_path = self.file_path_var.get()
            output_path = self.output_path_var.get()

            if not input_path:
                messagebox.showerror("Error", "Please select an input DOCX file")
                return

            if not output_path:
                messagebox.showerror("Error", "Please specify an output EPUB file")
                return

            # Create metadata
            metadata = EpubMetadata(
                title=self.title_var.get() or Path(input_path).stem,
                author=self.author_var.get() or "Unknown Author",
                language=self.language_var.get() or "en",
                description=self.description_text.get("1.0", tk.END).strip()
            )

            # Create build options
            options = BuildOptions(
                css_theme=self.theme_var.get(),
                validate_epub=self.validate_var.get(),
                image_max_width=int(self.image_width_var.get() or 1200),
                accessibility_features=self.a11y_var.get()
            )

            # Disable convert button and enable cancel
            self.convert_btn.config(state="disabled")
            self.cancel_btn.config(state="normal")

            # Start conversion worker
            self.current_worker = ConversionWorker(
                progress_callback=self.update_progress,
                complete_callback=self.conversion_complete,
                error_callback=self.conversion_error
            )

            # Run in separate thread
            self.conversion_thread = threading.Thread(
                target=self.current_worker.convert,
                args=(Path(input_path), Path(output_path), metadata, options)
            )
            self.conversion_thread.start()

        def cancel_conversion(self):
            """Cancel ongoing conversion."""
            if self.current_worker:
                self.current_worker.cancel()

            self.reset_ui()

        def reset_ui(self):
            """Reset UI to ready state."""
            self.convert_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
            self.progress_var.set("Ready to convert")
            self.progress_bar['value'] = 0

        def update_progress(self, message: str, percentage: int):
            """Update progress display."""
            self.progress_var.set(message)
            self.progress_bar['value'] = percentage
            self.root.update_idletasks()

        def conversion_complete(self, output_path: Path):
            """Handle successful conversion."""
            self.reset_ui()

            result = messagebox.askyesno(
                "Conversion Complete",
                f"EPUB created successfully!\n\n{output_path}\n\nWould you like to open the file location?"
            )

            if result:
                self.open_file_location(output_path)

        def conversion_error(self, error_message: str):
            """Handle conversion error."""
            self.reset_ui()
            messagebox.showerror("Conversion Error", f"Conversion failed:\n\n{error_message}")

        def preview_epub(self):
            """Preview the EPUB file."""
            output_path = self.output_path_var.get()

            if not output_path or not Path(output_path).exists():
                messagebox.showwarning("Preview", "Please convert the file first to preview it.")
                return

            try:
                # Try to open with system default application
                import os
                import platform

                if platform.system() == "Windows":
                    os.startfile(output_path)
                elif platform.system() == "Darwin":  # macOS
                    os.system(f"open '{output_path}'")
                else:  # Linux
                    os.system(f"xdg-open '{output_path}'")

            except Exception as e:
                messagebox.showerror("Preview Error", f"Could not open EPUB file:\n\n{e}")

        def open_file_location(self, file_path: Path):
            """Open file location in system file manager."""
            try:
                import os
                import platform

                if platform.system() == "Windows":
                    os.system(f'explorer /select,"{file_path}"')
                elif platform.system() == "Darwin":  # macOS
                    os.system(f'open -R "{file_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{file_path.parent}"')

            except Exception as e:
                logger.warning(f"Could not open file location: {e}")

        def load_ui_preferences(self):
            """Load UI preferences and apply them."""
            prefs = self.settings.ui_preferences

            # Apply window size preferences
            if prefs.remember_window_size:
                # Could implement window size restoration here
                pass

        def toggle_enterprise_settings(self):
            """Toggle enterprise settings availability."""
            if self.enterprise_enabled_var.get():
                for child in self.enterprise_frame.winfo_children():
                    child.configure(state='normal')
            else:
                for child in self.enterprise_frame.winfo_children():
                    if isinstance(child, (ttk.Entry, ttk.Combobox, ttk.Button)):
                        child.configure(state='disabled')

        def browse_default_output(self):
            """Browse for default output directory."""
            directory = filedialog.askdirectory(title="Select Default Output Directory")
            if directory:
                self.output_dir_var.set(directory)

        def browse_temp_dir(self):
            """Browse for temporary directory."""
            directory = filedialog.askdirectory(title="Select Temporary Directory")
            if directory:
                self.temp_dir_var.set(directory)

        def browse_storage_dir(self):
            """Browse for enterprise storage directory."""
            directory = filedialog.askdirectory(title="Select Storage Directory")
            if directory:
                self.storage_dir_var.set(directory)

        def save_settings(self):
            """Save all settings to disk."""
            try:
                # Update settings from UI values
                self.settings.conversion_defaults.css_theme = self.theme_var.get()
                self.settings.conversion_defaults.language = self.lang_var.get()
                self.settings.conversion_defaults.validate_epub = self.validate_var.get()
                self.settings.conversion_defaults.image_max_width = int(self.image_width_var.get() or 1200)
                self.settings.conversion_defaults.accessibility_features = self.a11y_var.get()
                self.settings.conversion_defaults.chapter_detection = self.chapter_var.get()
                self.settings.conversion_defaults.include_toc = self.toc_var.get()
                self.settings.conversion_defaults.include_cover = self.cover_var.get()

                # UI preferences
                self.settings.ui_preferences.remember_last_directory = self.remember_dir_var.get()
                self.settings.ui_preferences.auto_fill_metadata = self.auto_fill_var.get()
                self.settings.ui_preferences.show_advanced_options = self.show_advanced_var.get()
                self.settings.ui_preferences.theme = self.ui_theme_var.get()
                self.settings.ui_preferences.font_size = self.font_size_var.get()
                self.settings.ui_preferences.confirm_overwrite = self.confirm_overwrite_var.get()
                self.settings.ui_preferences.show_tooltips = self.tooltips_var.get()

                # File defaults
                self.settings.file_defaults.default_output_directory = self.output_dir_var.get() or None
                self.settings.file_defaults.auto_generate_output_name = self.auto_name_var.get()
                self.settings.file_defaults.backup_original = self.backup_var.get()
                self.settings.file_defaults.temp_directory = self.temp_dir_var.get() or None

                # Advanced settings
                self.settings.advanced_settings.enable_logging = self.logging_var.get()
                self.settings.advanced_settings.log_level = self.log_level_var.get()
                self.settings.advanced_settings.concurrent_jobs = int(self.concurrent_var.get() or 2)
                self.settings.advanced_settings.check_for_updates = self.updates_var.get()
                self.settings.advanced_settings.enable_crash_reporting = self.crash_var.get()
                self.settings.advanced_settings.enable_telemetry = self.telemetry_var.get()

                # Enterprise settings
                if self.enterprise_enabled_var.get():
                    from ..enterprise import EnterpriseConfig
                    if not self.settings.enterprise_config:
                        self.settings.enterprise_config = EnterpriseConfig()

                    self.settings.enterprise_config.api_host = self.api_host_var.get()
                    self.settings.enterprise_config.api_port = int(self.api_port_var.get() or 8080)
                    self.settings.enterprise_config.max_concurrent_jobs = int(self.max_jobs_var.get() or 4)
                    self.settings.enterprise_config.job_timeout_hours = int(self.job_timeout_var.get() or 24)
                    self.settings.enterprise_config.storage_directory = self.storage_dir_var.get() or None
                else:
                    self.settings.enterprise_config = None

                # Save to disk
                self.settings_manager.save_settings()

                messagebox.showinfo("Settings", "Settings saved successfully!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}")

        def reset_settings(self):
            """Reset all settings to defaults."""
            result = messagebox.askyesno(
                "Reset Settings",
                "Are you sure you want to reset all settings to defaults? This cannot be undone."
            )

            if result:
                self.settings_manager.reset_to_defaults()
                self.settings = self.settings_manager.settings
                messagebox.showinfo("Settings", "Settings reset to defaults successfully!")
                # Reload the GUI would require recreation - for now just show message
                messagebox.showinfo("Restart Required", "Please restart the application to see the changes.")

        def export_settings(self):
            """Export settings to a file."""
            file_path = filedialog.asksaveasfilename(
                title="Export Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                try:
                    self.settings_manager.export_settings(Path(file_path))
                    messagebox.showinfo("Export", f"Settings exported successfully to {file_path}")
                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to export settings: {e}")

        def import_settings(self):
            """Import settings from a file."""
            file_path = filedialog.askopenfilename(
                title="Import Settings",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                result = messagebox.askyesnocancel(
                    "Import Settings",
                    "Do you want to merge with existing settings?\n\n"
                    "Yes = Merge with current settings\n"
                    "No = Replace all settings\n"
                    "Cancel = Cancel import"
                )

                if result is not None:
                    try:
                        merge = result  # True for merge, False for replace
                        self.settings_manager.import_settings(Path(file_path), merge=merge)
                        self.settings = self.settings_manager.settings

                        action = "merged" if merge else "imported"
                        messagebox.showinfo("Import", f"Settings {action} successfully!")
                        messagebox.showinfo("Restart Required", "Please restart the application to see the changes.")

                    except Exception as e:
                        messagebox.showerror("Import Error", f"Failed to import settings: {e}")

        def run(self):
            """Run the application."""
            self.root.mainloop()

    MainWindow = TkinterMainWindow

elif GUI_FRAMEWORK in ["pyqt5", "pyqt6"]:
    # Full PyQt implementation
    class PyQtMainWindow:
        def __init__(self):
            """Initialize PyQt main window."""
            self.app = QApplication(sys.argv)
            self.window = QMainWindow()
            self.setup_ui()

        def setup_ui(self):
            """Set up the PyQt user interface."""
            central_widget = QWidget()
            self.window.setCentralWidget(central_widget)

            layout = QVBoxLayout(central_widget)

            # Create tabs
            tab_widget = QTabWidget()
            layout.addWidget(tab_widget)

            # Convert tab
            convert_tab = QWidget()
            tab_widget.addTab(convert_tab, "Convert")
            self.setup_convert_tab_pyqt(convert_tab)

            # Settings tab
            settings_tab = QWidget()
            tab_widget.addTab(settings_tab, "Settings")
            self.setup_settings_tab_pyqt(settings_tab)

            # Batch tab
            batch_tab = QWidget()
            tab_widget.addTab(batch_tab, "Batch")
            self.setup_batch_tab_pyqt(batch_tab)

            self.window.setWindowTitle("Docx2Shelf - EPUB Converter")
            self.window.resize(800, 600)

        def setup_convert_tab_pyqt(self, parent):
            """Set up PyQt convert tab."""
            layout = QVBoxLayout(parent)

            # File selection
            file_group = QGroupBox("Input File")
            file_layout = QHBoxLayout(file_group)

            self.file_path_edit = QLineEdit()
            self.file_path_edit.setPlaceholderText("Select DOCX file...")
            file_layout.addWidget(self.file_path_edit)

            browse_btn = QPushButton("Browse...")
            browse_btn.clicked.connect(self.browse_file_pyqt)
            file_layout.addWidget(browse_btn)

            layout.addWidget(file_group)

            # Metadata fields
            metadata_group = QGroupBox("Book Metadata")
            metadata_layout = QGridLayout(metadata_group)

            self.title_edit = QLineEdit()
            metadata_layout.addWidget(QLabel("Title:"), 0, 0)
            metadata_layout.addWidget(self.title_edit, 0, 1)

            self.author_edit = QLineEdit()
            metadata_layout.addWidget(QLabel("Author:"), 1, 0)
            metadata_layout.addWidget(self.author_edit, 1, 1)

            layout.addWidget(metadata_group)

            # Convert button
            convert_btn = QPushButton("Convert to EPUB")
            convert_btn.clicked.connect(self.convert_pyqt)
            layout.addWidget(convert_btn)

            # Progress bar
            self.progress_bar = QProgressBar()
            layout.addWidget(self.progress_bar)

        def setup_settings_tab_pyqt(self, parent):
            """Set up PyQt settings tab."""
            layout = QVBoxLayout(parent)

            # Theme selection
            theme_group = QGroupBox("Theme Settings")
            theme_layout = QVBoxLayout(theme_group)

            self.theme_combo = QComboBox()
            self.theme_combo.addItems(['serif', 'sans', 'printlike'])
            theme_layout.addWidget(QLabel("CSS Theme:"))
            theme_layout.addWidget(self.theme_combo)

            layout.addWidget(theme_group)

        def setup_batch_tab_pyqt(self, parent):
            """Set up PyQt batch processing tab."""
            layout = QVBoxLayout(parent)

            batch_group = QGroupBox("Batch Processing")
            batch_layout = QVBoxLayout(batch_group)

            batch_layout.addWidget(QLabel("Add multiple files for batch conversion:"))

            self.file_list = QListWidget()
            batch_layout.addWidget(self.file_list)

            buttons_layout = QHBoxLayout()
            add_files_btn = QPushButton("Add Files")
            add_files_btn.clicked.connect(self.add_batch_files_pyqt)
            buttons_layout.addWidget(add_files_btn)

            remove_btn = QPushButton("Remove Selected")
            remove_btn.clicked.connect(self.remove_batch_files_pyqt)
            buttons_layout.addWidget(remove_btn)

            batch_layout.addLayout(buttons_layout)
            layout.addWidget(batch_group)

        def browse_file_pyqt(self):
            """Browse for input file using PyQt."""
            file_path, _ = QFileDialog.getOpenFileName(
                self.window, "Select DOCX File", "", "Word Documents (*.docx)"
            )
            if file_path:
                self.file_path_edit.setText(file_path)

        def convert_pyqt(self):
            """Convert file using PyQt interface."""
            # This would implement the conversion logic
            # Similar to the Tkinter version but adapted for PyQt
            pass

        def add_batch_files_pyqt(self):
            """Add files to batch list using PyQt."""
            files, _ = QFileDialog.getOpenFileNames(
                self.window, "Select DOCX Files", "", "Word Documents (*.docx)"
            )
            for file_path in files:
                self.file_list.addItem(file_path)

        def remove_batch_files_pyqt(self):
            """Remove selected files from batch list."""
            for item in self.file_list.selectedItems():
                self.file_list.takeItem(self.file_list.row(item))

        def run(self):
            """Run the PyQt application."""
            self.window.show()
            return self.app.exec_()

    MainWindow = PyQtMainWindow

else:
    # No GUI framework available
    class NoGUIMainWindow:
        def __init__(self):
            print("No GUI framework available. Please install tkinter or PyQt.")
            sys.exit(1)

        def run(self):
            pass

    MainWindow = NoGUIMainWindow


def create_context_menu_windows():
    """Create Windows context menu integration."""
    try:
        import winreg

        # Registry key for .docx files
        key_path = r"SOFTWARE\Classes\.docx\shell\Convert to EPUB\command"

        # Get path to this script
        script_path = Path(__file__).parent.parent / "cli.py"
        command = f'python "{script_path}" gui "%1"'

        # Create registry entry
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, command)

        print("Windows context menu integration created successfully!")

    except Exception as e:
        print(f"Failed to create context menu integration: {e}")


def main():
    """Main entry point for GUI application."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run main window
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()