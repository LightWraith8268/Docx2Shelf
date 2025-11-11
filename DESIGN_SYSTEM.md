# Docx2Shelf Design System

A comprehensive modern design system for the Docx2Shelf application built on CustomTkinter with Material Design 3 principles.

## Table of Contents

1. [Colors](#colors)
2. [Typography](#typography)
3. [Components](#components)
4. [Animations](#animations)
5. [Accessibility](#accessibility)
6. [Responsive Design](#responsive-design)
7. [Usage Examples](#usage-examples)

---

## Colors

### Color Palette

The design system uses semantic color tokens organized by purpose rather than just hue.

#### Dark Theme (Default)

**Primary Colors**
- Primary: `#0078D4` (Microsoft blue)
- Primary Hover: `#106EBE` (darker blue)
- Primary Active: `#004578` (darkest blue)

**Semantic Colors**
- Success: `#28A745` (green)
- Warning: `#FFC107` (amber)
- Error: `#DC3545` (red)
- Info: `#17A2B8` (cyan)

**Neutral Colors**
- Background: `#1E1E1E`
- Surface: `#2D2D2D`
- Surface Hover: `#3D3D3D`
- Border: `#404040`
- Text Primary: `#FFFFFF`
- Text Secondary: `#B4B4B4`

**Gradients**
- Primary Gradient: `#0078D4` → `#106EBE`
- Success Gradient: `#28A745` → `#20C997`
- Warning Gradient: `#FFC107` → `#FF9800`

### Using Colors in Code

```python
from docx2shelf.ui_enhancements import DARK_THEME, LIGHT_THEME

# Access colors
button.configure(fg_color=DARK_THEME.primary)
label.configure(text_color=DARK_THEME.text_secondary)
```

---

## Typography

### Font Scales

The typography system provides a structured hierarchy of font sizes for consistent visual hierarchy.

**Display & Headings**
- Display: 24px (Bold) - Main page headers
- H1: 20px (Bold) - Section headers
- H2: 18px (Semibold) - Subsection headers
- H3: 16px (Semibold) - Minor headings
- H4: 14px (Semibold) - Small headings

**Body Text**
- Body: 13px (Regular) - Default text
- Body-Small: 12px (Regular) - Secondary text
- Caption: 11px (Regular) - Helper text, labels

### Font Families

- **Display & Body**: `Segoe UI, -apple-system, BlinkMacSystemFont` (system fonts)
- **Monospace**: `Consolas, Monaco, monospace` (code display)

### Using Typography in Code

```python
from docx2shelf.ui_enhancements import ModernLabel, TYPOGRAPHY

# Using ModernLabel with variants
title = ModernLabel(parent, text="Title", variant="h1")
subtitle = ModernLabel(parent, text="Subtitle", variant="h3")
body = ModernLabel(parent, text="Body text", variant="body")
caption = ModernLabel(parent, text="Helper text", variant="caption")

# Direct font access
font_size = TYPOGRAPHY.size_lg
font_weight = TYPOGRAPHY.weight_semibold
```

---

## Components

### Modern Button

Professional button component with size and variant options.

```python
from docx2shelf.ui_enhancements import ModernButton

# Primary button
btn = ModernButton(
    parent,
    text="Convert Document",
    command=convert_action,
    variant="primary",
    size="md"
)

# Danger button
delete_btn = ModernButton(
    parent,
    text="Delete",
    command=delete_action,
    variant="danger",
    size="sm"
)
```

**Variants**: `primary`, `secondary`, `success`, `danger`
**Sizes**: `sm`, `md`, `lg`

### Modern Entry

Text input field with placeholder support and placeholder styling.

```python
from docx2shelf.ui_enhancements import ModernEntry

entry = ModernEntry(
    parent,
    placeholder="Enter title...",
    width=300
)
```

### Modern Label

Label with typography hierarchy variants.

```python
from docx2shelf.ui_enhancements import ModernLabel

title = ModernLabel(parent, text="Document Title", variant="h1")
desc = ModernLabel(parent, text="Description", variant="body")
helper = ModernLabel(parent, text="Helper text", variant="caption")
```

### Gradient Frame

Frame with gradient background effect.

```python
from docx2shelf.ui_enhancements import GradientFrame

gradient = GradientFrame(
    parent,
    gradient_colors=("#0078D4", "#106EBE"),
    corner_radius=12
)
```

### Hover Effects

Add hover interactions to widgets.

```python
from docx2shelf.ui_enhancements import HoverEffect

button = HoverEffect.create_hover_button(
    parent,
    text="Hover Me",
    command=action,
    fg_color="#0078D4",
    hover_color="#106EBE"
)

label = HoverEffect.create_hover_label(
    parent,
    text="Interactive Label",
    normal_color="#B4B4B4",
    hover_color="#FFFFFF"
)
```

---

## Animations

### Basic Animation

Smooth animated transitions using easing functions.

```python
from docx2shelf.ui_enhancements import animate, EasingFunction

def animate_opacity(progress):
    widget.configure(text_color=f"#{int(255*progress):02x}")

animate(
    callback=animate_opacity,
    duration=0.5,
    easing=EasingFunction.EASE_OUT
)
```

### Animation Sequence

Chain multiple animations together.

```python
from docx2shelf.ui_enhancements import AnimationSequence, EasingFunction

sequence = AnimationSequence()
sequence.add(animate_step1, duration=0.3, easing=EasingFunction.EASE_OUT)
sequence.add(animate_step2, duration=0.4, easing=EasingFunction.EASE_IN)
sequence.add(animate_step3, duration=0.3, easing=EasingFunction.LINEAR)

sequence.play(root=window, on_complete=on_complete_callback)
```

### Available Easing Functions

- `LINEAR` - Constant speed
- `EASE_IN` - Slow start, fast end
- `EASE_OUT` - Fast start, slow end
- `EASE_IN_OUT` - Slow start and end
- `EASE_IN_CUBIC` - Cubic ease in
- `EASE_OUT_CUBIC` - Cubic ease out

---

## Visual Feedback

### Toast Notifications

Temporary messages with auto-dismiss.

```python
from docx2shelf.ui_enhancements import VisualFeedback, FeedbackType

VisualFeedback.create_toast(
    window,
    "Document converted successfully!",
    feedback_type=FeedbackType.SUCCESS,
    duration=3.0
)

VisualFeedback.create_toast(
    window,
    "An error occurred",
    feedback_type=FeedbackType.ERROR,
    duration=3.0
)
```

### Progress Ring

Animated circular progress indicator.

```python
from docx2shelf.ui_enhancements import VisualFeedback

ring = VisualFeedback.create_progress_ring(
    parent,
    size=60,
    thickness=4,
    color="#0078D4"
)

# Update progress
ring._draw_ring(0.5)  # 50% progress
```

### Status Indicator

Small colored dot showing status.

```python
from docx2shelf.ui_enhancements import VisualFeedback, FeedbackType

indicator = VisualFeedback.create_status_indicator(
    parent,
    status=FeedbackType.SUCCESS,
    size=12
)
```

---

## Accessibility

### Keyboard Navigation

Add keyboard navigation support to your application.

```python
from docx2shelf.ui_enhancements import AccessibilitySupport

widgets = [button1, button2, input_field, button3]
AccessibilitySupport.add_keyboard_navigation(window, widgets)

# Tab: move to next widget
# Shift+Tab: move to previous widget
```

### ARIA Labels

Add accessible labels for screen readers.

```python
from docx2shelf.ui_enhancements import AccessibilitySupport

AccessibilitySupport.add_aria_label(
    button,
    "Convert DOCX file to EPUB format"
)
```

### Focus Management

Make widgets focusable with keyboard.

```python
from docx2shelf.ui_enhancements import AccessibilitySupport

AccessibilitySupport.make_widget_focusable(button)
```

---

## Responsive Design

### Responsive Grid

Configure flexible grid layouts that adapt to content.

```python
from docx2shelf.ui_enhancements import ResponsiveGrid

# Configure columns
ResponsiveGrid.configure_responsive_columns(
    parent,
    num_columns=3,
    min_width=200
)

# Configure rows
ResponsiveGrid.configure_responsive_rows(
    parent,
    num_rows=4,
    min_height=50
)

# Place widgets in grid
widget1.grid(row=0, column=0, padx=10, pady=10)
widget2.grid(row=0, column=1, padx=10, pady=10)
```

---

## Usage Examples

### Complete Modern Interface Example

```python
import customtkinter as ctk
from docx2shelf.ui_enhancements import (
    ModernButton, ModernLabel, ModernEntry,
    GradientFrame, HoverEffect, VisualFeedback,
    FeedbackType, DARK_THEME, ResponsiveGrid
)

class ModernApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Docx2Shelf App")
        self.root.geometry("800x600")

        # Configure responsive grid
        ResponsiveGrid.configure_responsive_columns(root, 2, min_width=300)
        ResponsiveGrid.configure_responsive_rows(root, 3, min_height=100)

        # Create header with gradient
        header = GradientFrame(
            root,
            gradient_colors=("#0078D4", "#106EBE"),
            corner_radius=12
        )
        header.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)

        ModernLabel(
            header,
            text="Document Converter",
            variant="h1"
        ).pack(pady=20)

        # Create form
        form_frame = ctk.CTkFrame(root)
        form_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)

        ModernLabel(form_frame, text="Select Document", variant="h3").pack(pady=5)

        entry = ModernEntry(
            form_frame,
            placeholder="Enter file path...",
            width=400
        )
        entry.pack(pady=10)

        # Create buttons with hover effects
        button_frame = ctk.CTkFrame(root)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)

        convert_btn = ModernButton(
            button_frame,
            text="Convert to EPUB",
            command=self.convert,
            variant="primary",
            size="lg"
        )
        convert_btn.pack(side="left", padx=5)

        cancel_btn = ModernButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            variant="secondary",
            size="lg"
        )
        cancel_btn.pack(side="left", padx=5)

    def convert(self):
        VisualFeedback.create_toast(
            self.root,
            "Converting document...",
            FeedbackType.INFO
        )

    def cancel(self):
        VisualFeedback.create_toast(
            self.root,
            "Operation cancelled",
            FeedbackType.WARNING
        )

if __name__ == "__main__":
    root = ctk.CTk()
    app = ModernApp(root)
    root.mainloop()
```

---

## Best Practices

1. **Use Semantic Colors**: Use `DARK_THEME.success` instead of hardcoded colors
2. **Maintain Hierarchy**: Use typography variants consistently for visual hierarchy
3. **Add Feedback**: Always provide visual feedback for user actions
4. **Animate Transitions**: Use animations for state changes, not just eye candy
5. **Keyboard Navigation**: Always make interactive elements keyboard accessible
6. **Responsive Layouts**: Use ResponsiveGrid for flexible layouts
7. **Consistent Spacing**: Use padding/margin consistently throughout
8. **Theme Support**: Use colors that work with both light and dark themes

---

## Migration Guide

### Updating Existing Components

**Before**
```python
button = ctk.CTkButton(
    parent,
    text="Click Me",
    fg_color="#0078D4",
    font=("Arial", 12)
)
```

**After**
```python
from docx2shelf.ui_enhancements import ModernButton, TYPOGRAPHY

button = ModernButton(
    parent,
    text="Click Me",
    variant="primary",
    size="md"
)
```

---

## Contributing

When adding new components to the design system:

1. Extend from the modern component base classes
2. Use design tokens from `DARK_THEME` and `LIGHT_THEME`
3. Use `TYPOGRAPHY` for font configuration
4. Add documentation in this file
5. Include usage examples
6. Support both light and dark themes

---

**Last Updated**: 2025-11-11
**Version**: 1.0.0
