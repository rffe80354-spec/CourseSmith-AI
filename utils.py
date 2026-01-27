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
    
    Note: Keyboard shortcuts (Ctrl+A/C/V/X) are handled globally at the 
    root window level, so this class only provides the right-click menu.
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
        
        # Note: Keyboard shortcuts are NOT bound here. They are bound globally
        # at the root window level in app.py to avoid double-action issues.
    
    def _show_menu(self, event):
        """Show the context menu at cursor position."""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
        return "break"
    
    def _cut(self):
        """Cut selected text to clipboard."""
        clipboard_cut(self.widget)
        return "break"
    
    def _copy(self):
        """Copy selected text to clipboard."""
        clipboard_copy(self.widget)
        return "break"
    
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
                return "break"
            
            # Get clipboard content from focused widget for consistency
            text = focused_widget.clipboard_get()
        except tk.TclError:
            # Clipboard is empty or unavailable
            return "break"
        
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
        
        return "break"
    
    def _select_all(self):
        """Select all text in widget."""
        clipboard_select_all(self.widget)
        return "break"


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
    Add a right-click context menu to a widget AND bind all keyboard shortcuts.
    Works with CTkEntry and CTkTextbox (extracts underlying tk widget).
    Now also applies Ctrl+C, Ctrl+V, and Ctrl+A bindings automatically.
    
    Args:
        widget: The CTkEntry, CTkTextbox, or tkinter widget to bind to.
        
    Returns:
        RightClickMenu: The created context menu instance.
    """
    tk_widget = get_underlying_tk_widget(widget)
    # Also bind all keyboard shortcuts when adding context menu
    bind_all_shortcuts(widget)
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


def handle_custom_copy(event, widget):
    """
    Handle Ctrl+C copy event for CustomTkinter widgets.
    Returns "break" to prevent the default Tkinter handler from firing.
    
    Args:
        event: The key event (can be None for direct calls).
        widget: The CTkEntry, CTkTextbox, or tkinter widget to copy from.
        
    Returns:
        str: "break" to stop event propagation.
    """
    tk_widget = get_underlying_tk_widget(widget)
    clipboard_copy(tk_widget)
    return "break"


def handle_custom_select_all(event, widget):
    """
    Handle Ctrl+A select all event for CustomTkinter widgets.
    Returns "break" to prevent the default Tkinter handler from firing.
    
    Args:
        event: The key event (can be None for direct calls).
        widget: The CTkEntry, CTkTextbox, or tkinter widget to select all in.
        
    Returns:
        str: "break" to stop event propagation.
    """
    tk_widget = get_underlying_tk_widget(widget)
    clipboard_select_all(tk_widget)
    return "break"


def bind_all_shortcuts(widget):
    """
    Bind all standard keyboard shortcuts (Ctrl+C, Ctrl+V, Ctrl+A) to a CustomTkinter widget.
    This provides comprehensive clipboard support that works reliably with CTkEntry and CTkTextbox.
    
    Args:
        widget: The CTkEntry, CTkTextbox, or tkinter widget to bind to.
    """
    tk_widget = get_underlying_tk_widget(widget)
    
    # Bind Ctrl+V (Paste) - both uppercase and lowercase
    tk_widget.bind("<Control-v>", lambda e: handle_custom_paste(e, widget))
    tk_widget.bind("<Control-V>", lambda e: handle_custom_paste(e, widget))
    
    # Bind Ctrl+C (Copy) - both uppercase and lowercase
    tk_widget.bind("<Control-c>", lambda e: handle_custom_copy(e, widget))
    tk_widget.bind("<Control-C>", lambda e: handle_custom_copy(e, widget))
    
    # Bind Ctrl+A (Select All) - both uppercase and lowercase
    tk_widget.bind("<Control-a>", lambda e: handle_custom_select_all(e, widget))
    tk_widget.bind("<Control-A>", lambda e: handle_custom_select_all(e, widget))


def bind_paste_shortcut(widget):
    """
    Bind Ctrl+V paste shortcut to a CustomTkinter widget.
    This provides explicit paste handling that works reliably with CTkEntry and CTkTextbox.
    
    DEPRECATED: Use bind_all_shortcuts() instead for full clipboard support.
    
    Args:
        widget: The CTkEntry, CTkTextbox, or tkinter widget to bind to.
    """
    tk_widget = get_underlying_tk_widget(widget)
    
    # Bind both uppercase and lowercase for Ctrl+V
    tk_widget.bind("<Control-v>", lambda e: handle_custom_paste(e, widget))
    tk_widget.bind("<Control-V>", lambda e: handle_custom_paste(e, widget))
