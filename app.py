"""
CourseSmith AI Enterprise - Main Application GUI.
A commercial desktop tool to generate educational PDF books using AI with DRM protection.
Uses session token system for anti-tamper protection.
Features tiered licensing: Standard ($59) vs Extended ($249).

Enterprise Features:
- Splash screen with loading animation
- Persistent login with encrypted session storage
- HWID binding for hardware-locked licenses
- Expiration date checking
- Animated UI transitions
"""

import os
import re
import threading
import time
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog, Menu, TclError

from utils import resource_path, get_data_dir, clipboard_cut, clipboard_copy, clipboard_paste, clipboard_select_all, add_context_menu, get_underlying_tk_widget, patch_ctk_scrollbar
from license_guard import validate_license, load_license, save_license, remove_license, get_hwid
from session_manager import set_session, set_token, is_active, get_tier, is_extended, clear_session
from project_manager import CourseProject
from ai_worker import OutlineGenerator, ChapterWriter, CoverGenerator, AIWorkerBase
from pdf_engine import PDFBuilder
# Import exporters for multi-format output support
from docx_exporter import DOCXExporter
from html_exporter import HTMLExporter
from export_base import ExportManager, ExportError

# Apply scrollbar patch to prevent RecursionError in CTkScrollableFrame
# This must be called before creating any scrollable widgets
patch_ctk_scrollbar()

# Configure appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Performance tuning constants for live preview streaming
PREVIEW_UPDATE_INTERVAL = 5  # Update UI every N chunks (reduces update_idletasks calls by ~80%)
LARGE_CHUNK_THRESHOLD = 50  # Force immediate update for chunks larger than this (characters)


class SplashScreen(ctk.CTkToplevel):
    """Splash screen with loading animation for main application."""
    
    def __init__(self, parent):
        """Initialize splash screen."""
        super().__init__(parent)
        
        # Configure window
        self.title("")
        self.geometry("600x400")
        self.resizable(False, False)
        
        # Remove window decorations
        self.overrideredirect(True)
        
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (400 // 2)
        self.geometry(f"600x400+{x}+{y}")
        
        # Create UI
        self._create_ui()
        
        # Make sure it's on top
        self.lift()
        self.focus_force()
        
    def _create_ui(self):
        """Create splash screen UI."""
        # Main frame with depth and shadow effect
        main_frame = ctk.CTkFrame(
            self, 
            corner_radius=25, 
            border_width=3, 
            border_color=("#1f6aa5", "#3b8ed0"),
            fg_color=("#2b2b2b", "#1a1a1a")
        )
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Logo/Icon
        logo_label = ctk.CTkLabel(
            main_frame,
            text="📚",
            font=ctk.CTkFont(size=100)
        )
        logo_label.pack(pady=(60, 10))
        
        # App name
        app_name_label = ctk.CTkLabel(
            main_frame,
            text="CourseSmith AI Enterprise",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0")
        )
        app_name_label.pack(pady=(0, 5))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Professional PDF Course Generator",
            font=ctk.CTkFont(size=16),
            text_color=("gray60", "gray50")
        )
        subtitle_label.pack(pady=(0, 50))
        
        # Progress bar with animation
        self.progress = ctk.CTkProgressBar(
            main_frame,
            width=400,
            height=18,
            corner_radius=10,
            mode="indeterminate",
            progress_color=("#1f6aa5", "#3b8ed0")
        )
        self.progress.pack(pady=(0, 15))
        self.progress.start()
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Initializing...",
            font=ctk.CTkFont(size=13),
            text_color=("gray60", "gray50")
        )
        self.status_label.pack(pady=(0, 40))
        
        # Version info
        version_label = ctk.CTkLabel(
            main_frame,
            text="v2.0 Enterprise Edition",
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray30")
        )
        version_label.pack(pady=(0, 20))
    
    def update_status(self, text):
        """Update status message."""
        self.status_label.configure(text=text)
        self.update()
    
    def close_splash(self):
        """Close splash screen with fade effect."""
        self.progress.stop()
        self.destroy()


def bind_clipboard_menu(widget):
    """
    Bind a clipboard context menu and click-to-focus to a widget.
    Keyboard shortcuts (Ctrl+A/C/V/X) are handled globally at the root window level.
    
    Args:
        widget: The CTkEntry or CTkTextbox widget to bind to.
        
    Returns:
        RightClickMenu: The created context menu instance.
    """
    # Get the underlying tkinter widget for focus binding
    tk_widget = get_underlying_tk_widget(widget)
    
    # Bind Button-1 to ensure immediate keyboard focus on click
    tk_widget.bind("<Button-1>", lambda e: tk_widget.focus_set(), add="+")
    
    # Add right-click context menu (keyboard shortcuts are global)
    return add_context_menu(widget)


