"""
Utils Module - Helper functions for PyInstaller EXE compilation.
Provides resource path resolution for bundled applications.
Also includes clipboard helper functions for cross-platform compatibility.
"""

import os
import sys
import tkinter as tk


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    When running as a PyInstaller bundle, files are extracted to a 
    temporary folder (sys._MEIPASS). When running in development,
    files are in the current working directory.
    
    Args:
        relative_path: The relative path to the resource file.
        
    Returns:
        str: The absolute path to the resource.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in development mode
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_data_dir():
    """
    Get the application data directory for storing user files.
    
    Returns:
        str: Path to the application data directory.
    """
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        data_dir = os.path.join(app_data, "CourseSmith")
    else:
        data_dir = os.path.join(os.path.expanduser("~"), ".coursesmith")
    
    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    return data_dir


def ensure_dir(path):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The directory path to ensure exists.
        
    Returns:
        str: The path that was ensured.
    """
    os.makedirs(path, exist_ok=True)
    return path


# ==================== CLIPBOARD HELPERS ====================

def clipboard_cut(widget):
    """
    Cut selected text from widget to clipboard.
    
    Args:
        widget: The tkinter widget (Entry or Text) to cut from.
    """
    try:
        widget.event_generate("<<Cut>>")
    except tk.TclError:
        pass


def clipboard_copy(widget):
    """
    Copy selected text from widget to clipboard.
    
    Args:
        widget: The tkinter widget (Entry or Text) to copy from.
    """
    try:
        widget.event_generate("<<Copy>>")
    except tk.TclError:
        pass


def clipboard_paste(widget):
    """
    Paste text from clipboard into widget.
    
    Args:
        widget: The tkinter widget (Entry or Text) to paste into.
    """
    try:
        widget.event_generate("<<Paste>>")
    except tk.TclError:
        pass


def clipboard_select_all(widget):
    """
    Select all text in widget.
    
    Args:
        widget: The tkinter widget (Entry or Text) to select all in.
    """
    try:
        widget.event_generate("<<SelectAll>>")
    except tk.TclError:
        # Fallback for widgets that don't support <<SelectAll>>
        try:
            if hasattr(widget, 'select_range'):
                # For Entry widgets
                widget.select_range(0, 'end')
            elif hasattr(widget, 'tag_add'):
                # For Text widgets
                widget.tag_add('sel', '1.0', 'end')
        except Exception:
            pass
