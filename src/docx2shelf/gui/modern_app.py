"""
Modern Docx2Shelf GUI using CustomTkinter for true rounded corners and modern appearance.
This is a modernized version that addresses tkinter's limitations.
"""

import sys
import threading
from pathlib import Path

try:
    import customtkinter as ctk

    MODERN_GUI_AVAILABLE = True
except ImportError:
    MODERN_GUI_AVAILABLE = False
    print("CustomTkinter not available. Install with: pip install customtkinter")

# Import core functionality
from ..assemble import assemble_epub
from ..convert import docx_to_html_chunks
from ..metadata import BuildOptions, EpubMetadata
from ..settings import get_settings_manager
from ..update import download_and_install_update


class ModernDocx2ShelfApp:
    """Modern Docx2Shelf application using CustomTkinter."""

    def __init__(self):
        if not MODERN_GUI_AVAILABLE:
            raise ImportError("CustomTkinter is required for the modern GUI")

        # Configure CustomTkinter appearance with dark mode as default
        ctk.set_appearance_mode("dark")  # Default to dark mode
        ctk.set_default_color_theme("blue")  # Professional blue theme

        # Initialize main window with fixed positioning
        self.root = ctk.CTk()
        self.root.title("🪶 Docx2Shelf - Modern GUI")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Set icon if available
        self.set_window_icon()

        # Store initial window state
        self.initial_geometry = "1200x800"
        self.window_position = None

        # Initialize settings
        self.settings_manager = get_settings_manager()
        self.settings = self.settings_manager.settings

        # Initialize variables
        self.current_file = None
        self.current_worker = None

        # Setup the interface
        self.setup_ui()

        # Check for updates on startup if enabled
        self.root.after(2000, self.check_for_updates_on_startup)  # Check after 2 seconds

    def set_window_icon(self):
        """Set window icon if available."""
        try:
            from pathlib import Path

            # Try different icon locations
            icon_paths = [
                Path(__file__).parent / "assets" / "icon.ico",
                Path(__file__).parent.parent / "assets" / "icon.ico",
                Path(__file__).parent / "assets" / "docx2shelf.ico",
            ]

            for icon_path in icon_paths:
                if icon_path.exists():
                    # For CustomTkinter, we need to use iconbitmap on the underlying tk window
                    self.root.wm_iconbitmap(str(icon_path))
                    break
            else:
                # If no icon file found, create a simple text-based icon
                self.create_text_icon()

        except Exception as e:
            print(f"Could not set window icon: {e}")
            # Fallback to feather quill emoji in title
            self.root.title("🪶 Docx2Shelf - Modern GUI")

    def create_text_icon(self):
        """Create a simple text-based icon using PIL."""
        try:
            import os
            import tempfile

            from PIL import Image, ImageDraw, ImageFont

            # Create a simple icon with feather quill
            size = (32, 32)
            image = Image.new("RGBA", size, (0, 120, 204, 255))  # Blue background
            draw = ImageDraw.Draw(image)

            # Try to use a system font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except OSError:
                try:
                    font = ImageFont.truetype("calibri.ttf", 14)
                except OSError:
                    font = ImageFont.load_default()

            # Draw feather quill symbol in white
            text = "🪶"
            try:
                # Try to draw the feather emoji
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (size[0] - text_width) // 2
                y = (size[1] - text_height) // 2
                draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
            except (ValueError, TypeError):
                # Fallback to simple "Q" for Quill
                text = "Q"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (size[0] - text_width) // 2
                y = (size[1] - text_height) // 2
                draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

            # Save to temporary file
            temp_dir = tempfile.gettempdir()
            icon_path = os.path.join(temp_dir, "docx2shelf_icon.ico")
            image.save(icon_path, format="ICO")

            # Set the icon
            self.root.wm_iconbitmap(icon_path)

        except ImportError:
            # PIL not available, use emoji fallback
            print("PIL not available for icon creation")
        except Exception as e:
            print(f"Failed to create icon: {e}")

    def setup_ui(self):
        """Setup the modern user interface."""

        # Create main header
        header_frame = ctk.CTkFrame(self.root, height=80, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        # App title and theme toggle
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=20)

        title_label = ctk.CTkLabel(
            title_frame, text="📖 Docx2Shelf", font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")

        # Get actual version
        try:
            from ..version import get_version

            current_version = get_version()
        except Exception:
            try:
                from importlib import metadata

                current_version = metadata.version("docx2shelf")
            except Exception:
                current_version = "dev"

        version_label = ctk.CTkLabel(
            title_frame, text=f"v{current_version}", font=ctk.CTkFont(size=14)
        )
        version_label.pack(side="left", padx=(10, 0))

        # Theme controls
        theme_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        theme_frame.pack(side="right", padx=20, pady=20)

        theme_label = ctk.CTkLabel(theme_frame, text="Theme:")
        theme_label.pack(side="left", padx=(0, 10))

        self.theme_switch = ctk.CTkSwitch(theme_frame, text="Dark Mode", command=self.toggle_theme)
        self.theme_switch.pack(side="left")
        # Set switch to dark mode (on) by default
        self.theme_switch.select()

        # Main content area with sidebar
        main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Create tabview for main content
        self.tabview = ctk.CTkTabview(main_frame, corner_radius=15)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Add tabs with modern styling - logical order with settings before about (last)
        self.tabview.add("📄 Convert")
        self.tabview.add("🧙 Wizard")
        self.tabview.add("📦 Batch")
        self.tabview.add("🎨 Themes")
        self.tabview.add("🔍 Quality")
        self.tabview.add("🛠️ Tools")
        self.tabview.add("⚙️ Settings")
        self.tabview.add("ℹ️ About")

        # Setup individual tabs
        self.setup_convert_tab()
        self.setup_settings_tab()
        self.setup_batch_tab()
        self.setup_themes_tab()
        self.setup_quality_tab()
        self.setup_tools_tab()
        self.setup_wizard_tab()
        self.setup_about_tab()

    def setup_convert_tab(self):
        """Setup the modern conversion tab."""
        convert_frame = self.tabview.tab("📄 Convert")

        # Create scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(convert_frame)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # File Input Section
        file_section = ctk.CTkFrame(scrollable_frame, corner_radius=15)
        file_section.pack(fill="x", padx=5, pady=(0, 15))

        file_label = ctk.CTkLabel(
            file_section, text="📁 Input Document", font=ctk.CTkFont(size=18, weight="bold")
        )
        file_label.pack(pady=(15, 10))

        # File selection row
        file_row = ctk.CTkFrame(file_section, fg_color="transparent")
        file_row.pack(fill="x", padx=20, pady=(0, 15))

        self.file_entry = ctk.CTkEntry(
            file_row,
            placeholder_text="Select a document file...",
            height=40,
            font=ctk.CTkFont(size=12),
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            file_row,
            text="📂 Browse",
            command=self.browse_file,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=12),
        )
        browse_btn.pack(side="right")

    def setup_drag_and_drop(self, widget):
        """Setup drag and drop functionality for file input."""
        try:
            # Try to implement tkinterdnd2 if available
            try:
                import tkinterdnd2 as tkdnd

                # Convert CTk widget to underlying tk widget for drag/drop
                tk_widget = widget._canvas if hasattr(widget, "_canvas") else widget
                tk_widget.drop_target_register(tkdnd.DND_FILES)
                tk_widget.dnd_bind("<<Drop>>", self.handle_file_drop)
            except ImportError:
                # Fallback: just bind double-click to browse
                widget.bind("<Double-Button-1>", lambda e: self.browse_file())
        except Exception:
            # Silent fallback
            widget.bind("<Double-Button-1>", lambda e: self.browse_file())

    def handle_file_drop(self, event):
        """Handle dropped files."""
        try:
            files = event.data.split()
            if files:
                file_path = files[0].strip("{}")  # Remove braces if present
                if file_path.lower().endswith((".docx", ".md", ".txt", ".html", ".htm")):
                    self.file_entry.delete(0, "end")
                    self.file_entry.insert(0, file_path)
                    self.current_file = file_path
                else:
                    self.show_error(
                        "Unsupported file type. Please select a DOCX, MD, TXT, or HTML file."
                    )
        except Exception as e:
            self.show_error(f"Error handling dropped file: {str(e)}")

        # Drag and drop area (basic implementation)
        drop_frame = ctk.CTkFrame(
            file_section, height=100, corner_radius=15, border_width=2, border_color="#cccccc"
        )
        drop_frame.pack(fill="x", padx=20, pady=(0, 20))
        drop_frame.pack_propagate(False)

        drop_label = ctk.CTkLabel(
            drop_frame,
            text="💭 Drag and drop your document here\n(DOCX, MD, TXT, HTML)\n\nOr use the Browse button above",
            font=ctk.CTkFont(size=14),
        )
        drop_label.pack(expand=True)

        # Set up drag and drop event handlers
        self.setup_drag_and_drop(drop_frame)

        # Metadata Section
        metadata_section = ctk.CTkFrame(scrollable_frame, corner_radius=15)
        metadata_section.pack(fill="x", padx=5, pady=(0, 15))

        metadata_label = ctk.CTkLabel(
            metadata_section, text="📖 Book Metadata", font=ctk.CTkFont(size=18, weight="bold")
        )
        metadata_label.pack(pady=(15, 10))

        # Metadata form in grid
        metadata_grid = ctk.CTkFrame(metadata_section, fg_color="transparent")
        metadata_grid.pack(fill="x", padx=20, pady=(0, 20))

        # Title and Author row
        title_frame = ctk.CTkFrame(metadata_grid, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))

        # Title
        title_col = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(title_col, text="📖 Title *", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w"
        )
        self.title_entry = ctk.CTkEntry(
            title_col, placeholder_text="Enter book title...", height=35, font=ctk.CTkFont(size=12)
        )
        self.title_entry.pack(fill="x", pady=(5, 0))

        # Author
        author_col = ctk.CTkFrame(title_frame, fg_color="transparent")
        author_col.pack(side="right", fill="x", expand=True, padx=(10, 0))

        ctk.CTkLabel(author_col, text="✍️ Author *", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w"
        )
        self.author_entry = ctk.CTkEntry(
            author_col,
            placeholder_text="Enter author name...",
            height=35,
            font=ctk.CTkFont(size=12),
        )
        self.author_entry.pack(fill="x", pady=(5, 0))

        # Language and Genre row
        lang_genre_frame = ctk.CTkFrame(metadata_grid, fg_color="transparent")
        lang_genre_frame.pack(fill="x", pady=(0, 10))

        # Language
        lang_col = ctk.CTkFrame(lang_genre_frame, fg_color="transparent")
        lang_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(lang_col, text="🌍 Language", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w"
        )
        self.language_combo = ctk.CTkComboBox(
            lang_col,
            values=["English", "Spanish", "French", "German", "Italian"],
            height=35,
            font=ctk.CTkFont(size=12),
        )
        self.language_combo.pack(fill="x", pady=(5, 0))
        self.language_combo.set("English")

        # Genre
        genre_col = ctk.CTkFrame(lang_genre_frame, fg_color="transparent")
        genre_col.pack(side="right", fill="x", expand=True, padx=(10, 0))

        ctk.CTkLabel(genre_col, text="🏷️ Genre", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w"
        )
        self.genre_entry = ctk.CTkEntry(
            genre_col,
            placeholder_text="e.g., Fantasy, Romance...",
            height=35,
            font=ctk.CTkFont(size=12),
        )
        self.genre_entry.pack(fill="x", pady=(5, 0))

        # Description
        desc_frame = ctk.CTkFrame(metadata_grid, fg_color="transparent")
        desc_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            desc_frame, text="📝 Description", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        self.description_text = ctk.CTkTextbox(desc_frame, height=100, font=ctk.CTkFont(size=12))
        self.description_text.pack(fill="x", pady=(5, 0))

        # Conversion Options Section
        options_section = ctk.CTkFrame(scrollable_frame, corner_radius=15)
        options_section.pack(fill="x", padx=5, pady=(0, 15))

        options_label = ctk.CTkLabel(
            options_section, text="⚙️ Conversion Options", font=ctk.CTkFont(size=18, weight="bold")
        )
        options_label.pack(pady=(15, 10))

        # Options in segmented button style
        options_frame = ctk.CTkFrame(options_section, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=(0, 20))

        # CSS Theme
        theme_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            theme_frame, text="🎨 CSS Theme", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        self.css_theme = ctk.CTkSegmentedButton(
            theme_frame, values=["Serif", "Sans-serif", "Print-like"], font=ctk.CTkFont(size=12)
        )
        self.css_theme.pack(fill="x", pady=(5, 0))
        self.css_theme.set("Serif")

        # Checkboxes for options
        check_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        check_frame.pack(fill="x")

        self.include_toc = ctk.CTkCheckBox(
            check_frame, text="📋 Include Table of Contents", font=ctk.CTkFont(size=12)
        )
        self.include_toc.pack(anchor="w", pady=2)
        self.include_toc.select()

        self.ai_detection = ctk.CTkCheckBox(
            check_frame, text="🤖 AI Chapter Detection", font=ctk.CTkFont(size=12)
        )
        self.ai_detection.pack(anchor="w", pady=2)

        self.validate_epub = ctk.CTkCheckBox(
            check_frame, text="✅ Validate EPUB Output", font=ctk.CTkFont(size=12)
        )
        self.validate_epub.pack(anchor="w", pady=2)
        self.validate_epub.select()

        # Progress Section
        progress_section = ctk.CTkFrame(scrollable_frame, corner_radius=15)
        progress_section.pack(fill="x", padx=5, pady=(0, 15))

        self.progress_label = ctk.CTkLabel(
            progress_section, text="Ready to convert", font=ctk.CTkFont(size=14)
        )
        self.progress_label.pack(pady=(15, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_section, height=20)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.progress_bar.set(0)

        # Action Buttons
        button_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=5, pady=(0, 10))

        # Convert button
        self.convert_btn = ctk.CTkButton(
            button_frame,
            text="🚀 Convert to EPUB",
            command=self.start_conversion,
            height=50,
            corner_radius=25,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.convert_btn.pack(side="left", padx=(0, 10))

        # Help button
        help_btn = ctk.CTkButton(
            button_frame,
            text="❓ Help",
            command=self.show_help,
            height=50,
            corner_radius=25,
            font=ctk.CTkFont(size=14),
        )
        help_btn.pack(side="right")

    def setup_settings_tab(self):
        """Setup the comprehensive settings tab with improved multi-column layout."""
        settings_frame = self.tabview.tab("⚙️ Settings")

        # Settings header
        settings_header = ctk.CTkLabel(
            settings_frame, text="🔧 Application Settings", font=ctk.CTkFont(size=20, weight="bold")
        )
        settings_header.pack(pady=(15, 20))

        # Main container with two columns
        main_container = ctk.CTkFrame(settings_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Left column
        left_column = ctk.CTkScrollableFrame(main_container, corner_radius=15)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Right column
        right_column = ctk.CTkScrollableFrame(main_container, corner_radius=15)
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Setup left column content
        self.setup_general_settings(left_column)
        self.setup_conversion_settings(left_column)

        # Setup right column content
        self.setup_ui_settings(right_column)
        self.setup_advanced_settings(right_column)

    def setup_general_settings(self, parent):
        """Setup general application settings."""
        general_section = ctk.CTkFrame(parent, corner_radius=15)
        general_section.pack(fill="x", padx=10, pady=(0, 15))

        general_label = ctk.CTkLabel(
            general_section, text="🎯 General Settings", font=ctk.CTkFont(size=16, weight="bold")
        )
        general_label.pack(pady=(15, 10))

        general_content = ctk.CTkFrame(general_section, fg_color="transparent")
        general_content.pack(fill="x", padx=15, pady=(0, 15))

        # Auto-save settings
        self.auto_save_var = ctk.BooleanVar(value=True)
        auto_save_check = ctk.CTkCheckBox(
            general_content,
            text="🔄 Auto-save settings",
            variable=self.auto_save_var,
            font=ctk.CTkFont(size=12),
        )
        auto_save_check.pack(anchor="w", pady=3)

        # Check for updates
        self.updates_var = ctk.BooleanVar(value=True)
        updates_check = ctk.CTkCheckBox(
            general_content,
            text="🔄 Auto-check for updates",
            variable=self.updates_var,
            font=ctk.CTkFont(size=12),
        )
        updates_check.pack(anchor="w", pady=3)

        # Manual update check
        update_btn = ctk.CTkButton(
            general_content,
            text="🆙 Check for Updates Now",
            command=self.check_for_updates,
            height=30,
            corner_radius=15,
            font=ctk.CTkFont(size=11),
        )
        update_btn.pack(anchor="w", pady=5)

        # Remember window state
        self.remember_window_var = ctk.BooleanVar(value=True)
        remember_check = ctk.CTkCheckBox(
            general_content,
            text="📏 Remember window state",
            variable=self.remember_window_var,
            font=ctk.CTkFont(size=12),
        )
        remember_check.pack(anchor="w", pady=3)

    def setup_conversion_settings(self, parent):
        """Setup conversion-related settings."""
        conversion_section = ctk.CTkFrame(parent, corner_radius=15)
        conversion_section.pack(fill="x", padx=10, pady=(0, 15))

        conversion_label = ctk.CTkLabel(
            conversion_section,
            text="🔄 Conversion Settings",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        conversion_label.pack(pady=(15, 10))

        conversion_content = ctk.CTkFrame(conversion_section, fg_color="transparent")
        conversion_content.pack(fill="x", padx=15, pady=(0, 15))

        # Default output directory
        ctk.CTkLabel(
            conversion_content,
            text="📂 Default Output Directory:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(0, 5))

        dir_row = ctk.CTkFrame(conversion_content, fg_color="transparent")
        dir_row.pack(fill="x", pady=(0, 10))

        self.output_dir_var = ctk.StringVar()
        self.output_dir_entry = ctk.CTkEntry(
            dir_row,
            textvariable=self.output_dir_var,
            placeholder_text="Choose default output folder...",
            font=ctk.CTkFont(size=10),
        )
        self.output_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_dir_btn = ctk.CTkButton(
            dir_row,
            text="📁 Browse",
            command=self.browse_output_directory,
            width=70,
            height=28,
            corner_radius=14,
            font=ctk.CTkFont(size=10),
        )
        browse_dir_btn.pack(side="right")

        # Default theme
        ctk.CTkLabel(
            conversion_content, text="🎨 Default Theme:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 5))

        self.default_theme_var = ctk.StringVar(value="serif")
        theme_menu = ctk.CTkOptionMenu(
            conversion_content,
            variable=self.default_theme_var,
            values=["serif", "sans", "printlike", "fantasy", "romance"],
            width=200,
            height=28,
            font=ctk.CTkFont(size=10),
        )
        theme_menu.pack(anchor="w", pady=(0, 10))

        # Quality preset
        ctk.CTkLabel(
            conversion_content, text="🏆 Quality Preset:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        self.quality_preset_var = ctk.StringVar(value="standard")
        quality_menu = ctk.CTkOptionMenu(
            conversion_content,
            variable=self.quality_preset_var,
            values=["draft", "standard", "high", "premium"],
            width=200,
            height=28,
            font=ctk.CTkFont(size=10),
        )
        quality_menu.pack(anchor="w")

    def setup_ui_settings(self, parent):
        """Setup UI-related settings."""
        ui_section = ctk.CTkFrame(parent, corner_radius=15)
        ui_section.pack(fill="x", padx=10, pady=(0, 15))

        ui_label = ctk.CTkLabel(
            ui_section, text="🎨 Interface Settings", font=ctk.CTkFont(size=16, weight="bold")
        )
        ui_label.pack(pady=(15, 10))

        ui_content = ctk.CTkFrame(ui_section, fg_color="transparent")
        ui_content.pack(fill="x", padx=15, pady=(0, 15))

        # Show tooltips
        self.show_tooltips_var = ctk.BooleanVar(value=True)
        tooltips_check = ctk.CTkCheckBox(
            ui_content,
            text="💡 Show tooltips",
            variable=self.show_tooltips_var,
            font=ctk.CTkFont(size=12),
        )
        tooltips_check.pack(anchor="w", pady=3)

        # Show progress details
        self.show_progress_var = ctk.BooleanVar(value=False)
        progress_check = ctk.CTkCheckBox(
            ui_content,
            text="📈 Show detailed progress",
            variable=self.show_progress_var,
            font=ctk.CTkFont(size=12),
        )
        progress_check.pack(anchor="w", pady=3)

        # Theme
        ctk.CTkLabel(
            ui_content, text="🌙 App Theme:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(10, 5))

        self.app_theme_var = ctk.StringVar(value="dark")
        theme_menu = ctk.CTkOptionMenu(
            ui_content,
            variable=self.app_theme_var,
            values=["light", "dark", "system"],
            command=self.change_app_theme,
            width=150,
            height=28,
            font=ctk.CTkFont(size=10),
        )
        theme_menu.pack(anchor="w", pady=(0, 10))

        # Font scaling
        ctk.CTkLabel(
            ui_content, text="🔤 Interface Scale:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        self.ui_scale_var = ctk.StringVar(value="100%")
        scale_menu = ctk.CTkOptionMenu(
            ui_content,
            variable=self.ui_scale_var,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_ui_scale,
            width=150,
            height=28,
            font=ctk.CTkFont(size=10),
        )
        scale_menu.pack(anchor="w")

    def setup_advanced_settings(self, parent):
        """Setup advanced settings."""
        advanced_section = ctk.CTkFrame(parent, corner_radius=15)
        advanced_section.pack(fill="x", padx=10, pady=(0, 15))

        advanced_label = ctk.CTkLabel(
            advanced_section, text="⚙️ Advanced Settings", font=ctk.CTkFont(size=16, weight="bold")
        )
        advanced_label.pack(pady=(15, 10))

        advanced_content = ctk.CTkFrame(advanced_section, fg_color="transparent")
        advanced_content.pack(fill="x", padx=15, pady=(0, 15))

        # Debug mode
        self.debug_mode_var = ctk.BooleanVar(value=False)
        debug_check = ctk.CTkCheckBox(
            advanced_content,
            text="🐛 Debug mode",
            variable=self.debug_mode_var,
            font=ctk.CTkFont(size=12),
        )
        debug_check.pack(anchor="w", pady=3)

        # Parallel processing
        self.parallel_var = ctk.BooleanVar(value=True)
        parallel_check = ctk.CTkCheckBox(
            advanced_content,
            text="⚡ Parallel processing",
            variable=self.parallel_var,
            font=ctk.CTkFont(size=12),
        )
        parallel_check.pack(anchor="w", pady=3)

        # Cache cleanup
        cache_btn = ctk.CTkButton(
            advanced_content,
            text="🗿 Clear Cache",
            command=self.clear_cache,
            height=30,
            corner_radius=15,
            font=ctk.CTkFont(size=11),
            fg_color="orange",
            hover_color="darkorange",
        )
        cache_btn.pack(anchor="w", pady=10)

        # Reset settings
        reset_btn = ctk.CTkButton(
            advanced_content,
            text="🔄 Reset All Settings",
            command=self.reset_settings,
            height=30,
            corner_radius=15,
            font=ctk.CTkFont(size=11),
            fg_color="darkred",
            hover_color="red",
        )
        reset_btn.pack(anchor="w", pady=5)

        # Data directory
        ctk.CTkLabel(
            advanced_content, text="📁 Data Directory:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(15, 5))

        data_dir_btn = ctk.CTkButton(
            advanced_content,
            text="📂 Open Data Folder",
            command=self.open_data_directory,
            height=30,
            corner_radius=15,
            font=ctk.CTkFont(size=11),
        )
        data_dir_btn.pack(anchor="w")

        # Auto-generate filenames
        self.auto_filename_var = ctk.BooleanVar(value=True)
        auto_filename_check = ctk.CTkCheckBox(
            output_content,
            text="📝 Auto-generate output filenames",
            variable=self.auto_filename_var,
            font=ctk.CTkFont(size=12),
        )
        auto_filename_check.pack(anchor="w", pady=5)

        # Backup original files
        self.backup_original_var = ctk.BooleanVar(value=False)
        backup_check = ctk.CTkCheckBox(
            output_content,
            text="💾 Create backup of original files",
            variable=self.backup_original_var,
            font=ctk.CTkFont(size=12),
        )
        backup_check.pack(anchor="w", pady=5)

        # Default format
        format_frame = ctk.CTkFrame(output_content, fg_color="transparent")
        format_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(
            format_frame, text="📖 Default Output Format:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        self.format_var = ctk.StringVar(value="EPUB3")
        format_combo = ctk.CTkComboBox(
            format_frame,
            variable=self.format_var,
            values=["EPUB3", "EPUB2", "MOBI"],
            font=ctk.CTkFont(size=11),
        )
        format_combo.pack(fill="x", pady=(5, 0))

        # Preserve structure
        self.structure_var = ctk.BooleanVar(value=True)
        structure_check = ctk.CTkCheckBox(
            output_content,
            text="🏗️ Preserve document structure",
            variable=self.structure_var,
            font=ctk.CTkFont(size=12),
        )
        structure_check.pack(anchor="w", pady=5)

        # Create backup alias for compatibility
        self.backup_var = self.backup_original_var

        # AI Detection Settings Section
        ai_section = ctk.CTkFrame(scrollable_settings, corner_radius=15)
        ai_section.pack(fill="x", padx=5, pady=(0, 15))

        ai_label = ctk.CTkLabel(
            ai_section, text="🤖 AI Detection Settings", font=ctk.CTkFont(size=16, weight="bold")
        )
        ai_label.pack(pady=(15, 10))

        ai_content = ctk.CTkFrame(ai_section, fg_color="transparent")
        ai_content.pack(fill="x", padx=20, pady=(0, 20))

        # Enable AI features
        self.enable_ai_var = ctk.BooleanVar(value=True)
        enable_ai_check = ctk.CTkCheckBox(
            ai_content,
            text="🧠 Enable AI chapter detection",
            variable=self.enable_ai_var,
            font=ctk.CTkFont(size=12),
        )
        enable_ai_check.pack(anchor="w", pady=5)

        # Confidence threshold
        conf_frame = ctk.CTkFrame(ai_content, fg_color="transparent")
        conf_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            conf_frame, text="🎯 Confidence Threshold:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        self.confidence_var = ctk.DoubleVar(value=0.8)
        confidence_slider = ctk.CTkSlider(
            conf_frame, from_=0.5, to=1.0, variable=self.confidence_var, number_of_steps=10
        )
        confidence_slider.pack(fill="x", pady=(5, 0))

        self.confidence_label = ctk.CTkLabel(conf_frame, text="80%", font=ctk.CTkFont(size=11))
        self.confidence_label.pack(anchor="w")

        # Update confidence label
        confidence_slider.configure(command=self.update_confidence_label)

        # Advanced Settings Section
        advanced_section = ctk.CTkFrame(scrollable_settings, corner_radius=15)
        advanced_section.pack(fill="x", padx=5, pady=(0, 15))

        advanced_label = ctk.CTkLabel(
            advanced_section, text="⚡ Advanced Settings", font=ctk.CTkFont(size=16, weight="bold")
        )
        advanced_label.pack(pady=(15, 10))

        advanced_content = ctk.CTkFrame(advanced_section, fg_color="transparent")
        advanced_content.pack(fill="x", padx=20, pady=(0, 20))

        # Processing threads
        threads_frame = ctk.CTkFrame(advanced_content, fg_color="transparent")
        threads_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            threads_frame, text="🧵 Processing Threads:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        self.threads_var = ctk.IntVar(value=4)
        threads_slider = ctk.CTkSlider(
            threads_frame, from_=1, to=8, variable=self.threads_var, number_of_steps=7
        )
        threads_slider.pack(fill="x", pady=(5, 0))

        self.threads_label = ctk.CTkLabel(
            threads_frame, text="4 threads", font=ctk.CTkFont(size=11)
        )
        self.threads_label.pack(anchor="w")

        threads_slider.configure(command=self.update_threads_label)

        # Memory usage limit
        memory_frame = ctk.CTkFrame(advanced_content, fg_color="transparent")
        memory_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            memory_frame, text="💾 Memory Limit (MB):", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        self.memory_var = ctk.IntVar(value=512)
        memory_slider = ctk.CTkSlider(
            memory_frame, from_=256, to=2048, variable=self.memory_var, number_of_steps=7
        )
        memory_slider.pack(fill="x", pady=(5, 0))

        self.memory_label = ctk.CTkLabel(memory_frame, text="512 MB", font=ctk.CTkFont(size=11))
        self.memory_label.pack(anchor="w")

        memory_slider.configure(command=self.update_memory_label)

        # Action Buttons
        button_frame = ctk.CTkFrame(scrollable_settings, fg_color="transparent")
        button_frame.pack(fill="x", padx=5, pady=(10, 0))

        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        save_btn.pack(side="left", padx=(0, 10))

        reset_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Reset to Defaults",
            command=self.reset_settings,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=14),
        )
        reset_btn.pack(side="left", padx=(0, 10))

        export_btn = ctk.CTkButton(
            button_frame,
            text="📤 Export Settings",
            command=self.export_settings,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=14),
        )
        export_btn.pack(side="right", padx=(10, 0))

        import_btn = ctk.CTkButton(
            button_frame,
            text="📥 Import Settings",
            command=self.import_settings,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=14),
        )
        import_btn.pack(side="right")

    def setup_batch_tab(self):
        """Setup the batch processing tab."""
        batch_frame = self.tabview.tab("📦 Batch")

        # Create scrollable frame for batch processing
        scrollable_batch = ctk.CTkScrollableFrame(batch_frame)
        scrollable_batch.pack(fill="both", expand=True, padx=10, pady=10)

        # Batch header
        batch_label = ctk.CTkLabel(
            scrollable_batch, text="📦 Batch Processing", font=ctk.CTkFont(size=20, weight="bold")
        )
        batch_label.pack(pady=(0, 20))

        # File selection section
        files_section = ctk.CTkFrame(scrollable_batch, corner_radius=15)
        files_section.pack(fill="x", padx=5, pady=(0, 15))

        files_label = ctk.CTkLabel(
            files_section, text="📁 Input Files", font=ctk.CTkFont(size=16, weight="bold")
        )
        files_label.pack(pady=(15, 10))

        files_content = ctk.CTkFrame(files_section, fg_color="transparent")
        files_content.pack(fill="x", padx=20, pady=(0, 20))

        # File list with scroll area
        self.batch_files = []
        files_list_frame = ctk.CTkFrame(files_content)
        files_list_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.files_listbox = ctk.CTkScrollableFrame(files_list_frame, height=150)
        self.files_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        # File management buttons
        file_buttons = ctk.CTkFrame(files_content, fg_color="transparent")
        file_buttons.pack(fill="x", pady=5)

        add_files_btn = ctk.CTkButton(
            file_buttons,
            text="➕ Add Files",
            command=self.add_batch_files,
            height=35,
            corner_radius=17,
        )
        add_files_btn.pack(side="left", padx=(0, 10))

        add_folder_btn = ctk.CTkButton(
            file_buttons,
            text="📁 Add Folder",
            command=self.add_batch_folder,
            height=35,
            corner_radius=17,
        )
        add_folder_btn.pack(side="left", padx=(0, 10))

        clear_files_btn = ctk.CTkButton(
            file_buttons,
            text="🗑️ Clear All",
            command=self.clear_batch_files,
            height=35,
            corner_radius=17,
        )
        clear_files_btn.pack(side="right")

        # Batch settings section
        settings_section = ctk.CTkFrame(scrollable_batch, corner_radius=15)
        settings_section.pack(fill="x", padx=5, pady=(0, 15))

        settings_label = ctk.CTkLabel(
            settings_section, text="⚙️ Batch Settings", font=ctk.CTkFont(size=16, weight="bold")
        )
        settings_label.pack(pady=(15, 10))

        settings_content = ctk.CTkFrame(settings_section, fg_color="transparent")
        settings_content.pack(fill="x", padx=20, pady=(0, 20))

        # Common metadata
        common_frame = ctk.CTkFrame(settings_content, fg_color="transparent")
        common_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            common_frame, text="👤 Common Author:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")
        self.batch_author_var = ctk.StringVar()
        self.batch_author_entry = ctk.CTkEntry(
            common_frame,
            textvariable=self.batch_author_var,
            placeholder_text="Author name for all books...",
            font=ctk.CTkFont(size=11),
        )
        self.batch_author_entry.pack(fill="x", pady=(5, 0))

        # Output settings
        output_frame = ctk.CTkFrame(settings_content, fg_color="transparent")
        output_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            output_frame, text="📂 Output Directory:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        output_row = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_row.pack(fill="x", pady=(5, 0))

        self.batch_output_var = ctk.StringVar()
        self.batch_output_entry = ctk.CTkEntry(
            output_row,
            textvariable=self.batch_output_var,
            placeholder_text="Choose output directory...",
            font=ctk.CTkFont(size=11),
        )
        self.batch_output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_output_btn = ctk.CTkButton(
            output_row,
            text="📁 Browse",
            command=self.browse_batch_output,
            width=80,
            height=30,
            corner_radius=15,
        )
        browse_output_btn.pack(side="right")

        # Batch options
        options_frame = ctk.CTkFrame(settings_content, fg_color="transparent")
        options_frame.pack(fill="x", pady=10)

        self.batch_overwrite_var = ctk.BooleanVar(value=False)
        overwrite_check = ctk.CTkCheckBox(
            options_frame,
            text="♻️ Overwrite existing files",
            variable=self.batch_overwrite_var,
            font=ctk.CTkFont(size=12),
        )
        overwrite_check.pack(anchor="w", pady=2)

        self.batch_keep_structure_var = ctk.BooleanVar(value=True)
        structure_check = ctk.CTkCheckBox(
            options_frame,
            text="🏗️ Keep folder structure",
            variable=self.batch_keep_structure_var,
            font=ctk.CTkFont(size=12),
        )
        structure_check.pack(anchor="w", pady=2)

        self.batch_ai_detection_var = ctk.BooleanVar(value=True)
        ai_check = ctk.CTkCheckBox(
            options_frame,
            text="🤖 Use AI chapter detection",
            variable=self.batch_ai_detection_var,
            font=ctk.CTkFont(size=12),
        )
        ai_check.pack(anchor="w", pady=2)

        # Progress section
        progress_section = ctk.CTkFrame(scrollable_batch, corner_radius=15)
        progress_section.pack(fill="x", padx=5, pady=(0, 15))

        progress_label = ctk.CTkLabel(
            progress_section, text="📊 Progress", font=ctk.CTkFont(size=16, weight="bold")
        )
        progress_label.pack(pady=(15, 10))

        progress_content = ctk.CTkFrame(progress_section, fg_color="transparent")
        progress_content.pack(fill="x", padx=20, pady=(0, 20))

        # Overall progress
        overall_frame = ctk.CTkFrame(progress_content, fg_color="transparent")
        overall_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            overall_frame, text="Overall Progress:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        self.batch_progress_var = ctk.DoubleVar()
        self.batch_progress_bar = ctk.CTkProgressBar(
            overall_frame, variable=self.batch_progress_var
        )
        self.batch_progress_bar.pack(fill="x", pady=(5, 0))

        self.batch_progress_label = ctk.CTkLabel(
            overall_frame, text="0 / 0 files completed", font=ctk.CTkFont(size=11)
        )
        self.batch_progress_label.pack(anchor="w", pady=(2, 0))

        # Current file progress
        current_frame = ctk.CTkFrame(progress_content, fg_color="transparent")
        current_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            current_frame, text="Current File:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        self.current_file_label = ctk.CTkLabel(
            current_frame, text="No file processing...", font=ctk.CTkFont(size=11)
        )
        self.current_file_label.pack(anchor="w", pady=(2, 0))

        # Processing log
        log_frame = ctk.CTkFrame(progress_content, fg_color="transparent")
        log_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            log_frame, text="Processing Log:", font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w")

        self.batch_log = ctk.CTkTextbox(log_frame, height=100, font=ctk.CTkFont(size=10))
        self.batch_log.pack(fill="x", pady=(5, 0))

        # Control buttons
        control_section = ctk.CTkFrame(scrollable_batch, corner_radius=15)
        control_section.pack(fill="x", padx=5, pady=(0, 10))

        control_content = ctk.CTkFrame(control_section, fg_color="transparent")
        control_content.pack(fill="x", padx=20, pady=20)

        self.start_batch_btn = ctk.CTkButton(
            control_content,
            text="🚀 Start Batch Processing",
            command=self.start_batch_processing,
            height=45,
            corner_radius=22,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.start_batch_btn.pack(side="left", padx=(0, 15))

        self.pause_batch_btn = ctk.CTkButton(
            control_content,
            text="⏸️ Pause",
            command=self.pause_batch_processing,
            height=45,
            corner_radius=22,
            font=ctk.CTkFont(size=14),
        )
        self.pause_batch_btn.pack(side="left", padx=(0, 15))

        self.stop_batch_btn = ctk.CTkButton(
            control_content,
            text="⏹️ Stop",
            command=self.stop_batch_processing,
            height=45,
            corner_radius=22,
            font=ctk.CTkFont(size=14),
        )
        self.stop_batch_btn.pack(side="left")

        # Results button (initially hidden)
        self.results_btn = ctk.CTkButton(
            control_content,
            text="📋 View Results",
            command=self.show_batch_results,
            height=45,
            corner_radius=22,
            font=ctk.CTkFont(size=14),
        )
        # Don't pack initially - will be shown after completion

        # Initialize batch state
        self.batch_state = {
            "running": False,
            "paused": False,
            "current_index": 0,
            "completed": 0,
            "failed": 0,
            "results": [],
        }

    def setup_about_tab(self):
        """Setup the about tab."""
        about_frame = self.tabview.tab("ℹ️ About")

        # About content
        about_label = ctk.CTkLabel(
            about_frame, text="ℹ️ About Docx2Shelf", font=ctk.CTkFont(size=20, weight="bold")
        )
        about_label.pack(pady=20)

        # About info with CLI feature compatibility
        info_text = """Docx2Shelf v1.6.3 - Modern GUI

Document to EPUB Converter with AI Features

• Convert DOCX, Markdown, HTML, and TXT files to EPUB
• AI-powered chapter detection and metadata enhancement
• Professional EPUB output for all major ebook stores
• Modern interface with dark/light themes
• Batch processing for multiple documents
• Automatic updates and tool management
• Full feature parity with CLI interface
• Cross-platform compatibility

Built with CustomTkinter for a modern appearance.

CLI Access: Run 'docx2shelf --help' for command-line usage"""

        info_label = ctk.CTkLabel(
            about_frame, text=info_text, font=ctk.CTkFont(size=14), justify="left"
        )
        info_label.pack(padx=20, pady=20)

    def toggle_theme(self):
        """Toggle between light and dark themes while preserving window geometry."""
        # Store current window geometry and position
        current_geometry = self.root.geometry()

        # Apply theme change
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

        # Restore exact geometry after theme change
        self.root.after(1, lambda: self.root.geometry(current_geometry))

    def browse_file(self):
        """Browse for input file."""
        from tkinter import filedialog

        file_path = filedialog.askopenfilename(
            title="Select Document",
            filetypes=[
                ("All Supported", "*.docx *.md *.txt *.html *.htm"),
                ("Word Documents", "*.docx"),
                ("Markdown Files", "*.md"),
                ("Text Files", "*.txt"),
                ("HTML Files", "*.html *.htm"),
                ("All Files", "*.*"),
            ],
        )

        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.current_file = file_path

    def start_conversion(self):
        """Start the conversion process."""
        if not self.current_file:
            self.show_error("Please select a document file first.")
            return

        if not self.title_entry.get().strip():
            self.show_error("Please enter a book title.")
            return

        if not self.author_entry.get().strip():
            self.show_error("Please enter an author name.")
            return

        # Start conversion in background thread
        self.convert_btn.configure(state="disabled", text="Converting...")
        self.progress_bar.set(0)

        thread = threading.Thread(target=self.conversion_worker)
        thread.daemon = True
        thread.start()

    def conversion_worker(self):
        """Background conversion worker with real implementation."""
        try:
            from pathlib import Path
            from tkinter import filedialog

            from ..assemble import assemble_epub
            from ..convert import docx_to_html_chunks
            from ..metadata import BuildOptions, EpubMetadata

            # Update progress
            self.root.after(0, lambda: self.progress_bar.set(0.1))
            self.root.after(
                0, lambda: self.progress_label.configure(text="Preparing conversion...")
            )

            # Validate inputs
            if not self.current_file:
                raise ValueError("No input file selected")

            if not self.title_entry.get().strip():
                raise ValueError("Title is required")

            if not self.author_entry.get().strip():
                raise ValueError("Author is required")

            # Create metadata from form inputs
            metadata = EpubMetadata(
                title=self.title_entry.get().strip(),
                author=self.author_entry.get().strip(),
                language=self.language_combo.get().lower()[:2],
                description=self.description_text.get("0.0", "end").strip() or None,
                genre=self.genre_entry.get().strip() or None,
            )

            # Create build options
            options = BuildOptions(
                use_ai_detection=self.ai_detection.get(),
                theme=self.css_theme.get().lower().replace("-", ""),
                include_toc=self.include_toc.get(),
                validate_epub=self.validate_epub.get(),
            )

            # Update progress
            self.root.after(0, lambda: self.progress_bar.set(0.2))
            self.root.after(0, lambda: self.progress_label.configure(text="Reading document..."))

            # Convert document to HTML chunks
            chunks = docx_to_html_chunks(self.current_file)

            self.root.after(0, lambda: self.progress_bar.set(0.5))
            self.root.after(0, lambda: self.progress_label.configure(text="Processing content..."))

            # Generate output path
            input_path = Path(self.current_file)
            default_name = f"{metadata.title.replace(' ', '_').replace(':', '_')}.epub"

            # Use main thread to show save dialog
            output_path = None

            def show_save_dialog():
                nonlocal output_path
                output_path = filedialog.asksaveasfilename(
                    title="Save EPUB as...",
                    defaultextension=".epub",
                    filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")],
                    initialname=default_name,
                )

            self.root.after(0, show_save_dialog)

            # Wait for dialog to complete
            while output_path is None:
                import time

                time.sleep(0.1)

            if not output_path:
                # User cancelled
                self.root.after(
                    0, lambda: self.convert_btn.configure(state="normal", text="🚀 Convert to EPUB")
                )
                self.root.after(
                    0, lambda: self.progress_label.configure(text="Conversion cancelled")
                )
                self.root.after(0, lambda: self.progress_bar.set(0))
                return

            self.root.after(0, lambda: self.progress_bar.set(0.7))
            self.root.after(0, lambda: self.progress_label.configure(text="Generating EPUB..."))

            # Assemble EPUB
            assemble_epub(chunks, metadata, output_path, options)

            self.root.after(0, lambda: self.progress_bar.set(1.0))
            self.root.after(0, lambda: self.progress_label.configure(text="Conversion complete!"))

            # Re-enable button
            self.root.after(
                0, lambda: self.convert_btn.configure(state="normal", text="🚀 Convert to EPUB")
            )

            # Show success message with file location
            success_msg = f"EPUB conversion completed successfully!\n\nSaved to: {output_path}"
            self.root.after(0, lambda: self.show_success_with_open_option(success_msg, output_path))

        except Exception:
            self.root.after(0, lambda: self.show_error(f"Conversion failed: {str(e)}"))
            self.root.after(
                0, lambda: self.convert_btn.configure(state="normal", text="🚀 Convert to EPUB")
            )
            self.root.after(0, lambda: self.progress_bar.set(0))
            self.root.after(0, lambda: self.progress_label.configure(text="Conversion failed"))

    def show_help(self):
        """Show help dialog."""
        help_window = ctk.CTkToplevel(self.root)
        help_window.title("📖 Help Guide")
        help_window.geometry("800x600")
        help_window.transient(self.root)
        help_window.grab_set()

        # Help content
        help_label = ctk.CTkLabel(
            help_window, text="📖 Docx2Shelf Help", font=ctk.CTkFont(size=24, weight="bold")
        )
        help_label.pack(pady=20)

        help_text = """🚀 Quick Start Guide

1. 📁 Select your document file using the Browse button
2. 📝 Fill in the book metadata (title and author are required)
3. ⚙️ Choose your conversion options
4. 🚀 Click "Convert to EPUB" to generate your ebook

💡 Pro Tips:
• Use proper heading styles in your document for best chapter detection
• Fill out complete metadata for better ebook store compatibility
• Enable AI features for enhanced content analysis
• Validate your EPUB before publishing

🎨 Modern Interface:
• Toggle between light and dark themes
• Rounded corners and modern styling
• Responsive design that scales with your content
• Intuitive layout with clear visual hierarchy"""

        help_textbox = ctk.CTkTextbox(help_window, font=ctk.CTkFont(size=12))
        help_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        help_textbox.insert("0.0", help_text)
        help_textbox.configure(state="disabled")

        # Close button
        close_btn = ctk.CTkButton(
            help_window, text="✕ Close", command=help_window.destroy, height=40, corner_radius=20
        )
        close_btn.pack(pady=(0, 20))

    def update_confidence_label(self, value):
        """Update confidence threshold label."""
        percentage = int(float(value) * 100)
        self.confidence_label.configure(text=f"{percentage}%")

    def update_threads_label(self, value):
        """Update threads count label."""
        count = int(float(value))
        self.threads_label.configure(text=f"{count} threads")

    def update_memory_label(self, value):
        """Update memory limit label."""
        mb = int(float(value))
        self.memory_label.configure(text=f"{mb} MB")

    def save_settings(self):
        """Save current settings."""
        try:
            # Collect all settings from UI
            settings = {
                "general": {
                    "auto_save": self.auto_save_var.get(),
                    "show_tooltips": self.tooltips_var.get(),
                    "remember_window": self.remember_window_var.get(),
                    "check_updates": self.updates_var.get(),
                },
                "output": {
                    "default_format": self.format_var.get(),
                    "preserve_structure": self.structure_var.get(),
                    "create_backup": self.backup_var.get(),
                },
                "ai": {
                    "enable_ai": self.enable_ai_var.get(),
                    "confidence_threshold": self.confidence_var.get(),
                },
                "advanced": {
                    "processing_threads": self.threads_var.get(),
                    "memory_limit": self.memory_var.get(),
                },
            }

            # Save to settings manager
            for category, options in settings.items():
                for key, value in options.items():
                    self.settings_manager.set(f"{category}.{key}", value)

            self.settings_manager.save()
            self.show_success("Settings saved successfully!")

        except Exception as e:
            self.show_error(f"Failed to save settings: {str(e)}")

    def reset_settings(self):
        """Reset all settings to defaults."""
        try:
            # Reset UI controls to defaults
            self.auto_save_var.set(True)
            self.tooltips_var.set(True)
            self.remember_window_var.set(True)
            self.updates_var.set(True)
            self.format_var.set("EPUB3")
            self.structure_var.set(True)
            self.backup_var.set(False)
            self.enable_ai_var.set(True)
            self.confidence_var.set(0.8)
            self.threads_var.set(4)
            self.memory_var.set(512)

            # Update labels
            self.update_confidence_label(0.8)
            self.update_threads_label(4)
            self.update_memory_label(512)

            self.show_success("Settings reset to defaults!")

        except Exception as e:
            self.show_error(f"Failed to reset settings: {str(e)}")

    def export_settings(self):
        """Export settings to file."""
        try:
            import json
            from tkinter import filedialog

            file_path = filedialog.asksaveasfilename(
                title="Export Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )

            if file_path:
                # Collect current settings
                settings = {
                    "general": {
                        "auto_save": self.auto_save_var.get(),
                        "show_tooltips": self.tooltips_var.get(),
                        "remember_window": self.remember_window_var.get(),
                        "check_updates": self.updates_var.get(),
                    },
                    "output": {
                        "default_format": self.format_var.get(),
                        "preserve_structure": self.structure_var.get(),
                        "create_backup": self.backup_var.get(),
                    },
                    "ai": {
                        "enable_ai": self.enable_ai_var.get(),
                        "confidence_threshold": self.confidence_var.get(),
                    },
                    "advanced": {
                        "processing_threads": self.threads_var.get(),
                        "memory_limit": self.memory_var.get(),
                    },
                }

                with open(file_path, "w") as f:
                    json.dump(settings, f, indent=2)

                self.show_success(f"Settings exported to {file_path}")

        except Exception as e:
            self.show_error(f"Failed to export settings: {str(e)}")

    def import_settings(self):
        """Import settings from file."""
        try:
            import json
            from tkinter import filedialog

            file_path = filedialog.askopenfilename(
                title="Import Settings", filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                with open(file_path, "r") as f:
                    settings = json.load(f)

                # Apply imported settings to UI
                if "general" in settings:
                    self.auto_save_var.set(settings["general"].get("auto_save", True))
                    self.tooltips_var.set(settings["general"].get("show_tooltips", True))
                    self.remember_window_var.set(settings["general"].get("remember_window", True))
                    self.updates_var.set(settings["general"].get("check_updates", True))

                if "output" in settings:
                    self.format_var.set(settings["output"].get("default_format", "EPUB3"))
                    self.structure_var.set(settings["output"].get("preserve_structure", True))
                    self.backup_var.set(settings["output"].get("create_backup", False))

                if "ai" in settings:
                    self.enable_ai_var.set(settings["ai"].get("enable_ai", True))
                    self.confidence_var.set(settings["ai"].get("confidence_threshold", 0.8))
                    self.update_confidence_label(settings["ai"].get("confidence_threshold", 0.8))

                if "advanced" in settings:
                    self.threads_var.set(settings["advanced"].get("processing_threads", 4))
                    self.memory_var.set(settings["advanced"].get("memory_limit", 512))
                    self.update_threads_label(settings["advanced"].get("processing_threads", 4))
                    self.update_memory_label(settings["advanced"].get("memory_limit", 512))

                self.show_success(f"Settings imported from {file_path}")

        except Exception as e:
            self.show_error(f"Failed to import settings: {str(e)}")

    def check_for_updates(self):
        """Check for application updates."""
        import threading

        def update_thread():
            try:
                # Show checking message
                self.root.after(0, lambda: self.show_update_checking())

                # Import and check for updates
                from ..update import check_for_updates as check_updates

                result = check_updates()

                try:
                    from ..version import get_version

                    current_version = get_version()
                except Exception:
                    try:
                        from importlib import metadata

                        current_version = metadata.version("docx2shelf")
                    except:
                        current_version = "unknown"

                if result and result.get("update_available"):
                    latest_version = result.get("latest_version", "Unknown")
                    download_url = result.get("download_url", "")
                    installer_name = result.get("installer_name", "installer")
                    changelog = result.get("changelog", "No changelog available.")

                    # Show update available dialog
                    self.root.after(
                        0,
                        lambda: self.show_update_available(
                            current_version, latest_version, changelog, download_url, installer_name
                        ),
                    )
                else:
                    # No update available
                    self.root.after(0, lambda: self.show_update_current(current_version))

            except Exception:
                self.root.after(
                    0, lambda: self.show_error(f"Failed to check for updates: {str(e)}")
                )

        # Start update check in background thread
        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()

    def show_update_checking(self):
        """Show update checking dialog."""
        self.update_dialog = ctk.CTkToplevel(self.root)
        self.update_dialog.title("🔄 Checking for Updates")
        self.update_dialog.geometry("450x180")
        self.update_dialog.transient(self.root)
        self.update_dialog.grab_set()
        self.update_dialog.resizable(False, False)

        # Center the dialog
        self.update_dialog.update_idletasks()
        x = (self.update_dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.update_dialog.winfo_screenheight() // 2) - (180 // 2)
        self.update_dialog.geometry(f"450x180+{x}+{y}")

        ctk.CTkLabel(
            self.update_dialog,
            text="🔄 Checking for Updates...",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=20)

        # Progress bar
        progress = ctk.CTkProgressBar(self.update_dialog, mode="indeterminate")
        progress.pack(pady=10, padx=40, fill="x")
        progress.start()

        ctk.CTkLabel(
            self.update_dialog,
            text="Please wait while we check for the latest version...",
            font=ctk.CTkFont(size=12),
        ).pack(pady=10)

    def show_update_available(
        self, current_version, latest_version, changelog, download_url, installer_name=None
    ):
        """Show update available dialog."""
        if hasattr(self, "update_dialog"):
            self.update_dialog.destroy()

        update_window = ctk.CTkToplevel(self.root)
        update_window.title("🆙 Update Available")
        update_window.geometry("600x500")
        update_window.transient(self.root)
        update_window.grab_set()
        update_window.resizable(True, True)
        update_window.minsize(500, 400)

        # Center the dialog
        update_window.update_idletasks()
        x = (update_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (update_window.winfo_screenheight() // 2) - (500 // 2)
        update_window.geometry(f"600x500+{x}+{y}")

        # Header
        header_label = ctk.CTkLabel(
            update_window, text="🎉 Update Available!", font=ctk.CTkFont(size=20, weight="bold")
        )
        header_label.pack(pady=20)

        # Version info
        version_frame = ctk.CTkFrame(update_window)
        version_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            version_frame, text=f"Current Version: {current_version}", font=ctk.CTkFont(size=14)
        ).pack(pady=5)
        ctk.CTkLabel(
            version_frame,
            text=f"Latest Version: {latest_version}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=5)

        # Changelog
        ctk.CTkLabel(
            update_window, text="What's New:", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 5))

        changelog_text = ctk.CTkTextbox(update_window, height=150)
        changelog_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        changelog_text.insert("0.0", changelog)
        changelog_text.configure(state="disabled")

        # Buttons
        button_frame = ctk.CTkFrame(update_window, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        download_btn = ctk.CTkButton(
            button_frame,
            text="🔽 Download & Install",
            command=lambda: self.download_update(download_url, installer_name),
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        download_btn.pack(side="left", padx=(0, 10))

        later_btn = ctk.CTkButton(
            button_frame,
            text="⏰ Later",
            command=update_window.destroy,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=14),
        )
        later_btn.pack(side="right")

    def show_update_current(self, current_version):
        """Show already up to date dialog."""
        if hasattr(self, "update_dialog"):
            self.update_dialog.destroy()

        self.show_success(
            f"You're already running the latest version!\n\nCurrent version: {current_version}"
        )

    def download_update(self, download_url, installer_name=None):
        """Download and install update automatically."""
        import threading

        def download_thread():
            try:
                if download_url:
                    # Show downloading dialog
                    self.root.after(0, lambda: self.show_update_downloading())

                    # Use the enhanced download function
                    success = download_and_install_update(
                        download_url, installer_name or "installer"
                    )

                    if success:
                        self.root.after(0, lambda: self.show_update_success())
                    else:
                        self.root.after(0, lambda: self.show_update_manual(download_url))
                else:
                    self.root.after(
                        0,
                        lambda: self.show_error(
                            "Download URL not available.\nPlease visit the project page to download manually."
                        ),
                    )
            except Exception:
                self.root.after(0, lambda: self.show_error(f"Failed to download update: {str(e)}"))

        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

    # Batch processing methods
    def add_batch_files(self):
        """Add files to batch processing list."""
        try:
            from tkinter import filedialog

            file_paths = filedialog.askopenfilenames(
                title="Select Documents for Batch Processing",
                filetypes=[
                    ("All Supported", "*.docx *.md *.txt *.html *.htm"),
                    ("Word Documents", "*.docx"),
                    ("Markdown Files", "*.md"),
                    ("Text Files", "*.txt"),
                    ("HTML Files", "*.html *.htm"),
                    ("All Files", "*.*"),
                ],
            )

            for file_path in file_paths:
                if file_path not in self.batch_files:
                    self.batch_files.append(file_path)

            self.update_batch_file_list()

        except Exception as e:
            self.show_error(f"Failed to add files: {str(e)}")

    def add_batch_folder(self):
        """Add all supported files from a folder to batch processing."""
        try:
            import os
            from tkinter import filedialog

            folder_path = filedialog.askdirectory(title="Select Folder with Documents")

            if folder_path:
                supported_extensions = {".docx", ".md", ".txt", ".html", ".htm"}

                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in supported_extensions):
                            file_path = os.path.join(root, file)
                            if file_path not in self.batch_files:
                                self.batch_files.append(file_path)

                self.update_batch_file_list()
                self.log_batch_message(
                    f"Added {len(self.batch_files)} files from folder: {folder_path}"
                )

        except Exception as e:
            self.show_error(f"Failed to add folder: {str(e)}")

    def clear_batch_files(self):
        """Clear all files from batch processing list."""
        self.batch_files.clear()
        self.update_batch_file_list()
        self.log_batch_message("Cleared all files from batch list")

    def update_batch_file_list(self):
        """Update the visual list of batch files."""
        # Clear existing list
        for widget in self.files_listbox.winfo_children():
            widget.destroy()

        # Add files to list
        for i, file_path in enumerate(self.batch_files):
            file_frame = ctk.CTkFrame(self.files_listbox, fg_color="transparent")
            file_frame.pack(fill="x", padx=5, pady=2)

            # File info
            import os

            filename = os.path.basename(file_path)

            file_label = ctk.CTkLabel(
                file_frame, text=f"📄 {filename}", font=ctk.CTkFont(size=11), anchor="w"
            )
            file_label.pack(side="left", fill="x", expand=True)

            # Remove button
            remove_btn = ctk.CTkButton(
                file_frame,
                text="✕",
                command=lambda idx=i: self.remove_batch_file(idx),
                width=30,
                height=20,
                corner_radius=10,
            )
            remove_btn.pack(side="right")

        # Update file count
        count_text = f"{len(self.batch_files)} files selected"
        if hasattr(self, "batch_progress_label"):
            self.batch_progress_label.configure(text=f"0 / {len(self.batch_files)} files completed")

    def remove_batch_file(self, index):
        """Remove a specific file from batch processing list."""
        if 0 <= index < len(self.batch_files):
            removed_file = self.batch_files.pop(index)
            self.update_batch_file_list()
            import os

            self.log_batch_message(f"Removed: {os.path.basename(removed_file)}")

    def browse_batch_output(self):
        """Browse for batch output directory."""
        try:
            from tkinter import filedialog

            directory = filedialog.askdirectory(
                title="Select Output Directory for Batch Processing"
            )

            if directory:
                self.batch_output_var.set(directory)

        except Exception as e:
            self.show_error(f"Failed to select output directory: {str(e)}")

    def start_batch_processing(self):
        """Start batch processing of all files."""
        if not self.batch_files:
            self.show_error("No files selected for batch processing.")
            return

        if not self.batch_author_var.get().strip():
            self.show_error("Please enter a common author name.")
            return

        if not self.batch_output_var.get().strip():
            self.show_error("Please select an output directory.")
            return

        # Reset batch state
        self.batch_state = {
            "running": True,
            "paused": False,
            "current_index": 0,
            "completed": 0,
            "failed": 0,
            "results": [],
        }

        # Update UI
        self.start_batch_btn.configure(state="disabled")
        self.pause_batch_btn.configure(state="normal")
        self.stop_batch_btn.configure(state="normal")

        # Start processing in background thread
        import threading

        thread = threading.Thread(target=self.batch_processing_worker)
        thread.daemon = True
        thread.start()

        self.log_batch_message(f"Started batch processing of {len(self.batch_files)} files")

    def pause_batch_processing(self):
        """Pause/resume batch processing."""
        if self.batch_state["running"]:
            self.batch_state["paused"] = not self.batch_state["paused"]

            if self.batch_state["paused"]:
                self.pause_batch_btn.configure(text="▶️ Resume")
                self.log_batch_message("Batch processing paused")
            else:
                self.pause_batch_btn.configure(text="⏸️ Pause")
                self.log_batch_message("Batch processing resumed")

    def stop_batch_processing(self):
        """Stop batch processing."""
        self.batch_state["running"] = False
        self.batch_state["paused"] = False

        # Update UI
        self.start_batch_btn.configure(state="normal", text="🚀 Start Batch Processing")
        self.pause_batch_btn.configure(state="disabled", text="⏸️ Pause")
        self.stop_batch_btn.configure(state="disabled")

        self.log_batch_message("Batch processing stopped")

    def batch_processing_worker(self):
        """Background worker for batch processing."""
        import os
        import time

        try:
            total_files = len(self.batch_files)

            for i, file_path in enumerate(self.batch_files):
                if not self.batch_state["running"]:
                    break

                # Wait if paused
                while self.batch_state["paused"] and self.batch_state["running"]:
                    time.sleep(0.1)

                if not self.batch_state["running"]:
                    break

                # Update current file
                filename = os.path.basename(file_path)
                self.root.after(
                    0, lambda f=filename: self.current_file_label.configure(text=f"Processing: {f}")
                )

                try:
                    # Generate title from filename
                    title = Path(file_path).stem.replace("-", " ").replace("_", " ").title()

                    # Generate output path
                    output_dir = self.batch_output_var.get()
                    if self.batch_keep_structure_var.get():
                        # Preserve folder structure
                        relative_path = os.path.relpath(os.path.dirname(file_path))
                        output_subdir = os.path.join(output_dir, relative_path)
                        os.makedirs(output_subdir, exist_ok=True)
                        output_path = os.path.join(output_subdir, f"{title}.epub")
                    else:
                        output_path = os.path.join(output_dir, f"{title}.epub")

                    # Check if file exists and overwrite setting
                    if os.path.exists(output_path) and not self.batch_overwrite_var.get():
                        result = {"file": filename, "status": "skipped", "reason": "File exists"}
                        self.batch_state["results"].append(result)
                        self.root.after(
                            0, lambda: self.log_batch_message(f"Skipped: {filename} (file exists)")
                        )
                        continue

                    # Process file
                    self.process_single_file(file_path, title, output_path)

                    # Success
                    result = {"file": filename, "status": "success", "output": output_path}
                    self.batch_state["results"].append(result)
                    self.batch_state["completed"] += 1

                    self.root.after(0, lambda: self.log_batch_message(f"✅ Completed: {filename}"))

                except Exception as e:
                    # Error
                    result = {"file": filename, "status": "error", "reason": str(e)}
                    self.batch_state["results"].append(result)
                    self.batch_state["failed"] += 1

                    self.root.after(
                        0,
                        lambda err=str(e): self.log_batch_message(f"❌ Failed: {filename} - {err}"),
                    )

                # Update progress
                progress = (i + 1) / total_files
                completed = self.batch_state["completed"]
                failed = self.batch_state["failed"]

                self.root.after(
                    0,
                    lambda p=progress, c=completed, f=failed, t=total_files: self.update_batch_progress(
                        p, c, f, t
                    ),
                )

        except Exception:
            self.root.after(
                0, lambda: self.log_batch_message(f"Critical error in batch processing: {str(e)}")
            )

        finally:
            # Processing complete
            self.root.after(0, self.batch_processing_complete)

    def process_single_file(self, file_path, title, output_path):
        """Process a single file for batch conversion."""
        import os

        # Create metadata
        metadata = EpubMetadata(
            title=title,
            author=self.batch_author_var.get().strip(),
            language="en",
            description=f"Generated from {os.path.basename(file_path)}",
        )

        # Create build options
        options = BuildOptions(
            use_ai_detection=self.batch_ai_detection_var.get(), theme="modern", include_toc=True
        )

        # Convert document
        chunks = docx_to_html_chunks(file_path)

        # Assemble EPUB
        assemble_epub(chunks, metadata, output_path, options)

    def update_batch_progress(self, progress, completed, failed, total):
        """Update batch progress indicators."""
        self.batch_progress_var.set(progress)
        self.batch_progress_label.configure(text=f"{completed + failed} / {total} files completed")

    def batch_processing_complete(self):
        """Handle batch processing completion."""
        self.stop_batch_processing()

        completed = self.batch_state["completed"]
        failed = self.batch_state["failed"]
        total = len(self.batch_files)

        # Update UI
        self.current_file_label.configure(text="Batch processing complete!")
        self.results_btn.pack(side="right", padx=(15, 0))

        # Show completion message
        message = f"Batch processing complete!\n\n✅ Completed: {completed}\n❌ Failed: {failed}\n📊 Total: {total}"
        self.log_batch_message(f"🎉 {message.replace(chr(10), ' ')}")

        if failed == 0:
            self.show_success(message)
        else:
            self.show_error(message)

    def show_batch_results(self):
        """Show detailed batch processing results."""
        results_window = ctk.CTkToplevel(self.root)
        results_window.title("📋 Batch Processing Results")
        results_window.geometry("600x500")
        results_window.transient(self.root)
        results_window.grab_set()

        # Results header
        header_label = ctk.CTkLabel(
            results_window,
            text="📋 Batch Processing Results",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        header_label.pack(pady=20)

        # Results list
        results_frame = ctk.CTkScrollableFrame(results_window)
        results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for result in self.batch_state["results"]:
            result_row = ctk.CTkFrame(results_frame)
            result_row.pack(fill="x", padx=5, pady=2)

            # Status icon
            if result["status"] == "success":
                icon = "✅"
                color = "#28a745"
            elif result["status"] == "error":
                icon = "❌"
                color = "#dc3545"
            else:  # skipped
                icon = "⏭️"
                color = "#ffc107"

            status_label = ctk.CTkLabel(
                result_row, text=icon, font=ctk.CTkFont(size=14), text_color=color
            )
            status_label.pack(side="left", padx=(10, 5))

            # File name
            file_label = ctk.CTkLabel(result_row, text=result["file"], font=ctk.CTkFont(size=12))
            file_label.pack(side="left", fill="x", expand=True, padx=5)

            # Status text
            if result["status"] == "success":
                status_text = "Completed"
            elif result["status"] == "error":
                status_text = f"Error: {result.get('reason', 'Unknown')}"
            else:
                status_text = f"Skipped: {result.get('reason', 'Unknown')}"

            status_detail = ctk.CTkLabel(result_row, text=status_text, font=ctk.CTkFont(size=10))
            status_detail.pack(side="right", padx=(5, 10))

        # Close button
        close_btn = ctk.CTkButton(
            results_window,
            text="✕ Close",
            command=results_window.destroy,
            height=40,
            corner_radius=20,
        )
        close_btn.pack(pady=20)

    def log_batch_message(self, message):
        """Add a message to the batch processing log."""
        import time

        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.batch_log.insert("end", log_entry)
        self.batch_log.see("end")

    def setup_themes_tab(self):
        """Setup the comprehensive themes management tab with genre themes and customization."""
        themes_frame = self.tabview.tab("🎨 Themes")

        # Create main container with two columns
        main_container = ctk.CTkFrame(themes_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Left column - Theme Browser
        left_column = ctk.CTkFrame(main_container, corner_radius=15)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Right column - Theme Editor & Font Manager
        right_column = ctk.CTkFrame(main_container, corner_radius=15)
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Left Column Content
        themes_header = ctk.CTkLabel(
            left_column, text="🎨 Theme Browser", font=ctk.CTkFont(size=18, weight="bold")
        )
        themes_header.pack(pady=(15, 10))

        # Theme category tabs
        self.theme_tabview = ctk.CTkTabview(left_column, corner_radius=10)
        self.theme_tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Add theme category tabs
        self.theme_tabview.add("📚 General")
        self.theme_tabview.add("🏰 Fiction")
        self.theme_tabview.add("📖 Non-Fiction")
        self.theme_tabview.add("♿ Accessibility")
        self.theme_tabview.add("💫 Custom")

        # Setup theme categories
        self.setup_general_themes()
        self.setup_fiction_themes()
        self.setup_nonfiction_themes()
        self.setup_accessibility_themes()
        self.setup_custom_themes()

        # Right Column Content - Theme Editor
        editor_header = ctk.CTkLabel(
            right_column, text="✨ Theme Customization", font=ctk.CTkFont(size=18, weight="bold")
        )
        editor_header.pack(pady=(15, 10))

        # Theme editor tabview
        self.editor_tabview = ctk.CTkTabview(right_column, corner_radius=10)
        self.editor_tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.editor_tabview.add("🎨 Editor")
        self.editor_tabview.add("🔤 Fonts")
        self.editor_tabview.add("💾 Manager")

        # Setup editor tabs
        self.setup_theme_editor()
        self.setup_font_manager()
        self.setup_theme_manager()

    def setup_general_themes(self):
        """Setup general purpose themes."""
        general_frame = self.theme_tabview.tab("📚 General")
        scrollable_general = ctk.CTkScrollableFrame(general_frame)
        scrollable_general.pack(fill="both", expand=True, padx=5, pady=5)

        general_themes = [
            (
                "serif",
                "Classic Serif",
                "Traditional serif fonts for timeless readability",
                "\ud83d\udcd6",
            ),
            (
                "sans",
                "Modern Sans",
                "Clean sans-serif fonts for contemporary works",
                "\ud83d\uddfa",
            ),
            (
                "printlike",
                "Print-like",
                "Newspaper-style theme optimized for print",
                "\ud83d\udcf0",
            ),
        ]

        for theme_id, name, desc, emoji in general_themes:
            self.create_theme_card(scrollable_general, theme_id, name, desc, emoji)

    def setup_fiction_themes(self):
        """Setup fiction genre themes."""
        fiction_frame = self.theme_tabview.tab("\ud83c\udff0 Fiction")
        scrollable_fiction = ctk.CTkScrollableFrame(fiction_frame)
        scrollable_fiction.pack(fill="both", expand=True, padx=5, pady=5)

        fiction_themes = [
            ("fantasy", "Fantasy Epic", "Magical styling with elegant serif fonts", "\ud83c\udff0"),
            ("romance", "Romance", "Warm, inviting theme perfect for love stories", "\ud83d\udc96"),
            (
                "mystery",
                "Mystery & Crime",
                "Dark, atmospheric styling for suspense",
                "\ud83d\udd75\ufe0f",
            ),
            (
                "scifi",
                "Science Fiction",
                "Futuristic theme with clean modern fonts",
                "\ud83d\ude80",
            ),
            ("thriller", "Thriller", "High-contrast theme for edge-of-seat tension", "\u26a1"),
            (
                "contemporary",
                "Contemporary Fiction",
                "Modern, clean styling for literary works",
                "\ud83c\udfe2",
            ),
        ]

        for theme_id, name, desc, emoji in fiction_themes:
            self.create_theme_card(scrollable_fiction, theme_id, name, desc, emoji)

    def setup_nonfiction_themes(self):
        """Setup non-fiction themes."""
        nonfiction_frame = self.theme_tabview.tab("\ud83d\udcd6 Non-Fiction")
        scrollable_nonfiction = ctk.CTkScrollableFrame(nonfiction_frame)
        scrollable_nonfiction.pack(fill="both", expand=True, padx=5, pady=5)

        nonfiction_themes = [
            ("academic", "Academic", "Professional styling for scholarly works", "\ud83c\udf93"),
            (
                "business",
                "Business",
                "Corporate-friendly theme for professional content",
                "\ud83d\udcbc",
            ),
            ("biography", "Biography", "Classic styling perfect for life stories", "\ud83d\udcdc"),
            (
                "childrens",
                "Children's Books",
                "Playful, readable theme for young readers",
                "\ud83d\udcda",
            ),
        ]

        for theme_id, name, desc, emoji in nonfiction_themes:
            self.create_theme_card(scrollable_nonfiction, theme_id, name, desc, emoji)

    def setup_accessibility_themes(self):
        """Setup accessibility-focused themes."""
        access_frame = self.theme_tabview.tab("\u267f Accessibility")
        scrollable_access = ctk.CTkScrollableFrame(access_frame)
        scrollable_access.pack(fill="both", expand=True, padx=5, pady=5)

        access_themes = [
            (
                "dyslexic",
                "Dyslexia-Friendly",
                "OpenDyslexic font with optimized spacing",
                "\ud83d\udde3\ufe0f",
            ),
            ("night", "Night Reading", "Dark theme with reduced eye strain", "\ud83c\udf19"),
        ]

        for theme_id, name, desc, emoji in access_themes:
            self.create_theme_card(scrollable_access, theme_id, name, desc, emoji)

    def setup_custom_themes(self):
        """Setup custom theme management."""
        custom_frame = self.theme_tabview.tab("\ud83d\udcab Custom")

        # Header
        header_label = ctk.CTkLabel(
            custom_frame, text="Your Custom Themes", font=ctk.CTkFont(size=14, weight="bold")
        )
        header_label.pack(pady=(10, 15))

        # Scrollable list of custom themes
        self.custom_themes_frame = ctk.CTkScrollableFrame(custom_frame)
        self.custom_themes_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Create new theme button
        create_btn = ctk.CTkButton(
            custom_frame,
            text="+ Create New Theme",
            command=self.create_new_theme,
            height=35,
            corner_radius=17,
        )
        create_btn.pack(pady=10)

        # Load existing custom themes
        self.load_custom_themes()

    def create_theme_card(self, parent, theme_id, name, description, emoji):
        """Create a theme card with preview and apply buttons."""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(fill="x", padx=5, pady=5)

        # Theme info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=10)

        # Title with emoji
        title_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_frame.pack(fill="x")

        emoji_label = ctk.CTkLabel(title_frame, text=emoji, font=ctk.CTkFont(size=16))
        emoji_label.pack(side="left")

        name_label = ctk.CTkLabel(title_frame, text=name, font=ctk.CTkFont(size=13, weight="bold"))
        name_label.pack(side="left", padx=(5, 0))

        desc_label = ctk.CTkLabel(
            info_frame, text=description, font=ctk.CTkFont(size=10), wraplength=200, anchor="w"
        )
        desc_label.pack(anchor="w", pady=(2, 0))

        # Action buttons
        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.pack(side="right", padx=10, pady=10)

        preview_btn = ctk.CTkButton(
            action_frame,
            text="\ud83d\udc41\ufe0f Preview",
            command=lambda: self.preview_theme(theme_id),
            width=70,
            height=25,
            corner_radius=12,
            font=ctk.CTkFont(size=10),
        )
        preview_btn.pack(side="left", padx=(0, 5))

        apply_btn = ctk.CTkButton(
            action_frame,
            text="\u2713 Apply",
            command=lambda: self.apply_theme(theme_id),
            width=60,
            height=25,
            corner_radius=12,
            font=ctk.CTkFont(size=10),
        )
        apply_btn.pack(side="right")

    def setup_theme_editor(self):
        """Setup the theme editor interface."""
        editor_frame = self.editor_tabview.tab("\ud83c\udfa8 Editor")

        # Theme editor scrollable frame
        editor_scroll = ctk.CTkScrollableFrame(editor_frame)
        editor_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Current theme display
        current_section = ctk.CTkFrame(editor_scroll, corner_radius=10)
        current_section.pack(fill="x", padx=5, pady=5)

        current_label = ctk.CTkLabel(
            current_section,
            text="Current Theme: Classic Serif",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        current_label.pack(pady=10)

        # Theme properties
        props_frame = ctk.CTkFrame(editor_scroll, corner_radius=10)
        props_frame.pack(fill="x", padx=5, pady=5)

        props_label = ctk.CTkLabel(
            props_frame,
            text="\u2699\ufe0f Theme Properties",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        props_label.pack(pady=(10, 5))

        # Font family selection
        font_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        font_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(font_frame, text="Font Family:").pack(side="left")
        self.font_family_var = ctk.StringVar(value="serif")
        font_menu = ctk.CTkOptionMenu(
            font_frame, variable=self.font_family_var, values=["serif", "sans-serif", "monospace"]
        )
        font_menu.pack(side="right", padx=10)

        # Font size
        size_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        size_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(size_frame, text="Base Font Size:").pack(side="left")
        self.font_size_var = ctk.StringVar(value="16px")
        size_entry = ctk.CTkEntry(size_frame, textvariable=self.font_size_var, width=60)
        size_entry.pack(side="right", padx=10)

        # Line height
        lh_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        lh_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(lh_frame, text="Line Height:").pack(side="left")
        self.line_height_var = ctk.StringVar(value="1.5")
        lh_entry = ctk.CTkEntry(lh_frame, textvariable=self.line_height_var, width=60)
        lh_entry.pack(side="right", padx=10)

        # Margins
        margin_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        margin_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(margin_frame, text="Page Margins:").pack(side="left")
        self.margin_var = ctk.StringVar(value="2em")
        margin_entry = ctk.CTkEntry(margin_frame, textvariable=self.margin_var, width=60)
        margin_entry.pack(side="right", padx=10)

        # Action buttons
        btn_frame = ctk.CTkFrame(props_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        preview_btn = ctk.CTkButton(
            btn_frame, text="\ud83d\udc41\ufe0f Preview Changes", command=self.preview_theme_changes
        )
        preview_btn.pack(side="left", padx=5)

        save_btn = ctk.CTkButton(
            btn_frame, text="\ud83d\udcbe Save as New Theme", command=self.save_custom_theme
        )
        save_btn.pack(side="right", padx=5)

    def setup_font_manager(self):
        """Setup the font embedding interface."""
        font_frame = self.editor_tabview.tab("\ud83d\udd24 Fonts")

        font_scroll = ctk.CTkScrollableFrame(font_frame)
        font_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Font embedding section
        embed_section = ctk.CTkFrame(font_scroll, corner_radius=10)
        embed_section.pack(fill="x", padx=5, pady=5)

        embed_label = ctk.CTkLabel(
            embed_section,
            text="\ud83d\udd24 Font Embedding",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        embed_label.pack(pady=(10, 5))

        # Font file selector
        file_frame = ctk.CTkFrame(embed_section, fg_color="transparent")
        file_frame.pack(fill="x", padx=10, pady=5)

        self.font_file_entry = ctk.CTkEntry(
            file_frame, placeholder_text="Select font file (.ttf, .otf, .woff)"
        )
        self.font_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_font_btn = ctk.CTkButton(
            file_frame, text="\ud83d\udcc1 Browse", command=self.browse_font_file, width=80
        )
        browse_font_btn.pack(side="right")

        # Font name
        name_frame = ctk.CTkFrame(embed_section, fg_color="transparent")
        name_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(name_frame, text="Font Name:").pack(side="left")
        self.font_name_var = ctk.StringVar()
        name_entry = ctk.CTkEntry(name_frame, textvariable=self.font_name_var)
        name_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # Subset options
        subset_frame = ctk.CTkFrame(embed_section, fg_color="transparent")
        subset_frame.pack(fill="x", padx=10, pady=5)

        self.subset_var = ctk.BooleanVar(value=True)
        subset_cb = ctk.CTkCheckBox(
            subset_frame,
            text="Subset font (recommended for smaller file size)",
            variable=self.subset_var,
        )
        subset_cb.pack()

        # Add font button
        add_font_btn = ctk.CTkButton(
            embed_section, text="+ Add Font to Collection", command=self.add_custom_font, height=35
        )
        add_font_btn.pack(pady=10)

        # Current fonts section
        current_section = ctk.CTkFrame(font_scroll, corner_radius=10)
        current_section.pack(fill="x", padx=5, pady=5)

        current_label = ctk.CTkLabel(
            current_section,
            text="\ud83d\udcda Embedded Fonts",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        current_label.pack(pady=(10, 5))

        # Fonts list
        self.fonts_list_frame = ctk.CTkFrame(current_section, fg_color="transparent")
        self.fonts_list_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.refresh_fonts_list()

    def setup_theme_manager(self):
        """Setup the theme management interface."""
        manager_frame = self.editor_tabview.tab("\ud83d\udcbe Manager")

        manager_scroll = ctk.CTkScrollableFrame(manager_frame)
        manager_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Import/Export section
        io_section = ctk.CTkFrame(manager_scroll, corner_radius=10)
        io_section.pack(fill="x", padx=5, pady=5)

        io_label = ctk.CTkLabel(
            io_section, text="\ud83d\udce6 Import/Export", font=ctk.CTkFont(size=14, weight="bold")
        )
        io_label.pack(pady=(10, 5))

        btn_frame = ctk.CTkFrame(io_section, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        import_btn = ctk.CTkButton(
            btn_frame, text="\ud83d\udce5 Import Theme", command=self.import_theme
        )
        import_btn.pack(side="left", padx=5)

        export_btn = ctk.CTkButton(
            btn_frame, text="\ud83d\udce4 Export Theme", command=self.export_theme
        )
        export_btn.pack(side="right", padx=5)

        # Theme backup section
        backup_section = ctk.CTkFrame(manager_scroll, corner_radius=10)
        backup_section.pack(fill="x", padx=5, pady=5)

        backup_label = ctk.CTkLabel(
            backup_section,
            text="\ud83d\udcbe Backup & Restore",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        backup_label.pack(pady=(10, 5))

        backup_btn_frame = ctk.CTkFrame(backup_section, fg_color="transparent")
        backup_btn_frame.pack(fill="x", padx=10, pady=10)

        backup_btn = ctk.CTkButton(
            backup_btn_frame, text="\ud83d\udcbe Create Backup", command=self.backup_themes
        )
        backup_btn.pack(side="left", padx=5)

        restore_btn = ctk.CTkButton(
            backup_btn_frame, text="\ud83d\udd04 Restore Backup", command=self.restore_themes
        )
        restore_btn.pack(side="right", padx=5)

    def setup_quality_tab(self):
        """Setup the quality analysis tab."""
        quality_frame = self.tabview.tab("🔍 Quality")

        # Create scrollable frame
        scrollable_quality = ctk.CTkScrollableFrame(quality_frame)
        scrollable_quality.pack(fill="both", expand=True, padx=10, pady=10)

        # Quality header
        quality_label = ctk.CTkLabel(
            scrollable_quality, text="🔍 Quality Analysis", font=ctk.CTkFont(size=20, weight="bold")
        )
        quality_label.pack(pady=(0, 20))

        # File input section
        input_section = ctk.CTkFrame(scrollable_quality, corner_radius=15)
        input_section.pack(fill="x", padx=5, pady=(0, 15))

        input_label = ctk.CTkLabel(
            input_section, text="📁 Select EPUB File", font=ctk.CTkFont(size=16, weight="bold")
        )
        input_label.pack(pady=(15, 10))

        input_content = ctk.CTkFrame(input_section, fg_color="transparent")
        input_content.pack(fill="x", padx=20, pady=(0, 20))

        file_row = ctk.CTkFrame(input_content, fg_color="transparent")
        file_row.pack(fill="x")

        self.quality_file_entry = ctk.CTkEntry(
            file_row,
            placeholder_text="Select an EPUB file to analyze...",
            height=40,
            font=ctk.CTkFont(size=12),
        )
        self.quality_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_quality_btn = ctk.CTkButton(
            file_row, text="📂 Browse", command=self.browse_epub_file, height=40, corner_radius=20
        )
        browse_quality_btn.pack(side="right")

        # Analysis results
        results_section = ctk.CTkFrame(scrollable_quality, corner_radius=15)
        results_section.pack(fill="both", expand=True, padx=5, pady=(0, 15))

        results_label = ctk.CTkLabel(
            results_section, text="📈 Analysis Results", font=ctk.CTkFont(size=16, weight="bold")
        )
        results_label.pack(pady=(15, 10))

        self.quality_results = ctk.CTkTextbox(
            results_section, height=300, font=ctk.CTkFont(size=11)
        )
        self.quality_results.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.quality_results.insert(
            "0.0", "No analysis performed yet. Select an EPUB file and click 'Analyze' to begin."
        )

        # Action buttons
        action_frame = ctk.CTkFrame(scrollable_quality, fg_color="transparent")
        action_frame.pack(fill="x", padx=5, pady=(0, 10))

        analyze_btn = ctk.CTkButton(
            action_frame,
            text="🔍 Analyze EPUB",
            command=self.analyze_epub_quality,
            height=45,
            corner_radius=22,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        analyze_btn.pack(side="left", padx=(0, 15))

        doctor_btn = ctk.CTkButton(
            action_frame,
            text="🩺 Run Doctor",
            command=self.run_system_doctor,
            height=45,
            corner_radius=22,
            font=ctk.CTkFont(size=14),
        )
        doctor_btn.pack(side="right")

    def setup_tools_tab(self):
        """Setup the tools management tab."""
        tools_frame = self.tabview.tab("🛠️ Tools")

        # Create scrollable frame
        scrollable_tools = ctk.CTkScrollableFrame(tools_frame)
        scrollable_tools.pack(fill="both", expand=True, padx=10, pady=10)

        # Tools header
        tools_label = ctk.CTkLabel(
            scrollable_tools, text="🛠️ Tool Management", font=ctk.CTkFont(size=20, weight="bold")
        )
        tools_label.pack(pady=(0, 20))

        # Tool status section
        status_section = ctk.CTkFrame(scrollable_tools, corner_radius=15)
        status_section.pack(fill="x", padx=5, pady=(0, 15))

        status_label = ctk.CTkLabel(
            status_section, text="🔍 Tool Status", font=ctk.CTkFont(size=16, weight="bold")
        )
        status_label.pack(pady=(15, 10))

        status_content = ctk.CTkFrame(status_section, fg_color="transparent")
        status_content.pack(fill="x", padx=20, pady=(0, 20))

        # Tool status display
        self.tool_status_frame = ctk.CTkFrame(status_content)
        self.tool_status_frame.pack(fill="x")

        # Tool output
        output_section = ctk.CTkFrame(scrollable_tools, corner_radius=15)
        output_section.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        output_label = ctk.CTkLabel(
            output_section, text="📜 Tool Output", font=ctk.CTkFont(size=16, weight="bold")
        )
        output_label.pack(pady=(15, 10))

        self.tool_output = ctk.CTkTextbox(
            output_section, height=200, font=ctk.CTkFont(size=10, family="Courier")
        )
        self.tool_output.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.tool_output.insert("0.0", "Tool management output will appear here...")

        # Refresh button
        refresh_btn = ctk.CTkButton(
            scrollable_tools,
            text="🔄 Refresh Tool Status",
            command=self.refresh_tool_status,
            height=40,
            corner_radius=20,
        )
        refresh_btn.pack(pady=10)

        # Initialize tool status
        self.refresh_tool_status()

    # Theme management methods
    def preview_theme(self, theme_name):
        """Preview a theme."""
        try:
            preview_window = ctk.CTkToplevel(self.root)
            preview_window.title(f"🎨 Preview: {theme_name}")
            preview_window.geometry("600x400")
            preview_window.transient(self.root)

            content = f"""Preview of {theme_name} Theme

This shows how your EPUB will look with this theme.

Chapter 1: Introduction
Lorem ipsum dolor sit amet, consectetur adipiscing elit.

Bold text and italic text examples.
• List item 1
• List item 2"""

            preview_text = ctk.CTkTextbox(preview_window, font=ctk.CTkFont(size=12))
            preview_text.pack(fill="both", expand=True, padx=20, pady=20)
            preview_text.insert("0.0", content)
            preview_text.configure(state="disabled")

        except Exception as e:
            self.show_error(f"Failed to preview theme: {str(e)}")

    def apply_theme(self, theme_name):
        """Apply a theme as the default."""
        try:
            self.css_theme.set(theme_name)
            self.show_success(f"Theme '{theme_name}' applied as default.")
        except Exception as e:
            self.show_error(f"Failed to apply theme: {str(e)}")

    # Quality analysis methods
    def browse_epub_file(self):
        """Browse for EPUB file to analyze."""
        try:
            from tkinter import filedialog

            file_path = filedialog.askopenfilename(
                title="Select EPUB File", filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
            )

            if file_path:
                self.quality_file_entry.delete(0, "end")
                self.quality_file_entry.insert(0, file_path)

        except Exception as e:
            self.show_error(f"Failed to select EPUB file: {str(e)}")

    def analyze_epub_quality(self):
        """Analyze EPUB file quality."""
        try:
            epub_path = self.quality_file_entry.get().strip()
            if not epub_path:
                self.show_error("Please select an EPUB file first.")
                return

            self.quality_results.delete("0.0", "end")
            self.quality_results.insert("0.0", "Analyzing EPUB file...\n\n")

            import threading

            thread = threading.Thread(target=self.quality_analysis_worker, args=(epub_path,))
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.show_error(f"Failed to start analysis: {str(e)}")

    def quality_analysis_worker(self, epub_path):
        """Background worker for quality analysis."""
        try:
            import os
            import zipfile

            results = []
            results.append("Quality Analysis Report")
            results.append(f"File: {os.path.basename(epub_path)}")
            results.append(f"Size: {os.path.getsize(epub_path) / 1024:.1f} KB")
            results.append("=" * 50)

            # Basic EPUB validation
            try:
                with zipfile.ZipFile(epub_path, "r") as epub_zip:
                    file_list = epub_zip.namelist()
                    results.append(f"✓ Valid ZIP structure ({len(file_list)} files)")

                    # Check required files
                    if "META-INF/container.xml" in file_list:
                        results.append("✓ Found container.xml")
                    else:
                        results.append("✗ Missing container.xml")

                    if "mimetype" in file_list:
                        results.append("✓ Found mimetype")
                    else:
                        results.append("✗ Missing mimetype")

                    # Count content
                    html_files = [f for f in file_list if f.endswith((".html", ".xhtml"))]
                    results.append(f"Content files: {len(html_files)}")

            except zipfile.BadZipFile:
                results.append("✗ Invalid ZIP file")

            results.append("\nAnalysis complete.")
            final_report = "\n".join(results)
            self.root.after(0, lambda: self.update_quality_results(final_report))

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            self.root.after(0, lambda: self.update_quality_results(error_msg))

    def update_quality_results(self, results):
        """Update quality analysis results in UI."""
        self.quality_results.delete("0.0", "end")
        self.quality_results.insert("0.0", results)

    def run_system_doctor(self):
        """Run system diagnostics."""
        try:
            self.quality_results.delete("0.0", "end")
            self.quality_results.insert("0.0", "Running system diagnostics...\n\n")

            import threading

            thread = threading.Thread(target=self.doctor_worker)
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.show_error(f"Failed to run doctor: {str(e)}")

    def doctor_worker(self):
        """Background worker for system doctor."""
        try:
            import platform
            import sys
            from datetime import datetime

            results = []
            results.append("System Diagnostics Report")
            results.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            results.append("=" * 40)

            # System info
            results.append(f"Platform: {platform.system()} {platform.release()}")
            results.append(f"Python: {sys.version.split()[0]}")

            # Check dependencies
            packages = ["customtkinter", "ebooklib", "platformdirs"]
            for package in packages:
                try:
                    __import__(package)
                    results.append(f"✓ {package} - installed")
                except ImportError:
                    results.append(f"✗ {package} - missing")

            results.append("\nDiagnostics complete.")
            final_report = "\n".join(results)
            self.root.after(0, lambda: self.update_quality_results(final_report))

        except Exception as e:
            error_msg = f"Doctor failed: {str(e)}"
            self.root.after(0, lambda: self.update_quality_results(error_msg))

    # Tool management methods
    def refresh_tool_status(self):
        """Refresh the status of all tools."""
        try:
            # Clear existing status
            for widget in self.tool_status_frame.winfo_children():
                widget.destroy()

            # Check tool status
            tools = ["pandoc", "epubcheck"]

            for tool in tools:
                status_row = ctk.CTkFrame(self.tool_status_frame)
                status_row.pack(fill="x", pady=2)

                tool_label = ctk.CTkLabel(
                    status_row, text=tool.title(), font=ctk.CTkFont(size=12, weight="bold")
                )
                tool_label.pack(side="left", padx=15, pady=5)

                # Check availability
                try:
                    import subprocess

                    result = subprocess.run(
                        [tool, "--version"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        status_text = "✓ Available"
                        status_color = "green"
                    else:
                        status_text = "✗ Not working"
                        status_color = "red"
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    status_text = "✗ Not found"
                    status_color = "red"

                status_label = ctk.CTkLabel(
                    status_row, text=status_text, text_color=status_color, font=ctk.CTkFont(size=12)
                )
                status_label.pack(side="right", padx=15, pady=5)

        except Exception as e:
            self.tool_output.delete("0.0", "end")
            self.tool_output.insert("0.0", f"Error checking tools: {str(e)}")

    def setup_wizard_tab(self):
        """Setup the interactive conversion wizard tab."""
        wizard_frame = self.tabview.tab("🧙 Wizard")

        # Create scrollable frame
        scrollable_wizard = ctk.CTkScrollableFrame(wizard_frame)
        scrollable_wizard.pack(fill="both", expand=True, padx=10, pady=10)

        # Wizard header
        wizard_label = ctk.CTkLabel(
            scrollable_wizard,
            text="🧙 Interactive Conversion Wizard",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        wizard_label.pack(pady=(0, 20))

        # Step indicator
        steps_section = ctk.CTkFrame(scrollable_wizard, corner_radius=15)
        steps_section.pack(fill="x", padx=5, pady=(0, 15))

        steps_label = ctk.CTkLabel(
            steps_section, text="📋 Conversion Steps", font=ctk.CTkFont(size=16, weight="bold")
        )
        steps_label.pack(pady=(15, 10))

        # Step progress
        self.wizard_steps = [
            "1. Select Document",
            "2. Enter Metadata",
            "3. Choose Options",
            "4. Review Settings",
            "5. Convert",
        ]

        self.current_step = 0
        self.step_labels = []

        steps_content = ctk.CTkFrame(steps_section, fg_color="transparent")
        steps_content.pack(fill="x", padx=20, pady=(0, 20))

        for i, step in enumerate(self.wizard_steps):
            step_frame = ctk.CTkFrame(steps_content, fg_color="transparent")
            step_frame.pack(fill="x", pady=2)

            # Step indicator
            if i == 0:
                indicator = "▶️"
                color = ("blue", "lightblue")
            else:
                indicator = "⭕"
                color = ("gray", "lightgray")

            step_label = ctk.CTkLabel(
                step_frame, text=f"{indicator} {step}", font=ctk.CTkFont(size=12), text_color=color
            )
            step_label.pack(anchor="w")
            self.step_labels.append(step_label)

        # Current step content
        content_section = ctk.CTkFrame(scrollable_wizard, corner_radius=15)
        content_section.pack(fill="both", expand=True, padx=5, pady=(0, 15))

        self.wizard_content_label = ctk.CTkLabel(
            content_section,
            text="Step 1: Select Document",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.wizard_content_label.pack(pady=(15, 10))

        # Dynamic content area
        self.wizard_content_frame = ctk.CTkFrame(content_section, fg_color="transparent")
        self.wizard_content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Navigation buttons
        nav_frame = ctk.CTkFrame(scrollable_wizard, fg_color="transparent")
        nav_frame.pack(fill="x", padx=5, pady=(0, 10))

        self.wizard_back_btn = ctk.CTkButton(
            nav_frame,
            text="⬅️ Back",
            command=self.wizard_back,
            height=40,
            corner_radius=20,
            state="disabled",
        )
        self.wizard_back_btn.pack(side="left")

        self.wizard_next_btn = ctk.CTkButton(
            nav_frame, text="Next ➡️", command=self.wizard_next, height=40, corner_radius=20
        )
        self.wizard_next_btn.pack(side="right")

        # Initialize wizard
        self.setup_wizard_step()

    def setup_wizard_step(self):
        """Setup the current wizard step."""
        # Clear previous content
        for widget in self.wizard_content_frame.winfo_children():
            widget.destroy()

        # Update step indicator
        for i, label in enumerate(self.step_labels):
            if i == self.current_step:
                label.configure(text=f"▶️ {self.wizard_steps[i]}", text_color=("blue", "lightblue"))
            elif i < self.current_step:
                label.configure(
                    text=f"✅ {self.wizard_steps[i]}", text_color=("green", "lightgreen")
                )
            else:
                label.configure(text=f"⭕ {self.wizard_steps[i]}", text_color=("gray", "lightgray"))

        # Update navigation buttons
        self.wizard_back_btn.configure(state="normal" if self.current_step > 0 else "disabled")

        if self.current_step == 0:
            self.setup_wizard_file_step()
        elif self.current_step == 1:
            self.setup_wizard_metadata_step()
        elif self.current_step == 2:
            self.setup_wizard_options_step()
        elif self.current_step == 3:
            self.setup_wizard_review_step()
        elif self.current_step == 4:
            self.setup_wizard_convert_step()

    def setup_wizard_file_step(self):
        """Setup file selection step."""
        self.wizard_content_label.configure(text="Step 1: Select Your Document")

        instruction = ctk.CTkLabel(
            self.wizard_content_frame,
            text="Choose the document you want to convert to EPUB.\nSupported formats: DOCX, Markdown, TXT, HTML",
            font=ctk.CTkFont(size=12),
        )
        instruction.pack(pady=10)

        # File input
        file_frame = ctk.CTkFrame(self.wizard_content_frame)
        file_frame.pack(fill="x", pady=10)

        self.wizard_file_entry = ctk.CTkEntry(
            file_frame,
            placeholder_text="Select a document file...",
            height=40,
            font=ctk.CTkFont(size=12),
        )
        self.wizard_file_entry.pack(side="left", fill="x", expand=True, padx=(15, 10), pady=15)

        wizard_browse_btn = ctk.CTkButton(
            file_frame,
            text="📂 Browse",
            command=self.wizard_browse_file,
            height=40,
            corner_radius=20,
        )
        wizard_browse_btn.pack(side="right", padx=(0, 15), pady=15)

        # Copy from main tab if file is already selected
        if hasattr(self, "current_file") and self.current_file:
            self.wizard_file_entry.insert(0, self.current_file)

    def setup_wizard_metadata_step(self):
        """Setup metadata entry step."""
        self.wizard_content_label.configure(text="Step 2: Enter Book Information")

        instruction = ctk.CTkLabel(
            self.wizard_content_frame,
            text="Fill in the details about your book. Title and Author are required.",
            font=ctk.CTkFont(size=12),
        )
        instruction.pack(pady=10)

        # Metadata form
        form_frame = ctk.CTkFrame(self.wizard_content_frame)
        form_frame.pack(fill="x", pady=10, padx=20)

        # Title
        ctk.CTkLabel(form_frame, text="📖 Title *", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=15, pady=(15, 5)
        )
        self.wizard_title_entry = ctk.CTkEntry(
            form_frame, placeholder_text="Enter book title...", height=35
        )
        self.wizard_title_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Author
        ctk.CTkLabel(form_frame, text="✍️ Author *", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=15, pady=(0, 5)
        )
        self.wizard_author_entry = ctk.CTkEntry(
            form_frame, placeholder_text="Enter author name...", height=35
        )
        self.wizard_author_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Language and Genre
        lang_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        lang_frame.pack(fill="x", padx=15, pady=(0, 10))

        lang_col = ctk.CTkFrame(lang_frame, fg_color="transparent")
        lang_col.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(lang_col, text="🌍 Language", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w"
        )
        self.wizard_language_combo = ctk.CTkComboBox(
            lang_col, values=["English", "Spanish", "French", "German", "Italian"], height=35
        )
        self.wizard_language_combo.pack(fill="x", pady=(5, 0))
        self.wizard_language_combo.set("English")

        genre_col = ctk.CTkFrame(lang_frame, fg_color="transparent")
        genre_col.pack(side="right", fill="x", expand=True, padx=(10, 0))
        ctk.CTkLabel(genre_col, text="🏷️ Genre", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w"
        )
        self.wizard_genre_entry = ctk.CTkEntry(
            genre_col, placeholder_text="e.g., Fantasy, Romance...", height=35
        )
        self.wizard_genre_entry.pack(fill="x", pady=(5, 0))

        # Description
        ctk.CTkLabel(
            form_frame, text="📝 Description", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        self.wizard_description_text = ctk.CTkTextbox(form_frame, height=80)
        self.wizard_description_text.pack(fill="x", padx=15, pady=(0, 15))

    def setup_wizard_options_step(self):
        """Setup conversion options step."""
        self.wizard_content_label.configure(text="Step 3: Choose Conversion Options")

        instruction = ctk.CTkLabel(
            self.wizard_content_frame,
            text="Select how you want your EPUB to be created.",
            font=ctk.CTkFont(size=12),
        )
        instruction.pack(pady=10)

        options_frame = ctk.CTkFrame(self.wizard_content_frame)
        options_frame.pack(fill="x", pady=10, padx=20)

        # Theme selection
        ctk.CTkLabel(
            options_frame, text="🎨 CSS Theme", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        self.wizard_css_theme = ctk.CTkSegmentedButton(
            options_frame, values=["Serif", "Sans-serif", "Print-like"]
        )
        self.wizard_css_theme.pack(fill="x", padx=15, pady=(0, 15))
        self.wizard_css_theme.set("Serif")

        # Options checkboxes
        self.wizard_include_toc = ctk.CTkCheckBox(
            options_frame, text="📋 Include Table of Contents"
        )
        self.wizard_include_toc.pack(anchor="w", padx=15, pady=2)
        self.wizard_include_toc.select()

        self.wizard_ai_detection = ctk.CTkCheckBox(options_frame, text="🤖 AI Chapter Detection")
        self.wizard_ai_detection.pack(anchor="w", padx=15, pady=2)

        self.wizard_validate_epub = ctk.CTkCheckBox(options_frame, text="✅ Validate EPUB Output")
        self.wizard_validate_epub.pack(anchor="w", padx=15, pady=(2, 15))
        self.wizard_validate_epub.select()

    def setup_wizard_review_step(self):
        """Setup review settings step."""
        self.wizard_content_label.configure(text="Step 4: Review Your Settings")

        instruction = ctk.CTkLabel(
            self.wizard_content_frame,
            text="Please review your settings before conversion.",
            font=ctk.CTkFont(size=12),
        )
        instruction.pack(pady=10)

        review_frame = ctk.CTkFrame(self.wizard_content_frame)
        review_frame.pack(fill="both", expand=True, pady=10)

        # Review content
        self.wizard_review_text = ctk.CTkTextbox(review_frame, height=200)
        self.wizard_review_text.pack(fill="both", expand=True, padx=15, pady=15)

        # Generate review content
        self.update_wizard_review()

    def setup_wizard_convert_step(self):
        """Setup final conversion step."""
        self.wizard_content_label.configure(text="Step 5: Convert to EPUB")

        instruction = ctk.CTkLabel(
            self.wizard_content_frame,
            text="Ready to convert your document to EPUB!",
            font=ctk.CTkFont(size=12),
        )
        instruction.pack(pady=10)

        convert_frame = ctk.CTkFrame(self.wizard_content_frame)
        convert_frame.pack(fill="x", pady=10)

        # Progress
        self.wizard_progress_label = ctk.CTkLabel(
            convert_frame, text="Ready to convert", font=ctk.CTkFont(size=14)
        )
        self.wizard_progress_label.pack(pady=(15, 5))

        self.wizard_progress_bar = ctk.CTkProgressBar(convert_frame, height=20)
        self.wizard_progress_bar.pack(fill="x", padx=15, pady=(0, 15))
        self.wizard_progress_bar.set(0)

        # Update navigation for final step
        self.wizard_next_btn.configure(text="🚀 Convert", command=self.wizard_convert)

    def wizard_browse_file(self):
        """Browse for file in wizard."""
        try:
            from tkinter import filedialog

            file_path = filedialog.askopenfilename(
                title="Select Document File",
                filetypes=[
                    ("Word Documents", "*.docx"),
                    ("Markdown files", "*.md"),
                    ("Text files", "*.txt"),
                    ("HTML files", "*.html;*.htm"),
                    ("All files", "*.*"),
                ],
            )
            if file_path:
                self.wizard_file_entry.delete(0, "end")
                self.wizard_file_entry.insert(0, file_path)
        except Exception as e:
            self.show_error(f"Failed to select file: {str(e)}")

    def wizard_next(self):
        """Go to next wizard step."""
        if self.current_step < len(self.wizard_steps) - 1:
            # Validate current step
            if self.validate_wizard_step():
                self.current_step += 1
                self.setup_wizard_step()

    def wizard_back(self):
        """Go to previous wizard step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.setup_wizard_step()

    def validate_wizard_step(self):
        """Validate current wizard step."""
        if self.current_step == 0:  # File selection
            if not hasattr(self, "wizard_file_entry") or not self.wizard_file_entry.get().strip():
                self.show_error("Please select a document file.")
                return False
        elif self.current_step == 1:  # Metadata
            if not self.wizard_title_entry.get().strip():
                self.show_error("Please enter a title.")
                return False
            if not self.wizard_author_entry.get().strip():
                self.show_error("Please enter an author name.")
                return False
        return True

    def update_wizard_review(self):
        """Update the review text with current settings."""
        try:
            review_text = "Conversion Settings Review\n"
            review_text += "=" * 30 + "\n\n"

            review_text += (
                f"📁 Input File: {getattr(self, 'wizard_file_entry', {}).get() or 'Not selected'}\n"
            )
            review_text += (
                f"📖 Title: {getattr(self, 'wizard_title_entry', {}).get() or 'Not set'}\n"
            )
            review_text += (
                f"✍️ Author: {getattr(self, 'wizard_author_entry', {}).get() or 'Not set'}\n"
            )
            review_text += (
                f"🌍 Language: {getattr(self, 'wizard_language_combo', {}).get() or 'English'}\n"
            )
            review_text += (
                f"🏷️ Genre: {getattr(self, 'wizard_genre_entry', {}).get() or 'Not specified'}\n\n"
            )

            review_text += f"🎨 Theme: {getattr(self, 'wizard_css_theme', {}).get() or 'Serif'}\n"
            review_text += f"📋 Table of Contents: {'Yes' if getattr(self, 'wizard_include_toc', {}).get() else 'No'}\n"
            review_text += f"🤖 AI Detection: {'Yes' if getattr(self, 'wizard_ai_detection', {}).get() else 'No'}\n"
            review_text += f"✅ Validate EPUB: {'Yes' if getattr(self, 'wizard_validate_epub', {}).get() else 'No'}\n\n"

            desc = getattr(self, "wizard_description_text", {}).get("0.0", "end") or ""
            if desc.strip():
                review_text += f"📝 Description:\n{desc.strip()}\n"

            self.wizard_review_text.delete("0.0", "end")
            self.wizard_review_text.insert("0.0", review_text)
        except Exception as e:
            self.wizard_review_text.delete("0.0", "end")
            self.wizard_review_text.insert("0.0", f"Error generating review: {str(e)}")

    def wizard_convert(self):
        """Start conversion from wizard."""
        try:
            # Copy wizard values to main form
            if hasattr(self, "wizard_file_entry"):
                self.current_file = self.wizard_file_entry.get()
                self.file_entry.delete(0, "end")
                self.file_entry.insert(0, self.current_file)

            if hasattr(self, "wizard_title_entry"):
                self.title_entry.delete(0, "end")
                self.title_entry.insert(0, self.wizard_title_entry.get())

            if hasattr(self, "wizard_author_entry"):
                self.author_entry.delete(0, "end")
                self.author_entry.insert(0, self.wizard_author_entry.get())

            if hasattr(self, "wizard_language_combo"):
                self.language_combo.set(self.wizard_language_combo.get())

            if hasattr(self, "wizard_genre_entry"):
                self.genre_entry.delete(0, "end")
                self.genre_entry.insert(0, self.wizard_genre_entry.get())

            if hasattr(self, "wizard_description_text"):
                desc = self.wizard_description_text.get("0.0", "end").strip()
                self.description_text.delete("0.0", "end")
                self.description_text.insert("0.0", desc)

            if hasattr(self, "wizard_css_theme"):
                self.css_theme.set(self.wizard_css_theme.get())

            if hasattr(self, "wizard_include_toc"):
                if self.wizard_include_toc.get():
                    self.include_toc.select()
                else:
                    self.include_toc.deselect()

            if hasattr(self, "wizard_ai_detection"):
                if self.wizard_ai_detection.get():
                    self.ai_detection.select()
                else:
                    self.ai_detection.deselect()

            if hasattr(self, "wizard_validate_epub"):
                if self.wizard_validate_epub.get():
                    self.validate_epub.select()
                else:
                    self.validate_epub.deselect()

            # Start conversion using the main conversion worker
            self.start_conversion()

            # Show success message
            self.show_success("Conversion started! Check the Convert tab for progress.")

        except Exception as e:
            self.show_error(f"Failed to start conversion: {str(e)}")

    def show_error(self, message):
        """Show error message."""
        error_window = ctk.CTkToplevel(self.root)
        error_window.title("❌ Error")
        error_window.geometry("400x200")
        error_window.transient(self.root)
        error_window.grab_set()

        error_label = ctk.CTkLabel(
            error_window, text="❌ Error", font=ctk.CTkFont(size=18, weight="bold")
        )
        error_label.pack(pady=20)

        message_label = ctk.CTkLabel(
            error_window, text=message, font=ctk.CTkFont(size=12), wraplength=350
        )
        message_label.pack(padx=20, pady=10)

        ok_btn = ctk.CTkButton(
            error_window, text="OK", command=error_window.destroy, height=35, corner_radius=17
        )
        ok_btn.pack(pady=20)

    def show_update_downloading(self):
        """Show downloading update dialog."""
        self.download_dialog = ctk.CTkToplevel(self.root)
        self.download_dialog.title("🔽 Downloading Update")
        self.download_dialog.geometry("400x150")
        self.download_dialog.transient(self.root)
        self.download_dialog.grab_set()

        # Center the dialog
        self.download_dialog.update_idletasks()
        x = (self.download_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.download_dialog.winfo_screenheight() // 2) - (150 // 2)
        self.download_dialog.geometry(f"400x150+{x}+{y}")

        ctk.CTkLabel(
            self.download_dialog,
            text="🔽 Downloading Update...",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=20)

        # Progress bar
        progress = ctk.CTkProgressBar(self.download_dialog, mode="indeterminate")
        progress.pack(pady=10, padx=40, fill="x")
        progress.start()

        ctk.CTkLabel(
            self.download_dialog,
            text="Please wait while the update is downloaded and installed...",
            font=ctk.CTkFont(size=12),
        ).pack(pady=10)

    def show_update_success(self):
        """Show update success dialog."""
        if hasattr(self, "download_dialog"):
            self.download_dialog.destroy()

        success_window = ctk.CTkToplevel(self.root)
        success_window.title("✅ Update Complete")
        success_window.geometry("400x200")
        success_window.transient(self.root)
        success_window.grab_set()

        success_label = ctk.CTkLabel(
            success_window, text="🎉 Update Installed!", font=ctk.CTkFont(size=18, weight="bold")
        )
        success_label.pack(pady=20)

        message_label = ctk.CTkLabel(
            success_window,
            text="The update has been successfully installed.\n\nPlease restart Docx2Shelf to use the new version.",
            font=ctk.CTkFont(size=12),
            wraplength=350,
        )
        message_label.pack(padx=20, pady=10)

        restart_btn = ctk.CTkButton(
            success_window,
            text="🔄 Restart Now",
            command=self.restart_application,
            height=35,
            corner_radius=17,
        )
        restart_btn.pack(side="left", padx=(80, 10), pady=20)

        later_btn = ctk.CTkButton(
            success_window,
            text="⏰ Later",
            command=success_window.destroy,
            height=35,
            corner_radius=17,
        )
        later_btn.pack(side="right", padx=(10, 80), pady=20)

    def show_update_manual(self, download_url):
        """Show manual update dialog."""
        if hasattr(self, "download_dialog"):
            self.download_dialog.destroy()

        import webbrowser

        manual_window = ctk.CTkToplevel(self.root)
        manual_window.title("🔗 Manual Update Required")
        manual_window.geometry("450x200")
        manual_window.transient(self.root)
        manual_window.grab_set()

        header_label = ctk.CTkLabel(
            manual_window,
            text="🔗 Manual Update Required",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header_label.pack(pady=20)

        message_label = ctk.CTkLabel(
            manual_window,
            text="Automatic update failed. Please download and install the update manually.",
            font=ctk.CTkFont(size=12),
            wraplength=400,
        )
        message_label.pack(padx=20, pady=10)

        button_frame = ctk.CTkFrame(manual_window, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        open_btn = ctk.CTkButton(
            button_frame,
            text="🌐 Open Download Page",
            command=lambda: webbrowser.open(download_url),
            height=35,
            corner_radius=17,
        )
        open_btn.pack(side="left", padx=(0, 10))

        close_btn = ctk.CTkButton(
            button_frame, text="✖ Close", command=manual_window.destroy, height=35, corner_radius=17
        )
        close_btn.pack(side="right")

    def restart_application(self):
        """Restart the application."""
        import subprocess
        import sys

        try:
            # Close current application
            self.root.destroy()

            # Restart using the same command
            if hasattr(sys, "frozen"):
                # Running as executable
                subprocess.Popen([sys.executable] + sys.argv[1:])
            else:
                # Running as script
                subprocess.Popen([sys.executable, "-m", "docx2shelf.gui.modern_app"])
        except Exception as e:
            print(f"Failed to restart application: {e}")

        sys.exit(0)

    def browse_output_directory(self):
        """Browse for default output directory."""
        try:
            from tkinter import filedialog

            directory = filedialog.askdirectory(title="Select Default Output Directory")

            if directory:
                self.output_dir_var.set(directory)

        except Exception as e:
            self.show_error(f"Failed to select directory: {str(e)}")

    def show_success(self, message):
        """Show success message."""
        success_window = ctk.CTkToplevel(self.root)
        success_window.title("✅ Success")
        success_window.geometry("400x200")
        success_window.transient(self.root)
        success_window.grab_set()

        success_label = ctk.CTkLabel(
            success_window, text="✅ Success", font=ctk.CTkFont(size=18, weight="bold")
        )
        success_label.pack(pady=20)

        message_label = ctk.CTkLabel(
            success_window, text=message, font=ctk.CTkFont(size=12), wraplength=350
        )
        message_label.pack(padx=20, pady=10)

        ok_btn = ctk.CTkButton(
            success_window, text="OK", command=success_window.destroy, height=35, corner_radius=17
        )
        ok_btn.pack(pady=20)

    def show_success_with_open_option(self, message, file_path=None):
        """Show success message with option to open file."""
        success_window = ctk.CTkToplevel(self.root)
        success_window.title("✅ Success")
        success_window.geometry("450x250")
        success_window.transient(self.root)
        success_window.grab_set()

        success_label = ctk.CTkLabel(
            success_window, text="✅ Success", font=ctk.CTkFont(size=18, weight="bold")
        )
        success_label.pack(pady=20)

        message_label = ctk.CTkLabel(
            success_window, text=message, font=ctk.CTkFont(size=12), wraplength=400
        )
        message_label.pack(padx=20, pady=10)

        button_frame = ctk.CTkFrame(success_window, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        if file_path:
            import os
            import platform
            import subprocess

            def open_file():
                try:
                    if platform.system() == "Windows":
                        os.startfile(file_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", file_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", file_path])
                except Exception as e:
                    self.show_error(f"Failed to open file: {str(e)}")
                success_window.destroy()

            def open_folder():
                try:
                    folder_path = os.path.dirname(file_path)
                    if platform.system() == "Windows":
                        os.startfile(folder_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", folder_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", folder_path])
                except Exception as e:
                    self.show_error(f"Failed to open folder: {str(e)}")
                success_window.destroy()

            open_file_btn = ctk.CTkButton(
                button_frame, text="📄 Open EPUB", command=open_file, height=35, corner_radius=17
            )
            open_file_btn.pack(side="left", padx=(0, 10))

            open_folder_btn = ctk.CTkButton(
                button_frame,
                text="📁 Open Folder",
                command=open_folder,
                height=35,
                corner_radius=17,
            )
            open_folder_btn.pack(side="left", padx=(0, 10))

        ok_btn = ctk.CTkButton(
            button_frame, text="OK", command=success_window.destroy, height=35, corner_radius=17
        )
        ok_btn.pack(side="right")

    def check_for_updates_on_startup(self):
        """Check for updates on startup if enabled in settings."""
        try:
            # Only check if auto-update checking is enabled
            if hasattr(self, "updates_var") and self.updates_var.get():
                import threading

                def startup_update_check():
                    try:
                        from ..update import check_for_updates as check_updates

                        result = check_updates()
                        if result and result.get("update_available"):
                            # Show non-intrusive update notification
                            self.root.after(
                                0, lambda: self.show_startup_update_notification(result)
                            )
                    except Exception:
                        # Silently fail for startup checks
                        pass

                thread = threading.Thread(target=startup_update_check)
                thread.daemon = True
                thread.start()
        except Exception:
            # Silently fail for startup checks
            pass

    def show_startup_update_notification(self, update_info):
        """Show a non-intrusive update notification."""
        latest_version = update_info.get("latest_version", "Unknown")

        # Create a small notification at the top of the window
        notification = ctk.CTkFrame(
            self.root, height=40, corner_radius=0, fg_color=("#e3f2fd", "#1565c0")
        )
        notification.pack(fill="x", side="top", before=self.tabview.master)
        notification.pack_propagate(False)

        message_frame = ctk.CTkFrame(notification, fg_color="transparent")
        message_frame.pack(expand=True, fill="both")

        update_label = ctk.CTkLabel(
            message_frame,
            text=f"🎆 Update available: v{latest_version}",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        update_label.pack(side="left", padx=20, pady=10)

        button_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=20, pady=5)

        update_btn = ctk.CTkButton(
            button_frame,
            text="Update",
            command=lambda: self.handle_startup_update(update_info, notification),
            height=25,
            width=70,
            corner_radius=12,
            font=ctk.CTkFont(size=10),
        )
        update_btn.pack(side="left", padx=(0, 5))

        dismiss_btn = ctk.CTkButton(
            button_frame,
            text="✖",
            command=lambda: notification.destroy(),
            height=25,
            width=25,
            corner_radius=12,
            font=ctk.CTkFont(size=10),
        )
        dismiss_btn.pack(side="right")

    def handle_startup_update(self, update_info, notification):
        """Handle update from startup notification."""
        notification.destroy()

        # Show full update dialog
        try:
            from ..version import get_version

            current_version = get_version()
        except Exception:
            current_version = "unknown"

        latest_version = update_info.get("latest_version", "Unknown")
        download_url = update_info.get("download_url", "")
        installer_name = update_info.get("installer_name", "installer")
        changelog = update_info.get("changelog", "No changelog available.")

        self.show_update_available(
            current_version, latest_version, changelog, download_url, installer_name
        )

    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    """Main entry point for the modern GUI."""
    if not MODERN_GUI_AVAILABLE:
        print("Error: CustomTkinter is not installed.")
        print("Please install it with: pip install customtkinter")
        return 1

    try:
        app = ModernDocx2ShelfApp()
        app.run()
        return 0
    except Exception as e:
        print(f"Error running modern GUI: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
