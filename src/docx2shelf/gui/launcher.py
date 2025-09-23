"""
GUI Launcher for Docx2Shelf - Choose between traditional tkinter or modern CustomTkinter interface
"""

import sys
import tkinter as tk
from tkinter import messagebox, ttk

def launch_traditional_gui():
    """Launch the traditional tkinter GUI."""
    try:
        from .app import main as launch_traditional
        launch_traditional()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch traditional GUI: {e}")

def launch_modern_gui():
    """Launch the modern CustomTkinter GUI."""
    try:
        from .modern_app import main as launch_modern
        result = launch_modern()
        if result == 1:
            messagebox.showerror("Error",
                               "CustomTkinter is not installed.\n\n"
                               "Install it with: pip install customtkinter\n\n"
                               "Falling back to traditional GUI...")
            launch_traditional_gui()
    except ImportError:
        answer = messagebox.askyesno("CustomTkinter Not Found",
                                   "CustomTkinter is not installed for the modern GUI.\n\n"
                                   "Would you like to:\n"
                                   "• Yes: Install CustomTkinter automatically\n"
                                   "• No: Use traditional GUI instead")
        if answer:
            install_customtkinter()
        else:
            launch_traditional_gui()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to launch modern GUI: {e}")
        launch_traditional_gui()

def install_customtkinter():
    """Install CustomTkinter automatically."""
    try:
        import subprocess
        import sys

        # Show installation dialog
        install_window = tk.Toplevel()
        install_window.title("Installing CustomTkinter")
        install_window.geometry("400x150")
        install_window.transient()
        install_window.grab_set()

        tk.Label(install_window, text="Installing CustomTkinter...",
                font=("Arial", 12)).pack(pady=20)

        progress = ttk.Progressbar(install_window, mode='indeterminate')
        progress.pack(fill="x", padx=20, pady=10)
        progress.start()

        install_window.update()

        # Install CustomTkinter
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])

        progress.stop()
        install_window.destroy()

        messagebox.showinfo("Success", "CustomTkinter installed successfully!\nLaunching modern GUI...")
        launch_modern_gui()

    except subprocess.CalledProcessError as e:
        messagebox.showerror("Installation Failed",
                           f"Failed to install CustomTkinter: {e}\n\n"
                           "Please install manually with:\npip install customtkinter\n\n"
                           "Launching traditional GUI instead...")
        launch_traditional_gui()
    except Exception as e:
        messagebox.showerror("Error", f"Installation error: {e}")
        launch_traditional_gui()

class GUILauncher:
    """GUI selection launcher for Docx2Shelf."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Docx2Shelf - Choose Interface")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"600x500+{x}+{y}")

        self.setup_ui()

    def setup_ui(self):
        """Setup the launcher interface."""

        # Header
        header_frame = tk.Frame(self.root, bg="#007acc", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="📖 Docx2Shelf",
                              font=("Arial", 24, "bold"),
                              fg="white", bg="#007acc")
        title_label.pack(pady=20)

        # Main content
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Instructions
        instruction_label = tk.Label(main_frame,
                                    text="Choose your preferred interface style:",
                                    font=("Arial", 16), bg="white")
        instruction_label.pack(pady=(0, 30))

        # Option 1: Modern GUI
        modern_frame = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
        modern_frame.pack(fill="x", pady=(0, 20))

        modern_header = tk.Frame(modern_frame, bg="#f0f8ff")
        modern_header.pack(fill="x")

        modern_title = tk.Label(modern_header, text="🎨 Modern Interface (Recommended)",
                               font=("Arial", 14, "bold"), bg="#f0f8ff")
        modern_title.pack(pady=10)

        modern_desc = tk.Label(modern_frame,
                              text="• True rounded corners and modern styling\n"
                                   "• Smooth animations and transitions\n"
                                   "• Native dark/light theme switching\n"
                                   "• Professional appearance with CustomTkinter\n"
                                   "• Optimized for 2025 design standards",
                              font=("Arial", 11), justify="left", bg="white")
        modern_desc.pack(padx=20, pady=10, anchor="w")

        modern_btn = tk.Button(modern_frame, text="🚀 Launch Modern Interface",
                              command=self.launch_modern,
                              font=("Arial", 12, "bold"),
                              bg="#007acc", fg="white",
                              relief="flat", padx=20, pady=10)
        modern_btn.pack(pady=15)

        # Option 2: Traditional GUI
        traditional_frame = tk.Frame(main_frame, bg="white", relief="raised", bd=2)
        traditional_frame.pack(fill="x")

        traditional_header = tk.Frame(traditional_frame, bg="#f5f5f5")
        traditional_header.pack(fill="x")

        traditional_title = tk.Label(traditional_header, text="🖥️ Traditional Interface",
                                    font=("Arial", 14, "bold"), bg="#f5f5f5")
        traditional_title.pack(pady=10)

        traditional_desc = tk.Label(traditional_frame,
                                   text="• Enhanced tkinter with modern improvements\n"
                                        "• Compatible with all systems\n"
                                        "• Comprehensive help and features\n"
                                        "• Improved dark/light themes\n"
                                        "• All functionality preserved",
                                   font=("Arial", 11), justify="left", bg="white")
        traditional_desc.pack(padx=20, pady=10, anchor="w")

        traditional_btn = tk.Button(traditional_frame, text="📋 Launch Traditional Interface",
                                   command=self.launch_traditional,
                                   font=("Arial", 12),
                                   bg="#6c757d", fg="white",
                                   relief="flat", padx=20, pady=10)
        traditional_btn.pack(pady=15)

        # Footer
        footer_frame = tk.Frame(self.root, bg="#f8f9fa", height=50)
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)

        footer_label = tk.Label(footer_frame,
                               text="Both interfaces provide the same functionality - choose based on your preference",
                               font=("Arial", 10), fg="#6c757d", bg="#f8f9fa")
        footer_label.pack(pady=15)

    def launch_modern(self):
        """Launch modern interface and close launcher."""
        self.root.destroy()
        launch_modern_gui()

    def launch_traditional(self):
        """Launch traditional interface and close launcher."""
        self.root.destroy()
        launch_traditional_gui()

    def run(self):
        """Run the launcher."""
        self.root.mainloop()

def main():
    """Main entry point for the GUI launcher."""
    launcher = GUILauncher()
    launcher.run()

if __name__ == "__main__":
    main()