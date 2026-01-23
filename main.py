"""
CourseSmith ENTERPRISE - Entry Point
A commercial desktop application to generate educational PDF books using AI with DRM protection.
"""

import customtkinter as ctk
from dotenv import load_dotenv

from app import App


def main():
    """Initialize and run the CourseSmith ENTERPRISE application."""
    # Load environment variables
    load_dotenv()
    
    # Set appearance mode
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # Create and run the application
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
