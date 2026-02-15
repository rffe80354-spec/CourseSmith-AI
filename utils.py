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
import logging
import threading
import tkinter as tk
from tkinter import Menu, TclError
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Global flag to track if scrollbar patch has been applied (prevents multiple patches)
_SCROLLBAR_PATCHED = False

# ReportLab imports for font registration
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def patch_ctk_scrollbar():
    """
    Apply a patch to fix CTkScrollbar rendering issues, ensuring it only applies once.
    
    This fixes the RecursionError that occurs when CTkScrollableFrame's
    scrollbar tries to update its size and triggers an infinite loop of
    size calculations.
    
    Safe to call multiple times - only applies patch once via global flag.
    """
    global _SCROLLBAR_PATCHED
    if _SCROLLBAR_PATCHED:
        return
    
    try:
        from customtkinter.windows.widgets.ctk_scrollbar import CTkScrollbar
        original_draw = CTkScrollbar._draw
        
        def patched_draw(self, *args, **kwargs):
            # Guard against recursion using instance attribute
            if getattr(self, '_draw_in_progress', False):
                return  # Skip if already drawing to prevent infinite recursion
            
            self._draw_in_progress = True
            try:
                original_draw(self, *args, **kwargs)
            except Exception:
                pass  # Silently handle rendering errors to prevent UI crashes
            finally:
                self._draw_in_progress = False
        
        CTkScrollbar._draw = patched_draw
        _SCROLLBAR_PATCHED = True
    except ImportError:
        # CustomTkinter not available - skip patch
        pass
    except Exception as e:
        _logger = logging.getLogger(__name__)
        _logger.warning(f"Failed to patch scrollbar: {e}")


# Set up module logger
_logger = logging.getLogger(__name__)

# Thread-safe font registration tracking
_font_registration_lock = threading.Lock()
_fonts_registered = False
_fonts_available = False


