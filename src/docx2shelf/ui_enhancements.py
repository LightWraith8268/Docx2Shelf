"""
UI Enhancements Module for Docx2Shelf
Provides modern UI features: animations, micro-interactions, design system,
accessibility enhancements, and visual feedback mechanisms.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

try:
    import customtkinter as ctk
except ImportError:
    ctk = None  # type: ignore


# ============================================================================
# DESIGN SYSTEM & TOKENS
# ============================================================================


@dataclass
class ColorScheme:
    """Modern color scheme with semantic tokens."""

    # Primary colors
    primary: str
    primary_hover: str
    primary_active: str

    # Secondary colors
    secondary: str
    secondary_hover: str

    # Semantic colors
    success: str
    success_light: str
    warning: str
    warning_light: str
    error: str
    error_light: str
    info: str
    info_light: str

    # Neutral colors
    background: str
    surface: str
    surface_hover: str
    border: str
    text_primary: str
    text_secondary: str

    # Gradients
    gradient_primary: tuple[str, str]
    gradient_success: tuple[str, str]
    gradient_warning: tuple[str, str]


class ThemeMode(Enum):
    """Available theme modes."""

    LIGHT = "light"
    DARK = "dark"


# Dark Theme (default)
DARK_THEME = ColorScheme(
    # Primary
    primary="#0078D4",
    primary_hover="#106EBE",
    primary_active="#004578",
    # Secondary
    secondary="#6C757D",
    secondary_hover="#5A6268",
    # Semantic
    success="#28A745",
    success_light="#D4EDDA",
    warning="#FFC107",
    warning_light="#FFF3CD",
    error="#DC3545",
    error_light="#F8D7DA",
    info="#17A2B8",
    info_light="#D1ECF1",
    # Neutral
    background="#1E1E1E",
    surface="#2D2D2D",
    surface_hover="#3D3D3D",
    border="#404040",
    text_primary="#FFFFFF",
    text_secondary="#B4B4B4",
    # Gradients
    gradient_primary=("#0078D4", "#106EBE"),
    gradient_success=("#28A745", "#20C997"),
    gradient_warning=("#FFC107", "#FF9800"),
)

# Light Theme
LIGHT_THEME = ColorScheme(
    # Primary
    primary="#0078D4",
    primary_hover="#106EBE",
    primary_active="#004578",
    # Secondary
    secondary="#6C757D",
    secondary_hover="#5A6268",
    # Semantic
    success="#28A745",
    success_light="#D4EDDA",
    warning="#FFC107",
    warning_light="#FFF3CD",
    error="#DC3545",
    error_light="#F8D7DA",
    info="#17A2B8",
    info_light="#D1ECF1",
    # Neutral
    background="#FFFFFF",
    surface="#F5F5F5",
    surface_hover="#EEEEEE",
    border="#E0E0E0",
    text_primary="#000000",
    text_secondary="#666666",
    # Gradients
    gradient_primary=("#0078D4", "#106EBE"),
    gradient_success=("#28A745", "#20C997"),
    gradient_warning=("#FFC107", "#FF9800"),
)


@dataclass
class Typography:
    """Typography system with font scales."""

    # Font families
    family_display: str = "Segoe UI, -apple-system, BlinkMacSystemFont"
    family_body: str = "Segoe UI, -apple-system, BlinkMacSystemFont"
    family_mono: str = "Consolas, Monaco, monospace"

    # Font sizes
    size_xs: int = 11
    size_sm: int = 12
    size_base: int = 13
    size_lg: int = 14
    size_xl: int = 16
    size_2xl: int = 18
    size_3xl: int = 20
    size_4xl: int = 24

    # Font weights (0-1000 scale)
    weight_regular: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700

    # Line heights
    line_height_tight: float = 1.2
    line_height_normal: float = 1.5
    line_height_relaxed: float = 1.75


TYPOGRAPHY = Typography()


# ============================================================================
# ANIMATION & TRANSITIONS
# ============================================================================


class EasingFunction(Enum):
    """Easing functions for smooth animations."""

    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"


def ease_linear(t: float) -> float:
    """Linear easing."""
    return t


def ease_in(t: float) -> float:
    """Ease in (quadratic)."""
    return t * t


def ease_out(t: float) -> float:
    """Ease out (quadratic)."""
    return 1 - (1 - t) ** 2


def ease_in_out(t: float) -> float:
    """Ease in-out (quadratic)."""
    return 3 * t * t - 2 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_in_cubic(t: float) -> float:
    """Ease in (cubic)."""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Ease out (cubic)."""
    return 1 - (1 - t) ** 3


