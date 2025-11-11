# Icon Guidelines for Docx2Shelf

Comprehensive guidelines for consistent icon usage throughout the application.

## Icon System Overview

The Docx2Shelf application uses a unified icon system based on modern icon design principles. All icons should follow these guidelines to maintain visual consistency and professional appearance.

## Icon Standards

### Size Standards

Icons are available in standardized sizes to match their context:

- **16px** - Navigation, toolbar, inline
- **20px** - Buttons, list items
- **24px** - Primary buttons, headers
- **32px** - Dialog headers, featured actions
- **48px** - Large feature icons, empty states
- **64px** - Application icon, hero sections
- **128px** - Application installer icon

### Style Consistency

All icons in Docx2Shelf follow a unified style:

- **Stroke Weight**: 2px for 16-24px icons, 1.5px for larger icons
- **Corner Radius**: 2px for consistent roundness
- **Padding**: Built-in padding to prevent crowding
- **Colors**: Follow theme colors (primary, secondary, semantic)
- **Format**: SVG for scalability, PNG fallback

### Icon Categories

#### Navigation Icons
Used in menus and navigation systems.

```
- Home
- Settings
- Help
- About
- Exit/Close
- Menu (hamburger)
- Back (chevron)
- Forward (chevron)
```

#### Document Actions
Used for document-related operations.

```
- New Document
- Open File
- Save
- Export
- Import
- Upload
- Download
- Delete
- Duplicate
- Rename
```

#### Formatting Icons
Used in text and document formatting.

```
- Bold
- Italic
- Underline
- Align Left
- Align Center
- Align Right
- Justify
- Heading 1-6
- List (ordered)
- List (unordered)
- Indent
- Outdent
```

#### Status Icons
Indicate document or operation status.

```
- Success (checkmark in circle)
- Error (X in circle)
- Warning (exclamation in triangle)
- Info (i in circle)
- Processing (spinner)
- Pause
- Resume
- Complete
```

#### Feature Icons
Represent major features and settings.

```
- Convert (arrows or gears)
- Settings (gear or sliders)
- Theme (sun/moon)
- Accessibility
- Security
- Analytics
- Plugins
- Marketplace
```

#### Social & External
Links to external services.

```
- GitHub
- Web Link
- Share
- Download
- Upload
```

## Usage Examples

### In Buttons

```python
from docx2shelf.ui_enhancements import ModernButton

# With icon (emoji as fallback)
convert_btn = ModernButton(
    parent,
    text="📄 Convert to EPUB",
    command=convert,
    variant="primary"
)

settings_btn = ModernButton(
    parent,
    text="⚙️ Settings",
    command=open_settings,
    variant="secondary"
)
```

### In Navigation

```python
import customtkinter as ctk

nav_items = [
    ("🏠", "Home", home_command),
    ("📄", "Documents", docs_command),
    ("⚙️", "Settings", settings_command),
    ("❓", "Help", help_command),
]

for icon, label, command in nav_items:
    btn = ctk.CTkButton(
        nav_frame,
        text=f"{icon} {label}",
        command=command
    )
    btn.pack(fill="x", padx=10, pady=5)
```

### In Status Messages

```python
from docx2shelf.ui_enhancements import VisualFeedback, FeedbackType

# Icons are built into FeedbackType colors
VisualFeedback.create_toast(
    window,
    "✓ Conversion complete!",
    FeedbackType.SUCCESS
)

VisualFeedback.create_toast(
    window,
    "⚠ Please select a file",
    FeedbackType.WARNING
)

VisualFeedback.create_toast(
    window,
    "✗ Conversion failed",
    FeedbackType.ERROR
)
```

## Icon Recommendations by Context

### Toolbar
- Size: 20px
- Color: Theme-aware (text_primary in light theme, text_secondary in dark)
- Spacing: 8px horizontal padding

### Buttons
- Size: 16-20px
- Color: Match text color of button
- Alignment: Left of text with 6-8px spacing

### Navigation Menu
- Size: 20-24px
- Color: Primary or secondary based on state
- Padding: 10px around icon

### Headers
- Size: 24-32px
- Color: Primary color
- Padding: 10-20px

### Empty States
- Size: 48-64px
- Color: Light gray (text_secondary)
- Positioning: Centered

### Dialogs
- Size: 32px (header), 20px (action buttons)
- Color: Theme-aware

## Icon Sets

### Recommended Free Icon Libraries

1. **Material Design Icons** (Google)
   - Format: SVG, PNG
   - License: Apache 2.0
   - Sizes: 16, 24, 48px
   - URL: https://fonts.google.com/icons

2. **Feather Icons** (Cole Bemis)
   - Format: SVG
   - License: MIT
   - Sizes: 24px (scalable)
   - URL: https://feathericons.com

