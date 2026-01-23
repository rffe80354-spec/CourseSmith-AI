"""
Utils Module - Helper functions for PyInstaller EXE compilation.
Provides resource path resolution for bundled applications.
Also includes clipboard helper functions and right-click menu for cross-platform compatibility.
"""

import os
import sys
import tkinter as tk
from tkinter import Menu


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
        data_dir = os.path.join(app_data, "FaleovadAI")
    else:
        data_dir = os.path.join(os.path.expanduser("~"), ".faleovad_ai")
    
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


# ==================== RIGHT-CLICK CONTEXT MENU ====================

class RightClickMenu:
    """
    Right-click context menu for text input widgets.
    Provides Cut, Copy, Paste, and Select All functionality.
    Works with tkinter Entry and Text widgets.
    """
    
    def __init__(self, widget):
        """
        Initialize context menu for a widget.
        
        Args:
            widget: The tkinter Entry or Text widget to attach the menu to.
        """
        self.widget = widget
        
        # Create the context menu
        self.menu = Menu(widget, tearoff=0)
        self.menu.add_command(label="Cut", accelerator="Ctrl+X", command=self._cut)
        self.menu.add_command(label="Copy", accelerator="Ctrl+C", command=self._copy)
        self.menu.add_command(label="Paste", accelerator="Ctrl+V", command=self._paste)
        self.menu.add_separator()
        self.menu.add_command(label="Select All", accelerator="Ctrl+A", command=self._select_all)
        
        # Bind right-click to show menu
        widget.bind("<Button-3>", self._show_menu)
        
        # Explicitly bind keyboard shortcuts (both upper and lowercase)
        shortcuts = [
            ('c', self._copy), ('C', self._copy),
            ('x', self._cut), ('X', self._cut),
            ('v', self._paste), ('V', self._paste),
            ('a', self._select_all), ('A', self._select_all),
        ]
        for key, action in shortcuts:
            widget.bind(f"<Control-{key}>", lambda e, a=action: a())
    
    def _show_menu(self, event):
        """Show the context menu at cursor position."""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
    
    def _cut(self):
        """Cut selected text to clipboard."""
        clipboard_cut(self.widget)
    
    def _copy(self):
        """Copy selected text to clipboard."""
        clipboard_copy(self.widget)
    
    def _paste(self):
        """Paste text from clipboard."""
        clipboard_paste(self.widget)
    
    def _select_all(self):
        """Select all text in widget."""
        clipboard_select_all(self.widget)


def add_context_menu(widget):
    """
    Add a right-click context menu to a widget.
    Works with CTkEntry and CTkTextbox (extracts underlying tk widget).
    
    Args:
        widget: The CTkEntry, CTkTextbox, or tkinter widget to bind to.
        
    Returns:
        RightClickMenu: The created context menu instance.
    """
    # Get the underlying tkinter widget for customtkinter widgets
    if hasattr(widget, '_entry'):
        tk_widget = widget._entry
    elif hasattr(widget, '_textbox'):
        tk_widget = widget._textbox
    else:
        tk_widget = widget
    
    return RightClickMenu(tk_widget)
