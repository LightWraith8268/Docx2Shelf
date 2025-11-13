"""
Enhanced Error Handling for Docx2Shelf.

Provides contextual help, automated fix suggestions, and improved user experience
when errors occur during conversion, wizard, or theme editing workflows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils import prompt_bool, prompt_select


@dataclass
class ErrorSolution:
    """Represents a solution for an error."""
    title: str
    description: str
    action: Optional[str] = None  # Action code for automated fixes
    confidence: int = 100  # Confidence level (0-100)
    requires_input: bool = False  # Whether user input is needed


@dataclass
class ErrorContext:
    """Context information for an error."""
    operation: str  # What was being done when error occurred
    file_path: Optional[Path] = None
    step: Optional[str] = None  # Wizard step, etc.
    user_input: Optional[str] = None  # User input that caused error


class EnhancedErrorHandler:
    """Enhanced error handler with contextual help and fix suggestions."""

    def __init__(self):
        self._error_patterns = self._initialize_error_patterns()
        self._solution_registry = self._initialize_solution_registry()

    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        interactive: bool = True
    ) -> bool:
        """
        Handle an error with enhanced messaging and fix suggestions.

        Args:
            error: The exception that occurred
            context: Context about what was happening when error occurred
            interactive: Whether to show interactive fix options

        Returns:
            True if error was handled/fixed, False if should propagate
        """
        print(f"\n❌ Error during {context.operation}")
        print(f"   {type(error).__name__}: {error}")

        # Analyze error and find solutions
        solutions = self._analyze_error(error, context)

        if not solutions:
            # Generic error handling
            self._show_generic_help(error, context)
            return False

        # Show contextual help
        self._show_contextual_help(error, context, solutions)

        if not interactive:
            return False

        # Offer fix options
        return self._offer_fix_options(solutions, context)

    def _analyze_error(self, error: Exception, context: ErrorContext) -> List[ErrorSolution]:
        """Analyze an error and return potential solutions."""
        solutions = []
        error_text = str(error).lower()
        error_type = type(error).__name__

        # Check each error pattern
        for pattern_info in self._error_patterns:
            if self._matches_pattern(error, error_text, error_type, pattern_info, context):
                # Get solutions for this pattern
                solution_ids = pattern_info.get('solutions', [])
                for solution_id in solution_ids:
                    if solution_id in self._solution_registry:
                        solutions.append(self._solution_registry[solution_id])

        # Sort by confidence level
        solutions.sort(key=lambda s: s.confidence, reverse=True)
        return solutions[:5]  # Return top 5 solutions

    def _matches_pattern(
        self,
        error: Exception,
        error_text: str,
        error_type: str,
        pattern_info: Dict[str, Any],
        context: ErrorContext
    ) -> bool:
        """Check if an error matches a pattern."""
        # Check error type
        if 'error_types' in pattern_info:
            if error_type not in pattern_info['error_types']:
                return False

        # Check error message patterns
        if 'message_patterns' in pattern_info:
            for pattern in pattern_info['message_patterns']:
                if re.search(pattern, error_text, re.IGNORECASE):
                    return True
            return False

        # Check context-specific patterns
        if 'context_patterns' in pattern_info:
            context_patterns = pattern_info['context_patterns']

            if 'operation' in context_patterns:
                if context.operation not in context_patterns['operation']:
                    return False

            if 'file_extensions' in context_patterns and context.file_path:
                allowed_exts = context_patterns['file_extensions']
                if context.file_path.suffix.lower() not in allowed_exts:
                    return False

        return True

    def _show_contextual_help(
        self,
        error: Exception,
        context: ErrorContext,
        solutions: List[ErrorSolution]
    ):
        """Show contextual help for the error."""
        print("\n💡 Here's what might help:")

        if context.file_path:
            print(f"   File: {context.file_path}")
        if context.step:
            print(f"   Step: {context.step}")

        print("\n📋 Suggested solutions:")
        for i, solution in enumerate(solutions, 1):
            confidence_bar = "🟢" if solution.confidence >= 80 else "🟡" if solution.confidence >= 60 else "🔴"
            print(f"   {i}. {confidence_bar} {solution.title}")
            print(f"      {solution.description}")

    def _show_generic_help(self, error: Exception, context: ErrorContext):
        """Show generic help when no specific solutions are found."""
        print("\n💡 General troubleshooting tips:")

        if context.file_path:
            print(f"   • Check that the file exists and is not corrupted: {context.file_path}")
            print("   • Ensure the file is not open in another program")

        if "permission" in str(error).lower():
            print("   • Check file permissions and try running as administrator")

        if "network" in str(error).lower() or "connection" in str(error).lower():
            print("   • Check your internet connection")
            print("   • Try again in a few moments")

        print("   • Try the operation again")
        print("   • Check the documentation for more details")

    def _offer_fix_options(self, solutions: List[ErrorSolution], context: ErrorContext) -> bool:
        """Offer interactive fix options to the user."""
        if not solutions:
            return False

        # Create menu options
        options = []
        for i, solution in enumerate(solutions):
            confidence_icon = "🟢" if solution.confidence >= 80 else "🟡" if solution.confidence >= 60 else "🔴"
            options.append(f"{confidence_icon} {solution.title}")

        options.append("⏭️  Skip and continue")
        options.append("❌ Exit")

        choice_idx = prompt_select("Choose a solution", options)

        if choice_idx == len(options) - 1:  # Exit
            return False
        elif choice_idx == len(options) - 2:  # Skip
            return True
        else:
            # Apply selected solution
            solution = solutions[choice_idx]
            return self._apply_solution(solution, context)

    def _apply_solution(self, solution: ErrorSolution, context: ErrorContext) -> bool:
        """Apply a solution."""
        if not solution.action:
            print("✅ Please follow the manual steps described above.")
            return True

        # Execute automated fix
        try:
            success = self._execute_fix_action(solution.action, context)
            if success:
                print("✅ Solution applied successfully!")
                return True
            else:
                print("❌ Automatic fix failed. Please try manual steps.")
                return False
        except Exception as e:
            print(f"❌ Error applying fix: {e}")
            return False

    def _execute_fix_action(self, action: str, context: ErrorContext) -> bool:
        """Execute an automated fix action."""
        if action == "install_pandoc":
            return self._fix_install_pandoc()
        elif action == "install_epubcheck":
            return self._fix_install_epubcheck()
        elif action == "create_metadata_file":
            return self._fix_create_metadata_file(context)
        elif action == "fix_file_permissions":
            return self._fix_file_permissions(context)
        elif action == "create_output_directory":
            return self._fix_create_output_directory(context)
        else:
            print(f"Unknown fix action: {action}")
            return False

    def _fix_install_pandoc(self) -> bool:
        """Automatically install Pandoc."""
        try:
            from .tools import install_pandoc
            print("🔧 Installing Pandoc...")
            install_pandoc()
            print("✅ Pandoc installed successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to install Pandoc: {e}")
            return False

    def _fix_install_epubcheck(self) -> bool:
        """Automatically install EPUBCheck."""
        try:
            from .tools import install_epubcheck
            print("🔧 Installing EPUBCheck...")
            install_epubcheck()
            print("✅ EPUBCheck installed successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to install EPUBCheck: {e}")
            return False

    def _fix_create_metadata_file(self, context: ErrorContext) -> bool:
        """Create a basic metadata file."""
        try:
            if not context.file_path:
                return False

            metadata_path = context.file_path.parent / "metadata.txt"

            if metadata_path.exists():
                if not prompt_bool(f"Metadata file exists. Overwrite {metadata_path}?"):
                    return False

            # Create basic metadata template
            template = '''title: My Book
author: Author Name
language: en
description: A brief description of your book.

# Optional fields:
# seriesName: My Series
# seriesNumber: 1
# genre: Fiction
# isbn: 978-0-000000-00-0
# publisher: Publisher Name
# publicationDate: 2024-01-01
'''

            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(template)

            print(f"✅ Created metadata template: {metadata_path}")
            print("   Please edit this file with your book details.")
            return True

        except Exception as e:
            print(f"❌ Failed to create metadata file: {e}")
            return False

    def _fix_file_permissions(self, context: ErrorContext) -> bool:
        """Attempt to fix file permission issues."""
        if not context.file_path:
            return False

        try:
            # Try to make the file readable/writable
            context.file_path.chmod(0o644)
            print(f"✅ Fixed permissions for: {context.file_path}")
            return True
        except Exception as e:
            print(f"❌ Could not fix permissions: {e}")
            return False

    def _fix_create_output_directory(self, context: ErrorContext) -> bool:
        """Create missing output directory."""
        try:
            # Determine output directory
            if context.file_path:
                output_dir = context.file_path.parent / "output"
            else:
                output_dir = Path.cwd() / "output"

            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created output directory: {output_dir}")
            return True

        except Exception as e:
            print(f"❌ Failed to create output directory: {e}")
            return False

    def _initialize_error_patterns(self) -> List[Dict[str, Any]]:
        """Initialize error pattern matching rules."""
        return [
            # Pandoc not found
            {
                'message_patterns': [r'pandoc.*not found', r'pandoc.*command not found'],
                'solutions': ['install_pandoc', 'use_fallback_parser']
            },
            # EPUBCheck not found
            {
                'message_patterns': [r'epubcheck.*not found', r'java.*not found'],
                'solutions': ['install_epubcheck', 'skip_validation']
            },
            # File not found
            {
                'error_types': ['FileNotFoundError'],
                'solutions': ['check_file_path', 'create_file']
            },
            # Permission errors
            {
                'error_types': ['PermissionError'],
                'solutions': ['fix_file_permissions', 'run_as_admin']
            },
            # Metadata issues
            {
                'message_patterns': [r'metadata.*missing', r'title.*required', r'author.*required'],
                'solutions': ['create_metadata_file', 'provide_metadata_interactive']
            },
            # DOCX parsing errors
            {
                'message_patterns': [r'docx.*corrupt', r'zip.*error', r'invalid.*docx'],
                'context_patterns': {'file_extensions': ['.docx']},
                'solutions': ['try_repair_docx', 'use_alternative_format']
            },
            # Output directory issues
            {
                'message_patterns': [r'output.*directory', r'cannot.*create.*directory'],
                'solutions': ['create_output_directory', 'specify_different_output']
            },
            # Memory issues
            {
                'message_patterns': [r'memory.*error', r'out of memory'],
                'solutions': ['reduce_image_size', 'process_in_chunks']
            },
            # Network/download issues
            {
                'message_patterns': [r'download.*failed', r'network.*error', r'connection.*error'],
                'solutions': ['check_internet', 'retry_download', 'use_offline_mode']
            }
        ]

    def _initialize_solution_registry(self) -> Dict[str, ErrorSolution]:
        """Initialize the solution registry with all available solutions."""
        return {
            'install_pandoc': ErrorSolution(
                title="Install Pandoc",
                description="Download and install Pandoc for better DOCX conversion",
                action="install_pandoc",
                confidence=95
            ),
            'install_epubcheck': ErrorSolution(
                title="Install EPUBCheck",
                description="Download and install EPUBCheck for EPUB validation",
                action="install_epubcheck",
                confidence=95
            ),
            'use_fallback_parser': ErrorSolution(
                title="Use fallback DOCX parser",
                description="Continue with built-in DOCX parser (limited features)",
                confidence=75
            ),
            'skip_validation': ErrorSolution(
                title="Skip EPUB validation",
                description="Continue without validating the generated EPUB",
                confidence=60
            ),
            'check_file_path': ErrorSolution(
                title="Check file path",
                description="Verify the file path is correct and the file exists",
                confidence=90
            ),
            'create_file': ErrorSolution(
                title="Create missing file",
                description="Create the missing file with default content",
                requires_input=True,
                confidence=70
            ),
            'fix_file_permissions': ErrorSolution(
                title="Fix file permissions",
                description="Attempt to fix file access permissions",
                action="fix_file_permissions",
                confidence=80
            ),
            'run_as_admin': ErrorSolution(
                title="Run as administrator",
                description="Try running the command with administrator privileges",
                confidence=70
            ),
            'create_metadata_file': ErrorSolution(
                title="Create metadata file",
                description="Create a metadata.txt file with default values",
                action="create_metadata_file",
                confidence=90
            ),
            'provide_metadata_interactive': ErrorSolution(
                title="Provide metadata interactively",
                description="Enter metadata details through interactive prompts",
                confidence=85
            ),
            'try_repair_docx': ErrorSolution(
                title="Try repairing DOCX",
                description="Attempt to repair the corrupted DOCX file",
                confidence=60
            ),
            'use_alternative_format': ErrorSolution(
                title="Use alternative format",
                description="Save the document as RTF or HTML and try again",
                confidence=75
            ),
            'create_output_directory': ErrorSolution(
                title="Create output directory",
                description="Create the missing output directory",
                action="create_output_directory",
                confidence=95
            ),
            'specify_different_output': ErrorSolution(
                title="Specify different output location",
                description="Choose a different location for output files",
                requires_input=True,
                confidence=80
            ),
            'reduce_image_size': ErrorSolution(
                title="Reduce image sizes",
                description="Compress or resize large images in the document",
                confidence=75
            ),
            'process_in_chunks': ErrorSolution(
                title="Process in smaller chunks",
                description="Break large documents into smaller parts",
                confidence=70
            ),
            'check_internet': ErrorSolution(
                title="Check internet connection",
                description="Verify your internet connection and try again",
                confidence=85
            ),
            'retry_download': ErrorSolution(
                title="Retry download",
                description="Try downloading the required files again",
                confidence=80
            ),
            'use_offline_mode': ErrorSolution(
                title="Use offline mode",
                description="Continue without downloading external resources",
                confidence=70
            )
        }


# Global error handler instance
_error_handler = EnhancedErrorHandler()


def handle_error(
    error: Exception,
    operation: str,
    file_path: Optional[Path] = None,
    step: Optional[str] = None,
    user_input: Optional[str] = None,
    interactive: bool = True
) -> bool:
    """
    Handle an error with enhanced messaging and fix suggestions.

    Args:
        error: The exception that occurred
        operation: What was being done when error occurred
        file_path: Path to file being processed (if applicable)
        step: Current step/phase (if applicable)
        user_input: User input that caused error (if applicable)
        interactive: Whether to show interactive fix options

    Returns:
        True if error was handled/fixed, False if should propagate
    """
    context = ErrorContext(
        operation=operation,
        file_path=file_path,
        step=step,
        user_input=user_input
    )

    return _error_handler.handle_error(error, context, interactive)


def wrap_with_error_handling(operation: str, step: Optional[str] = None):
    """
    Decorator to wrap functions with enhanced error handling.

    Args:
        operation: Description of what the function does
        step: Optional step name for context
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Try to extract file path from args/kwargs
                file_path = None
                for arg in args:
                    if isinstance(arg, Path):
                        file_path = arg
                        break

                if not file_path:
                    for value in kwargs.values():
                        if isinstance(value, Path):
                            file_path = value
                            break

                handled = handle_error(
                    error=e,
                    operation=operation,
                    file_path=file_path,
                    step=step,
                    interactive=True
                )

                if not handled:
                    raise

        return wrapper
    return decorator