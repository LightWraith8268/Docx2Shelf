"""Enhanced terminal UI utilities using rich library."""

from __future__ import annotations

import sys
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.layout import Layout
from rich.style import Style
from rich import box


class TerminalUI:
    """Enhanced terminal UI with rich formatting and cross-platform support."""

    def __init__(self):
        """Initialize the terminal UI."""
        self.console = Console()
        self.command_history: list[str] = []
        self.history_index: int = -1

    def clear(self):
        """Clear the terminal screen."""
        self.console.clear()

    def print_header(self, title: str, version: str, subtitle: str = ""):
        """Print an attractive header with version info."""
        header_text = Text()
        header_text.append("📚 ", style="bold cyan")
        header_text.append(title, style="bold cyan")
        header_text.append(f" v{version}", style="dim cyan")

        if subtitle:
            panel_content = Text.from_markup(
                f"[bold cyan]{title}[/bold cyan] [dim cyan]v{version}[/dim cyan]\n"
                f"[dim]{subtitle}[/dim]"
            )
        else:
            panel_content = header_text

        self.console.print(
            Panel(
                panel_content,
                border_style="cyan",
                box=box.DOUBLE,
                padding=(0, 2),
            )
        )
        self.console.print()

    def print_breadcrumb(self, path: list[str]):
        """Print breadcrumb navigation showing current location."""
        if not path:
            return

        breadcrumb = Text(" 🏠 ", style="cyan")
        for i, item in enumerate(path):
            if i > 0:
                breadcrumb.append(" › ", style="dim")
            breadcrumb.append(item, style="bold" if i == len(path) - 1 else "dim")

        self.console.print(breadcrumb)
        self.console.print()

    def print_menu(
        self,
        title: str,
        options: list[tuple[str, str, str]],
        show_back: bool = False,
        status_info: Optional[dict[str, Any]] = None,
    ):
        """
        Print an enhanced menu with options.

        Args:
            title: Menu title
            options: List of (key, emoji, description) tuples
            show_back: Whether to show back option
            status_info: Optional dict with status information to display
        """
        # Create menu table
        table = Table(
            show_header=False,
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 1),
            expand=True,
        )

        table.add_column("Key", style="bold yellow", width=4)
        table.add_column("Option", style="white")

        # Add numbered options
        for i, (key, emoji, description) in enumerate(options, 1):
            option_text = f"{emoji}  {description}"
            table.add_row(f"[{i}]", option_text)

        # Add separator before navigation options
        if options:
            table.add_row("", "")

        # Add back option if available
        if show_back:
            table.add_row("[b]", "⬅️  Back to previous menu")

        # Always show quit
        table.add_row("[q]", "🚪 Quit")

        # Add help option
        table.add_row("[h]", "❓ Help")

        # Print menu panel
        panel_content = table
        if status_info:
            # Add status information above the menu
            status_text = Text()
            for key, value in status_info.items():
                status_text.append(f"{key}: ", style="dim")
                status_text.append(f"{value}\n", style="bold green" if value else "dim red")

            from rich.columns import Columns
            panel_content = Columns([status_text, table])

        self.console.print(
            Panel(
                panel_content,
                title=f"[bold cyan]{title}[/bold cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    def get_input(
        self,
        prompt_text: str = "Select option",
        valid_options: Optional[list[str]] = None,
        allow_empty: bool = False,
    ) -> str:
        """
        Get user input with validation.

        Args:
            prompt_text: Text to display as prompt
            valid_options: List of valid option values (None = any input)
            allow_empty: Whether to allow empty input

        Returns:
            User's input string
        """
        while True:
            try:
                value = Prompt.ask(
                    f"[bold yellow]{prompt_text}[/bold yellow]",
                    console=self.console,
                )

                value = value.strip().lower()

                if not value and not allow_empty:
                    self.print_error("Input cannot be empty. Please try again.")
                    continue

                if valid_options and value not in valid_options:
                    self.print_error(
                        f"Invalid option '[cyan]{value}[/cyan]'. "
                        f"Valid options: {', '.join(f'[cyan]{opt}[/cyan]' for opt in valid_options)}"
                    )
                    continue

                # Add to history
                if value and value not in ["h", "help"]:
                    self.command_history.append(value)
                    self.history_index = len(self.command_history)

                return value

            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim]Interrupted by user[/dim]")
                return "q"

    def confirm(self, message: str, default: bool = False) -> bool:
        """Ask for user confirmation."""
        return Confirm.ask(f"[bold yellow]{message}[/bold yellow]", default=default)

    def print_success(self, message: str):
        """Print a success message."""
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def print_error(self, message: str):
        """Print an error message."""
        self.console.print(f"[bold red]✗[/bold red] {message}")

    def print_warning(self, message: str):
        """Print a warning message."""
        self.console.print(f"[bold yellow]⚠[/bold yellow]  {message}")

    def print_info(self, message: str):
        """Print an info message."""
        self.console.print(f"[bold cyan]ℹ[/bold cyan]  {message}")

    def print_status(self, label: str, value: str, is_good: bool = True):
        """Print a status line with label and value."""
        status_style = "bold green" if is_good else "bold red"
        symbol = "✓" if is_good else "✗"
        self.console.print(f"  [dim]{label}:[/dim] [{status_style}]{symbol} {value}[/{status_style}]")

    def print_help(self, help_text: str):
        """Print help information in a panel."""
        self.console.print(
            Panel(
                Text.from_markup(help_text),
                title="[bold cyan]Help[/bold cyan]",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    def create_progress(self, description: str) -> Progress:
        """Create a progress bar for long-running operations."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        )

    def pause(self, message: str = "Press Enter to continue..."):
        """Pause and wait for user input."""
        Prompt.ask(f"[dim]{message}[/dim]", console=self.console, default="")

    def print_table(
        self,
        title: str,
        columns: list[tuple[str, str]],
        rows: list[list[str]],
        show_border: bool = True,
    ):
        """
        Print a formatted table.

        Args:
            title: Table title
            columns: List of (header, style) tuples
            rows: List of row data
            show_border: Whether to show table borders
        """
        table = Table(
            title=title,
            box=box.ROUNDED if show_border else None,
            border_style="cyan",
            show_header=True,
            header_style="bold cyan",
        )

        for header, style in columns:
            table.add_column(header, style=style)

        for row in rows:
            table.add_row(*row)

        self.console.print(table)

    def print_section(self, title: str, content: str, style: str = "cyan"):
        """Print a section with title and content."""
        self.console.print()
        self.console.print(f"[bold {style}]{title}[/bold {style}]")
        self.console.print(f"[dim]{'─' * len(title)}[/dim]")
        self.console.print(content)
        self.console.print()

    def show_spinner(self, message: str, task_func, *args, **kwargs):
        """Show a spinner while executing a task."""
        with self.console.status(f"[bold cyan]{message}...", spinner="dots"):
            return task_func(*args, **kwargs)

    def print_list(self, items: list[str], style: str = "white", bullet: str = "•"):
        """Print a formatted list."""
        for item in items:
            self.console.print(f"  [{style}]{bullet}[/{style}] {item}")

    def print_key_value_pairs(self, pairs: dict[str, Any], value_style: str = "cyan"):
        """Print key-value pairs in a formatted way."""
        max_key_length = max(len(str(key)) for key in pairs.keys()) if pairs else 0

        for key, value in pairs.items():
            key_padded = str(key).ljust(max_key_length)
            self.console.print(f"  [dim]{key_padded}:[/dim] [{value_style}]{value}[/{value_style}]")


def create_ui() -> TerminalUI:
    """Create and return a TerminalUI instance."""
    return TerminalUI()
