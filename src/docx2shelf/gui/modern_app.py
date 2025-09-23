"""
Modern Docx2Shelf GUI using CustomTkinter for true rounded corners and modern appearance.
This is a modernized version that addresses tkinter's limitations.
"""

import sys
import threading
from pathlib import Path
from typing import List

try:
    import customtkinter as ctk
    MODERN_GUI_AVAILABLE = True
except ImportError:
    MODERN_GUI_AVAILABLE = False
    print("CustomTkinter not available. Install with: pip install customtkinter")

# Import core functionality
from ..assemble import assemble_epub
from ..convert import docx_to_html_chunks
from ..metadata import EpubMetadata, BuildOptions
from ..settings import get_settings_manager
from ..update import check_for_updates as check_updates, perform_update

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
        self.root.title("Docx2Shelf - Modern GUI")
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

    def set_window_icon(self):
        """Set window icon if available."""
        try:
            from pathlib import Path

            # Try different icon locations
            icon_paths = [
                Path(__file__).parent / "assets" / "icon.ico",
                Path(__file__).parent.parent / "assets" / "icon.ico",
                Path(__file__).parent / "assets" / "docx2shelf.ico"
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
            # Fallback to emoji in title
            self.root.title("📖 Docx2Shelf - Modern GUI")

    def create_text_icon(self):
        """Create a simple text-based icon using PIL."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import tempfile
            import os

            # Create a simple icon with "D2S" text
            size = (32, 32)
            image = Image.new('RGBA', size, (0, 120, 204, 255))  # Blue background
            draw = ImageDraw.Draw(image)

            # Try to use a system font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                try:
                    font = ImageFont.truetype("calibri.ttf", 14)
                except:
                    font = ImageFont.load_default()

            # Draw "D2S" text in white
            text = "D2S"
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

        title_label = ctk.CTkLabel(title_frame, text="📖 Docx2Shelf",
                                 font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(side="left")

        version_label = ctk.CTkLabel(title_frame, text="v1.6.3",
                                   font=ctk.CTkFont(size=14))
        version_label.pack(side="left", padx=(10, 0))

        # Theme controls
        theme_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        theme_frame.pack(side="right", padx=20, pady=20)

        theme_label = ctk.CTkLabel(theme_frame, text="Theme:")
        theme_label.pack(side="left", padx=(0, 10))

        self.theme_switch = ctk.CTkSwitch(theme_frame, text="Dark Mode",
                                        command=self.toggle_theme)
        self.theme_switch.pack(side="left")
        # Set switch to dark mode (on) by default
        self.theme_switch.select()

        # Main content area with sidebar
        main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Create tabview for main content
        self.tabview = ctk.CTkTabview(main_frame, corner_radius=15)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        # Add tabs with modern styling
        self.tabview.add("📄 Convert")
        self.tabview.add("⚙️ Settings")
        self.tabview.add("📦 Batch")
        self.tabview.add("ℹ️ About")

        # Setup individual tabs
        self.setup_convert_tab()
        self.setup_settings_tab()
        self.setup_batch_tab()
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

        file_label = ctk.CTkLabel(file_section, text="📁 Input Document",
                                font=ctk.CTkFont(size=18, weight="bold"))
        file_label.pack(pady=(15, 10))

        # File selection row
        file_row = ctk.CTkFrame(file_section, fg_color="transparent")
        file_row.pack(fill="x", padx=20, pady=(0, 15))

        self.file_entry = ctk.CTkEntry(file_row, placeholder_text="Select a document file...",
                                     height=40, font=ctk.CTkFont(size=12))
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(file_row, text="📂 Browse",
                                 command=self.browse_file,
                                 height=40, corner_radius=20,
                                 font=ctk.CTkFont(size=12))
        browse_btn.pack(side="right")

        # Drag and drop area
        drop_frame = ctk.CTkFrame(file_section, height=100, corner_radius=15,
                                border_width=2, border_color="#cccccc")
        drop_frame.pack(fill="x", padx=20, pady=(0, 20))
        drop_frame.pack_propagate(False)

        drop_label = ctk.CTkLabel(drop_frame,
                                text="💭 Drag and drop your document here\n(DOCX, MD, TXT, HTML)",
                                font=ctk.CTkFont(size=14))
        drop_label.pack(expand=True)

        # Metadata Section
        metadata_section = ctk.CTkFrame(scrollable_frame, corner_radius=15)
        metadata_section.pack(fill="x", padx=5, pady=(0, 15))

        metadata_label = ctk.CTkLabel(metadata_section, text="📖 Book Metadata",
                                    font=ctk.CTkFont(size=18, weight="bold"))
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

        ctk.CTkLabel(title_col, text="📖 Title *",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.title_entry = ctk.CTkEntry(title_col, placeholder_text="Enter book title...",
                                      height=35, font=ctk.CTkFont(size=12))
        self.title_entry.pack(fill="x", pady=(5, 0))

        # Author
        author_col = ctk.CTkFrame(title_frame, fg_color="transparent")
        author_col.pack(side="right", fill="x", expand=True, padx=(10, 0))

        ctk.CTkLabel(author_col, text="✍️ Author *",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.author_entry = ctk.CTkEntry(author_col, placeholder_text="Enter author name...",
                                       height=35, font=ctk.CTkFont(size=12))
        self.author_entry.pack(fill="x", pady=(5, 0))

        # Language and Genre row
        lang_genre_frame = ctk.CTkFrame(metadata_grid, fg_color="transparent")
        lang_genre_frame.pack(fill="x", pady=(0, 10))

        # Language
        lang_col = ctk.CTkFrame(lang_genre_frame, fg_color="transparent")
        lang_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(lang_col, text="🌍 Language",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.language_combo = ctk.CTkComboBox(lang_col,
                                            values=["English", "Spanish", "French", "German", "Italian"],
                                            height=35, font=ctk.CTkFont(size=12))
        self.language_combo.pack(fill="x", pady=(5, 0))
        self.language_combo.set("English")

        # Genre
        genre_col = ctk.CTkFrame(lang_genre_frame, fg_color="transparent")
        genre_col.pack(side="right", fill="x", expand=True, padx=(10, 0))

        ctk.CTkLabel(genre_col, text="🏷️ Genre",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.genre_entry = ctk.CTkEntry(genre_col, placeholder_text="e.g., Fantasy, Romance...",
                                      height=35, font=ctk.CTkFont(size=12))
        self.genre_entry.pack(fill="x", pady=(5, 0))

        # Description
        desc_frame = ctk.CTkFrame(metadata_grid, fg_color="transparent")
        desc_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(desc_frame, text="📝 Description",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.description_text = ctk.CTkTextbox(desc_frame, height=100,
                                             font=ctk.CTkFont(size=12))
        self.description_text.pack(fill="x", pady=(5, 0))

        # Conversion Options Section
        options_section = ctk.CTkFrame(scrollable_frame, corner_radius=15)
        options_section.pack(fill="x", padx=5, pady=(0, 15))

        options_label = ctk.CTkLabel(options_section, text="⚙️ Conversion Options",
                                   font=ctk.CTkFont(size=18, weight="bold"))
        options_label.pack(pady=(15, 10))

        # Options in segmented button style
        options_frame = ctk.CTkFrame(options_section, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=(0, 20))

        # CSS Theme
        theme_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(theme_frame, text="🎨 CSS Theme",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.css_theme = ctk.CTkSegmentedButton(theme_frame,
                                              values=["Serif", "Sans-serif", "Print-like"],
                                              font=ctk.CTkFont(size=12))
        self.css_theme.pack(fill="x", pady=(5, 0))
        self.css_theme.set("Serif")

        # Checkboxes for options
        check_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        check_frame.pack(fill="x")

        self.include_toc = ctk.CTkCheckBox(check_frame, text="📋 Include Table of Contents",
                                         font=ctk.CTkFont(size=12))
        self.include_toc.pack(anchor="w", pady=2)
        self.include_toc.select()

        self.ai_detection = ctk.CTkCheckBox(check_frame, text="🤖 AI Chapter Detection",
                                          font=ctk.CTkFont(size=12))
        self.ai_detection.pack(anchor="w", pady=2)

        self.validate_epub = ctk.CTkCheckBox(check_frame, text="✅ Validate EPUB Output",
                                           font=ctk.CTkFont(size=12))
        self.validate_epub.pack(anchor="w", pady=2)
        self.validate_epub.select()

        # Progress Section
        progress_section = ctk.CTkFrame(scrollable_frame, corner_radius=15)
        progress_section.pack(fill="x", padx=5, pady=(0, 15))

        self.progress_label = ctk.CTkLabel(progress_section, text="Ready to convert",
                                         font=ctk.CTkFont(size=14))
        self.progress_label.pack(pady=(15, 5))

        self.progress_bar = ctk.CTkProgressBar(progress_section, height=20)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.progress_bar.set(0)

        # Action Buttons
        button_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=5, pady=(0, 10))

        # Convert button
        self.convert_btn = ctk.CTkButton(button_frame, text="🚀 Convert to EPUB",
                                       command=self.start_conversion,
                                       height=50, corner_radius=25,
                                       font=ctk.CTkFont(size=16, weight="bold"))
        self.convert_btn.pack(side="left", padx=(0, 10))

        # Help button
        help_btn = ctk.CTkButton(button_frame, text="❓ Help",
                               command=self.show_help,
                               height=50, corner_radius=25,
                               font=ctk.CTkFont(size=14))
        help_btn.pack(side="right")

    def setup_settings_tab(self):
        """Setup the comprehensive settings tab."""
        settings_frame = self.tabview.tab("⚙️ Settings")

        # Create scrollable frame for settings
        scrollable_settings = ctk.CTkScrollableFrame(settings_frame)
        scrollable_settings.pack(fill="both", expand=True, padx=10, pady=10)

        # Settings header
        settings_label = ctk.CTkLabel(scrollable_settings, text="🔧 Application Settings",
                                    font=ctk.CTkFont(size=20, weight="bold"))
        settings_label.pack(pady=(0, 20))

        # General Settings Section
        general_section = ctk.CTkFrame(scrollable_settings, corner_radius=15)
        general_section.pack(fill="x", padx=5, pady=(0, 15))

        general_label = ctk.CTkLabel(general_section, text="🎯 General Settings",
                                   font=ctk.CTkFont(size=16, weight="bold"))
        general_label.pack(pady=(15, 10))

        general_content = ctk.CTkFrame(general_section, fg_color="transparent")
        general_content.pack(fill="x", padx=20, pady=(0, 20))

        # Auto-save settings
        self.auto_save_var = ctk.BooleanVar(value=True)
        auto_save_check = ctk.CTkCheckBox(general_content, text="🔄 Auto-save settings",
                                        variable=self.auto_save_var,
                                        font=ctk.CTkFont(size=12))
        auto_save_check.pack(anchor="w", pady=5)

        # Show tooltips
        self.tooltips_var = ctk.BooleanVar(value=True)
        tooltips_check = ctk.CTkCheckBox(general_content, text="💡 Show tooltips",
                                       variable=self.tooltips_var,
                                       font=ctk.CTkFont(size=12))
        tooltips_check.pack(anchor="w", pady=5)

        # Check for updates
        self.updates_var = ctk.BooleanVar(value=True)
        updates_check = ctk.CTkCheckBox(general_content, text="🔄 Check for updates automatically",
                                      variable=self.updates_var,
                                      font=ctk.CTkFont(size=12))
        updates_check.pack(anchor="w", pady=5)

        # Manual update check
        update_frame = ctk.CTkFrame(general_content, fg_color="transparent")
        update_frame.pack(fill="x", pady=5)

        update_btn = ctk.CTkButton(update_frame, text="🆙 Check for Updates Now",
                                 command=self.check_for_updates,
                                 height=35, corner_radius=17,
                                 font=ctk.CTkFont(size=12))
        update_btn.pack(anchor="w")

        # Remember window size
        self.remember_window_var = ctk.BooleanVar(value=True)
        remember_check = ctk.CTkCheckBox(general_content, text="📏 Remember window size and position",
                                       variable=self.remember_window_var,
                                       font=ctk.CTkFont(size=12))
        remember_check.pack(anchor="w", pady=5)

        # Show tooltips
        self.show_tooltips_var = ctk.BooleanVar(value=True)
        tooltips_check = ctk.CTkCheckBox(general_content, text="💭 Show helpful tooltips",
                                       variable=self.show_tooltips_var,
                                       font=ctk.CTkFont(size=12))
        tooltips_check.pack(anchor="w", pady=5)

        # Default Output Settings Section
        output_section = ctk.CTkFrame(scrollable_settings, corner_radius=15)
        output_section.pack(fill="x", padx=5, pady=(0, 15))

        output_label = ctk.CTkLabel(output_section, text="📁 Default Output Settings",
                                  font=ctk.CTkFont(size=16, weight="bold"))
        output_label.pack(pady=(15, 10))

        output_content = ctk.CTkFrame(output_section, fg_color="transparent")
        output_content.pack(fill="x", padx=20, pady=(0, 20))

        # Default output directory
        dir_frame = ctk.CTkFrame(output_content, fg_color="transparent")
        dir_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(dir_frame, text="📂 Default Output Directory:",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        dir_row = ctk.CTkFrame(dir_frame, fg_color="transparent")
        dir_row.pack(fill="x", pady=(5, 0))

        self.output_dir_var = ctk.StringVar()
        self.output_dir_entry = ctk.CTkEntry(dir_row, textvariable=self.output_dir_var,
                                           placeholder_text="Choose default output folder...",
                                           font=ctk.CTkFont(size=11))
        self.output_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_dir_btn = ctk.CTkButton(dir_row, text="📂 Browse",
                                     command=self.browse_output_directory,
                                     width=80, height=32, corner_radius=16)
        browse_dir_btn.pack(side="right")

        # Auto-generate filenames
        self.auto_filename_var = ctk.BooleanVar(value=True)
        auto_filename_check = ctk.CTkCheckBox(output_content, text="📝 Auto-generate output filenames",
                                            variable=self.auto_filename_var,
                                            font=ctk.CTkFont(size=12))
        auto_filename_check.pack(anchor="w", pady=5)

        # Backup original files
        self.backup_original_var = ctk.BooleanVar(value=False)
        backup_check = ctk.CTkCheckBox(output_content, text="💾 Create backup of original files",
                                     variable=self.backup_original_var,
                                     font=ctk.CTkFont(size=12))
        backup_check.pack(anchor="w", pady=5)

        # Default format
        format_frame = ctk.CTkFrame(output_content, fg_color="transparent")
        format_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(format_frame, text="📖 Default Output Format:",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.format_var = ctk.StringVar(value="EPUB3")
        format_combo = ctk.CTkComboBox(format_frame, variable=self.format_var,
                                      values=["EPUB3", "EPUB2", "MOBI"],
                                      font=ctk.CTkFont(size=11))
        format_combo.pack(fill="x", pady=(5, 0))

        # Preserve structure
        self.structure_var = ctk.BooleanVar(value=True)
        structure_check = ctk.CTkCheckBox(output_content, text="🏗️ Preserve document structure",
                                        variable=self.structure_var,
                                        font=ctk.CTkFont(size=12))
        structure_check.pack(anchor="w", pady=5)

        # Create backup alias for compatibility
        self.backup_var = self.backup_original_var

        # AI Detection Settings Section
        ai_section = ctk.CTkFrame(scrollable_settings, corner_radius=15)
        ai_section.pack(fill="x", padx=5, pady=(0, 15))

        ai_label = ctk.CTkLabel(ai_section, text="🤖 AI Detection Settings",
                              font=ctk.CTkFont(size=16, weight="bold"))
        ai_label.pack(pady=(15, 10))

        ai_content = ctk.CTkFrame(ai_section, fg_color="transparent")
        ai_content.pack(fill="x", padx=20, pady=(0, 20))

        # Enable AI features
        self.enable_ai_var = ctk.BooleanVar(value=True)
        enable_ai_check = ctk.CTkCheckBox(ai_content, text="🧠 Enable AI chapter detection",
                                        variable=self.enable_ai_var,
                                        font=ctk.CTkFont(size=12))
        enable_ai_check.pack(anchor="w", pady=5)

        # Confidence threshold
        conf_frame = ctk.CTkFrame(ai_content, fg_color="transparent")
        conf_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(conf_frame, text="🎯 Confidence Threshold:",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        self.confidence_var = ctk.DoubleVar(value=0.8)
        confidence_slider = ctk.CTkSlider(conf_frame, from_=0.5, to=1.0,
                                        variable=self.confidence_var,
                                        number_of_steps=10)
        confidence_slider.pack(fill="x", pady=(5, 0))

        self.confidence_label = ctk.CTkLabel(conf_frame, text="80%",
                                           font=ctk.CTkFont(size=11))
        self.confidence_label.pack(anchor="w")

        # Update confidence label
        confidence_slider.configure(command=self.update_confidence_label)

        # Advanced Settings Section
        advanced_section = ctk.CTkFrame(scrollable_settings, corner_radius=15)
        advanced_section.pack(fill="x", padx=5, pady=(0, 15))

        advanced_label = ctk.CTkLabel(advanced_section, text="⚡ Advanced Settings",
                                    font=ctk.CTkFont(size=16, weight="bold"))
        advanced_label.pack(pady=(15, 10))

        advanced_content = ctk.CTkFrame(advanced_section, fg_color="transparent")
        advanced_content.pack(fill="x", padx=20, pady=(0, 20))

        # Processing threads
        threads_frame = ctk.CTkFrame(advanced_content, fg_color="transparent")
        threads_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(threads_frame, text="🧵 Processing Threads:",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        self.threads_var = ctk.IntVar(value=4)
        threads_slider = ctk.CTkSlider(threads_frame, from_=1, to=8,
                                     variable=self.threads_var,
                                     number_of_steps=7)
        threads_slider.pack(fill="x", pady=(5, 0))

        self.threads_label = ctk.CTkLabel(threads_frame, text="4 threads",
                                        font=ctk.CTkFont(size=11))
        self.threads_label.pack(anchor="w")

        threads_slider.configure(command=self.update_threads_label)

        # Memory usage limit
        memory_frame = ctk.CTkFrame(advanced_content, fg_color="transparent")
        memory_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(memory_frame, text="💾 Memory Limit (MB):",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        self.memory_var = ctk.IntVar(value=512)
        memory_slider = ctk.CTkSlider(memory_frame, from_=256, to=2048,
                                    variable=self.memory_var,
                                    number_of_steps=7)
        memory_slider.pack(fill="x", pady=(5, 0))

        self.memory_label = ctk.CTkLabel(memory_frame, text="512 MB",
                                       font=ctk.CTkFont(size=11))
        self.memory_label.pack(anchor="w")

        memory_slider.configure(command=self.update_memory_label)

        # Action Buttons
        button_frame = ctk.CTkFrame(scrollable_settings, fg_color="transparent")
        button_frame.pack(fill="x", padx=5, pady=(10, 0))

        save_btn = ctk.CTkButton(button_frame, text="💾 Save Settings",
                               command=self.save_settings,
                               height=40, corner_radius=20,
                               font=ctk.CTkFont(size=14, weight="bold"))
        save_btn.pack(side="left", padx=(0, 10))

        reset_btn = ctk.CTkButton(button_frame, text="🔄 Reset to Defaults",
                                command=self.reset_settings,
                                height=40, corner_radius=20,
                                font=ctk.CTkFont(size=14))
        reset_btn.pack(side="left", padx=(0, 10))

        export_btn = ctk.CTkButton(button_frame, text="📤 Export Settings",
                                 command=self.export_settings,
                                 height=40, corner_radius=20,
                                 font=ctk.CTkFont(size=14))
        export_btn.pack(side="right", padx=(10, 0))

        import_btn = ctk.CTkButton(button_frame, text="📥 Import Settings",
                                 command=self.import_settings,
                                 height=40, corner_radius=20,
                                 font=ctk.CTkFont(size=14))
        import_btn.pack(side="right")

    def setup_batch_tab(self):
        """Setup the batch processing tab."""
        batch_frame = self.tabview.tab("📦 Batch")

        # Create scrollable frame for batch processing
        scrollable_batch = ctk.CTkScrollableFrame(batch_frame)
        scrollable_batch.pack(fill="both", expand=True, padx=10, pady=10)

        # Batch header
        batch_label = ctk.CTkLabel(scrollable_batch, text="📦 Batch Processing",
                                 font=ctk.CTkFont(size=20, weight="bold"))
        batch_label.pack(pady=(0, 20))

        # File selection section
        files_section = ctk.CTkFrame(scrollable_batch, corner_radius=15)
        files_section.pack(fill="x", padx=5, pady=(0, 15))

        files_label = ctk.CTkLabel(files_section, text="📁 Input Files",
                                 font=ctk.CTkFont(size=16, weight="bold"))
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

        add_files_btn = ctk.CTkButton(file_buttons, text="➕ Add Files",
                                    command=self.add_batch_files,
                                    height=35, corner_radius=17)
        add_files_btn.pack(side="left", padx=(0, 10))

        add_folder_btn = ctk.CTkButton(file_buttons, text="📁 Add Folder",
                                     command=self.add_batch_folder,
                                     height=35, corner_radius=17)
        add_folder_btn.pack(side="left", padx=(0, 10))

        clear_files_btn = ctk.CTkButton(file_buttons, text="🗑️ Clear All",
                                      command=self.clear_batch_files,
                                      height=35, corner_radius=17)
        clear_files_btn.pack(side="right")

        # Batch settings section
        settings_section = ctk.CTkFrame(scrollable_batch, corner_radius=15)
        settings_section.pack(fill="x", padx=5, pady=(0, 15))

        settings_label = ctk.CTkLabel(settings_section, text="⚙️ Batch Settings",
                                    font=ctk.CTkFont(size=16, weight="bold"))
        settings_label.pack(pady=(15, 10))

        settings_content = ctk.CTkFrame(settings_section, fg_color="transparent")
        settings_content.pack(fill="x", padx=20, pady=(0, 20))

        # Common metadata
        common_frame = ctk.CTkFrame(settings_content, fg_color="transparent")
        common_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(common_frame, text="👤 Common Author:",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.batch_author_var = ctk.StringVar()
        self.batch_author_entry = ctk.CTkEntry(common_frame, textvariable=self.batch_author_var,
                                             placeholder_text="Author name for all books...",
                                             font=ctk.CTkFont(size=11))
        self.batch_author_entry.pack(fill="x", pady=(5, 0))

        # Output settings
        output_frame = ctk.CTkFrame(settings_content, fg_color="transparent")
        output_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(output_frame, text="📂 Output Directory:",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        output_row = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_row.pack(fill="x", pady=(5, 0))

        self.batch_output_var = ctk.StringVar()
        self.batch_output_entry = ctk.CTkEntry(output_row, textvariable=self.batch_output_var,
                                             placeholder_text="Choose output directory...",
                                             font=ctk.CTkFont(size=11))
        self.batch_output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_output_btn = ctk.CTkButton(output_row, text="📁 Browse",
                                        command=self.browse_batch_output,
                                        width=80, height=30, corner_radius=15)
        browse_output_btn.pack(side="right")

        # Batch options
        options_frame = ctk.CTkFrame(settings_content, fg_color="transparent")
        options_frame.pack(fill="x", pady=10)

        self.batch_overwrite_var = ctk.BooleanVar(value=False)
        overwrite_check = ctk.CTkCheckBox(options_frame, text="♻️ Overwrite existing files",
                                        variable=self.batch_overwrite_var,
                                        font=ctk.CTkFont(size=12))
        overwrite_check.pack(anchor="w", pady=2)

        self.batch_keep_structure_var = ctk.BooleanVar(value=True)
        structure_check = ctk.CTkCheckBox(options_frame, text="🏗️ Keep folder structure",
                                        variable=self.batch_keep_structure_var,
                                        font=ctk.CTkFont(size=12))
        structure_check.pack(anchor="w", pady=2)

        self.batch_ai_detection_var = ctk.BooleanVar(value=True)
        ai_check = ctk.CTkCheckBox(options_frame, text="🤖 Use AI chapter detection",
                                 variable=self.batch_ai_detection_var,
                                 font=ctk.CTkFont(size=12))
        ai_check.pack(anchor="w", pady=2)

        # Progress section
        progress_section = ctk.CTkFrame(scrollable_batch, corner_radius=15)
        progress_section.pack(fill="x", padx=5, pady=(0, 15))

        progress_label = ctk.CTkLabel(progress_section, text="📊 Progress",
                                    font=ctk.CTkFont(size=16, weight="bold"))
        progress_label.pack(pady=(15, 10))

        progress_content = ctk.CTkFrame(progress_section, fg_color="transparent")
        progress_content.pack(fill="x", padx=20, pady=(0, 20))

        # Overall progress
        overall_frame = ctk.CTkFrame(progress_content, fg_color="transparent")
        overall_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(overall_frame, text="Overall Progress:",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        self.batch_progress_var = ctk.DoubleVar()
        self.batch_progress_bar = ctk.CTkProgressBar(overall_frame, variable=self.batch_progress_var)
        self.batch_progress_bar.pack(fill="x", pady=(5, 0))

        self.batch_progress_label = ctk.CTkLabel(overall_frame, text="0 / 0 files completed",
                                               font=ctk.CTkFont(size=11))
        self.batch_progress_label.pack(anchor="w", pady=(2, 0))

        # Current file progress
        current_frame = ctk.CTkFrame(progress_content, fg_color="transparent")
        current_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(current_frame, text="Current File:",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        self.current_file_label = ctk.CTkLabel(current_frame, text="No file processing...",
                                             font=ctk.CTkFont(size=11))
        self.current_file_label.pack(anchor="w", pady=(2, 0))

        # Processing log
        log_frame = ctk.CTkFrame(progress_content, fg_color="transparent")
        log_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(log_frame, text="Processing Log:",
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        self.batch_log = ctk.CTkTextbox(log_frame, height=100, font=ctk.CTkFont(size=10))
        self.batch_log.pack(fill="x", pady=(5, 0))

        # Control buttons
        control_section = ctk.CTkFrame(scrollable_batch, corner_radius=15)
        control_section.pack(fill="x", padx=5, pady=(0, 10))

        control_content = ctk.CTkFrame(control_section, fg_color="transparent")
        control_content.pack(fill="x", padx=20, pady=20)

        self.start_batch_btn = ctk.CTkButton(control_content, text="🚀 Start Batch Processing",
                                           command=self.start_batch_processing,
                                           height=45, corner_radius=22,
                                           font=ctk.CTkFont(size=16, weight="bold"))
        self.start_batch_btn.pack(side="left", padx=(0, 15))

        self.pause_batch_btn = ctk.CTkButton(control_content, text="⏸️ Pause",
                                           command=self.pause_batch_processing,
                                           height=45, corner_radius=22,
                                           font=ctk.CTkFont(size=14))
        self.pause_batch_btn.pack(side="left", padx=(0, 15))

        self.stop_batch_btn = ctk.CTkButton(control_content, text="⏹️ Stop",
                                          command=self.stop_batch_processing,
                                          height=45, corner_radius=22,
                                          font=ctk.CTkFont(size=14))
        self.stop_batch_btn.pack(side="left")

        # Results button (initially hidden)
        self.results_btn = ctk.CTkButton(control_content, text="📋 View Results",
                                       command=self.show_batch_results,
                                       height=45, corner_radius=22,
                                       font=ctk.CTkFont(size=14))
        # Don't pack initially - will be shown after completion

        # Initialize batch state
        self.batch_state = {
            'running': False,
            'paused': False,
            'current_index': 0,
            'completed': 0,
            'failed': 0,
            'results': []
        }

    def setup_about_tab(self):
        """Setup the about tab."""
        about_frame = self.tabview.tab("ℹ️ About")

        # About content
        about_label = ctk.CTkLabel(about_frame, text="ℹ️ About Docx2Shelf",
                                 font=ctk.CTkFont(size=20, weight="bold"))
        about_label.pack(pady=20)

        # About info
        info_text = """Docx2Shelf v1.6.3 - Modern GUI

Document to EPUB Converter with AI Features

• Convert DOCX, Markdown, HTML, and TXT files to EPUB
• AI-powered chapter detection and metadata enhancement
• Professional EPUB output for all major ebook stores
• Modern interface with dark/light themes

Built with CustomTkinter for a modern appearance."""

        info_label = ctk.CTkLabel(about_frame, text=info_text,
                                font=ctk.CTkFont(size=14),
                                justify="left")
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
                ("All Files", "*.*")
            ]
        )

        if file_path:
            self.file_entry.delete(0, 'end')
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
        """Background conversion worker."""
        try:
            # Update progress
            self.root.after(0, lambda: self.progress_bar.set(0.2))
            self.root.after(0, lambda: self.progress_label.configure(text="Reading document..."))

            # Simulate conversion steps
            import time
            time.sleep(1)

            self.root.after(0, lambda: self.progress_bar.set(0.4))
            self.root.after(0, lambda: self.progress_label.configure(text="Processing content..."))
            time.sleep(1)

            self.root.after(0, lambda: self.progress_bar.set(0.6))
            self.root.after(0, lambda: self.progress_label.configure(text="Generating EPUB..."))
            time.sleep(1)

            self.root.after(0, lambda: self.progress_bar.set(0.8))
            self.root.after(0, lambda: self.progress_label.configure(text="Finalizing..."))
            time.sleep(1)

            self.root.after(0, lambda: self.progress_bar.set(1.0))
            self.root.after(0, lambda: self.progress_label.configure(text="Conversion complete!"))

            # Re-enable button
            self.root.after(0, lambda: self.convert_btn.configure(state="normal", text="🚀 Convert to EPUB"))

            # Show success message
            self.root.after(0, lambda: self.show_success("EPUB conversion completed successfully!"))

        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"Conversion failed: {str(e)}"))
            self.root.after(0, lambda: self.convert_btn.configure(state="normal", text="🚀 Convert to EPUB"))

    def show_help(self):
        """Show help dialog."""
        help_window = ctk.CTkToplevel(self.root)
        help_window.title("📖 Help Guide")
        help_window.geometry("800x600")
        help_window.transient(self.root)
        help_window.grab_set()

        # Help content
        help_label = ctk.CTkLabel(help_window, text="📖 Docx2Shelf Help",
                                font=ctk.CTkFont(size=24, weight="bold"))
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
        close_btn = ctk.CTkButton(help_window, text="✕ Close",
                                command=help_window.destroy,
                                height=40, corner_radius=20)
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
                'general': {
                    'auto_save': self.auto_save_var.get(),
                    'show_tooltips': self.tooltips_var.get(),
                    'remember_window': self.remember_window_var.get(),
                    'check_updates': self.updates_var.get()
                },
                'output': {
                    'default_format': self.format_var.get(),
                    'preserve_structure': self.structure_var.get(),
                    'create_backup': self.backup_var.get()
                },
                'ai': {
                    'enable_ai': self.enable_ai_var.get(),
                    'confidence_threshold': self.confidence_var.get()
                },
                'advanced': {
                    'processing_threads': self.threads_var.get(),
                    'memory_limit': self.memory_var.get()
                }
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
            from tkinter import filedialog
            import json

            file_path = filedialog.asksaveasfilename(
                title="Export Settings",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                # Collect current settings
                settings = {
                    'general': {
                        'auto_save': self.auto_save_var.get(),
                        'show_tooltips': self.tooltips_var.get(),
                        'remember_window': self.remember_window_var.get(),
                        'check_updates': self.updates_var.get()
                    },
                    'output': {
                        'default_format': self.format_var.get(),
                        'preserve_structure': self.structure_var.get(),
                        'create_backup': self.backup_var.get()
                    },
                    'ai': {
                        'enable_ai': self.enable_ai_var.get(),
                        'confidence_threshold': self.confidence_var.get()
                    },
                    'advanced': {
                        'processing_threads': self.threads_var.get(),
                        'memory_limit': self.memory_var.get()
                    }
                }

                with open(file_path, 'w') as f:
                    json.dump(settings, f, indent=2)

                self.show_success(f"Settings exported to {file_path}")

        except Exception as e:
            self.show_error(f"Failed to export settings: {str(e)}")

    def import_settings(self):
        """Import settings from file."""
        try:
            from tkinter import filedialog
            import json

            file_path = filedialog.askopenfilename(
                title="Import Settings",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                with open(file_path, 'r') as f:
                    settings = json.load(f)

                # Apply imported settings to UI
                if 'general' in settings:
                    self.auto_save_var.set(settings['general'].get('auto_save', True))
                    self.tooltips_var.set(settings['general'].get('show_tooltips', True))
                    self.remember_window_var.set(settings['general'].get('remember_window', True))
                    self.updates_var.set(settings['general'].get('check_updates', True))

                if 'output' in settings:
                    self.format_var.set(settings['output'].get('default_format', 'EPUB3'))
                    self.structure_var.set(settings['output'].get('preserve_structure', True))
                    self.backup_var.set(settings['output'].get('create_backup', False))

                if 'ai' in settings:
                    self.enable_ai_var.set(settings['ai'].get('enable_ai', True))
                    self.confidence_var.set(settings['ai'].get('confidence_threshold', 0.8))
                    self.update_confidence_label(settings['ai'].get('confidence_threshold', 0.8))

                if 'advanced' in settings:
                    self.threads_var.set(settings['advanced'].get('processing_threads', 4))
                    self.memory_var.set(settings['advanced'].get('memory_limit', 512))
                    self.update_threads_label(settings['advanced'].get('processing_threads', 4))
                    self.update_memory_label(settings['advanced'].get('memory_limit', 512))

                self.show_success(f"Settings imported from {file_path}")

        except Exception as e:
            self.show_error(f"Failed to import settings: {str(e)}")

    def check_for_updates(self):
        """Check for application updates."""
        import threading
        from ..version import get_version_info

        def update_thread():
            try:
                # Show checking message
                self.root.after(0, lambda: self.show_update_checking())

                # Check for updates
                result = check_updates()
                current_version = get_version_info()['version']

                if result and result.get('update_available'):
                    latest_version = result.get('latest_version', 'Unknown')
                    download_url = result.get('download_url', '')
                    changelog = result.get('changelog', 'No changelog available.')

                    # Show update available dialog
                    self.root.after(0, lambda: self.show_update_available(
                        current_version, latest_version, changelog, download_url))
                else:
                    # No update available
                    self.root.after(0, lambda: self.show_update_current(current_version))

            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Failed to check for updates: {str(e)}"))

        # Start update check in background thread
        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()

    def show_update_checking(self):
        """Show update checking dialog."""
        self.update_dialog = ctk.CTkToplevel(self.root)
        self.update_dialog.title("🔄 Checking for Updates")
        self.update_dialog.geometry("400x150")
        self.update_dialog.transient(self.root)
        self.update_dialog.grab_set()

        # Center the dialog
        self.update_dialog.update_idletasks()
        x = (self.update_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.update_dialog.winfo_screenheight() // 2) - (150 // 2)
        self.update_dialog.geometry(f"400x150+{x}+{y}")

        ctk.CTkLabel(self.update_dialog, text="🔄 Checking for Updates...",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)

        # Progress bar
        progress = ctk.CTkProgressBar(self.update_dialog, mode="indeterminate")
        progress.pack(pady=10, padx=40, fill="x")
        progress.start()

        ctk.CTkLabel(self.update_dialog, text="Please wait while we check for the latest version...",
                    font=ctk.CTkFont(size=12)).pack(pady=10)

    def show_update_available(self, current_version, latest_version, changelog, download_url):
        """Show update available dialog."""
        if hasattr(self, 'update_dialog'):
            self.update_dialog.destroy()

        update_window = ctk.CTkToplevel(self.root)
        update_window.title("🆙 Update Available")
        update_window.geometry("500x400")
        update_window.transient(self.root)
        update_window.grab_set()

        # Header
        header_label = ctk.CTkLabel(update_window, text="🎉 Update Available!",
                                   font=ctk.CTkFont(size=20, weight="bold"))
        header_label.pack(pady=20)

        # Version info
        version_frame = ctk.CTkFrame(update_window)
        version_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(version_frame, text=f"Current Version: {current_version}",
                    font=ctk.CTkFont(size=14)).pack(pady=5)
        ctk.CTkLabel(version_frame, text=f"Latest Version: {latest_version}",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        # Changelog
        ctk.CTkLabel(update_window, text="What's New:",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))

        changelog_text = ctk.CTkTextbox(update_window, height=150)
        changelog_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        changelog_text.insert("0.0", changelog)
        changelog_text.configure(state="disabled")

        # Buttons
        button_frame = ctk.CTkFrame(update_window, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        download_btn = ctk.CTkButton(button_frame, text="🔽 Download Update",
                                   command=lambda: self.download_update(download_url),
                                   height=40, corner_radius=20,
                                   font=ctk.CTkFont(size=14, weight="bold"))
        download_btn.pack(side="left", padx=(0, 10))

        later_btn = ctk.CTkButton(button_frame, text="⏰ Later",
                                command=update_window.destroy,
                                height=40, corner_radius=20,
                                font=ctk.CTkFont(size=14))
        later_btn.pack(side="right")

    def show_update_current(self, current_version):
        """Show already up to date dialog."""
        if hasattr(self, 'update_dialog'):
            self.update_dialog.destroy()

        self.show_success(f"You're already running the latest version!\n\nCurrent version: {current_version}")

    def download_update(self, download_url):
        """Download and install update."""
        import webbrowser
        import threading

        def download_thread():
            try:
                if download_url:
                    # Open download URL in browser
                    webbrowser.open(download_url)
                    self.root.after(0, lambda: self.show_success(
                        "Update download started!\n\nThe download page has been opened in your browser.\n"
                        "Please download and install the latest version."))
                else:
                    self.root.after(0, lambda: self.show_error(
                        "Download URL not available.\nPlease visit the project page to download manually."))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Failed to open download: {str(e)}"))

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
                    ("All Files", "*.*")
                ]
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
            from tkinter import filedialog
            import os

            folder_path = filedialog.askdirectory(
                title="Select Folder with Documents"
            )

            if folder_path:
                supported_extensions = {'.docx', '.md', '.txt', '.html', '.htm'}

                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in supported_extensions):
                            file_path = os.path.join(root, file)
                            if file_path not in self.batch_files:
                                self.batch_files.append(file_path)

                self.update_batch_file_list()
                self.log_batch_message(f"Added {len(self.batch_files)} files from folder: {folder_path}")

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

            file_label = ctk.CTkLabel(file_frame, text=f"📄 {filename}",
                                    font=ctk.CTkFont(size=11),
                                    anchor="w")
            file_label.pack(side="left", fill="x", expand=True)

            # Remove button
            remove_btn = ctk.CTkButton(file_frame, text="✕",
                                     command=lambda idx=i: self.remove_batch_file(idx),
                                     width=30, height=20, corner_radius=10)
            remove_btn.pack(side="right")

        # Update file count
        count_text = f"{len(self.batch_files)} files selected"
        if hasattr(self, 'batch_progress_label'):
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
            'running': True,
            'paused': False,
            'current_index': 0,
            'completed': 0,
            'failed': 0,
            'results': []
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
        if self.batch_state['running']:
            self.batch_state['paused'] = not self.batch_state['paused']

            if self.batch_state['paused']:
                self.pause_batch_btn.configure(text="▶️ Resume")
                self.log_batch_message("Batch processing paused")
            else:
                self.pause_batch_btn.configure(text="⏸️ Pause")
                self.log_batch_message("Batch processing resumed")

    def stop_batch_processing(self):
        """Stop batch processing."""
        self.batch_state['running'] = False
        self.batch_state['paused'] = False

        # Update UI
        self.start_batch_btn.configure(state="normal", text="🚀 Start Batch Processing")
        self.pause_batch_btn.configure(state="disabled", text="⏸️ Pause")
        self.stop_batch_btn.configure(state="disabled")

        self.log_batch_message("Batch processing stopped")

    def batch_processing_worker(self):
        """Background worker for batch processing."""
        import os
        import time
        from pathlib import Path

        try:
            total_files = len(self.batch_files)

            for i, file_path in enumerate(self.batch_files):
                if not self.batch_state['running']:
                    break

                # Wait if paused
                while self.batch_state['paused'] and self.batch_state['running']:
                    time.sleep(0.1)

                if not self.batch_state['running']:
                    break

                # Update current file
                filename = os.path.basename(file_path)
                self.root.after(0, lambda f=filename: self.current_file_label.configure(text=f"Processing: {f}"))

                try:
                    # Generate title from filename
                    title = Path(file_path).stem.replace('-', ' ').replace('_', ' ').title()

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
                        result = {'file': filename, 'status': 'skipped', 'reason': 'File exists'}
                        self.batch_state['results'].append(result)
                        self.root.after(0, lambda: self.log_batch_message(f"Skipped: {filename} (file exists)"))
                        continue

                    # Process file
                    self.process_single_file(file_path, title, output_path)

                    # Success
                    result = {'file': filename, 'status': 'success', 'output': output_path}
                    self.batch_state['results'].append(result)
                    self.batch_state['completed'] += 1

                    self.root.after(0, lambda: self.log_batch_message(f"✅ Completed: {filename}"))

                except Exception as e:
                    # Error
                    result = {'file': filename, 'status': 'error', 'reason': str(e)}
                    self.batch_state['results'].append(result)
                    self.batch_state['failed'] += 1

                    self.root.after(0, lambda err=str(e): self.log_batch_message(f"❌ Failed: {filename} - {err}"))

                # Update progress
                progress = (i + 1) / total_files
                completed = self.batch_state['completed']
                failed = self.batch_state['failed']

                self.root.after(0, lambda p=progress, c=completed, f=failed, t=total_files: self.update_batch_progress(p, c, f, t))

        except Exception as e:
            self.root.after(0, lambda: self.log_batch_message(f"Critical error in batch processing: {str(e)}"))

        finally:
            # Processing complete
            self.root.after(0, self.batch_processing_complete)

    def process_single_file(self, file_path, title, output_path):
        """Process a single file for batch conversion."""
        from ..metadata import EpubMetadata, BuildOptions
        from ..convert import docx_to_html_chunks
        from ..assemble import assemble_epub
        import os

        # Create metadata
        metadata = EpubMetadata(
            title=title,
            author=self.batch_author_var.get().strip(),
            language='en',
            description=f"Generated from {os.path.basename(file_path)}"
        )

        # Create build options
        options = BuildOptions(
            use_ai_detection=self.batch_ai_detection_var.get(),
            theme='modern',
            include_toc=True
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

        completed = self.batch_state['completed']
        failed = self.batch_state['failed']
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
        header_label = ctk.CTkLabel(results_window, text="📋 Batch Processing Results",
                                  font=ctk.CTkFont(size=18, weight="bold"))
        header_label.pack(pady=20)

        # Results list
        results_frame = ctk.CTkScrollableFrame(results_window)
        results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for result in self.batch_state['results']:
            result_row = ctk.CTkFrame(results_frame)
            result_row.pack(fill="x", padx=5, pady=2)

            # Status icon
            if result['status'] == 'success':
                icon = "✅"
                color = "#28a745"
            elif result['status'] == 'error':
                icon = "❌"
                color = "#dc3545"
            else:  # skipped
                icon = "⏭️"
                color = "#ffc107"

            status_label = ctk.CTkLabel(result_row, text=icon,
                                      font=ctk.CTkFont(size=14),
                                      text_color=color)
            status_label.pack(side="left", padx=(10, 5))

            # File name
            file_label = ctk.CTkLabel(result_row, text=result['file'],
                                    font=ctk.CTkFont(size=12))
            file_label.pack(side="left", fill="x", expand=True, padx=5)

            # Status text
            if result['status'] == 'success':
                status_text = "Completed"
            elif result['status'] == 'error':
                status_text = f"Error: {result.get('reason', 'Unknown')}"
            else:
                status_text = f"Skipped: {result.get('reason', 'Unknown')}"

            status_detail = ctk.CTkLabel(result_row, text=status_text,
                                       font=ctk.CTkFont(size=10))
            status_detail.pack(side="right", padx=(5, 10))

        # Close button
        close_btn = ctk.CTkButton(results_window, text="✕ Close",
                                command=results_window.destroy,
                                height=40, corner_radius=20)
        close_btn.pack(pady=20)

    def log_batch_message(self, message):
        """Add a message to the batch processing log."""
        import time
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.batch_log.insert("end", log_entry)
        self.batch_log.see("end")

    def show_error(self, message):
        """Show error message."""
        error_window = ctk.CTkToplevel(self.root)
        error_window.title("❌ Error")
        error_window.geometry("400x200")
        error_window.transient(self.root)
        error_window.grab_set()

        error_label = ctk.CTkLabel(error_window, text="❌ Error",
                                 font=ctk.CTkFont(size=18, weight="bold"))
        error_label.pack(pady=20)

        message_label = ctk.CTkLabel(error_window, text=message,
                                   font=ctk.CTkFont(size=12),
                                   wraplength=350)
        message_label.pack(padx=20, pady=10)

        ok_btn = ctk.CTkButton(error_window, text="OK",
                             command=error_window.destroy,
                             height=35, corner_radius=17)
        ok_btn.pack(pady=20)

    def show_success(self, message):
        """Show success message."""
        success_window = ctk.CTkToplevel(self.root)
        success_window.title("✅ Success")
        success_window.geometry("400x200")
        success_window.transient(self.root)
        success_window.grab_set()

        success_label = ctk.CTkLabel(success_window, text="✅ Success",
                                   font=ctk.CTkFont(size=18, weight="bold"))
        success_label.pack(pady=20)

        message_label = ctk.CTkLabel(success_window, text=message,
                                   font=ctk.CTkFont(size=12),
                                   wraplength=350)
        message_label.pack(padx=20, pady=10)

        ok_btn = ctk.CTkButton(success_window, text="OK",
                             command=success_window.destroy,
                             height=35, corner_radius=17)
        ok_btn.pack(pady=20)

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