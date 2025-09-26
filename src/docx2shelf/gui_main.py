#!/usr/bin/env python3
"""
Standalone GUI entry point for Docx2Shelf.

This is the main entry point for the GUI-only version of Docx2Shelf.
No CLI dependencies - pure GUI application.
"""

import sys
import os
from pathlib import Path

def main():
    """Main entry point for standalone GUI application."""

    # Ensure we can import our modules
    try:
        # Add the source directory to path if running from development
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle (legacy support)
            base_path = Path(sys._MEIPASS)
        elif getattr(sys, 'frozen', False):
            # Running as Nuitka compiled executable
            base_path = Path(sys.executable).parent
        else:
            # Running from source
            base_path = Path(__file__).parent

        sys.path.insert(0, str(base_path))

        # Import and launch the modern GUI
        try:
            from docx2shelf.gui.modern_app import ModernDocx2ShelfApp
        except ImportError:
            # Try relative import for PyInstaller bundles
            try:
                # Add current directory and parent directories to Python path
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                sys.path.insert(0, current_dir)
                sys.path.insert(0, parent_dir)
                sys.path.insert(0, os.path.join(parent_dir, 'src'))

                from docx2shelf.gui.modern_app import ModernDocx2ShelfApp
            except ImportError as e2:
                # Try direct import
                try:
                    import docx2shelf.gui.modern_app as modern_app_module
                    ModernDocx2ShelfApp = modern_app_module.ModernDocx2ShelfApp
                except ImportError:
                    raise ImportError(f"Could not import ModernDocx2ShelfApp: {e2}")

        # Set up error handling for GUI mode
        try:
            # Create and run the GUI application
            app = ModernDocx2ShelfApp()

            # If a file was passed as argument, load it
            if len(sys.argv) > 1:
                file_path = sys.argv[1]
                if os.path.exists(file_path) and file_path.lower().endswith(('.docx', '.md', '.txt', '.html', '.htm')):
                    # Set the file in the GUI
                    app.file_entry.delete(0, 'end')
                    app.file_entry.insert(0, file_path)
                    app.current_file = file_path

            app.run()
            return 0
        except Exception as e:
            # Show error dialog instead of console output
            try:
                import tkinter as tk
                from tkinter import messagebox

                root = tk.Tk()
                root.withdraw()  # Hide main window

                messagebox.showerror(
                    "Docx2Shelf Error",
                    f"An error occurred while starting Docx2Shelf:\n\n{str(e)}\n\n"
                    f"Please check that all dependencies are installed."
                )
                root.destroy()
            except:
                # Last resort - print to console
                print(f"Error starting Docx2Shelf: {e}")

            return 1

    except ImportError as e:
        # Handle missing dependencies gracefully
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()

            if "customtkinter" in str(e):
                messagebox.showerror(
                    "Missing Dependency",
                    "CustomTkinter is required for the GUI.\n\n"
                    "Please install it with:\n"
                    "pip install customtkinter\n\n"
                    "Or download the complete installer from:\n"
                    "https://github.com/LightWraith8268/Docx2Shelf/releases"
                )
            else:
                messagebox.showerror(
                    "Import Error",
                    f"Failed to import required modules:\n\n{str(e)}\n\n"
                    f"Please reinstall Docx2Shelf or contact support."
                )

            root.destroy()
        except:
            print(f"Import error: {e}")
            print("Please ensure all dependencies are installed.")

        return 1

if __name__ == "__main__":
    sys.exit(main())