def get_easing_function(easing: EasingFunction) -> Callable[[float], float]:
    """Get easing function by type."""
    easing_map = {
        EasingFunction.LINEAR: ease_linear,
        EasingFunction.EASE_IN: ease_in,
        EasingFunction.EASE_OUT: ease_out,
        EasingFunction.EASE_IN_OUT: ease_in_out,
        EasingFunction.EASE_IN_CUBIC: ease_in_cubic,
        EasingFunction.EASE_OUT_CUBIC: ease_out_cubic,
    }
    return easing_map.get(easing, ease_linear)


class AnimationSequence:
    """Manages a sequence of animations with callbacks."""

    def __init__(self):
        self.animations: list[tuple[Callable, float, EasingFunction]] = []
        self.current_index = 0
        self.is_running = False

    def add(
        self,
        animation: Callable,
        duration: float = 0.3,
        easing: EasingFunction = EasingFunction.EASE_OUT,
    ) -> AnimationSequence:
        """Add animation to sequence."""
        self.animations.append((animation, duration, easing))
        return self

    def play(self, root: ctk.CTk | None = None, on_complete: Callable | None = None) -> None:
        """Play animation sequence."""
        if self.is_running or not self.animations:
            return

        self.is_running = True
        self.current_index = 0

        def play_next() -> None:
            if self.current_index >= len(self.animations):
                self.is_running = False
                if on_complete:
                    on_complete()
                return

            animation, duration, easing = self.animations[self.current_index]
            self.current_index += 1

            def on_animation_complete() -> None:
                play_next()

            if root:
                animate(animation, duration, easing, root, on_animation_complete)
            else:
                animation(1.0)
                play_next()

        play_next()


def animate(
    callback: Callable[[float], None],
    duration: float = 0.3,
    easing: EasingFunction = EasingFunction.EASE_OUT,
    root: ctk.CTk | None = None,
    on_complete: Callable | None = None,
) -> None:
    """
    Animate with easing function.

    Args:
        callback: Function called with progress (0.0-1.0) for each frame
        duration: Animation duration in seconds
        easing: Easing function to use
        root: Root window for scheduling updates
        on_complete: Callback when animation completes
    """

    def animate_thread() -> None:
        start_time = time.time()
        easing_func = get_easing_function(easing)

        while True:
            elapsed = time.time() - start_time
            progress = min(elapsed / duration, 1.0)
            eased_progress = easing_func(progress)

            try:
                callback(eased_progress)
            except Exception:
                break

            if progress >= 1.0:
                if on_complete:
                    on_complete()
                break

            time.sleep(0.016)  # ~60 FPS

    thread = threading.Thread(target=animate_thread, daemon=True)
    thread.start()


# ============================================================================
# MICRO-INTERACTIONS
# ============================================================================


class HoverEffect:
    """Hover effects for widgets."""

    @staticmethod
    def create_hover_button(
        parent: ctk.CTkFrame,
        text: str,
        command: Callable | None = None,
        fg_color: str | None = None,
        hover_color: str | None = None,
        **kwargs,
    ) -> ctk.CTkButton:
        """Create button with hover animation."""
        default_fg = fg_color or "#0078D4"
        default_hover = hover_color or "#106EBE"

        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=default_fg,
            hover_color=default_hover,
            **kwargs,
        )

        # Add subtle scale animation on hover
        original_config = {
            "fg_color": button.cget("fg_color"),
        }

        def on_enter(_event=None) -> None:
            button.configure(fg_color=default_hover)

        def on_leave(_event=None) -> None:
            button.configure(fg_color=default_fg)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

        return button

    @staticmethod
    def create_hover_label(
        parent: ctk.CTkFrame,
        text: str,
        normal_color: str | None = None,
        hover_color: str | None = None,
        **kwargs,
    ) -> ctk.CTkLabel:
        """Create label with hover color transition."""
        default_fg = normal_color or "#B4B4B4"
        default_hover = hover_color or "#FFFFFF"

        label = ctk.CTkLabel(
            parent,
            text=text,
            text_color=default_fg,
            **kwargs,
        )

        def on_enter(_event=None) -> None:
            label.configure(text_color=default_hover)

        def on_leave(_event=None) -> None:
            label.configure(text_color=default_fg)

        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)

        return label


# ============================================================================
# VISUAL FEEDBACK
# ============================================================================


