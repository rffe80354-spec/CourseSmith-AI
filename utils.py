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
        # Return "break" to prevent event propagation (fixes double paste bug)
        shortcuts = [
            ('c', self._copy_event), ('C', self._copy_event),
            ('x', self._cut_event), ('X', self._cut_event),
            ('v', self._paste_event), ('V', self._paste_event),
            ('a', self._select_all_event), ('A', self._select_all_event),
        ]
        for key, action in shortcuts:
            widget.bind(f"<Control-{key}>", action)
    
    def _show_menu(self, event):
        """Show the context menu at cursor position."""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
        return "break"
    
    def _cut_event(self, event=None):
        """Cut selected text to clipboard (event handler)."""
        self._cut()
        return "break"
    
    def _copy_event(self, event=None):
        """Copy selected text to clipboard (event handler)."""
        self._copy()
        return "break"
    
    def _paste_event(self, event=None):
        """Paste text from clipboard (event handler)."""
        self._paste()
        return "break"
    
    def _select_all_event(self, event=None):
        """Select all text in widget (event handler)."""
        self._select_all()
        return "break"
    
    def _cut(self):
        """Cut selected text to clipboard."""
        clipboard_cut(self.widget)
    
    def _copy(self):
        """Copy selected text to clipboard."""
        clipboard_copy(self.widget)
    
    def _paste(self):
        """Paste text from clipboard directly using focus_get (avoids double-paste bug)."""
        try:
            # Get the currently focused widget (handles CustomTkinter focus issues)
            focused_widget = self.widget.focus_get()
            if focused_widget is None:
                focused_widget = self.widget
            
            # Check if widget is in normal state (can accept input)
            widget_state = str(focused_widget.cget("state")) if hasattr(focused_widget, "cget") else "normal"
            if widget_state == "disabled" or widget_state == "readonly":
                return
            
            # Get clipboard content from focused widget for consistency
            text = focused_widget.clipboard_get()
        except tk.TclError:
            # Clipboard is empty or unavailable
            return
        
        # Delete selected text first (if any), then insert clipboard content
        try:
            focused_widget.delete("sel.first", "sel.last")
        except tk.TclError:
            # No selection exists, which is fine
            pass
        
        # Insert text at current cursor position
        try:
            focused_widget.insert("insert", text)
        except tk.TclError:
            # Fallback: try inserting at the widget itself
            self.widget.insert("insert", text)
    
    def _select_all(self):
        """Select all text in widget."""
        clipboard_select_all(self.widget)


def get_underlying_tk_widget(widget):
    """
    Get the underlying tkinter widget from a CustomTkinter widget.
    CTkEntry uses _entry, CTkTextbox uses _textbox.
    
    Args:
        widget: The CTkEntry, CTkTextbox, or tkinter widget.
        
    Returns:
        The underlying tkinter widget.
    """
    if hasattr(widget, '_entry'):
        return widget._entry
    elif hasattr(widget, '_textbox'):
        return widget._textbox
    return widget


def add_context_menu(widget):
    """
    Add a right-click context menu to a widget.
    Works with CTkEntry and CTkTextbox (extracts underlying tk widget).
    
    Args:
        widget: The CTkEntry, CTkTextbox, or tkinter widget to bind to.
        
    Returns:
        RightClickMenu: The created context menu instance.
    """
    tk_widget = get_underlying_tk_widget(widget)
    return RightClickMenu(tk_widget)


def handle_custom_paste(event, widget):
    """
    Handle Ctrl+V paste event for CustomTkinter widgets.
    This function directly accesses the clipboard and inserts text at the cursor.
    Returns "break" to prevent the default Tkinter handler from firing.
    
    Args:
        event: The key event (can be None for direct calls).
        widget: The CTkEntry, CTkTextbox, or tkinter widget to paste into.
        
    Returns:
        str: "break" to stop event propagation.
    """
    tk_widget = get_underlying_tk_widget(widget)
    
    try:
        # Check if widget is in normal state (can accept input)
        widget_state = str(tk_widget.cget("state")) if hasattr(tk_widget, "cget") else "normal"
        if widget_state == "disabled" or widget_state == "readonly":
            return "break"
        
        # Get clipboard content
        text = tk_widget.clipboard_get()
    except tk.TclError:
        # Clipboard is empty or unavailable
        return "break"
    
    # Delete selected text first (if any)
    try:
        tk_widget.delete("sel.first", "sel.last")
    except tk.TclError:
        # No selection exists, which is fine
        pass
    
    # Insert text at current cursor position
    try:
        tk_widget.insert("insert", text)
    except tk.TclError:
        pass
    
    # Return "break" to prevent default handler (CRITICAL)
    return "break"


def bind_paste_shortcut(widget):
    """
    Bind Ctrl+V paste shortcut to a CustomTkinter widget.
    This provides explicit paste handling that works reliably with CTkEntry and CTkTextbox.
    
    Args:
        widget: The CTkEntry, CTkTextbox, or tkinter widget to bind to.
    """
    tk_widget = get_underlying_tk_widget(widget)
    
    # Bind both uppercase and lowercase for Ctrl+V
    tk_widget.bind("<Control-v>", lambda e: handle_custom_paste(e, widget))
    tk_widget.bind("<Control-V>", lambda e: handle_custom_paste(e, widget))