class App(ctk.CTk):
    """Main application window for CourseSmith AI Enterprise with DRM protection."""
    
    # Class-level constants for export format configuration
    DEFAULT_EXPORT_FORMAT = "PDF"
    FORMAT_ICONS = {"PDF": "📄", "DOCX": "📝", "HTML": "🌐"}
    FORMAT_CONFIG = {
        "PDF": {"ext": ".pdf", "filter": [("PDF Files", "*.pdf")]},
        "DOCX": {"ext": ".docx", "filter": [("Word Documents", "*.docx")]},
        "HTML": {"ext": ".html", "filter": [("HTML Files", "*.html")]},
    }
    
    # Button color constants for format selector - selected vs unselected states
    FORMAT_BTN_SELECTED = {"fg": "#1f6aa5", "hover": "#3b8ed0", "border": "#3b8ed0"}
    FORMAT_BTN_UNSELECTED = {"fg": "#4a4a4a", "hover": "#666666", "border": "#555555"}

    def _get_format_icon(self, format_name):
        """
        Get the icon for a given export format.
        
        Args:
            format_name: The export format (PDF, DOCX, HTML).
            
        Returns:
            str: The emoji icon for the format, or default format icon if not found.
        """
        return self.FORMAT_ICONS.get(format_name, self.FORMAT_ICONS[self.DEFAULT_EXPORT_FORMAT])

    def __init__(self):
        """Initialize the application window and widgets."""
        super().__init__()

        # Window configuration
        self.title("CourseSmith AI Enterprise - Educational PDF Generator")
        self.geometry("1000x700")
        self.minsize(900, 600)

        # Set window icon if it exists (PyInstaller compatible)
        icon_path = resource_path("resources/coursesmithai.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass  # Icon not critical, continue without it

        # Initialize project
        self.project = CourseProject()
        
        # Track state
        self.is_licensed = False
        self.licensed_email = None
        self.license_tier = None  # 'standard' or 'extended'
        self.is_generating = False
        self.current_chapter_index = 0
        self.total_chapters = 0
        self.target_pages = 50  # Global page count from Setup, default 50
        
        # Animation state for progress indicators
        self._animation_running = False
        self._animation_step = 0

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Bind global keyboard shortcuts for clipboard operations
        self._bind_global_shortcuts()

        # Hide main window initially
        self.withdraw()

        # Show splash screen and check license
        self._show_splash()

    def _show_splash(self):
        """Show splash screen with loading animation."""
        splash = SplashScreen(self)
        
        def load_app():
            """Load app with minimal delays for better UX."""
            # Reduced delays from 0.3s to 0.1s for faster startup
            # while still providing visual feedback
            time.sleep(0.1)
            splash.update_status("Loading modules...")
            time.sleep(0.1)
            splash.update_status("Loading license system...")
            time.sleep(0.1)
            splash.update_status("Checking saved session...")
            time.sleep(0.1)
            
            # Check for saved license
            has_session = self._check_license_silent()
            
            if has_session:
                splash.update_status("Restoring session...")
                time.sleep(0.1)
            else:
                splash.update_status("No saved session found...")
                time.sleep(0.1)
            
            splash.update_status("Loading UI components...")
            time.sleep(0.1)
            splash.update_status("Ready!")
            time.sleep(0.1)
            
            # Close splash and show main window
            self.after(0, lambda: self._finish_loading(splash, has_session))
        
        # Run loading in thread
        thread = threading.Thread(target=load_app, daemon=True)
        thread.start()
    
    def _finish_loading(self, splash, has_session):
        """Finish loading and show appropriate screen."""
        splash.close_splash()
        self.deiconify()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1000x700+{x}+{y}")
        
        if has_session:
            # Show main UI directly
            self._create_main_ui()
        else:
            # Show login screen
            self._create_activation_ui()

    def _check_license_silent(self):
        """
        Check for saved license session silently (no UI).
        Returns True if valid session found, False otherwise.
        """
        try:
            # Try to load saved session
            token, email, tier, expires_at, license_key = load_license()
            
            if token and email and tier:
                # Valid session found
                set_session(token, email, tier, license_key=license_key)
                self.is_licensed = True
                self.licensed_email = email
                self.license_tier = tier
                return True
        except Exception as e:
            print(f"Failed to load saved session: {e}")
        
        # No valid session
        self.is_licensed = False
        self.license_tier = None
        clear_session()
        return False

    def _create_activation_ui(self):
        """Create the license activation screen with modern, professional design."""
        # Clear any existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Main activation frame - centered with modern styling and depth
        # Using responsive padding that scales with window size
        self.activation_frame = ctk.CTkFrame(
            self, 
            corner_radius=20, 
            border_width=3, 
            border_color=("#3b8ed0", "#1f6aa5"),
            fg_color=("#2b2b2b", "#1a1a1a")
        )
        self.activation_frame.grid(row=0, column=0, padx=100, pady=40, sticky="nsew")
        self.activation_frame.grid_columnconfigure(0, weight=1)
        # Add row weight for the spacer row to enable flexible expansion
        self.activation_frame.grid_rowconfigure(9, weight=1)

        # Logo/Title with enhanced styling
        title_label = ctk.CTkLabel(
            self.activation_frame,
            text="🔐 CourseSmith AI Enterprise",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0"),
        )
        title_label.grid(row=0, column=0, padx=40, pady=(30, 10))

        subtitle_label = ctk.CTkLabel(
            self.activation_frame,
            text="Professional PDF Course Generator",
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray50"),
        )
        subtitle_label.grid(row=1, column=0, padx=40, pady=(0, 5))
        
        subtitle_label2 = ctk.CTkLabel(
            self.activation_frame,
            text="License Activation Required",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#555", "#aaa"),
        )
        subtitle_label2.grid(row=2, column=0, padx=40, pady=(0, 25))

        # Email entry with modern styling
        email_label = ctk.CTkLabel(
            self.activation_frame,
            text="📧 Email Address:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        email_label.grid(row=3, column=0, padx=40, pady=(10, 5), sticky="w")

        self.email_entry = ctk.CTkEntry(
            self.activation_frame,
            placeholder_text="your.email@example.com",
            width=420,
            height=50,
            font=ctk.CTkFont(size=14),
            border_width=2,
            corner_radius=10,
        )
        self.email_entry.grid(row=4, column=0, padx=40, pady=(0, 15))
        bind_clipboard_menu(self.email_entry)

        # License key entry with modern styling
        key_label = ctk.CTkLabel(
            self.activation_frame,
            text="🔑 License Key:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        key_label.grid(row=5, column=0, padx=40, pady=(10, 5), sticky="w")

        self.key_entry = ctk.CTkEntry(
            self.activation_frame,
            placeholder_text="XXXXXX-XXX-XXXXXXXX-XXXXXXXX",
            width=420,
            height=50,
            font=ctk.CTkFont(size=14),
            border_width=2,
            corner_radius=10,
        )
        self.key_entry.grid(row=6, column=0, padx=40, pady=(0, 15))
        bind_clipboard_menu(self.key_entry)

        # Remember me checkbox
        self.remember_var = ctk.BooleanVar(value=True)
        remember_checkbox = ctk.CTkCheckBox(
            self.activation_frame,
            text="Remember me on this computer",
            variable=self.remember_var,
            font=ctk.CTkFont(size=12),
            corner_radius=5
        )
        remember_checkbox.grid(row=7, column=0, padx=40, pady=(0, 15))
        
        # Status label for validation feedback
        self.activation_status_label = ctk.CTkLabel(
            self.activation_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.activation_status_label.grid(row=8, column=0, padx=40, pady=(0, 10))

        # Flexible spacer that expands to push button to bottom
        # This row has weight=1, so it will expand in fullscreen
        spacer_frame = ctk.CTkFrame(self.activation_frame, fg_color="transparent")
        spacer_frame.grid(row=9, column=0, sticky="nsew")

        # Activate button with enhanced styling - anchored to bottom
        self.activate_btn = ctk.CTkButton(
            self.activation_frame,
            text="🔓 ACTIVATE & ENTER",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=55,
            width=320,
            corner_radius=12,
            fg_color=("#28a745", "#20873a"),
            hover_color=("#218838", "#1a6d2e"),
            border_width=0,
            command=self._on_activate_click,
        )
        self.activate_btn.grid(row=10, column=0, padx=40, pady=(10, 30))

    def _on_activate_click(self):
        """Handle license activation with enterprise features in background thread."""
        email = self.email_entry.get().strip()
        key = self.key_entry.get().strip()

        if not email:
            messagebox.showerror("Error", "Please enter your email address.")
            return

        if not key:
            messagebox.showerror("Error", "Please enter your license key.")
            return

        # Disable activate button during validation
        self.activate_btn.configure(state="disabled", text="⏳ Validating...")
        self.activation_status_label.configure(text="Validating license...", text_color="orange")
        
        # Run validation in background thread to prevent UI freeze
        def validate_in_background():
            try:
                # Validate the license with new enterprise validation
                result = validate_license(email, key, check_expiration=True)
                
                # Schedule UI update on main thread
                self.after(0, lambda: self._on_validation_complete(result, email, key))
            except Exception as e:
                # Schedule error handling on main thread
                self.after(0, lambda: self._on_validation_error(str(e)))
        
        # Start validation thread
        thread = threading.Thread(target=validate_in_background, daemon=True)
        thread.start()
    
    def _on_validation_complete(self, result, email, key):
        """Handle validation completion on main thread."""
        # Re-enable activate button
        self.activate_btn.configure(state="normal", text="🚀 Activate License")
        
        if not result or not result.get('valid'):
            # Show appropriate error message
            error_msg = result.get('message', 'Invalid license key or email.') if result else 'Invalid license key or email.'
            
            # Check if expired
            if result and result.get('expired'):
                expires_at = result.get('expires_at')
                if expires_at:
                    try:
                        exp_date = datetime.fromisoformat(expires_at).strftime('%Y-%m-%d')
                        error_msg = f"License Expired\n\nYour license expired on {exp_date}.\nPlease contact support to renew your license."
                    except:
                        error_msg = "License Expired\n\nYour license has expired.\nPlease contact support to renew your license."
                else:
                    error_msg = "License Expired\n\nYour license has expired.\nPlease contact support to renew your license."
            
            self.activation_status_label.configure(text="Validation failed", text_color="red")
            messagebox.showerror("License Validation Failed", error_msg)
            return
        
        # Valid license - extract info
        tier = result.get('tier', 'standard')
        token = result.get('token')
        expires_at = result.get('expires_at')
        
        # Set the session
        set_session(token, email, tier, license_key=key)
        self.is_licensed = True
        self.licensed_email = email
        self.license_tier = tier
        
        # Save session if "Remember me" is checked
        remember_me = self.remember_var.get()
        if remember_me:
            try:
                save_license(email, key, tier, expires_at)
            except Exception as e:
                print(f"Warning: Failed to save session: {e}")
                # Continue anyway - validation succeeded
        
        # Show success message
        tier_label_map = {
            'trial': 'Trial',
            'standard': 'Standard',
            'enterprise': 'Enterprise',
            'lifetime': 'Lifetime',
            'extended': 'Enterprise'  # Legacy support
        }
        tier_label = tier_label_map.get(tier, 'Trial')
        expires_msg = ""
        if expires_at:
            try:
                exp_date = datetime.fromisoformat(expires_at).strftime('%Y-%m-%d')
                expires_msg = f"\nExpires: {exp_date}"
            except:
                expires_msg = ""
        else:
            expires_msg = "\nExpires: Never (Lifetime)"
        
        # Note: HWID is not displayed to user for security reasons
        # It's only used internally for hardware binding validation
        
        self.activation_status_label.configure(text="Success!", text_color="green")
        
        messagebox.showinfo(
            "Success",
            f"License activated successfully!\n\n"
            f"Tier: {tier_label}{expires_msg}\n\n"
            f"Welcome to CourseSmith AI Enterprise!",
        )
        
        # Transition to main UI with fade effect
        self._transition_to_main_ui()
    
    def _on_validation_error(self, error_msg):
        """Handle validation error on main thread."""
        # Re-enable activate button
        self.activate_btn.configure(state="normal", text="🚀 Activate License")
        self.activation_status_label.configure(text="Validation error", text_color="red")
        messagebox.showerror("Error", f"License validation failed:\n\n{error_msg}")
    
    def _transition_to_main_ui(self):
        """Transition from login to main UI with animation."""
        # Simple fade - destroy activation UI and create main UI
        # In a more advanced version, you could implement actual fade effects
        self._create_main_ui()

    def _create_main_ui(self):
        """Create the main application UI with tabs."""
        # Clear any existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header bar
        self._create_header()

        # Tab view
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        # Create tabs
        self.tab_setup = self.tabview.add("📝 Setup")
        self.tab_blueprint = self.tabview.add("📋 Blueprint")
        self.tab_drafting = self.tabview.add("✍️ Drafting")
        self.tab_export = self.tabview.add("📤 Export")

        # Build tab contents
        self._create_setup_tab()
        self._create_blueprint_tab()
        self._create_drafting_tab()
        self._create_export_tab()
        
        # Set up tab change handler for auto-scroll to top
        self.tabview.configure(command=self._on_tab_change)
    
    def _on_tab_change(self):
        """Handle tab change to auto-scroll to top.
        
        Note: Uses _parent_canvas which is a private attribute of CTkScrollableFrame.
        This is the standard approach in CustomTkinter for programmatic scrolling.
        """
        current_tab = self.tabview.get()
        
        # Scroll to top of the current tab's scrollable frames
        if current_tab == "📝 Setup":
            if hasattr(self, 'setup_left_scroll'):
                self.setup_left_scroll._parent_canvas.yview_moveto(0)
            if hasattr(self, 'setup_right_scroll'):
                self.setup_right_scroll._parent_canvas.yview_moveto(0)
        elif current_tab == "✍️ Drafting":
            if hasattr(self, 'preview_scroll'):
                self.preview_scroll._parent_canvas.yview_moveto(0)
        elif current_tab == "📤 Export":
            if hasattr(self, 'export_cover_scroll'):
                self.export_cover_scroll._parent_canvas.yview_moveto(0)
            if hasattr(self, 'export_pdf_scroll'):
                self.export_pdf_scroll._parent_canvas.yview_moveto(0)

    def _create_header(self):
        """Create the header bar with title, tier info, and settings."""
        header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        # Configure grid columns: column 1 (tier label) expands to fill space
        header_frame.grid_columnconfigure(0, weight=0)  # Title - fixed
        header_frame.grid_columnconfigure(1, weight=1)  # Tier label - expands
        header_frame.grid_columnconfigure(2, weight=0)  # Switch Key - fixed
        header_frame.grid_columnconfigure(3, weight=0)  # Settings - fixed
        header_frame.grid_columnconfigure(4, weight=0)  # User info - fixed

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Faleovad AI Enterprise",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Tier indicator - Support all 4 tiers
        tier_display_map = {
            'trial': ('Trial (10 pages)', '#ff9800'),
            'standard': ('Standard (50 pages)', '#888888'),
            'enterprise': ('✓ Enterprise (300 pages)', '#ffd700'),
            'lifetime': ('✓ Lifetime (Unlimited)', '#00ff00'),
            'extended': ('✓ Enterprise (300 pages)', '#ffd700')  # Legacy support
        }
        
        tier_text, tier_color = tier_display_map.get(
            self.license_tier, 
            ('Trial', '#888888')
        )
        
        tier_label = ctk.CTkLabel(
            header_frame,
            text=tier_text,
            font=ctk.CTkFont(size=12, weight="bold" if self.license_tier in ('enterprise', 'lifetime', 'extended') else "normal"),
            text_color=tier_color,
        )
        tier_label.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        # Switch/Reset Key button - subtle secondary button
        switch_key_btn = ctk.CTkButton(
            header_frame,
            text="🔑 Switch Key",
            font=ctk.CTkFont(size=11),
            width=95,
            height=32,
            fg_color="#444444",
            hover_color="#555555",
            border_width=1,
            border_color="#666666",
            command=self._switch_license_key,
        )
        switch_key_btn.grid(row=0, column=2, padx=10, pady=15, sticky="e")

        # Settings button
        settings_btn = ctk.CTkButton(
            header_frame,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=12),
            width=100,
            height=32,
            fg_color="#555555",
            hover_color="#666666",
            command=self._show_settings,
        )
        settings_btn.grid(row=0, column=3, padx=10, pady=15, sticky="e")

        # User info
        if self.licensed_email:
            user_label = ctk.CTkLabel(
                header_frame,
                text=f"✓ {self.licensed_email}",
                font=ctk.CTkFont(size=12),
                text_color="#28a745",
            )
            user_label.grid(row=0, column=4, padx=20, pady=15, sticky="e")

    def _switch_license_key(self):
        """
        Allow user to switch/reset their license key without deleting project data.
        This enables upgrading from Standard to Enterprise or changing keys.
        """
        # Confirm action with user
        confirm = messagebox.askyesno(
            "Switch License Key",
            "This will log you out and allow you to enter a new license key.\n\n"
            "Your project data will NOT be deleted.\n\n"
            "Do you want to continue?",
            parent=self
        )
        
        if not confirm:
            return
        
        # Clear the current session and saved license
        clear_session()
        remove_license()
        
        # Reset license state
        self.is_licensed = False
        self.licensed_email = None
        self.license_tier = None
        
        # Show info message
        messagebox.showinfo(
            "License Key Reset",
            "Your license has been reset.\n\n"
            "You will now be redirected to the login screen to enter a new key.",
            parent=self
        )
        
        # Recreate activation UI
        self._create_activation_ui()

    def _show_settings(self):
        """Show the settings dialog with configuration info."""
        # Create modal dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("500x200")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        # Title
        ctk.CTkLabel(
            dialog,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(padx=20, pady=(20, 10))

        # Info section (API key is managed internally)
        ctk.CTkLabel(
            dialog,
            text="ℹ️ API Configuration",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=20, pady=(20, 5), anchor="w")

        # Help text
        ctk.CTkLabel(
            dialog,
            text="API access is managed automatically. Credits are deducted from your license when generating courses.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=450,
            justify="left",
        ).pack(padx=20, pady=(0, 20))

        # Close button
        ctk.CTkButton(
            dialog,
            text="Close",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=200,
            fg_color="#6c757d",
            hover_color="#5a6268",
            command=dialog.destroy,
        ).pack(pady=20)

    # ==================== SETUP TAB ====================
    def _create_setup_tab(self):
        """Create the Setup tab content with tier-based branding restrictions."""
        self.tab_setup.grid_columnconfigure(0, weight=1)
        self.tab_setup.grid_columnconfigure(1, weight=1)
        self.tab_setup.grid_rowconfigure(0, weight=1)

        # Left column - Course Info (Scrollable)
        left_frame = ctk.CTkScrollableFrame(self.tab_setup, corner_radius=10)
        left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(
            left_frame,
            text="📚 Course Information",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 20), sticky="w")

        # Topic
        ctk.CTkLabel(left_frame, text="Topic:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=1, column=0, padx=20, pady=(20, 5), sticky="w"
        )
        self.topic_entry = ctk.CTkEntry(
            left_frame, placeholder_text="e.g., Bitcoin Trading Strategies", width=350, height=40
        )
        self.topic_entry.grid(row=2, column=0, padx=20, pady=(0, 20))
        bind_clipboard_menu(self.topic_entry)

        # Audience
        ctk.CTkLabel(left_frame, text="Target Audience:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=3, column=0, padx=20, pady=(20, 5), sticky="w"
        )
        self.audience_entry = ctk.CTkEntry(
            left_frame, placeholder_text="e.g., Beginners with no trading experience", width=350, height=40
        )
        self.audience_entry.grid(row=4, column=0, padx=20, pady=(0, 20))
        bind_clipboard_menu(self.audience_entry)

        # === NEW FEATURE: Page Count Selector ===
        ctk.CTkLabel(
            left_frame, 
            text="📄 Target Page Count:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=5, column=0, padx=20, pady=(20, 5), sticky="w")
        
        # Page slider with value display
        page_selector_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        page_selector_frame.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.page_count_slider = ctk.CTkSlider(
            page_selector_frame,
            from_=10,
            to=300,
            number_of_steps=145,  # (300-10)/2 = 145 steps for increments of 2
            width=250,
            command=self._update_page_count_display,
        )
        self.page_count_slider.set(50)  # Default to 50 pages
        self.page_count_slider.pack(side="left", padx=(0, 15))
        
        self.page_count_label = ctk.CTkLabel(
            page_selector_frame,
            text="50 pages",
            font=ctk.CTkFont(size=16, weight="bold"),
            width=80,
        )
        self.page_count_label.pack(side="left")

        # === NEW FEATURE: Custom Media Upload ===
        ctk.CTkLabel(
            left_frame,
            text="🖼️ Custom Images:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=7, column=0, padx=20, pady=(20, 5), sticky="w")
        
        custom_media_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        custom_media_frame.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        self.select_images_btn = ctk.CTkButton(
            custom_media_frame,
            text="📁 Select Custom Images",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            width=200,
            fg_color="#6c5ce7",
            hover_color="#5b4cdb",
            command=self._select_custom_images,
        )
        self.select_images_btn.pack(side="left", padx=(0, 10))
        
        self.selected_images_label = ctk.CTkLabel(
            custom_media_frame,
            text="No images selected",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.selected_images_label.pack(side="left")
        
        # Store selected images
        self.custom_images = []

        # === NEW FEATURE: Typography Controls ===
        ctk.CTkLabel(
            left_frame,
            text="✍️ Content Styling:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=9, column=0, padx=20, pady=(20, 5), sticky="w")
        
        typography_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        typography_frame.grid(row=10, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Text style selector (Segmented button)
        self.text_style_var = ctk.StringVar(value="Normal Text")
        self.text_style_selector = ctk.CTkSegmentedButton(
            typography_frame,
            values=["Normal Text", "Header H1", "Header H2"],
            variable=self.text_style_var,
            font=ctk.CTkFont(size=12),
            width=320,
        )
        self.text_style_selector.pack(pady=(0, 10))
        
        # Font size selector
        font_size_frame = ctk.CTkFrame(typography_frame, fg_color="transparent")
        font_size_frame.pack(fill="x")
        
        ctk.CTkLabel(
            font_size_frame,
            text="Font Size:",
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(0, 10))
        
        self.font_size_var = ctk.StringVar(value="Medium")
        self.font_size_selector = ctk.CTkOptionMenu(
            font_size_frame,
            values=["Small", "Medium", "Large"],
            variable=self.font_size_var,
            width=120,
        )
        self.font_size_selector.pack(side="left")

        # Right column - Branding (Scrollable)
        right_frame = ctk.CTkScrollableFrame(self.tab_setup, corner_radius=10)
        right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Check if Extended tier for branding access
        is_extended_tier = is_extended()
        
        branding_title = "🎨 Branding (PRO)" if is_extended_tier else "🔒 Branding (Extended Only)"
        ctk.CTkLabel(
            right_frame,
            text=branding_title,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 20), sticky="w")

        # Logo path
        ctk.CTkLabel(right_frame, text="Logo Image:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=1, column=0, padx=20, pady=(20, 5), sticky="w"
        )
        
        logo_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        logo_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")
        
        self.logo_entry = ctk.CTkEntry(
            logo_frame, 
            placeholder_text="Path to logo image..." if is_extended_tier else "🔒 Extended License Required",
            width=250, 
            height=35,
            state="normal" if is_extended_tier else "disabled"
        )
        self.logo_entry.grid(row=0, column=0, padx=(0, 10))
        if is_extended_tier:
            bind_clipboard_menu(self.logo_entry)
        
        self.browse_logo_btn = ctk.CTkButton(
            logo_frame, 
            text="Browse", 
            width=80, 
            height=35, 
            command=self._browse_logo,
            state="normal" if is_extended_tier else "disabled"
        )
        self.browse_logo_btn.grid(row=0, column=1)

        # Website URL
        ctk.CTkLabel(right_frame, text="Website URL:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=3, column=0, padx=20, pady=(20, 5), sticky="w"
        )
        self.website_entry = ctk.CTkEntry(
            right_frame, 
            placeholder_text="e.g., www.yourcompany.com" if is_extended_tier else "🔒 Extended License Required",
            width=350, 
            height=40,
            state="normal" if is_extended_tier else "disabled"
        )
        self.website_entry.grid(row=4, column=0, padx=20, pady=(0, 20))
        if is_extended_tier:
            bind_clipboard_menu(self.website_entry)

        # Upgrade button for Standard tier users
        if not is_extended_tier:
            upgrade_btn = ctk.CTkButton(
                right_frame,
                text="🔒 Unlock Branding (Get Extended)",
                font=ctk.CTkFont(size=13, weight="bold"),
                height=40,
                width=300,
                fg_color="#ffd700",
                hover_color="#e6c200",
                text_color="black",
                command=self._open_upgrade_url,
            )
            upgrade_btn.grid(row=5, column=0, padx=20, pady=(20, 20))
        
        # Store references for auto-scroll to top
        self.setup_left_scroll = left_frame
        self.setup_right_scroll = right_frame

        # Save button
        ctk.CTkButton(
            self.tab_setup,
            text="💾 Save Setup & Continue to Blueprint →",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            fg_color="#0066cc",
            hover_color="#0052a3",
            command=self._save_setup,
        ).grid(row=1, column=0, columnspan=2, padx=20, pady=20)

    def _browse_logo(self):
        """Open file browser for logo selection."""
        filepath = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")],
        )
        if filepath:
            self.logo_entry.delete(0, "end")
            self.logo_entry.insert(0, filepath)
    
    def _normalize_page_count(self, value):
        """
        Normalize page count to even numbers within valid range.
        
        Args:
            value: The raw page count value
            
        Returns:
            int: Normalized even page count between 10 and 300
        """
        page_count = int(float(value))
        # Clamp to valid range
        page_count = max(10, min(300, page_count))
        # Ensure even number
        if page_count % 2 != 0:
            page_count = min(page_count + 1, 300)
        return page_count
    
    def _update_page_count_display(self, value):
        """Update the page count label when slider moves."""
        page_count = self._normalize_page_count(value)
        self.page_count_label.configure(text=f"{page_count} pages")
    
    def _select_custom_images(self):
        """Open file dialog to select multiple custom images."""
        filepaths = filedialog.askopenfilenames(
            title="Select Custom Images for PDF",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All Files", "*.*")
            ],
        )
        if filepaths:
            self.custom_images = list(filepaths)
            count = len(self.custom_images)
            if count == 1:
                self.selected_images_label.configure(
                    text="1 image selected",
                    text_color="#28a745"
                )
            else:
                self.selected_images_label.configure(
                    text=f"{count} images selected",
                    text_color="#28a745"
                )
        else:
            # User cancelled selection
            pass

    def _open_upgrade_url(self):
        """Show upgrade information message (marketplace-agnostic)."""
        messagebox.showinfo(
            "Upgrade to Extended License",
            "To unlock Extended features, please return to the marketplace where you purchased this software "
            "(Fiverr, Whop, etc.) and purchase the 'Extended License' upgrade.\n\n"
            "Then enter your new key here to activate Extended features."
        )

    def _save_setup(self):
        """Save setup data and move to Blueprint tab."""
        topic = self.topic_entry.get().strip()
        audience = self.audience_entry.get().strip()

        if not topic:
            messagebox.showerror("Error", "Please enter a course topic.")
            return

        if not audience:
            messagebox.showerror("Error", "Please enter a target audience.")
            return

        # Save to project
        self.project.set_topic(topic)
        self.project.set_audience(audience)
        self.project.set_branding(
            logo_path=self.logo_entry.get().strip(),
            website_url=self.website_entry.get().strip(),
        )
        
        # Store new UI settings in project metadata (using helper for consistency)
        page_count = self._normalize_page_count(self.page_count_slider.get())
        
        # Set global target_pages for synchronization with Blueprint
        self.target_pages = page_count
        
        # Add custom properties to project (these can be used by PDF engine)
        if not hasattr(self.project, 'ui_settings'):
            self.project.ui_settings = {}
        
        self.project.ui_settings['target_page_count'] = page_count
        self.project.ui_settings['custom_images'] = self.custom_images
        self.project.ui_settings['text_style'] = self.text_style_var.get()
        self.project.ui_settings['font_size'] = self.font_size_var.get()
        
        self._log_message(f"Setup saved. Target: {page_count} pages, {len(self.custom_images)} custom images.")

        # Switch to Blueprint tab and update page display
        self.tabview.set("📋 Blueprint")
        self._update_blueprint_page_display()
        self._log_message("Ready to generate outline.")

    # ==================== BLUEPRINT TAB ====================
    def _create_blueprint_tab(self):
        """Create the Blueprint tab content with professional curriculum designer UI."""
        # Configure grid: column 0 for main content, column 1 for sidebar
        self.tab_blueprint.grid_columnconfigure(0, weight=1)
        self.tab_blueprint.grid_columnconfigure(1, weight=0)
        self.tab_blueprint.grid_rowconfigure(2, weight=1)

        # === Header Row ===
        header_frame = ctk.CTkFrame(self.tab_blueprint, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")

        ctk.CTkLabel(
            header_frame,
            text="📋 Course Blueprint (Outline)",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="🤖 Generate Outline with AI",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#6c5ce7",
            hover_color="#5b4cdb",
            command=self._generate_outline,
        ).pack(side="right")

        # === Stats Header Row (4 Info Cards) ===
        stats_frame = ctk.CTkFrame(
            self.tab_blueprint,
            fg_color=("gray90", "gray17"),
            border_width=1,
            border_color=("gray70", "gray30"),
            corner_radius=8,
        )
        stats_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(5, 20), sticky="ew")
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Initialize stats labels with default values
        self.stats_pages_label = self._create_stat_card(stats_frame, "📄 Pages", "50", 0)
        self.stats_level_label = self._create_stat_card(stats_frame, "🎓 Level", "Expert", 1)
        self.stats_modules_label = self._create_stat_card(stats_frame, "🧩 Modules", "8", 2)
        self.stats_keywords_label = self._create_stat_card(stats_frame, "🔑 Keywords", "15+", 3)

        # === Main Content Area (Textbox only - manual buttons removed) ===
        content_frame = ctk.CTkFrame(self.tab_blueprint, fg_color="transparent")
        content_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Editable outline textbox (full width)
        textbox_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        textbox_frame.grid(row=0, column=0, sticky="nsew")
        textbox_frame.grid_columnconfigure(0, weight=1)
        textbox_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            textbox_frame,
            text="Edit the chapter titles below (one per line):",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=0, column=0, pady=(0, 5), sticky="nw")

        self.outline_textbox = ctk.CTkTextbox(
            textbox_frame,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
        )
        self.outline_textbox.grid(row=1, column=0, sticky="nsew")
        bind_clipboard_menu(self.outline_textbox)

        # Note: Manual +/X/arrow buttons removed per requirement
        # The outline can be edited directly in the textbox
        # Quiz button removed as well for cleaner UI

        # === Confirm Button Row ===
        ctk.CTkButton(
            self.tab_blueprint,
            text="✅ Confirm Outline & Continue to Drafting →",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            fg_color="#28a745",
            hover_color="#218838",
            command=self._confirm_outline,
        ).grid(row=3, column=0, columnspan=2, padx=20, pady=(20, 20))

    def _create_stat_card(self, parent, icon_label, value, column):
        """
        Create a single stat info card for the Stats Header.
        
        Args:
            parent: The parent frame.
            icon_label: The label text with icon (e.g., "📄 Pages").
            value: The default value to display.
            column: The column position in the grid.
            
        Returns:
            CTkLabel: The value label for updating later.
        """
        card_frame = ctk.CTkFrame(parent, fg_color="transparent")
        card_frame.grid(row=0, column=column, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(
            card_frame,
            text=icon_label,
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(anchor="center")

        value_label = ctk.CTkLabel(
            card_frame,
            text=value,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        value_label.pack(anchor="center")

        return value_label

    def _add_chapter(self):
        """Add a new chapter to the outline."""
        current_text = self.outline_textbox.get("1.0", "end").strip()
        lines = [line.strip() for line in current_text.split("\n") if line.strip()]
        new_chapter_num = len(lines) + 1
        new_chapter = f"{new_chapter_num}. New Chapter Title"
        
        if current_text:
            self.outline_textbox.insert("end", f"\n{new_chapter}")
        else:
            self.outline_textbox.insert("1.0", new_chapter)
        
        self._update_stats_from_outline()

    def _delete_chapter(self):
        """Delete the last chapter from the outline."""
        current_text = self.outline_textbox.get("1.0", "end").strip()
        lines = [line.strip() for line in current_text.split("\n") if line.strip()]
        
        if len(lines) > 0:
            lines.pop()  # Remove last line
            self._update_outline_textbox(lines)
            self._update_stats_from_outline()

    def _strip_chapter_number(self, line):
        """Strip the chapter number prefix from a line."""
        return re.sub(r'^\d+\.\s*', '', line)

    def _update_outline_textbox(self, lines):
        """
        Update the outline textbox with renumbered chapter lines.
        
        Args:
            lines: List of chapter lines (may include old numbering).
        """
        renumbered = [f"{i+1}. {self._strip_chapter_number(line)}" for i, line in enumerate(lines)]
        self.outline_textbox.delete("1.0", "end")
        if renumbered:
            self.outline_textbox.insert("1.0", "\n".join(renumbered))

    def _move_chapter_up(self):
        """Swap the last two chapters in the outline."""
        current_text = self.outline_textbox.get("1.0", "end").strip()
        lines = [line.strip() for line in current_text.split("\n") if line.strip()]
        
        if len(lines) >= 2:
            lines[-1], lines[-2] = lines[-2], lines[-1]
            self._update_outline_textbox(lines)
            self._update_stats_from_outline()

    def _move_chapter_down(self):
        """Swap the first two chapters in the outline."""
        current_text = self.outline_textbox.get("1.0", "end").strip()
        lines = [line.strip() for line in current_text.split("\n") if line.strip()]
        
        if len(lines) >= 2:
            lines[0], lines[1] = lines[1], lines[0]
            self._update_outline_textbox(lines)
            self._update_stats_from_outline()

    def _add_quiz(self):
        """Add a quiz to the course. Extended feature only."""
        if not is_extended():
            # Show upgrade popup for Standard users
            result = messagebox.askquestion(
                "Extended Feature",
                "🔒 Add Quiz is an Extended feature!\n\n"
                "Upgrade to the Extended license to unlock:\n"
                "• Quiz generation for each chapter\n"
                "• Custom branding options\n"
                "• Priority support\n\n"
                "Would you like to see upgrade information?",
                icon="info"
            )
            if result == "yes":
                self._open_upgrade_url()
            return
        
        # Extended user - add quiz placeholder
        current_text = self.outline_textbox.get("1.0", "end").strip()
        if current_text:
            self.outline_textbox.insert("end", "\n\n[QUIZ] Chapter Review Questions")
        else:
            self.outline_textbox.insert("1.0", "[QUIZ] Chapter Review Questions")
        
        self._log_message("Quiz placeholder added. Quizzes will be generated with chapter content.")

    def _update_blueprint_page_display(self):
        """Update the Blueprint page display to show exact value from Setup."""
        # Display exact page count from Setup instead of estimate
        self.stats_pages_label.configure(text=str(self.target_pages))
    
    def _update_stats_from_outline(self):
        """Update stats header based on the current outline content."""
        current_text = self.outline_textbox.get("1.0", "end").strip()
        lines = [line.strip() for line in current_text.split("\n") if line.strip()]
        num_chapters = len(lines)
        
        # Update Modules count
        self.stats_modules_label.configure(text=str(num_chapters) if num_chapters > 0 else "0")
        
        # Update Pages to show exact target from Setup (synchronized)
        self.stats_pages_label.configure(text=str(self.target_pages))
        
        # Update level based on chapters
        if num_chapters <= 3:
            level = "Beginner"
        elif num_chapters <= 6:
            level = "Intermediate"
        else:
            level = "Expert"
        self.stats_level_label.configure(text=level)
        
        # Keywords estimate (3 per chapter minimum)
        keywords = max(num_chapters * 3, 5) if num_chapters > 0 else "0"
        self.stats_keywords_label.configure(text=f"{keywords}+")

    def _generate_outline(self):
        """Generate course outline using AI."""
        if not self.project.topic:
            messagebox.showerror("Error", "Please complete the Setup tab first.")
            self.tabview.set("📝 Setup")
            return

        if self.is_generating:
            messagebox.showwarning("In Progress", "Please wait for the current operation to complete.")
            return

        self.is_generating = True
        self._log_message("Generating course outline...")

        def on_success(chapters):
            self.after(0, lambda: self._on_outline_generated(chapters))

        def on_error(error):
            self.after(0, lambda: self._on_generation_error(error))

        worker = OutlineGenerator(
            self.project.topic,
            self.project.audience,
            callback=on_success,
            error_callback=on_error,
        )
        worker.start()

    def _on_outline_generated(self, chapters):
        """Handle successful outline generation."""
        self.is_generating = False
        
        # Format chapters with numbers
        outline_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(chapters)])
        
        # Update textbox
        self.outline_textbox.delete("1.0", "end")
        self.outline_textbox.insert("1.0", outline_text)
        
        # Update stats header based on the generated outline
        self._update_stats_from_outline()
        
        self._log_message(f"✓ Generated {len(chapters)} chapter titles. You can edit them now.")

    def _confirm_outline(self):
        """Confirm the edited outline and move to Drafting tab."""
        outline_text = self.outline_textbox.get("1.0", "end").strip()

        if not outline_text:
            messagebox.showerror("Error", "Please generate or enter an outline first.")
            return

        # Parse the outline
        chapters = self.project.parse_outline_text(outline_text)

        if len(chapters) < 1:
            messagebox.showerror("Error", "Please enter at least one chapter title.")
            return

        # Save to project
        self.project.set_outline(chapters)
        
        self._log_message(f"Outline confirmed with {len(chapters)} chapters.")
        self.tabview.set("✍️ Drafting")

    # ==================== DRAFTING TAB ====================
    def _create_drafting_tab(self):
        """Create the Drafting tab content with split view (console + live preview)."""
        # Configure grid for split view with proper weights for responsiveness
        self.tab_drafting.grid_columnconfigure(0, weight=1)  # Left: Console - expands
        self.tab_drafting.grid_columnconfigure(1, weight=1)  # Right: Preview - expands
        self.tab_drafting.grid_rowconfigure(0, weight=0)  # Header - fixed
        self.tab_drafting.grid_rowconfigure(1, weight=1)  # Main content - expands to fill space
        self.tab_drafting.grid_rowconfigure(2, weight=0)  # Progress bar - fixed
        self.tab_drafting.grid_rowconfigure(3, weight=0)  # Continue button - fixed

        # Header with button (spans both columns)
        header_frame = ctk.CTkFrame(self.tab_drafting, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")

        ctk.CTkLabel(
            header_frame,
            text="✍️ Chapter Drafting",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        self.draft_btn = ctk.CTkButton(
            header_frame,
            text="🚀 Start Writing Chapters",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#e17055",
            hover_color="#d35400",
            command=self._start_drafting,
        )
        self.draft_btn.pack(side="right")

        # ========== LEFT SIDE: Progress Console ==========
        left_frame = ctk.CTkFrame(self.tab_drafting)
        left_frame.grid(row=1, column=0, padx=(20, 10), pady=(0, 10), sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=0)  # Label - fixed
        left_frame.grid_rowconfigure(1, weight=1)  # Textbox - expands

        ctk.CTkLabel(
            left_frame,
            text="📋 Progress Console",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        # Progress log - expands to fill available space
        self.drafting_log = ctk.CTkTextbox(
            left_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            state="disabled",
        )
        self.drafting_log.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="nsew")
        bind_clipboard_menu(self.drafting_log)

        # ========== RIGHT SIDE: Live Page Preview ==========
        right_frame = ctk.CTkFrame(self.tab_drafting)
        right_frame.grid(row=1, column=1, padx=(10, 20), pady=(0, 10), sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=0)  # Label - fixed
        right_frame.grid_rowconfigure(1, weight=1)  # Preview - expands

        ctk.CTkLabel(
            right_frame,
            text="📄 Live Page Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        # White "paper" frame for document preview (scrollable) - expands to fill
        self.preview_scroll = ctk.CTkScrollableFrame(
            right_frame,
            fg_color="white",
            corner_radius=5,
        )
        self.preview_scroll.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="nsew")
        self.preview_scroll.grid_columnconfigure(0, weight=1)

        # Chapter title label (appears above content during generation)
        self.preview_chapter_title = ctk.CTkLabel(
            self.preview_scroll,
            text="",
            font=ctk.CTkFont(family="Times New Roman", size=18, weight="bold"),
            text_color="black",
            justify="left",
            anchor="w",
            wraplength=400,
        )
        self.preview_chapter_title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nw")

        # Content label for live streaming text (like a typewriter)
        self.preview_content_label = ctk.CTkLabel(
            self.preview_scroll,
            text="Content will appear here as it's being written...",
            font=ctk.CTkFont(family="Times New Roman", size=16),
            text_color="#333333",
            justify="left",
            anchor="nw",
            wraplength=400,
        )
        self.preview_content_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nw")

        # ========== BOTTOM: Progress Bar (spans both columns) ==========
        progress_frame = ctk.CTkFrame(self.tab_drafting)
        progress_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self.drafting_progress_label = ctk.CTkLabel(
            progress_frame, text="Ready to draft", font=ctk.CTkFont(size=13)
        )
        self.drafting_progress_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        self.drafting_progress = ctk.CTkProgressBar(progress_frame, height=15)
        self.drafting_progress.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.drafting_progress.set(0)

        # Continue button (spans both columns)
        self.continue_export_btn = ctk.CTkButton(
            self.tab_drafting,
            text="Continue to Export →",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            fg_color="#0066cc",
            hover_color="#0052a3",
            state="disabled",
            command=lambda: self.tabview.set("📤 Export"),
        )
        self.continue_export_btn.grid(row=3, column=0, columnspan=2, padx=20, pady=(10, 15))

        # Track current preview content for accumulation using list for O(1) append
        # Performance optimization: Using list instead of string concatenation
        # to avoid O(n²) complexity when accumulating streaming text
        self._preview_accumulated_chunks = []
        self._preview_update_counter = 0

    def _log_drafting(self, message):
        """Add message to drafting log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"

        self.drafting_log.configure(state="normal")
        self.drafting_log.insert("end", formatted_msg)
        self.drafting_log.see("end")
        self.drafting_log.configure(state="disabled")

    def update_live_preview(self, text_chunk):
        """
        Update the live preview with a new text chunk (typewriter effect).
        Called from the AI worker streaming callback.
        
        Performance optimization: Uses list accumulation with periodic UI updates
        to avoid O(n²) string concatenation and reduce UI update overhead.
        Only joins chunks since last update for O(k) work instead of O(n).
        
        Args:
            text_chunk: The incremental text chunk to append.
        """
        self._preview_accumulated_chunks.append(text_chunk)
        self._preview_update_counter += 1
        
        # Update UI every PREVIEW_UPDATE_INTERVAL chunks to balance responsiveness with performance
        # Force immediate update for large chunks (likely meaningful content boundaries)
        if self._preview_update_counter % PREVIEW_UPDATE_INTERVAL == 0 or len(text_chunk) > LARGE_CHUNK_THRESHOLD:
            # Join all chunks - this is O(n) but only happens every N chunks
            # For streaming text, n is bounded by chapter size which is reasonable
            full_text = ''.join(self._preview_accumulated_chunks)
            self.preview_content_label.configure(text=full_text)
            # Force update to show the change immediately
            self.preview_content_label.update_idletasks()
            # Scroll to bottom of preview using safe method
            try:
                # Try to scroll to bottom - CTkScrollableFrame may have internal canvas
                if hasattr(self.preview_scroll, '_parent_canvas'):
                    self.preview_scroll._parent_canvas.yview_moveto(1.0)
            except (AttributeError, Exception):
                pass  # Scrolling is optional; content update is the priority

    def _clear_live_preview(self):
        """Clear the live preview content for a new chapter."""
        self._preview_accumulated_chunks = []
        self._preview_update_counter = 0
        self.preview_content_label.configure(text="")

    def _set_preview_chapter_title(self, title, chapter_num):
        """Set the chapter title in the preview area."""
        self.preview_chapter_title.configure(text=f"Chapter {chapter_num}: {title}")

    def _start_drafting(self):
        """Start the chapter drafting process."""
        if not self.project.outline:
            self._log_drafting("❌ Cannot start: No outline confirmed")
            messagebox.showerror("Error", "Please confirm an outline in the Blueprint tab first.")
            self.tabview.set("📋 Blueprint")
            return

        if self.is_generating:
            self._log_drafting("⚠️ Already generating - please wait")
            messagebox.showwarning("In Progress", "Please wait for the current operation to complete.")
            return

        self.is_generating = True
        self.draft_btn.configure(state="disabled", text="⏳ Writing...")
        self.project.chapters_content = {}  # Reset content
        self.current_chapter_index = 0
        self.total_chapters = len(self.project.outline)

        # Clear preview for fresh start
        self._clear_live_preview()
        self.preview_chapter_title.configure(text="")

        # Log start action
        self._log_drafting("🚀 Starting chapter generation...")
        self._log_drafting(f"📚 Topic: {self.project.topic}")
        self._log_drafting(f"📋 Total chapters: {self.total_chapters}")
        self._write_next_chapter()

    def _write_next_chapter(self):
        """Write the next chapter in the queue."""
        if self.current_chapter_index >= self.total_chapters:
            # All chapters done
            self.is_generating = False
            self.draft_btn.configure(state="normal", text="🚀 Start Writing Chapters")
            self.continue_export_btn.configure(state="normal")
            self._log_drafting("=" * 40)
            self._log_drafting("✅ All chapters written successfully!")
            self._log_drafting(f"📄 Ready for export")
            self.drafting_progress.set(1.0)
            self.drafting_progress_label.configure(text="Complete!")
            return

        chapter_title = self.project.outline[self.current_chapter_index]
        chapter_num = self.current_chapter_index + 1

        progress = self.current_chapter_index / self.total_chapters
        self.drafting_progress.set(progress)
        self.drafting_progress_label.configure(
            text=f"Writing chapter {chapter_num}/{self.total_chapters}..."
        )

        # Clear preview and set new chapter title
        self._clear_live_preview()
        self._set_preview_chapter_title(chapter_title, chapter_num)

        self._log_drafting(f"✍️ Writing Chapter {chapter_num}: {chapter_title}...")

        def on_success(title, content):
            self.after(0, lambda: self._on_chapter_written(title, content))

        def on_error(error):
            self.after(0, lambda: self._on_drafting_error(error))

        def on_stream(text_chunk):
            # Schedule UI update on main thread for streaming text
            # Capture text_chunk by value to avoid race conditions
            self.after(0, lambda chunk=text_chunk: self.update_live_preview(chunk))

        worker = ChapterWriter(
            self.project.topic,
            chapter_title,
            chapter_num,
            callback=on_success,
            error_callback=on_error,
            stream_callback=on_stream,
        )
        worker.start()

    def _on_chapter_written(self, title, content):
        """Handle successful chapter writing."""
        self.project.set_chapter_content(title, content)
        
        # Calculate page count for this chapter using ContentDistributor
        from generator import ContentDistributor
        from session_manager import get_tier
        distributor = ContentDistributor(get_tier())
        pages = distributor.distribute_content(content)
        page_count = len(pages)
        
        # Log with page count instead of just character count
        self._log_drafting(f"✓ Chapter '{title}' complete ({page_count} pages, {len(content)} characters)")

        self.current_chapter_index += 1
        self._write_next_chapter()

    def _on_drafting_error(self, error):
        """Handle drafting error."""
        self.is_generating = False
        self.draft_btn.configure(state="normal", text="🚀 Start Writing Chapters")
        self._log_drafting(f"❌ Error: {error}")
        messagebox.showerror("Error", f"Failed to write chapter:\n\n{error}")

    # ==================== EXPORT TAB ====================
    def _create_export_tab(self):
        """Create the Export tab content."""
        self.tab_export.grid_columnconfigure(0, weight=1)
        self.tab_export.grid_columnconfigure(1, weight=1)
        self.tab_export.grid_rowconfigure(0, weight=1)

        # Left - Cover generation (Scrollable)
        cover_frame = ctk.CTkScrollableFrame(self.tab_export, corner_radius=10)
        cover_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(
            cover_frame,
            text="🎨 Cover Image",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 20), sticky="w")

        self.cover_status = ctk.CTkLabel(
            cover_frame,
            text="No cover generated yet",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.cover_status.grid(row=1, column=0, padx=20, pady=(0, 20))

        self.generate_cover_btn = ctk.CTkButton(
            cover_frame,
            text="🖼️ Generate Cover with DALL-E",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            width=280,
            fg_color="#6c5ce7",
            hover_color="#5b4cdb",
            command=self._generate_cover,
        )
        self.generate_cover_btn.grid(row=2, column=0, padx=20, pady=(0, 20))

        # Right - Document export (Scrollable) - supports PDF, DOCX, and HTML formats
        export_frame = ctk.CTkScrollableFrame(self.tab_export, corner_radius=10)
        export_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Section header for document export
        ctk.CTkLabel(
            export_frame,
            text="📄 Document Export",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 20), sticky="w")

        # Format selector label for format buttons
        ctk.CTkLabel(
            export_frame,
            text="Select Output Format:",
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")
        
        # Format buttons frame - replaces dropdown with visual buttons
        self.format_buttons_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        self.format_buttons_frame.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="w")
        
        # Store format buttons for selection state management
        self.format_buttons = {}
        self.export_format_var = ctk.StringVar(value=self.DEFAULT_EXPORT_FORMAT)
        
        # Create format buttons with visual feedback using class constants
        for idx, (format_name, config) in enumerate(self.FORMAT_CONFIG.items()):
            icon = self.FORMAT_ICONS.get(format_name, "📄")
            is_default = format_name == self.DEFAULT_EXPORT_FORMAT
            colors = self.FORMAT_BTN_SELECTED if is_default else self.FORMAT_BTN_UNSELECTED
            
            btn = ctk.CTkButton(
                self.format_buttons_frame,
                text=f"{icon} {format_name}",
                font=ctk.CTkFont(size=13, weight="bold" if is_default else "normal"),
                width=100,
                height=40,
                corner_radius=8,
                fg_color=colors["fg"],
                hover_color=colors["hover"],
                border_width=2,
                border_color=colors["border"],
                command=lambda f=format_name: self._select_format(f),
            )
            btn.grid(row=0, column=idx, padx=(0, 10), pady=5)
            self.format_buttons[format_name] = btn

        # Status label showing current export readiness
        self.export_status = ctk.CTkLabel(
            export_frame,
            text="Ready to generate document",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.export_status.grid(row=3, column=0, padx=20, pady=(0, 20))

        # Main export button - generates output in the selected format
        # Initialize button text based on default export format for consistency
        default_icon = self._get_format_icon(self.DEFAULT_EXPORT_FORMAT)
        self.build_export_btn = ctk.CTkButton(
            export_frame,
            text=f"{default_icon} GENERATE FINAL {self.DEFAULT_EXPORT_FORMAT}",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=55,
            width=300,
            corner_radius=12,
            fg_color=("#28a745", "#20873a"),
            hover_color=("#218838", "#1a6d2e"),
            border_width=2,
            border_color=("#20873a", "#28a745"),
            command=self._build_export,
        )
        self.build_export_btn.grid(row=4, column=0, padx=20, pady=(0, 20))
        
        # Progress label for export status animation
        self.export_progress_label = ctk.CTkLabel(
            export_frame,
            text="",
            font=ctk.CTkFont(size=12),
        )
        self.export_progress_label.grid(row=5, column=0, padx=20, pady=(20, 5))
        
        # Progress bar for export progress indication
        self.export_progress_bar = ctk.CTkProgressBar(export_frame, width=260)
        self.export_progress_bar.grid(row=6, column=0, padx=20, pady=(0, 20))
        self.export_progress_bar.set(0)
        
        # Backward compatibility: alias old names for existing code
        self.pdf_status = self.export_status
        self.pdf_progress_label = self.export_progress_label
        self.pdf_progress_bar = self.export_progress_bar
        self.build_pdf_btn = self.build_export_btn
        
        # Store references for auto-scroll to top
        self.export_cover_scroll = cover_frame
        self.export_pdf_scroll = export_frame

        # Bottom - Export log
        self.export_log = ctk.CTkTextbox(
            self.tab_export,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            state="disabled",
            height=200,
        )
        self.export_log.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        bind_clipboard_menu(self.export_log)

    def _log_export(self, message):
        """Add message to export log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"

        self.export_log.configure(state="normal")
        self.export_log.insert("end", formatted_msg)
        self.export_log.see("end")
        self.export_log.configure(state="disabled")

    def _generate_cover(self):
        """Generate cover image using DALL-E."""
        if not self.project.topic:
            messagebox.showerror("Error", "Please complete the Setup tab first.")
            return

        if self.is_generating:
            messagebox.showwarning("In Progress", "Please wait for the current operation to complete.")
            return

        self.is_generating = True
        self.generate_cover_btn.configure(state="disabled", text="⏳ Generating...")
        self.cover_status.configure(text="Generating cover image...")
        self._log_export("Generating cover image with DALL-E 3...")

        def on_success(image_path):
            self.after(0, lambda: self._on_cover_generated(image_path))

        def on_error(error):
            self.after(0, lambda: self._on_cover_error(error))

        worker = CoverGenerator(
            self.project.topic,
            callback=on_success,
            error_callback=on_error,
        )
        worker.start()

    def _on_cover_generated(self, image_path):
        """Handle successful cover generation."""
        self.is_generating = False
        self.generate_cover_btn.configure(state="normal", text="🖼️ Generate Cover with DALL-E")
        self.project.set_cover_image(image_path)
        self.cover_status.configure(text="✓ Cover image ready!", text_color="#28a745")
        self._log_export(f"✓ Cover image generated: {image_path}")

    def _on_cover_error(self, error):
        """Handle cover generation error."""
        self.is_generating = False
        self.generate_cover_btn.configure(state="normal", text="🖼️ Generate Cover with DALL-E")
        self.cover_status.configure(text="❌ Generation failed", text_color="#e74c3c")
        self._log_export(f"❌ Error: {error}")
        messagebox.showerror("Error", f"Failed to generate cover:\n\n{error}")

    def _select_format(self, selected_format):
        """
        Handle format button click - select export format with visual feedback.
        Updates button states and triggers format change event.
        
        Args:
            selected_format: The format to select (PDF, DOCX, or HTML).
        """
        # Update internal format variable
        self.export_format_var.set(selected_format)
        
        # Update button visual states - highlight selected, dim others
        for format_name, btn in self.format_buttons.items():
            is_selected = format_name == selected_format
            icon = self.FORMAT_ICONS.get(format_name, "📄")
            colors = self.FORMAT_BTN_SELECTED if is_selected else self.FORMAT_BTN_UNSELECTED
            
            btn.configure(
                fg_color=colors["fg"],
                hover_color=colors["hover"],
                border_color=colors["border"],
                font=ctk.CTkFont(size=13, weight="bold" if is_selected else "normal"),
                text=f"{icon} {format_name}",
            )
        
        # Trigger format change handler for consistency
        self._on_format_changed(selected_format)
        
        # Log user action for format selection
        self._log_export(f"📋 User selected format: {selected_format}")

    def _on_format_changed(self, selected_format):
        """
        Handle format selector change event.
        Updates the export button text and status to reflect the selected format.
        
        Args:
            selected_format: The newly selected format (PDF, DOCX, or HTML).
        """
        # Update button text based on selected format using helper method
        icon = self._get_format_icon(selected_format)
        self.build_export_btn.configure(text=f"{icon} GENERATE FINAL {selected_format}")
        
        # Update status message with visual feedback
        self.export_status.configure(
            text=f"✓ Ready to generate {selected_format} document",
            text_color="#28a745"
        )

    def _build_export(self):
        """
        Build the final document in the selected format (PDF, DOCX, or HTML).
        This method handles multi-format export for commercial-ready output.
        """
        # Validate project completeness
        if not self.project.is_complete():
            missing = []
            if not self.project.topic:
                missing.append("Topic (Setup tab)")
            if not self.project.outline:
                missing.append("Outline (Blueprint tab)")
            if len(self.project.chapters_content) < len(self.project.outline):
                missing.append("Chapter content (Drafting tab)")
            
            # Log validation error
            self._log_export("❌ Export validation failed - incomplete project")
            for m in missing:
                self._log_export(f"   Missing: {m}")
            
            messagebox.showerror(
                "Incomplete Project",
                f"Please complete the following before exporting:\n\n" + "\n".join(f"• {m}" for m in missing),
            )
            return

        # Get selected export format
        selected_format = self.export_format_var.get()
        
        # Log user action
        self._log_export(f"🚀 Starting {selected_format} export...")
        
        # Get file extension and filter from class-level constant
        config = self.FORMAT_CONFIG.get(selected_format, self.FORMAT_CONFIG[self.DEFAULT_EXPORT_FORMAT])
        
        # Generate safe filename from topic
        safe_topic = "".join(c if c.isalnum() or c == " " else "_" for c in self.project.topic)
        safe_topic = safe_topic.replace(" ", "_")[:30]
        default_name = f"CourseSmith_{safe_topic}{config['ext']}"

        # Ask user for save location
        filepath = filedialog.asksaveasfilename(
            title=f"Save {selected_format} As",
            defaultextension=config['ext'],
            initialfile=default_name,
            filetypes=config['filter'],
        )

        if not filepath:
            self._log_export("⚠️ Export cancelled by user")
            return

        # Update UI to show export in progress
        self._log_export(f"📁 Output file: {os.path.basename(filepath)}")
        self._log_export(f"⏳ Building {selected_format} document...")
        self.export_status.configure(text=f"Building {selected_format}...")
        self.export_progress_label.configure(text="Initializing...")
        self.export_progress_bar.set(0.1)
        self.build_export_btn.configure(state="disabled", text="⏳ BUILDING...")
        
        # Start progress animation
        self._start_status_animation(self.export_progress_label, f"Generating {selected_format}")

        def build():
            """Background thread function to build the document."""
            try:
                # Get current license tier for tier-specific features
                current_tier = get_tier()
                
                if selected_format == "PDF":
                    # Use existing PDF builder for PDF format
                    result = self._build_pdf_internal(filepath, current_tier)
                elif selected_format == "DOCX":
                    # Use DOCX exporter for Microsoft Word format
                    result = self._build_docx_internal(filepath)
                elif selected_format == "HTML":
                    # Use HTML exporter for web format
                    result = self._build_html_internal(filepath)
                else:
                    raise ValueError(f"Unsupported format: {selected_format}")
                
                self.after(0, lambda: self.export_progress_bar.set(1.0))
                self.after(0, lambda: self._on_export_complete(result, selected_format))
            except Exception as e:
                self.after(0, lambda: self._on_export_error(str(e), selected_format))

        # Run export in background thread for smooth UI
        thread = threading.Thread(target=build, daemon=True)
        thread.start()

    def _build_pdf_internal(self, filepath, current_tier):
        """
        Internal method to build PDF document.
        
        Args:
            filepath: Output file path for the PDF.
            current_tier: License tier for feature access.
            
        Returns:
            str: Path to the generated PDF file.
        """
        # Calculate estimated page count for progress
        total_pages = self.target_pages
        
        # Update progress at intervals
        for i in range(1, min(10, total_pages + 1)):
            def update_progress(p):
                progress = p / total_pages if total_pages > 0 else 0.5
                self.after(0, lambda: self.export_progress_bar.set(min(0.9, progress)))
            self.after(i * 100, lambda p=i: update_progress(p))
        
        # Create PDF builder with tier parameter
        builder = PDFBuilder(filepath, tier=current_tier)
        
        # Get custom images from project UI settings
        custom_images = []
        if hasattr(self.project, 'ui_settings') and self.project.ui_settings:
            custom_images = self.project.ui_settings.get('custom_images', [])
        
        # Convert to absolute paths for safety
        custom_images = [os.path.abspath(img) for img in custom_images if img]
        
        # Build the PDF
        result = builder.build_pdf(self.project, tier=current_tier, custom_images=custom_images)
        
        # Calculate actual pages for logging
        from generator import ContentDistributor
        distributor = ContentDistributor(current_tier)
        total_pages_created = 0
        if self.project.chapters_content:
            for chapter_content in self.project.chapters_content.values():
                pages = distributor.distribute_content(chapter_content)
                total_pages_created += len(pages)
        
        self._log_export(f"[SUCCESS] Course generated: {total_pages_created} pages completed")
        return result

    def _build_docx_internal(self, filepath):
        """
        Internal method to build DOCX document using DOCXExporter.
        
        Args:
            filepath: Output file path for the DOCX.
            
        Returns:
            str: Path to the generated DOCX file.
        """
        # Create DOCX exporter with the project and output path
        exporter = DOCXExporter(self.project, filepath)
        
        # Update progress during export
        self.after(0, lambda: self.export_progress_bar.set(0.5))
        
        # Export to DOCX format
        result = exporter.export()
        
        self._log_export(f"[SUCCESS] DOCX document exported successfully")
        return result

    def _build_html_internal(self, filepath):
        """
        Internal method to build HTML document using HTMLExporter.
        
        Args:
            filepath: Output file path for the HTML.
            
        Returns:
            str: Path to the generated HTML file.
        """
        # Create HTML exporter with the project and output path
        exporter = HTMLExporter(self.project, filepath)
        
        # Update progress during export
        self.after(0, lambda: self.export_progress_bar.set(0.5))
        
        # Export to HTML format
        result = exporter.export()
        
        self._log_export(f"[SUCCESS] HTML document exported successfully")
        return result

    def _on_export_complete(self, filepath, format_name):
        """
        Handle successful document export completion.
        
        Args:
            filepath: Path to the generated document.
            format_name: The format that was exported (PDF, DOCX, HTML).
        """
        # Stop progress animation
        self._stop_status_animation()
        
        # Update progress indicators
        self.export_progress_bar.set(1.0)
        self.export_progress_label.configure(text="✓ Complete!")
        
        # Restore button state with selected format using helper method
        icon = self._get_format_icon(format_name)
        self.build_export_btn.configure(state="normal", text=f"{icon} GENERATE FINAL {format_name}")
        
        # Update status
        self.export_status.configure(text=f"✓ {format_name} exported!", text_color="#28a745")
        self._log_export(f"✓ {format_name} saved: {filepath}")
        
        # Store output path on project (kept as output_pdf_path for backward compatibility)
        self.project.output_pdf_path = filepath

        # Show success message
        messagebox.showinfo(
            "Success",
            f"{format_name} generated successfully!\n\nFile saved as:\n{filepath}",
        )

    def _on_export_error(self, error, format_name):
        """
        Handle document export error.
        
        Args:
            error: Error message describing what went wrong.
            format_name: The format that failed to export.
        """
        # Stop progress animation
        self._stop_status_animation()
        
        # Reset progress indicators
        self.export_progress_bar.set(0)
        self.export_progress_label.configure(text="❌ Failed")
        
        # Restore button state using helper method
        icon = self._get_format_icon(format_name)
        self.build_export_btn.configure(state="normal", text=f"{icon} GENERATE FINAL {format_name}")
        
        # Update status
        self.export_status.configure(text="❌ Export failed", text_color="#e74c3c")
        self._log_export(f"❌ Error: {error}")
        
        # Show error message
        messagebox.showerror("Error", f"Failed to export {format_name}:\n\n{error}")

    def _build_pdf(self):
        """
        Build the final PDF document.
        This method provides backward compatibility by delegating to _build_export
        with PDF format selected. Ensures existing code continues to work.
        """
        # Set format to PDF for backward compatibility using class constant
        self.export_format_var.set(self.DEFAULT_EXPORT_FORMAT)
        self._on_format_changed(self.DEFAULT_EXPORT_FORMAT)
        # Delegate to the unified export method
        self._build_export()

    def _on_pdf_built(self, filepath, total_pages_created=None):
        """Handle successful PDF build.
        
        Args:
            filepath: The path to the generated PDF
            total_pages_created: Optional total number of pages created
        """
        # Stop animation
        self._stop_status_animation()
        
        self.pdf_progress_bar.set(1.0)
        
        # Show page count in completion message if available
        if total_pages_created:
            self.pdf_progress_label.configure(text=f"✓ Complete! ({total_pages_created} pages)")
        else:
            self.pdf_progress_label.configure(text="✓ Complete!")
        
        self.build_pdf_btn.configure(state="normal", text="📑 GENERATE FINAL PDF")
        self.pdf_status.configure(text="✓ PDF exported!", text_color="#28a745")
        self._log_export(f"✓ PDF saved: {filepath}")
        self.project.output_pdf_path = filepath

        messagebox.showinfo(
            "Success",
            f"PDF generated successfully!\n\nFile saved as:\n{filepath}",
        )

    def _on_pdf_error(self, error):
        """Handle PDF build error."""
        # Stop animation
        self._stop_status_animation()
        
        self.pdf_progress_bar.set(0)
        self.pdf_progress_label.configure(text="❌ Failed")
        self.build_pdf_btn.configure(state="normal", text="📑 GENERATE FINAL PDF")
        self.pdf_status.configure(text="❌ Build failed", text_color="#e74c3c")
        self._log_export(f"❌ Error: {error}")
        messagebox.showerror("Error", f"Failed to build PDF:\n\n{error}")

    def _start_status_animation(self, label_widget, base_text):
        """
        Start a pulsing animation on a status label.
        
        Args:
            label_widget: The CTkLabel widget to animate
            base_text: The base text to display with animation
        """
        self._animation_running = True
        self._animation_step = 0
        self._animate_status(label_widget, base_text)
    
    def _stop_status_animation(self):
        """Stop the status animation."""
        self._animation_running = False
    
    def _animate_status(self, label_widget, base_text):
        """
        Recursively animate a status label with pulsing dots.
        
        Args:
            label_widget: The CTkLabel widget to animate
            base_text: The base text to display
        """
        if not self._animation_running:
            return
        
        # Create pulsing effect with dots
        dots = ["", ".", "..", "..."]
        current_dots = dots[self._animation_step % len(dots)]
        label_widget.configure(text=f"{base_text}{current_dots}")
        
        self._animation_step += 1
        
        # Schedule next animation frame (500ms for smooth pulsing)
        self.after(500, lambda: self._animate_status(label_widget, base_text))

    # ==================== SHARED UTILITIES ====================
    def _log_message(self, message):
        """Log message to appropriate log based on current tab."""
        # For now just print - could be expanded
        print(f"[LOG] {message}")

    def _on_generation_error(self, error):
        """Handle general generation errors."""
        self.is_generating = False
        messagebox.showerror("Error", f"An error occurred:\n\n{error}")

    # ==================== GLOBAL KEYBOARD SHORTCUTS ====================
    def _bind_global_shortcuts(self):
        """Bind global keyboard shortcuts for clipboard operations to the root window."""
        # NUCLEAR FIX: Unbind default class-level paste events to prevent double paste
        # This prevents the OS/Tkinter from handling paste separately from our custom handler
        self.unbind_class("Entry", "<<Paste>>")
        self.unbind_class("Text", "<<Paste>>")
        
        # Bind Ctrl+A for Select All (both uppercase and lowercase)
        self.bind_all("<Control-a>", self._on_select_all)
        self.bind_all("<Control-A>", self._on_select_all)
        
        # Bind Ctrl+C for Copy (both uppercase and lowercase)
        self.bind_all("<Control-c>", self._on_copy)
        self.bind_all("<Control-C>", self._on_copy)
        
        # Bind Ctrl+V for Paste (both uppercase and lowercase)
        self.bind_all("<Control-v>", self._on_paste)
        self.bind_all("<Control-V>", self._on_paste)
        
        # Bind Ctrl+X for Cut (both uppercase and lowercase)
        self.bind_all("<Control-x>", self._on_cut)
        self.bind_all("<Control-X>", self._on_cut)

    def _get_focused_tk_widget(self):
        """
        Get the currently focused widget and its underlying tkinter widget.
        
        Returns:
            tuple: (focused_widget, tk_widget) or (None, None) if no widget is focused.
        """
        focused = self.focus_get()
        if focused is None:
            return None, None
        
        # Get the underlying tkinter widget for CustomTkinter widgets
        tk_widget = focused
        if hasattr(focused, '_entry'):
            # CTkEntry has underlying _entry widget
            tk_widget = focused._entry
        elif hasattr(focused, '_textbox'):
            # CTkTextbox has underlying _textbox widget
            tk_widget = focused._textbox
        
        return focused, tk_widget

    def _on_select_all(self, event=None):
        """Handle Ctrl+A (Select All) globally."""
        focused, tk_widget = self._get_focused_tk_widget()
        if tk_widget is None:
            return "break"
        
        try:
            # Check widget type and select all text accordingly
            if hasattr(tk_widget, 'tag_add'):
                # Text-based widget (CTkTextbox or tk.Text)
                # Use 'end-1c' to exclude the trailing newline character
                tk_widget.tag_add("sel", "1.0", "end-1c")
            elif hasattr(tk_widget, 'select_range'):
                # Entry-based widget (CTkEntry or tk.Entry)
                tk_widget.select_range(0, "end")
                # Move cursor to end after selection
                tk_widget.icursor("end")
        except Exception:
            pass
        
        return "break"

    def _get_selected_text(self, tk_widget):
        """
        Get selected text from a widget.
        
        Args:
            tk_widget: The underlying tkinter widget (Entry or Text).
            
        Returns:
            tuple: (selected_text, is_text_widget) or (None, None) if no selection.
        """
        if hasattr(tk_widget, 'tag_ranges'):
            # Text-based widget (CTkTextbox or tk.Text)
            sel_ranges = tk_widget.tag_ranges("sel")
            if sel_ranges:
                return tk_widget.get("sel.first", "sel.last"), True
            return None, None
        elif hasattr(tk_widget, 'selection_present') and tk_widget.selection_present():
            # Entry-based widget (CTkEntry or tk.Entry)
            return tk_widget.selection_get(), False
        return None, None

    def _on_copy(self, event=None):
        """Handle Ctrl+C (Copy) globally."""
        focused, tk_widget = self._get_focused_tk_widget()
        if tk_widget is None:
            return "break"
        
        try:
            selected_text, _ = self._get_selected_text(tk_widget)
            if selected_text is None:
                return "break"  # No selection
            
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(selected_text)
        except Exception:
            pass
        
        return "break"

    def _on_paste(self, event=None):
        """
        Handle Ctrl+V (Paste) globally.
        This method provides reliable paste functionality for all input fields.
        It manually deletes selected text and inserts clipboard content to avoid
        double-paste issues common with CustomTkinter widgets.
        
        Returns:
            str: "break" to prevent default event propagation.
        """
        focused, tk_widget = self._get_focused_tk_widget()
        if tk_widget is None:
            return "break"
        
        try:
            # Check if widget is in normal state (can accept input)
            widget_state = str(tk_widget.cget("state")) if hasattr(tk_widget, "cget") else "normal"
            if widget_state == "disabled" or widget_state == "readonly":
                return "break"
            
            # Get clipboard content - handle various clipboard formats
            text = None
            try:
                text = tk_widget.clipboard_get()
            except TclError:
                # TclError: clipboard unavailable from widget, try root window fallback
                try:
                    text = self.clipboard_get()
                except TclError:
                    # TclError: clipboard still unavailable
                    return "break"
        except TclError:
            # TclError: widget state check failed
            return "break"
        except AttributeError:
            # AttributeError: widget doesn't have expected methods
            return "break"
        
        # Validate that we have text content to paste
        if not text:
            return "break"
        
        # Note: We manually delete selected text and insert instead of using
        # event_generate("<<Paste>>") to avoid double-paste issues with CustomTkinter.
        # Delete selected text first (if any)
        try:
            tk_widget.delete("sel.first", "sel.last")
        except TclError:
            # TclError: no selection exists, which is expected
            pass
        
        # Insert text at current cursor position
        try:
            tk_widget.insert("insert", text)
        except TclError:
            # TclError: insert failed on tk_widget, try with focused widget directly
            try:
                if hasattr(focused, 'insert'):
                    focused.insert("insert", text)
            except TclError:
                # TclError: both insert attempts failed
                pass
        
        return "break"

    def _on_cut(self, event=None):
        """Handle Ctrl+X (Cut) globally."""
        focused, tk_widget = self._get_focused_tk_widget()
        if tk_widget is None:
            return "break"
        
        try:
            # Check if widget is in normal state (can accept input)
            widget_state = str(tk_widget.cget("state")) if hasattr(tk_widget, "cget") else "normal"
            if widget_state == "disabled" or widget_state == "readonly":
                return "break"
            
            selected_text, is_text_widget = self._get_selected_text(tk_widget)
            if selected_text is None:
                return "break"  # No selection
            
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(selected_text)
            
            # Delete selected text (different methods for text vs entry widgets)
            if is_text_widget:
                tk_widget.delete("sel.first", "sel.last")
            else:
                # Entry widget: delete using selection indices
                tk_widget.delete("sel.first", "sel.last")
        except Exception:
            pass
        
        return "break"


if __name__ == "__main__":
    app = App()
    app.mainloop()