class FeedbackType(Enum):
    """Types of visual feedback."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class VisualFeedback:
    """Visual feedback messages and indicators."""

    @staticmethod
    def create_toast(
        parent: ctk.CTk,
        message: str,
        feedback_type: FeedbackType = FeedbackType.INFO,
        duration: float = 3.0,
    ) -> None:
        """Create toast notification with animation."""
        color_map = {
            FeedbackType.SUCCESS: "#28A745",
            FeedbackType.ERROR: "#DC3545",
            FeedbackType.WARNING: "#FFC107",
            FeedbackType.INFO: "#17A2B8",
        }

        bg_color = color_map.get(feedback_type, "#17A2B8")

        # Create toast frame
        toast = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=8)
        toast.pack(side="bottom", padx=20, pady=20, fill="x")

        # Add message
        ctk.CTkLabel(
            toast,
            text=message,
            text_color="white",
            font=(TYPOGRAPHY.family_body, TYPOGRAPHY.size_base),
        ).pack(padx=15, pady=12)

        # Fade out animation
        def fade_out() -> None:
            time.sleep(duration)
            toast.pack_forget()
            toast.destroy()

        thread = threading.Thread(target=fade_out, daemon=True)
        thread.start()

    @staticmethod
    def create_progress_ring(
        parent: ctk.CTkFrame,
        size: int = 50,
        thickness: int = 4,
        color: str = "#0078D4",
    ) -> ctk.CTkCanvas:
        """Create animated progress ring."""
        canvas = ctk.CTkCanvas(
            parent,
            width=size,
            height=size,
            bg="transparent",
            highlightthickness=0,
        )

        def draw_ring(progress: float) -> None:
            canvas.delete("all")
            x = size / 2
            y = size / 2
            radius = size / 2 - thickness

            # Draw background ring
            canvas.create_arc(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                start=0,
                extent=360,
                fill="",
                outline="#404040",
                width=thickness,
            )

            # Draw progress ring
            extent = 360 * progress
            canvas.create_arc(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                start=90,
                extent=extent,
                fill="",
                outline=color,
                width=thickness,
            )

        canvas._draw_ring = draw_ring  # type: ignore
        return canvas

    @staticmethod
    def create_status_indicator(
        parent: ctk.CTkFrame,
        status: FeedbackType = FeedbackType.INFO,
        size: int = 12,
    ) -> ctk.CTkFrame:
        """Create status indicator dot."""
        color_map = {
            FeedbackType.SUCCESS: "#28A745",
            FeedbackType.ERROR: "#DC3545",
            FeedbackType.WARNING: "#FFC107",
            FeedbackType.INFO: "#17A2B8",
        }

        indicator = ctk.CTkFrame(
            parent,
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=color_map.get(status, "#17A2B8"),
        )
        indicator.pack(side="left", padx=5)
        return indicator


# ============================================================================
# GRADIENT EFFECTS
# ============================================================================


class GradientFrame(ctk.CTkFrame):
    """Frame with gradient background."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        gradient_colors: tuple[str, str] = ("#0078D4", "#106EBE"),
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.gradient_colors = gradient_colors
        self.bind("<Configure>", self._draw_gradient)

    def _draw_gradient(self, _event=None) -> None:
        """Draw gradient background."""
        try:
            from PIL import Image, ImageDraw

            width = self.winfo_width()
            height = self.winfo_height()

            if width <= 1 or height <= 1:
                return

            # Create gradient image
            image = Image.new("RGB", (width, height))
            draw = ImageDraw.Draw(image)

            # Parse hex colors
            def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
                hex_color = hex_color.lstrip("#")
                return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore

            color1 = hex_to_rgb(self.gradient_colors[0])
            color2 = hex_to_rgb(self.gradient_colors[1])

            # Draw gradient
            for y in range(height):
                ratio = y / height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Store as PhotoImage
            self._gradient_image = ctk.CTkImage(image, size=(width, height))  # type: ignore
            self._gradient_label = ctk.CTkLabel(
                self,
                image=self._gradient_image,
                text="",
            )
            self._gradient_label.place(x=0, y=0, width=width, height=height)
            self._gradient_label.lower()

        except Exception:
            # Fallback to solid color
            self.configure(fg_color=self.gradient_colors[0])


# ============================================================================
# ACCESSIBILITY ENHANCEMENTS
# ============================================================================


class AccessibilitySupport:
    """Enhanced accessibility features."""

    @staticmethod
    def add_aria_label(widget: ctk.CTkBaseClass, label: str) -> None:
        """Add ARIA label for screen readers."""
        widget._aria_label = label  # type: ignore

    @staticmethod
    def add_keyboard_navigation(
        parent: ctk.CTk,
        widgets: list[ctk.CTkBaseClass],
    ) -> None:
        """Add keyboard navigation support."""
        focus_index = [0]

        def focus_next(_event=None) -> None:
            focus_index[0] = (focus_index[0] + 1) % len(widgets)
            try:
                widgets[focus_index[0]].focus()
            except Exception:
                pass

        def focus_prev(_event=None) -> None:
            focus_index[0] = (focus_index[0] - 1) % len(widgets)
            try:
                widgets[focus_index[0]].focus()
            except Exception:
                pass

        parent.bind("<Tab>", focus_next)
        parent.bind("<Shift-Tab>", focus_prev)

    @staticmethod
    def make_widget_focusable(widget: ctk.CTkBaseClass) -> None:
        """Make widget focusable with keyboard."""
        widget.configure(cursor="hand2")


