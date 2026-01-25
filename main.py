"""
CourseSmith ENTERPRISE - Entry Point
A commercial desktop application to generate educational PDF books using AI with DRM protection.
"""

import os
import sys
import customtkinter as ctk
from dotenv import load_dotenv


def main():
    """Initialize and run the CourseSmith ENTERPRISE application."""
    # Load environment variables with PyInstaller support
    # Try to find .env in the executable directory (works for both dev and EXE)
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in development mode
        base_path = os.path.abspath(".")
    
    env_path = os.path.join(base_path, ".env")
    
    # Load .env if it exists
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        # Fallback to current directory for development
        load_dotenv()
    
    # Set appearance mode
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # Import app here after environment is loaded
    from app import App
    
    # Create and run the application
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