def _register_roboto_fonts():
    """
    Register Roboto fonts for PDF generation with proper Unicode support.
    
    This function registers Roboto-Regular and Roboto-Bold fonts for use
    in ReportLab PDF generation. These fonts support Cyrillic and other
    Unicode characters, fixing the "squares instead of text" issue.
    
    Thread-safe: Uses a lock to prevent duplicate registration attempts
    when called from multiple threads.
    
    Returns:
        bool: True if Roboto fonts are available for use, False if falling
              back to Helvetica (either due to missing files or registration error).
              Subsequent calls return the cached result.
    """
    global _fonts_registered, _fonts_available
    
    with _font_registration_lock:
        # Return cached result if already attempted
        if _fonts_registered:
            return _fonts_available
        
        try:
            # Get the path to fonts directory (works for both dev and PyInstaller)
            fonts_dir = resource_path('fonts')
            
            roboto_regular_path = os.path.join(fonts_dir, 'Roboto-Regular.ttf')
            roboto_bold_path = os.path.join(fonts_dir, 'Roboto-Bold.ttf')
            
            # Check if font files exist
            if not os.path.exists(roboto_regular_path):
                _logger.warning(
                    "Roboto-Regular.ttf not found at %s. Using Helvetica fallback.",
                    roboto_regular_path
                )
                _fonts_registered = True
                _fonts_available = False
                return False
            
            if not os.path.exists(roboto_bold_path):
                _logger.warning(
                    "Roboto-Bold.ttf not found at %s. Using Helvetica fallback.",
                    roboto_bold_path
                )
                _fonts_registered = True
                _fonts_available = False
                return False
            
            # Register fonts
            pdfmetrics.registerFont(TTFont('Roboto', roboto_regular_path))
            pdfmetrics.registerFont(TTFont('Roboto-Bold', roboto_bold_path))
            
            _fonts_registered = True
            _fonts_available = True
            return True
            
        except Exception as e:
            _logger.warning(
                "Failed to register Roboto fonts: %s. Using Helvetica fallback.",
                e
            )
            _fonts_registered = True
            _fonts_available = False
            return False


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
        """
        Paste text from clipboard directly using focus_get.
        This implementation avoids double-paste bugs common with CustomTkinter
        by manually handling text insertion instead of using event_generate.
        
        Returns:
            str: "break" to stop event propagation.
        """
        try:
            # Get the currently focused widget (handles CustomTkinter focus issues)
            focused_widget = self.widget.focus_get()
            if focused_widget is None:
                focused_widget = self.widget
            
            # Check if widget is in normal state (can accept input)
            widget_state = str(focused_widget.cget("state")) if hasattr(focused_widget, "cget") else "normal"
            if widget_state == "disabled" or widget_state == "readonly":
                return "break"
            
            # Get clipboard content - try multiple methods for reliability
            text = None
            try:
                # Primary method: get from focused widget
                text = focused_widget.clipboard_get()
            except tk.TclError:
                # TclError: clipboard is empty or unavailable from focused widget
                # Fallback: try getting from the widget directly
                try:
                    text = self.widget.clipboard_get()
                except tk.TclError:
                    # TclError: clipboard still unavailable, give up gracefully
                    pass
            
            # If no text available, return without error
            if not text:
                return "break"
                
        except tk.TclError:
            # TclError: widget state or clipboard access failed
            return "break"
        except AttributeError:
            # AttributeError: widget doesn't have expected methods
            return "break"
        
        # Delete selected text first (if any), then insert clipboard content
        try:
            focused_widget.delete("sel.first", "sel.last")
        except tk.TclError:
            # TclError: no selection exists, which is expected
            pass
        
        # Insert text at current cursor position
        try:
            focused_widget.insert("insert", text)
        except tk.TclError:
            # TclError: insert failed on focused widget, try fallback
            try:
                self.widget.insert("insert", text)
            except tk.TclError:
                # TclError: both insert attempts failed, give up gracefully
                pass
        
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
    
    This implementation provides reliable paste functionality that works with
    any text content including special characters and multiline text.
    
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
        
        # Get clipboard content - try multiple methods for reliability
        text = None
        try:
            text = tk_widget.clipboard_get()
        except tk.TclError:
            # TclError: clipboard empty or unavailable, try root window as fallback
            try:
                root = tk_widget.winfo_toplevel()
                text = root.clipboard_get()
            except tk.TclError:
                # TclError: clipboard still unavailable from root
                pass
            except AttributeError:
                # AttributeError: winfo_toplevel or clipboard_get not available
                pass
        
        # If no text available, return without error
        if not text:
            return "break"
            
    except tk.TclError:
        # TclError: widget state check or clipboard access failed
        return "break"
    except AttributeError:
        # AttributeError: widget doesn't have expected methods
        return "break"
    
    # Delete selected text first (if any)
    try:
        tk_widget.delete("sel.first", "sel.last")
    except tk.TclError:
        # TclError: no selection exists, which is expected
        pass
    
    # Insert text at current cursor position
    try:
        tk_widget.insert("insert", text)
    except tk.TclError:
        # TclError: insert failed, give up gracefully
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
    
    SECURITY NOTE: This function uses shell=True as specified in requirements.
    This is less secure than shell=False with argument list. The command is hardcoded
    to prevent injection attacks, but consider using shell=False if requirements allow.
    
    Returns:
        str: The hardware UUID or "UNKNOWN_ID" if an error occurs.
    """
    try:
        # Primary method: Get system UUID using wmic csproduct
        # Using shell=True as specified in requirements (hardcoded command - no user input)
        result = subprocess.check_output(
            'wmic csproduct get uuid',
            timeout=5,
            shell=True
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
    This is "The Gatekeeper" - validates license key with email and manages device binding.
    
    Validation Logic:
    - Query Supabase for a row matching BOTH email AND key. If not found -> "Invalid Credentials"
    - Device Limit Check:
        * Scenario A (Match): If stored hwid == current hwid -> ALLOW ACCESS
        * Scenario B (New Device): If stored hwid is NULL and limit not reached -> UPDATE database with current hwid -> ALLOW ACCESS
        * Scenario C (Limit Reached): If stored hwid != current hwid -> DENY ACCESS (Return "Device Limit Reached")
    
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
                'license_data': None
            }
        
        # Connect to Supabase
        supabase = create_client(supabase_url, supabase_key)
        
        # Query Supabase for a row matching BOTH email AND key
        response = supabase.table("licenses").select("*").eq("license_key", license_key).eq("email", email).execute()
        
        # If not found -> Return "Invalid Credentials"
        if not response.data or len(response.data) == 0:
            return {
                'valid': False,
                'message': 'Invalid Credentials',
                'license_data': None
            }
        
        license_record = response.data[0]
        
        # Check if license is banned
        if license_record.get("is_banned") is True:
            return {
                'valid': False,
                'message': 'This license has been revoked. Contact support.',
                'license_data': license_record
            }
        
        # Check if license has expired
        if is_license_expired(license_record.get("valid_until")):
            return {
                'valid': False,
                'message': 'This license has expired. Please renew your subscription.',
                'license_data': license_record
            }
        
        # Get stored hwid from database
        stored_hwid = license_record.get("hwid")
        
        # Normalize HWIDs for comparison (case-insensitive)
        stored_hwid_normalized = stored_hwid.lower() if stored_hwid else None
        current_hwid_normalized = current_hwid.lower() if current_hwid else None
        
        # Scenario A (Match): If stored hwid == current hwid -> ALLOW ACCESS
        if stored_hwid_normalized and stored_hwid_normalized == current_hwid_normalized:
            return {
                'valid': True,
                'message': 'License is valid and activated on this device.',
                'license_data': license_record
            }
        
        # Scenario B (New Device): If stored hwid is NULL -> UPDATE database with current hwid -> ALLOW ACCESS
        if stored_hwid is None or stored_hwid == "":
            # Update database with current hwid
            supabase.table("licenses").update({
                "hwid": current_hwid
            }).eq("license_key", license_key).eq("email", email).execute()
            
            return {
                'valid': True,
                'message': 'License activated successfully on this device.',
                'license_data': license_record
            }
        
        # Scenario C (Limit Reached): If stored hwid != current hwid -> DENY ACCESS
        if stored_hwid_normalized != current_hwid_normalized:
            return {
                'valid': False,
                'message': 'Device Limit Reached',
                'license_data': license_record
            }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f'Error validating license: {str(e)}',
            'license_data': None
        }


# ==================== PDF GENERATION UTILITIES ====================

# Word banks for procedural chapter title generation
_CHAPTER_PREFIXES = [
    "Introduction to", "Understanding", "Exploring", "Mastering", "Deep Dive into",
    "Fundamentals of", "Advanced", "Practical", "Strategic", "Essential",
    "Comprehensive Guide to", "Key Aspects of", "Modern Approaches to", "Critical Analysis of",
    "Building Blocks of", "Core Principles of", "Professional", "Expert-Level",
    "Hands-On", "Real-World Applications of", "Theoretical Framework for", "Emerging Trends in"
]

_CHAPTER_TOPICS = [
    "Concepts", "Methodologies", "Frameworks", "Best Practices", "Case Studies",
    "Implementation Strategies", "Tools and Techniques", "Analysis Methods", "Design Patterns",
    "Problem Solving", "Decision Making", "Resource Management", "Quality Assurance",
    "Performance Optimization", "Security Considerations", "Scalability Solutions",
    "Integration Approaches", "Testing Strategies", "Deployment Workflows", "Monitoring Systems",
    "Data Management", "User Experience", "Business Logic", "Architecture Patterns",
    "Communication Protocols", "Error Handling", "Documentation Standards", "Team Collaboration",
    "Project Planning", "Risk Assessment", "Cost Analysis", "Timeline Management"
]

_CHAPTER_SUFFIXES = [
    "", "in Practice", "Essentials", "Foundations", "Strategies",
    "Techniques", "Principles", "Overview", "Deep Dive", "Masterclass"
]

_PARAGRAPH_TEMPLATES = [
    "This chapter explores the fundamental aspects of {topic}. Understanding these concepts is crucial for building a solid foundation in this domain. We will examine the key principles that govern {topic} and how they can be applied effectively in real-world scenarios.",
    
    "The importance of {topic} cannot be overstated in today's rapidly evolving landscape. Organizations that master these concepts gain significant competitive advantages. This section provides a comprehensive overview of the most effective approaches.",
    
    "When approaching {topic}, it is essential to consider multiple perspectives. Different stakeholders may have varying requirements and priorities. A balanced approach ensures that all considerations are properly addressed.",
    
    "Practical implementation of {topic} requires careful planning and execution. This involves identifying key requirements, designing appropriate solutions, and validating results through systematic testing. We will walk through each step in detail.",
    
    "The theoretical foundations of {topic} provide the groundwork for practical applications. By understanding the underlying principles, practitioners can make informed decisions and adapt their approaches to specific contexts.",
    
    "Advanced practitioners recognize that {topic} involves nuanced trade-offs. There is rarely a one-size-fits-all solution. Instead, success comes from understanding the specific requirements and constraints of each situation.",
    
    "Industry best practices for {topic} have evolved significantly over time. What was considered optimal a few years ago may no longer be the most effective approach. Staying current with emerging trends is essential.",
    
    "The relationship between {topic} and overall organizational success is well-documented. Research consistently shows that organizations investing in these areas achieve better outcomes across multiple dimensions.",
    
    "Implementing {topic} effectively requires cross-functional collaboration. Different team members bring unique perspectives and expertise. Leveraging this diversity leads to more robust and comprehensive solutions.",
    
    "Looking ahead, {topic} will continue to evolve as new technologies and methodologies emerge. Preparing for these changes requires building adaptable frameworks and maintaining a commitment to continuous learning."
]

_BULLET_POINTS = [
    "Key consideration: Ensure alignment with organizational objectives",
    "Best practice: Document all decisions and their rationale",
    "Important: Regular review and iteration improves outcomes",
    "Note: Context-specific factors may require adaptation",
    "Tip: Start with simple approaches before adding complexity",
    "Recommendation: Involve stakeholders early in the process",
    "Guideline: Measure progress against defined metrics",
    "Principle: Balance short-term needs with long-term goals",
    "Strategy: Build upon proven foundations while innovating",
    "Insight: Learn from both successes and failures"
]


def _generate_unique_chapter_title(chapter_num: int, total_chapters: int) -> str:
    """
    Generate a unique chapter title using procedural word combination.
    
    Args:
        chapter_num: Current chapter number (1-indexed)
        total_chapters: Total number of chapters in the document
        
    Returns:
        str: Unique chapter title
    """
    # Use chapter number as seed for deterministic but varied selection
    seed = chapter_num * 7 + total_chapters * 3  # Prime multipliers for better distribution
    
    # Special cases for first and last chapters (with edge case handling for small books)
    if chapter_num == 1:
        return f"Chapter 1: Introduction and Overview"
    elif chapter_num == total_chapters:
        return f"Chapter {chapter_num}: Conclusion and Future Directions"
    elif total_chapters > 3 and chapter_num == 2:
        return f"Chapter 2: Foundational Concepts"
    elif total_chapters > 4 and chapter_num == total_chapters - 1:
        return f"Chapter {chapter_num}: Putting It All Together"
    
    # Procedural selection using modular arithmetic for variety
    prefix_idx = (seed + chapter_num) % len(_CHAPTER_PREFIXES)
    topic_idx = (seed * 2 + chapter_num * 3) % len(_CHAPTER_TOPICS)
    suffix_idx = (seed + chapter_num * 5) % len(_CHAPTER_SUFFIXES)
    
    prefix = _CHAPTER_PREFIXES[prefix_idx]
    topic = _CHAPTER_TOPICS[topic_idx]
    suffix = _CHAPTER_SUFFIXES[suffix_idx]
    
    # Construct title with optional suffix
    if suffix:
        title = f"Chapter {chapter_num}: {prefix} {topic} - {suffix}"
    else:
        title = f"Chapter {chapter_num}: {prefix} {topic}"
    
    return title


def _generate_chapter_content(chapter_num: int, total_chapters: int, chapter_title: str) -> str:
    """
    Generate unique, varied content for a chapter using procedural techniques.
    
    Args:
        chapter_num: Current chapter number (1-indexed)
        total_chapters: Total number of chapters
        chapter_title: Title of this chapter for context
        
    Returns:
        str: Multi-paragraph content with varied structure
    """
    # Extract topic from title for templating
    topic = chapter_title.split(":")[-1].strip() if ":" in chapter_title else "this topic"
    
    # Calculate content length variation (earlier chapters tend to be longer)
    if chapter_num <= 2:
        num_paragraphs = 4  # Introduction chapters
    elif chapter_num >= total_chapters - 1:
        num_paragraphs = 3  # Conclusion chapters
    else:
        # Vary between 3-5 paragraphs based on chapter number
        num_paragraphs = 3 + (chapter_num % 3)
    
    content_parts = []
    
    # Select and format paragraphs using procedural indexing
    seed = chapter_num * 11 + total_chapters
    
    for para_idx in range(num_paragraphs):
        template_idx = (seed + para_idx * 7) % len(_PARAGRAPH_TEMPLATES)
        template = _PARAGRAPH_TEMPLATES[template_idx]
        paragraph = template.format(topic=topic)
        content_parts.append(paragraph)
        
        # Add bullet points section for some chapters (varied placement and count)
        if para_idx == 1 and chapter_num % 3 == 0:
            bullet_start = (seed + chapter_num) % len(_BULLET_POINTS)
            # Use chapter_num // 3 for actual variation (3, 4, or 5 bullets)
            num_bullets = 3 + ((chapter_num // 3) % 3)
            bullets = []
            for b in range(num_bullets):
                bullet_idx = (bullet_start + b) % len(_BULLET_POINTS)
                bullets.append(f"• {_BULLET_POINTS[bullet_idx]}")
            content_parts.append("\n".join(bullets))
    
    # Add a summary paragraph for longer chapters
    if num_paragraphs >= 4:
        summary = f"In summary, this chapter has provided essential insights into {topic}. The concepts covered here form a critical foundation for understanding the subsequent material and applying these principles effectively."
        content_parts.append(summary)
    
    return "\n\n".join(content_parts)


def generate_pdf(course_data: Dict[str, Any], page_count: int = 10, output_path: Optional[str] = None, media_files: list = None) -> str:
    """
    Generate a styled PDF document from course data using reportlab.
    Uses PROCEDURAL GENERATION to create unique chapter titles and varied content.
    NO CONTENT DUPLICATION - each chapter is uniquely generated.
    
    Args:
        course_data: Dictionary containing:
            - 'title': Course title (required)
            - 'chapters': List of chapter dicts with 'title' and 'content' keys
                         If empty or insufficient, procedural chapters will be generated
        page_count: Target number of pages (5-100). Determines unique chapter count.
                   Formula: 1 chapter per 2 pages (page_count // 2).
        output_path: Optional custom output path. If None, saves to Downloads folder.
        media_files: Optional list of media file paths for reference (listed at end of PDF).
        
    Returns:
        str: Path to the generated PDF file
        
    Raises:
        ImportError: If reportlab is not installed
        IOError: If PDF cannot be written to disk
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.colors import HexColor
    from xml.sax.saxutils import escape
    
    # Register Roboto fonts for proper Unicode/Cyrillic support
    fonts_available = _register_roboto_fonts()
    
    # Choose font names based on availability
    font_regular = 'Roboto' if fonts_available else 'Helvetica'
    font_bold = 'Roboto-Bold' if fonts_available else 'Helvetica-Bold'
    
    # Validate and clamp page_count to acceptable range (5-100)
    page_count = max(5, min(100, int(page_count)))
    
    # Calculate number of unique chapters needed (~2-3 pages per chapter)
    # This ensures each chapter is UNIQUE, not duplicated
    num_chapters = max(3, page_count // 2)  # Minimum 3 chapters, ~2 pages per chapter
    
    # Determine output path - default to Downloads folder using os.path.expanduser
    if output_path is None:
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        title = course_data.get('title', 'Untitled Course')
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50] if safe_title else "Course"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.pdf"
        output_path = os.path.join(downloads_dir, filename)
    
    # Ensure parent directory exists
    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Update base styles to use Roboto fonts for proper Unicode support
    styles['Normal'].fontName = font_regular
    styles['BodyText'].fontName = font_regular
    styles['Title'].fontName = font_bold
    styles['Heading1'].fontName = font_bold
    styles['Heading2'].fontName = font_bold
    styles['Heading3'].fontName = font_bold
    
    # Create custom styles for professional appearance
    title_style = ParagraphStyle(
        'CourseTitle',
        parent=styles['Heading1'],
        fontSize=28,
        alignment=TA_CENTER,
        spaceAfter=40,
        spaceBefore=60,
        textColor=HexColor('#1a1a2e'),
        fontName=font_bold
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=HexColor('#666666'),
        fontName=font_regular  # Roboto doesn't have oblique, use regular
    )
    
    chapter_style = ParagraphStyle(
        'ChapterTitle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=16,
        spaceBefore=24,
        textColor=HexColor('#2c3e50'),
        fontName=font_bold
    )
    
    content_style = ParagraphStyle(
        'ContentText',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        leading=16,
        alignment=TA_JUSTIFY,
        fontName=font_regular
    )
    
    # Build document content
    story = []
    
    # ===== TITLE PAGE =====
    title = course_data.get('title', 'Untitled Course')
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph(escape(title), title_style))
    story.append(Paragraph(f"A Comprehensive {num_chapters}-Chapter Guide", subtitle_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    story.append(PageBreak())
    
    # ===== TABLE OF CONTENTS =====
    toc_title_style = ParagraphStyle(
        'TOCTitle',
        parent=styles['Heading1'],
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=HexColor('#1a1a2e'),
        fontName=font_bold
    )
    toc_entry_style = ParagraphStyle(
        'TOCEntry',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=8,
        leftIndent=20,
        fontName=font_regular
    )
    
    story.append(Paragraph("Table of Contents", toc_title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Generate TOC entries (unique titles)
    chapter_titles = []
    for i in range(1, num_chapters + 1):
        chapter_title = _generate_unique_chapter_title(i, num_chapters)
        chapter_titles.append(chapter_title)
        story.append(Paragraph(escape(chapter_title), toc_entry_style))
    
    story.append(PageBreak())
    
    # ===== CHAPTERS WITH UNIQUE CONTENT =====
    # Get existing chapters from course_data, or use procedural generation
    existing_chapters = course_data.get('chapters', [])
    
    for i, chapter_title in enumerate(chapter_titles):
        chapter_num = i + 1
        
        # Add chapter title
        story.append(Paragraph(escape(chapter_title), chapter_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Get content: use existing if available, otherwise generate procedurally
        if i < len(existing_chapters) and existing_chapters[i].get('content'):
            chapter_content = existing_chapters[i].get('content', '')
        else:
            # Procedurally generate unique content
            chapter_content = _generate_chapter_content(chapter_num, num_chapters, chapter_title)
        
        # Add content paragraphs
        for paragraph in chapter_content.split('\n\n'):
            if paragraph.strip():
                story.append(Paragraph(escape(paragraph.strip()), content_style))
                story.append(Spacer(1, 0.1 * inch))
        
        story.append(Spacer(1, 0.4 * inch))
        
        # Add page break between chapters (except last)
        if chapter_num < num_chapters:
            story.append(PageBreak())
    
    # Add media files appendix if any media files were attached
    if media_files:
        story.append(PageBreak())
        story.append(Paragraph("Attached Media Files", chapter_style))
        story.append(Spacer(1, 0.2 * inch))
        
        for idx, media_path in enumerate(media_files, 1):
            filename = os.path.basename(media_path)
            story.append(Paragraph(f"{idx}. {escape(filename)}", content_style))
        
        story.append(Spacer(1, 0.3 * inch))
    
    # Build the PDF
    doc.build(story)
    
    return output_path