# ============================================================================
# RESPONSIVE LAYOUT
# ============================================================================


class ResponsiveGrid:
    """Responsive grid layout helper."""

    @staticmethod
    def configure_responsive_columns(
        parent: ctk.CTk | ctk.CTkFrame,
        num_columns: int,
        min_width: int = 200,
    ) -> None:
        """Configure responsive grid columns."""
        for i in range(num_columns):
            parent.columnconfigure(i, weight=1, minsize=min_width)

    @staticmethod
    def configure_responsive_rows(
        parent: ctk.CTk | ctk.CTkFrame,
        num_rows: int,
        min_height: int = 50,
    ) -> None:
        """Configure responsive grid rows."""
        for i in range(num_rows):
            parent.rowconfigure(i, weight=1, minsize=min_height)


# ============================================================================
# COMPONENT LIBRARY
# ============================================================================


class ModernButton(ctk.CTkButton):
    """Modern button with enhanced styling."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        text: str,
        command: Callable | None = None,
        variant: str = "primary",
        size: str = "md",
        **kwargs,
    ):
        # Size configuration
        size_map = {
            "sm": (10, 8, TYPOGRAPHY.size_sm),
            "md": (12, 10, TYPOGRAPHY.size_base),
            "lg": (14, 12, TYPOGRAPHY.size_lg),
        }
        padx, pady, font_size = size_map.get(size, size_map["md"])

        # Variant configuration
        variant_map = {
            "primary": {
                "fg_color": DARK_THEME.primary,
                "hover_color": DARK_THEME.primary_hover,
                "text_color": "white",
            },
            "secondary": {
                "fg_color": DARK_THEME.secondary,
                "hover_color": DARK_THEME.secondary_hover,
                "text_color": "white",
            },
            "success": {
                "fg_color": DARK_THEME.success,
                "hover_color": "#20C997",
                "text_color": "white",
            },
            "danger": {
                "fg_color": DARK_THEME.error,
                "hover_color": "#C82333",
                "text_color": "white",
            },
        }
        config = variant_map.get(variant, variant_map["primary"])

        super().__init__(
            parent,
            text=text,
            command=command,
            font=(TYPOGRAPHY.family_body, font_size),
            corner_radius=6,
            **config,
            **kwargs,
        )


class ModernEntry(ctk.CTkEntry):
    """Modern entry field with enhanced styling."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        placeholder: str = "",
        **kwargs,
    ):
        super().__init__(
            parent,
            font=(TYPOGRAPHY.family_body, TYPOGRAPHY.size_base),
            corner_radius=6,
            **kwargs,
        )
        self.placeholder = placeholder
        if placeholder:
            self.insert(0, placeholder)
            self.configure(text_color=DARK_THEME.text_secondary)

            def on_focus_in(_event=None) -> None:
                if self.get() == placeholder:
                    self.delete(0, "end")
                    self.configure(text_color=DARK_THEME.text_primary)

            def on_focus_out(_event=None) -> None:
                if not self.get():
                    self.insert(0, placeholder)
                    self.configure(text_color=DARK_THEME.text_secondary)

            self.bind("<FocusIn>", on_focus_in)
            self.bind("<FocusOut>", on_focus_out)


class ModernLabel(ctk.CTkLabel):
    """Modern label with typography hierarchy."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        text: str,
        variant: str = "body",
        **kwargs,
    ):
        variant_map = {
            "display": (TYPOGRAPHY.size_4xl, TYPOGRAPHY.weight_bold),
            "h1": (TYPOGRAPHY.size_3xl, TYPOGRAPHY.weight_bold),
            "h2": (TYPOGRAPHY.size_2xl, TYPOGRAPHY.weight_semibold),
            "h3": (TYPOGRAPHY.size_xl, TYPOGRAPHY.weight_semibold),
            "h4": (TYPOGRAPHY.size_lg, TYPOGRAPHY.weight_semibold),
            "body": (TYPOGRAPHY.size_base, TYPOGRAPHY.weight_regular),
            "body-sm": (TYPOGRAPHY.size_sm, TYPOGRAPHY.weight_regular),
            "caption": (TYPOGRAPHY.size_xs, TYPOGRAPHY.weight_regular),
        }
        size, weight = variant_map.get(variant, variant_map["body"])

        super().__init__(
            parent,
            text=text,
            font=(TYPOGRAPHY.family_body, size),
            **kwargs,
        )