3. **Bootstrap Icons** (Bootstrap)
   - Format: SVG, Font
   - License: MIT
   - Sizes: Scalable
   - URL: https://icons.getbootstrap.com

### Icon Usage in Code

```python
# Using emoji (built-in, no dependencies)
button = ModernButton(parent, text="🔄 Refresh", command=refresh)

# Using text icons (accessible, theme-aware)
button = ModernButton(parent, text="✓ Complete", command=complete)

# Using custom SVG (advanced)
from PIL import Image, ImageTk

icon_image = Image.open("path/to/icon.png")
icon_photo = ImageTk.PhotoImage(icon_image)
button = ctk.CTkButton(parent, image=icon_photo, text="")
```

## Icon Color Guidelines

### Light Theme
- Primary Icons: Use `#0078D4` (primary color)
- Secondary Icons: Use `#6C757D` (secondary color)
- Success Icons: Use `#28A745` (success color)
- Warning Icons: Use `#FFC107` (warning color)
- Error Icons: Use `#DC3545` (error color)
- Disabled Icons: Use `#E0E0E0` (light border)

### Dark Theme
- Primary Icons: Use `#0078D4` (primary color)
- Secondary Icons: Use `#B4B4B4` (text secondary)
- Success Icons: Use `#28A745` (success color)
- Warning Icons: Use `#FFC107` (warning color)
- Error Icons: Use `#DC3545` (error color)
- Disabled Icons: Use `#404040` (border)

## Icon Export Guidelines

If creating custom icons:

1. **Design in vector format** (Illustrator, Figma, Inkscape)
2. **Export as SVG** with:
   - No embedded fonts
   - Strokes converted to paths (for Web)
   - Viewbox preserved
   - Clean code

3. **Create PNG fallbacks** at multiple sizes:
   - 16x16px @ 1x and 2x
   - 24x24px @ 1x and 2x
   - 32x32px @ 1x and 2x
   - 48x48px @ 1x and 2x

4. **Optimize files**:
   - SVG: Use SVGO
   - PNG: Use PNGQuant or similar

## Implementation Checklist

When adding new icons to the application:

- [ ] Icon style matches existing icons
- [ ] Icon size is appropriate for context
- [ ] Icon has sufficient padding around it
- [ ] Icon color contrasts with background
- [ ] Icon has alt text or accessibility label
- [ ] Icon works in light and dark themes
- [ ] Icon is optimized (SVG or compressed PNG)
- [ ] Icon is placed in correct directory
- [ ] Icon is referenced in code correctly
- [ ] Icon tested on target screen sizes

## Directory Structure

```
src/docx2shelf/
├── assets/
│   ├── icons/
│   │   ├── navigation/
│   │   │   ├── home.svg
│   │   │   ├── settings.svg
│   │   │   └── help.svg
│   │   ├── actions/
│   │   │   ├── convert.svg
│   │   │   ├── save.svg
│   │   │   └── delete.svg
│   │   ├── status/
│   │   │   ├── success.svg
│   │   │   ├── error.svg
│   │   │   └── warning.svg
│   │   └── features/
│   │       ├── plugin.svg
│   │       ├── theme.svg
│   │       └── accessibility.svg
│   └── icon.ico (main app icon)
```

## Accessibility Considerations

1. **Meaningful Labels**: Every icon button needs a text label or aria-label
2. **Color Not Alone**: Don't rely on color to convey meaning
3. **Keyboard Navigation**: All icon buttons must be keyboard accessible
4. **Screen Reader Text**: Include descriptive text for screen readers

```python
from docx2shelf.ui_enhancements import AccessibilitySupport, ModernButton

# Good - descriptive label
button = ModernButton(parent, text="🔄 Refresh Document", command=refresh)

# Better - with accessibility label
button = ModernButton(parent, text="🔄", command=refresh)
AccessibilitySupport.add_aria_label(button, "Refresh the current document")
```

## Performance Tips

1. **Use Emoji for Basic Icons** - No file I/O needed
2. **Cache Icons** - Load once, use multiple times
3. **Use Proper Formats** - SVG for scalability, PNG for complex graphics
4. **Optimize Sizes** - Compress before use
5. **Lazy Load** - Load icons only when needed

## Common Mistakes to Avoid

❌ **Don't:**
- Mix icon styles (emoji with Material Design)
- Use inconsistent icon sizes
- Rely on color alone for meaning
- Add text + icon in small spaces
- Use low-contrast colors
- Forget accessibility labels

✅ **Do:**
- Keep icons consistent in style
- Use standard sizes (16, 20, 24, 32px)
- Provide text or labels with icons
- Test icons for color contrast
- Include accessibility information
- Test icons on all supported themes

---

**Last Updated**: 2025-11-11
**Version**: 1.0.0
**Maintainer**: Docx2Shelf Team
