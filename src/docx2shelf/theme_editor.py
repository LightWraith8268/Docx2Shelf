"""
Advanced Theme Editor for Docx2Shelf.

Provides visual customization and live preview capabilities for creating
and editing CSS themes with enhanced user experience.
"""

from __future__ import annotations

import json
import re
import tempfile
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils import prompt, prompt_bool


@dataclass
class ThemeProperty:
    """Individual theme property that can be customized."""

    name: str
    display_name: str
    description: str
    property_type: str  # 'color', 'font', 'size', 'spacing', 'choice'
    current_value: str
    default_value: str
    choices: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: Optional[str] = None


@dataclass
class ThemeSection:
    """Section of theme properties grouped together."""

    name: str
    display_name: str
    description: str
    properties: List[ThemeProperty] = field(default_factory=list)


@dataclass
class CustomTheme:
    """Complete custom theme definition."""

    name: str
    display_name: str
    description: str
    base_theme: str
    sections: List[ThemeSection] = field(default_factory=list)
    custom_css: str = ""
    preview_text: str = ""


class ThemeEditor:
    """Advanced theme editor with visual customization."""

    def __init__(self, themes_dir: Optional[Path] = None):
        """Initialize the theme editor.

        Args:
            themes_dir: Directory to store custom themes
        """
        self.themes_dir = themes_dir or Path.home() / ".docx2shelf" / "themes"
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.current_theme: Optional[CustomTheme] = None
        self.preview_server = None
        self._initialize_base_properties()

    def _initialize_base_properties(self):
        """Initialize the base theme properties that can be customized."""
        self.base_sections = [
            ThemeSection(
                name="typography",
                display_name="Typography",
                description="Font families, sizes, and text styling",
                properties=[
                    ThemeProperty(
                        name="body_font",
                        display_name="Body Font",
                        description="Main text font family",
                        property_type="choice",
                        current_value="Georgia, serif",
                        default_value="Georgia, serif",
                        choices=[
                            "Georgia, serif",
                            "Times New Roman, serif",
                            "Arial, sans-serif",
                            "Helvetica, sans-serif",
                            "Verdana, sans-serif",
                            "system-ui, sans-serif",
                        ],
                    ),
                    ThemeProperty(
                        name="heading_font",
                        display_name="Heading Font",
                        description="Font family for headings",
                        property_type="choice",
                        current_value="Georgia, serif",
                        default_value="Georgia, serif",
                        choices=[
                            "Georgia, serif",
                            "Times New Roman, serif",
                            "Arial, sans-serif",
                            "Helvetica, sans-serif",
                            "Verdana, sans-serif",
                            "system-ui, sans-serif",
                        ],
                    ),
                    ThemeProperty(
                        name="body_font_size",
                        display_name="Body Font Size",
                        description="Base font size for body text",
                        property_type="size",
                        current_value="1.0em",
                        default_value="1.0em",
                        min_value=0.8,
                        max_value=1.5,
                        unit="em",
                    ),
                    ThemeProperty(
                        name="line_height",
                        display_name="Line Height",
                        description="Spacing between lines",
                        property_type="size",
                        current_value="1.5",
                        default_value="1.5",
                        min_value=1.0,
                        max_value=2.5,
                    ),
                ],
            ),
            ThemeSection(
                name="colors",
                display_name="Colors",
                description="Text colors and background styling",
                properties=[
                    ThemeProperty(
                        name="text_color",
                        display_name="Text Color",
                        description="Main text color",
                        property_type="color",
                        current_value="#000000",
                        default_value="#000000",
                    ),
                    ThemeProperty(
                        name="background_color",
                        display_name="Background Color",
                        description="Page background color",
                        property_type="color",
                        current_value="#ffffff",
                        default_value="#ffffff",
                    ),
                    ThemeProperty(
                        name="link_color",
                        display_name="Link Color",
                        description="Color for hyperlinks",
                        property_type="color",
                        current_value="#0066cc",
                        default_value="#0066cc",
                    ),
                    ThemeProperty(
                        name="heading_color",
                        display_name="Heading Color",
                        description="Color for headings",
                        property_type="color",
                        current_value="#000000",
                        default_value="#000000",
                    ),
                ],
            ),
            ThemeSection(
                name="layout",
                display_name="Layout & Spacing",
                description="Margins, padding, and spacing settings",
                properties=[
                    ThemeProperty(
                        name="page_margin",
                        display_name="Page Margin",
                        description="Margin around page content",
                        property_type="size",
                        current_value="1.5em",
                        default_value="1.5em",
                        min_value=0.5,
                        max_value=3.0,
                        unit="em",
                    ),
                    ThemeProperty(
                        name="paragraph_spacing",
                        display_name="Paragraph Spacing",
                        description="Space between paragraphs",
                        property_type="size",
                        current_value="1.0em",
                        default_value="1.0em",
                        min_value=0.0,
                        max_value=2.0,
                        unit="em",
                    ),
                    ThemeProperty(
                        name="text_align",
                        display_name="Text Alignment",
                        description="How text is aligned",
                        property_type="choice",
                        current_value="left",
                        default_value="left",
                        choices=["left", "justify", "center"],
                    ),
                ],
            ),
            ThemeSection(
                name="advanced",
                display_name="Advanced",
                description="Advanced styling options",
                properties=[
                    ThemeProperty(
                        name="chapter_break",
                        display_name="Chapter Break",
                        description="Page break before chapters",
                        property_type="choice",
                        current_value="page",
                        default_value="page",
                        choices=["page", "none", "column"],
                    ),
                    ThemeProperty(
                        name="drop_caps",
                        display_name="Drop Caps",
                        description="Large first letter in chapters",
                        property_type="choice",
                        current_value="none",
                        default_value="none",
                        choices=["none", "simple", "ornate"],
                    ),
                ],
            ),
        ]

    def run_interactive_editor(self, base_theme: str = "serif") -> Optional[Dict[str, str]]:
        """Run the interactive theme editor for wizard integration.

        Args:
            base_theme: Base theme to start from

        Returns:
            Dictionary with theme_id and theme_path if successful, None if cancelled
        """
        print("🎨 Welcome to the Advanced Theme Editor!")
        print("=" * 50)

        # Create or load theme
        if not self._setup_theme(base_theme):
            return None

        # Main editor loop
        while True:
            action = self._display_main_menu()

            if action == "quit":
                # Ask if they want to save before quitting
                if self.current_theme and prompt_bool("Save theme before exiting?"):
                    if self._save_theme():
                        theme_path = self.themes_dir / f"{self.current_theme.name}.json"
                        return {"theme_id": self.current_theme.name, "theme_path": str(theme_path)}
                return None
            elif action == "preview":
                self._generate_live_preview()
            elif action == "save":
                if self._save_theme():
                    print("✅ Theme saved successfully!")
                    # Ask if they want to use this theme and exit
                    if prompt_bool("Use this theme and return to wizard?"):
                        theme_path = self.themes_dir / f"{self.current_theme.name}.json"
                        return {"theme_id": self.current_theme.name, "theme_path": str(theme_path)}
                else:
                    print("❌ Failed to save theme")
            elif action == "export":
                self._export_theme()
            elif action == "reset":
                if prompt_bool("Reset all changes to defaults?"):
                    self._reset_to_defaults()
            elif action.startswith("edit_"):
                section_name = action[5:]
                self._edit_section(section_name)
            elif action == "custom_css":
                self._edit_custom_css()

    def start_editor(self, base_theme: str = "serif") -> int:
        """Start the interactive theme editor.

        Args:
            base_theme: Base theme to start from

        Returns:
            Exit code (0 for success)
        """
        result = self.run_interactive_editor(base_theme)
        return 0 if result else 1

    def _setup_theme(self, base_theme: str) -> bool:
        """Set up the theme for editing."""
        print(f"Starting with base theme: {base_theme}")

        # Create new custom theme
        self.current_theme = CustomTheme(
            name="custom_theme",
            display_name="My Custom Theme",
            description="Custom theme created with the theme editor",
            base_theme=base_theme,
            sections=self._copy_base_sections(),
            preview_text=self._get_sample_content(),
        )

        # Apply base theme defaults
        self._apply_base_theme_defaults(base_theme)

        return True

    def _copy_base_sections(self) -> List[ThemeSection]:
        """Create a copy of base sections for editing."""
        import copy

        return copy.deepcopy(self.base_sections)

    def _apply_base_theme_defaults(self, base_theme: str):
        """Apply defaults from a base theme."""
        theme_defaults = {
            "serif": {
                "body_font": "Georgia, serif",
                "heading_font": "Georgia, serif",
                "text_color": "#000000",
                "background_color": "#ffffff",
            },
            "sans": {
                "body_font": "Arial, sans-serif",
                "heading_font": "Arial, sans-serif",
                "text_color": "#333333",
                "background_color": "#ffffff",
            },
            "printlike": {
                "body_font": "Times New Roman, serif",
                "heading_font": "Times New Roman, serif",
                "text_color": "#000000",
                "background_color": "#fffef7",
                "page_margin": "2.0em",
            },
        }

        defaults = theme_defaults.get(base_theme, theme_defaults["serif"])

        for section in self.current_theme.sections:
            for prop in section.properties:
                if prop.name in defaults:
                    prop.current_value = defaults[prop.name]

    def _display_main_menu(self) -> str:
        """Display the main theme editor menu."""
        print(f"\n🎨 Theme Editor - {self.current_theme.display_name}")
        print("-" * 40)

        # Display current theme summary
        self._display_theme_summary()

        print("\nActions:")
        print("  1. Edit Typography")
        print("  2. Edit Colors")
        print("  3. Edit Layout & Spacing")
        print("  4. Edit Advanced Settings")
        print("  5. Custom CSS")
        print("  6. Generate Preview")
        print("  7. Save Theme")
        print("  8. Export Theme")
        print("  9. Reset to Defaults")
        print("  q. Quit Editor")

        choice = prompt("Choose action (1-9, q)").lower()

        action_map = {
            "1": "edit_typography",
            "2": "edit_colors",
            "3": "edit_layout",
            "4": "edit_advanced",
            "5": "custom_css",
            "6": "preview",
            "7": "save",
            "8": "export",
            "9": "reset",
            "q": "quit",
            "quit": "quit",
        }

        return action_map.get(choice, "unknown")

    def _display_theme_summary(self):
        """Display a summary of current theme settings."""
        print("Current Settings:")

        # Get key properties for summary
        typography = self._get_section("typography")
        colors = self._get_section("colors")
        layout = self._get_section("layout")

        if typography:
            body_font = self._get_property(typography, "body_font")
            font_size = self._get_property(typography, "body_font_size")
            print(f"  Font: {body_font.current_value} ({font_size.current_value})")

        if colors:
            text_color = self._get_property(colors, "text_color")
            bg_color = self._get_property(colors, "background_color")
            print(f"  Colors: Text {text_color.current_value}, Background {bg_color.current_value}")

        if layout:
            margin = self._get_property(layout, "page_margin")
            align = self._get_property(layout, "text_align")
            print(f"  Layout: {margin.current_value} margin, {align.current_value} aligned")

    def _edit_section(self, section_name: str):
        """Edit properties in a specific section."""
        section = self._get_section(section_name)
        if not section:
            print(f"❌ Section not found: {section_name}")
            return

        print(f"\n📝 Editing {section.display_name}")
        print(f"   {section.description}")
        print("-" * 40)

        while True:
            # Display current properties
            for i, prop in enumerate(section.properties, 1):
                print(f"  {i}. {prop.display_name}: {prop.current_value}")
                print(f"     {prop.description}")

            print(f"  {len(section.properties) + 1}. Back to main menu")

            choice = prompt("Select property to edit (number)")

            if choice.isdigit():
                prop_index = int(choice) - 1
                if 0 <= prop_index < len(section.properties):
                    self._edit_property(section.properties[prop_index])
                elif prop_index == len(section.properties):
                    break
                else:
                    print("❌ Invalid selection")
            else:
                print("❌ Please enter a number")

    def _edit_property(self, prop: ThemeProperty):
        """Edit a single theme property."""
        print(f"\n✏️  Editing {prop.display_name}")
        print(f"   {prop.description}")
        print(f"   Current value: {prop.current_value}")

        if prop.property_type == "choice":
            self._edit_choice_property(prop)
        elif prop.property_type == "color":
            self._edit_color_property(prop)
        elif prop.property_type == "size":
            self._edit_size_property(prop)
        else:
            self._edit_text_property(prop)

    def _edit_choice_property(self, prop: ThemeProperty):
        """Edit a property with predefined choices."""
        if not prop.choices:
            return

        print("\nAvailable options:")
        for i, choice in enumerate(prop.choices, 1):
            marker = "→" if choice == prop.current_value else " "
            print(f"  {i}. {marker} {choice}")

        selection = prompt("Select option (number)")

        if selection.isdigit():
            choice_index = int(selection) - 1
            if 0 <= choice_index < len(prop.choices):
                old_value = prop.current_value
                prop.current_value = prop.choices[choice_index]
                print(f"✅ Changed from '{old_value}' to '{prop.current_value}'")
            else:
                print("❌ Invalid selection")
        else:
            print("❌ Please enter a number")

    def _edit_color_property(self, prop: ThemeProperty):
        """Edit a color property."""
        print("\nColor formats supported:")
        print("  • Hex: #000000, #fff")
        print("  • Named: black, white, red")
        print("  • RGB: rgb(255, 255, 255)")

        new_color = prompt(f"Enter new color [{prop.current_value}]")

        if new_color and self._validate_color(new_color):
            old_value = prop.current_value
            prop.current_value = new_color
            print(f"✅ Changed from '{old_value}' to '{prop.current_value}'")
        elif new_color:
            print("❌ Invalid color format")

    def _edit_size_property(self, prop: ThemeProperty):
        """Edit a size property."""
        unit_info = f" ({prop.unit})" if prop.unit else ""
        range_info = ""

        if prop.min_value is not None and prop.max_value is not None:
            range_info = f" (range: {prop.min_value}-{prop.max_value})"

        new_size = prompt(f"Enter new size{unit_info}{range_info} [{prop.current_value}]")

        if new_size and self._validate_size(new_size, prop):
            old_value = prop.current_value
            prop.current_value = new_size
            print(f"✅ Changed from '{old_value}' to '{prop.current_value}'")
        elif new_size:
            print("❌ Invalid size format or out of range")

    def _edit_text_property(self, prop: ThemeProperty):
        """Edit a general text property."""
        new_value = prompt(f"Enter new value [{prop.current_value}]")

        if new_value:
            old_value = prop.current_value
            prop.current_value = new_value
            print(f"✅ Changed from '{old_value}' to '{prop.current_value}'")

    def _edit_custom_css(self):
        """Edit custom CSS rules."""
        print("\n📝 Custom CSS Editor")
        print("Enter additional CSS rules to customize your theme further.")
        print("Press Ctrl+D (Unix) or Ctrl+Z (Windows) when finished.")
        print("Current custom CSS:")

        if self.current_theme.custom_css:
            print(self.current_theme.custom_css)
        else:
            print("(none)")

        print("\nEnter new CSS:")

        css_lines = []
        try:
            while True:
                line = input()
                css_lines.append(line)
        except EOFError:
            pass

        if css_lines:
            self.current_theme.custom_css = "\n".join(css_lines)
            print("✅ Custom CSS updated")

    def _generate_live_preview(self):
        """Generate a live preview of the theme."""
        print("\n🔍 Generating theme preview...")

        try:
            # Generate CSS from current theme
            css_content = self._generate_css()

            # Create HTML preview
            html_content = self._generate_preview_html(css_content)

            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False, encoding="utf-8"
            ) as f:
                f.write(html_content)
                preview_path = Path(f.name)

            print(f"✅ Preview generated: {preview_path}")

            if prompt_bool("Open preview in browser?"):
                webbrowser.open(f"file://{preview_path}")

        except Exception as e:
            print(f"❌ Failed to generate preview: {e}")

    def _generate_css(self) -> str:
        """Generate CSS from current theme settings."""
        css_rules = []

        # Add base CSS
        css_rules.append("/* Generated by Docx2Shelf Theme Editor */")

        # Typography
        typography = self._get_section("typography")
        if typography:
            body_font = self._get_property(typography, "body_font")
            heading_font = self._get_property(typography, "heading_font")
            font_size = self._get_property(typography, "body_font_size")
            line_height = self._get_property(typography, "line_height")

            css_rules.append("body {")
            css_rules.append(f"    font-family: {body_font.current_value};")
            css_rules.append(f"    font-size: {font_size.current_value};")
            css_rules.append(f"    line-height: {line_height.current_value};")
            css_rules.append("}")

            css_rules.append("h1, h2, h3, h4, h5, h6 {")
            css_rules.append(f"    font-family: {heading_font.current_value};")
            css_rules.append("}")

        # Colors
        colors = self._get_section("colors")
        if colors:
            text_color = self._get_property(colors, "text_color")
            bg_color = self._get_property(colors, "background_color")
            link_color = self._get_property(colors, "link_color")
            heading_color = self._get_property(colors, "heading_color")

            css_rules.append("body {")
            css_rules.append(f"    color: {text_color.current_value};")
            css_rules.append(f"    background-color: {bg_color.current_value};")
            css_rules.append("}")

            css_rules.append("a {")
            css_rules.append(f"    color: {link_color.current_value};")
            css_rules.append("}")

            css_rules.append("h1, h2, h3, h4, h5, h6 {")
            css_rules.append(f"    color: {heading_color.current_value};")
            css_rules.append("}")

        # Layout
        layout = self._get_section("layout")
        if layout:
            margin = self._get_property(layout, "page_margin")
            spacing = self._get_property(layout, "paragraph_spacing")
            align = self._get_property(layout, "text_align")

            css_rules.append("body {")
            css_rules.append(f"    margin: {margin.current_value};")
            css_rules.append(f"    text-align: {align.current_value};")
            css_rules.append("}")

            css_rules.append("p {")
            css_rules.append(f"    margin-bottom: {spacing.current_value};")
            css_rules.append("}")

        # Custom CSS
        if self.current_theme.custom_css:
            css_rules.append("\n/* Custom CSS */")
            css_rules.append(self.current_theme.custom_css)

        return "\n".join(css_rules)

    def _generate_preview_html(self, css_content: str) -> str:
        """Generate HTML preview with the theme applied."""
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Theme Preview - {self.current_theme.display_name}</title>
    <style>
        {css_content}

        /* Preview-specific styles */
        .preview-container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 2em;
        }}

        .theme-info {{
            background: #f5f5f5;
            padding: 1em;
            margin-bottom: 2em;
            border-left: 3px solid #0066cc;
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <div class="theme-info">
            <h3>Theme Preview</h3>
            <p><strong>Theme:</strong> {self.current_theme.display_name}</p>
            <p><strong>Base:</strong> {self.current_theme.base_theme}</p>
        </div>

        <h1>Chapter 1: The Beginning</h1>

        <p>This is a preview of your custom theme. The quick brown fox jumps over the lazy dog.
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
        ut labore et dolore magna aliqua.</p>

        <h2>A Second-Level Heading</h2>

        <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
        commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum
        dolore eu fugiat nulla pariatur.</p>

        <p>Here is a paragraph with a <a href="#">hyperlink example</a> to show link styling.
        Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit
        anim id est laborum.</p>

        <h3>A Third-Level Heading</h3>

        <p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque
        laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi
        architecto beatae vitae dicta sunt explicabo.</p>

        <blockquote>
            <p>This is a blockquote to demonstrate quote styling. Nemo enim ipsam voluptatem quia
            voluptas sit aspernatur aut odit aut fugit.</p>
        </blockquote>

        <p>At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium
        voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati
        cupiditate non provident.</p>
    </div>
</body>
</html>"""
        return html_template

    def _save_theme(self) -> bool:
        """Save the current theme to disk."""
        try:
            # Generate theme data
            theme_data = {
                "name": self.current_theme.name,
                "display_name": self.current_theme.display_name,
                "description": self.current_theme.description,
                "base_theme": self.current_theme.base_theme,
                "css": self._generate_css(),
                "properties": self._serialize_properties(),
                "custom_css": self.current_theme.custom_css,
                "created_with": "Docx2Shelf Theme Editor",
            }

            # Save to theme file
            theme_file = self.themes_dir / f"{self.current_theme.name}.json"
            with open(theme_file, "w", encoding="utf-8") as f:
                json.dump(theme_data, f, indent=2)

            # Also save as CSS file
            css_file = self.themes_dir / f"{self.current_theme.name}.css"
            with open(css_file, "w", encoding="utf-8") as f:
                f.write(self._generate_css())

            print(f"Theme saved to: {theme_file}")
            return True

        except Exception as e:
            print(f"Failed to save theme: {e}")
            return False

    def _export_theme(self):
        """Export theme for sharing."""
        export_path = prompt("Export path (optional)")

        if not export_path:
            export_path = f"{self.current_theme.name}_theme.css"

        try:
            css_content = self._generate_css()

            with open(export_path, "w", encoding="utf-8") as f:
                f.write(css_content)

            print(f"✅ Theme exported to: {export_path}")

        except Exception as e:
            print(f"❌ Export failed: {e}")

    def _reset_to_defaults(self):
        """Reset all properties to their default values."""
        for section in self.current_theme.sections:
            for prop in section.properties:
                prop.current_value = prop.default_value

        self.current_theme.custom_css = ""
        print("✅ All settings reset to defaults")

    def _serialize_properties(self) -> Dict[str, Any]:
        """Serialize current property values for saving."""
        properties = {}

        for section in self.current_theme.sections:
            for prop in section.properties:
                properties[prop.name] = prop.current_value

        return properties

    def _get_section(self, name: str) -> Optional[ThemeSection]:
        """Get a section by name."""
        for section in self.current_theme.sections:
            if section.name == name:
                return section
        return None

    def _get_property(self, section: ThemeSection, name: str) -> Optional[ThemeProperty]:
        """Get a property by name from a section."""
        for prop in section.properties:
            if prop.name == name:
                return prop
        return None

    def _validate_color(self, color: str) -> bool:
        """Validate a color value."""
        color = color.strip()

        # Hex colors
        if re.match(r"^#[0-9A-Fa-f]{3}$", color) or re.match(r"^#[0-9A-Fa-f]{6}$", color):
            return True

        # RGB colors
        if re.match(r"^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$", color):
            return True

        # Named colors (basic check)
        named_colors = [
            "black",
            "white",
            "red",
            "green",
            "blue",
            "yellow",
            "cyan",
            "magenta",
            "gray",
            "grey",
            "darkred",
            "darkgreen",
            "darkblue",
            "orange",
            "purple",
            "brown",
            "pink",
            "lime",
            "navy",
            "maroon",
            "olive",
            "teal",
            "silver",
        ]

        return color.lower() in named_colors

    def _validate_size(self, size: str, prop: ThemeProperty) -> bool:
        """Validate a size value."""
        size = size.strip()

        # Extract numeric value
        try:
            if prop.unit:
                # Remove unit if present
                if size.endswith(prop.unit):
                    numeric_part = size[: -len(prop.unit)]
                else:
                    numeric_part = size
            else:
                numeric_part = size

            value = float(numeric_part)

            # Check range
            if prop.min_value is not None and value < prop.min_value:
                return False
            if prop.max_value is not None and value > prop.max_value:
                return False

            return True

        except ValueError:
            return False

    def _get_sample_content(self) -> str:
        """Get sample content for preview."""
        return """
        <h1>Chapter 1: The Adventure Begins</h1>
        <p>This is sample content to preview your theme. The quick brown fox jumps over the lazy dog.</p>
        <h2>A Subheading</h2>
        <p>More sample text with a <a href="#">link example</a> to show styling.</p>
        """


def run_theme_editor(base_theme: str = "serif") -> int:
    """Run the theme editor.

    Args:
        base_theme: Base theme to start from

    Returns:
        Exit code (0 for success)
    """
    editor = ThemeEditor()
    return editor.start_editor(base_theme)
