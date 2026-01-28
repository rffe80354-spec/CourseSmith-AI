"""
Utils Module - Helper functions for PyInstaller EXE compilation.
Provides resource path resolution for bundled applications.
Also includes clipboard helper functions, right-click menu for cross-platform compatibility,
and HWID/license checking utilities.
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import Menu, TclError
from datetime import datetime, timezone
from typing import Optional, Dict, Any


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


# ==================== GLOBAL WINDOW-LEVEL SHORTCUTS ====================

def setup_global_window_shortcuts(window):
    """
    Setup GLOBAL keyboard shortcuts at root window level.
    This ensures shortcuts work regardless of widget-specific bindings or focus issues.
    Uses bind_all() to intercept events at the application level.
    
    This function should be called once during window initialization to enable
    application-wide keyboard shortcuts (Ctrl+C, Ctrl+V, Ctrl+A, Ctrl+X).
    
    Args:
        window: The root window (CTk or Tk instance) to bind shortcuts to.
    """
    # Create handler functions with proper error handling
    def global_copy(event):
        """Global handler for Ctrl+C (Copy)."""
        try:
            focused = window.focus_get()
            if focused:
                focused.event_generate("<<Copy>>")
        except (AttributeError, TclError):
            pass
        return "break"
    
    def global_paste(event):
        """Global handler for Ctrl+V (Paste)."""
        try:
            focused = window.focus_get()
            if focused:
                # Check if widget is editable
                try:
                    state = str(focused.cget("state"))
                    if state in ("disabled", "readonly"):
                        return "break"
                except (AttributeError, TclError):
                    pass
                focused.event_generate("<<Paste>>")
        except (AttributeError, TclError):
            pass
        return "break"
    
    def global_select_all(event):
        """Global handler for Ctrl+A (Select All)."""
        try:
            focused = window.focus_get()
            if focused:
                # Try event_generate first
                try:
                    focused.event_generate("<<SelectAll>>")
                except (AttributeError, TclError):
                    # Fallback to manual selection for Entry/Text widgets
                    if hasattr(focused, 'select_range'):
                        focused.select_range(0, 'end')
                    elif hasattr(focused, 'tag_add'):
                        focused.tag_add('sel', '1.0', 'end')
        except (AttributeError, TclError):
            pass
        return "break"
    
    def global_cut(event):
        """Global handler for Ctrl+X (Cut)."""
        try:
            focused = window.focus_get()
            if focused:
                # Check if widget is editable
                try:
                    state = str(focused.cget("state"))
                    if state in ("disabled", "readonly"):
                        return "break"
                except (AttributeError, TclError):
                    pass
                focused.event_generate("<<Cut>>")
        except (AttributeError, TclError):
            pass
        return "break"
    
    # Bind Ctrl+C (Copy) - both uppercase and lowercase variants
    window.bind_all("<Control-c>", global_copy)
    window.bind_all("<Control-C>", global_copy)
    
    # Bind Ctrl+V (Paste) - both uppercase and lowercase variants
    window.bind_all("<Control-v>", global_paste)
    window.bind_all("<Control-V>", global_paste)
    
    # Bind Ctrl+A (Select All) - both uppercase and lowercase variants
    window.bind_all("<Control-a>", global_select_all)
    window.bind_all("<Control-A>", global_select_all)
    
    # Bind Ctrl+X (Cut) - both uppercase and lowercase variants
    window.bind_all("<Control-x>", global_cut)
    window.bind_all("<Control-X>", global_cut)


# ==================== HWID & LICENSE UTILITIES ====================

def get_hwid() -> str:
    """
    Get the Windows Hardware ID (UUID) using wmic command with robust fallback.
    This is the primary method for identifying unique devices for license management.
    
    Returns:
        str: The hardware UUID or "UNKNOWN_ID" if an error occurs.
    """
    try:
        # Primary method: Get system UUID using wmic csproduct
        # Security: Using list of arguments instead of shell=True to prevent shell injection
        result = subprocess.check_output(
            ['wmic', 'csproduct', 'get', 'uuid'],
            timeout=5,
            shell=False
        ).decode()
        
        # Parse output - UUID is on second line
        lines = result.strip().split('\n')
        if len(lines) >= 2:
            uuid = lines[1].strip()
            if uuid and uuid != "UUID":
                return uuid
        
    except Exception as e:
        print(f"Primary HWID method failed: {e}")
    
    # Fallback method: Try disk drive serial number
    try:
        # Security: Using list of arguments instead of shell=True to prevent shell injection
        result = subprocess.check_output(
            ['wmic', 'diskdrive', 'get', 'serialnumber'],
            timeout=5,
            shell=False
        ).decode()
        
        # Parse output - Serial number is on second line
        lines = result.strip().split('\n')
        if len(lines) >= 2:
            serial = lines[1].strip()
            if serial and serial != "SerialNumber":
                return serial
                
    except Exception as e:
        print(f"Fallback HWID method failed: {e}")
    
    # If both methods fail, return UNKNOWN_ID
    return "UNKNOWN_ID"


def parse_hwids_array(hwids_value) -> list:
    """
    Helper function to safely parse used_hwids JSONB array from database.
    
    Args:
        hwids_value: The value from the database (could be list, None, or string)
        
    Returns:
        list: Parsed list of HWIDs, or empty list if None/invalid
    """
    if hwids_value is None:
        return []
    if isinstance(hwids_value, list):
        return hwids_value
    if isinstance(hwids_value, str):
        try:
            return json.loads(hwids_value)
        except Exception:
            return []
    return []


def is_device_limit_reached(used_hwids: list, max_devices: int) -> bool:
    """
    Check if the device limit has been reached for a license.
    
    Args:
        used_hwids: List of HWIDs already registered
        max_devices: Maximum number of devices allowed
        
    Returns:
        bool: True if limit reached, False otherwise
    """
    return len(used_hwids) >= max_devices


def is_license_expired(valid_until: Optional[str]) -> bool:
    """
    Check if a license has expired based on valid_until timestamp.
    
    Security Note: This function fails closed - if parsing fails, it treats
    the license as expired to prevent unauthorized access with malformed dates.
    
    Args:
        valid_until: ISO format timestamp string (or None for no expiration)
        
    Returns:
        bool: True if expired, False if still valid or no expiration
    """
    if not valid_until:
        # No expiration date means lifetime license
        return False
    
    try:
        expiration_date = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
        current_date = datetime.now(timezone.utc)
        return current_date > expiration_date
    except Exception as e:
        print(f"Error parsing expiration date: {e}")
        # SECURITY: Fail closed - treat as expired if we can't parse the date
        return True


def check_license(license_key: str, email: str, supabase_url: str, supabase_key: str) -> Dict[str, Any]:
    """
    Comprehensive license validation with HWID checking and device registration.
    This function validates a license key, checks HWID authorization, and registers
    new devices if the limit hasn't been reached.
    
    Args:
        license_key: The license key to validate
        email: The email associated with the license
        supabase_url: Supabase project URL
        supabase_key: Supabase API key
        
    Returns:
        dict: License validation result with the following structure:
            {
                'valid': bool,  # Whether the license is valid
                'message': str,  # Human-readable status message
                'license_data': dict or None,  # Full license record from database
                'hwid_registered': bool,  # Whether current HWID is registered
                'devices_used': int,  # Number of devices registered
                'max_devices': int  # Maximum devices allowed
            }
    """
    try:
        # Import Supabase client
        from supabase import create_client
        
        # Get current hardware ID
        current_hwid = get_hwid()
        
        if not current_hwid or current_hwid == "UNKNOWN_ID":
            return {
                'valid': False,
                'message': 'Unable to identify device hardware ID.',
                'license_data': None,
                'hwid_registered': False,
                'devices_used': 0,
                'max_devices': 0
            }
        
        # Connect to Supabase
        supabase = create_client(supabase_url, supabase_key)
        
        # Query licenses table for the provided license key
        response = supabase.table("licenses").select("*").eq("license_key", license_key).execute()
        
        # Check if license key exists
        if not response.data or len(response.data) == 0:
            return {
                'valid': False,
                'message': 'Invalid license key.',
                'license_data': None,
                'hwid_registered': False,
                'devices_used': 0,
                'max_devices': 0
            }
        
        license_record = response.data[0]
        
        # Verify email matches (case-insensitive)
        if license_record.get('email', '').lower() != email.lower():
            return {
                'valid': False,
                'message': 'License key does not match the provided email address.',
                'license_data': None,
                'hwid_registered': False,
                'devices_used': 0,
                'max_devices': 0
            }
        
        # Check if license is banned
        if license_record.get("is_banned") is True:
            return {
                'valid': False,
                'message': 'This license has been revoked. Contact support.',
                'license_data': license_record,
                'hwid_registered': False,
                'devices_used': 0,
                'max_devices': license_record.get('max_devices', 0)
            }
        
        # Check if license has expired
        if is_license_expired(license_record.get("valid_until")):
            return {
                'valid': False,
                'message': 'This license has expired. Please renew your subscription.',
                'license_data': license_record,
                'hwid_registered': False,
                'devices_used': 0,
                'max_devices': license_record.get('max_devices', 0)
            }
        
        # Parse used_hwids (JSONB array)
        used_hwids = parse_hwids_array(license_record.get("used_hwids"))
        max_devices = license_record.get("max_devices", 1)
        
        # Check if current HWID is already registered
        if current_hwid in used_hwids:
            # Already activated on this device
            return {
                'valid': True,
                'message': 'License is valid and already activated on this device.',
                'license_data': license_record,
                'hwid_registered': True,
                'devices_used': len(used_hwids),
                'max_devices': max_devices
            }
        
        # Check if there's room for a new device
        if not is_device_limit_reached(used_hwids, max_devices):
            # Add current HWID to the list
            used_hwids.append(current_hwid)
            
            # Update Supabase with new HWID
            supabase.table("licenses").update({
                "used_hwids": used_hwids
            }).eq("license_key", license_key).execute()
            
            return {
                'valid': True,
                'message': f'License activated successfully! Device {len(used_hwids)}/{max_devices} registered.',
                'license_data': license_record,
                'hwid_registered': True,
                'devices_used': len(used_hwids),
                'max_devices': max_devices
            }
        else:
            # Device limit reached
            return {
                'valid': False,
                'message': f'Device limit reached ({max_devices} devices). Please deactivate a device or upgrade your license.',
                'license_data': license_record,
                'hwid_registered': False,
                'devices_used': len(used_hwids),
                'max_devices': max_devices
            }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f'Error validating license: {str(e)}',
            'license_data': None,
            'hwid_registered': False,
            'devices_used': 0,
            'max_devices': 0
        }

