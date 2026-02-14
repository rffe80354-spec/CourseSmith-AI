#!/usr/bin/env python3
"""
Admin Key Generator - Full License Management Suite for CourseSmith AI Enterprise.
GUI-based version for PyInstaller --noconsole mode compatibility.

This script is for the SELLER only to generate tiered license keys for buyers.

Tiers:
- Standard: Basic features, no custom branding
- Extended: Full features, custom branding support
- Professional: Premium features with priority support

Features:
- Direct access to all features (no God Mode required)
- Powerful Search: Filter licenses by Email, HWID, License Key, or Creation Date
- Supabase Integration: Automatically syncs keys to cloud database
- Global Key Explorer: View ALL licenses from database with real-time search
- Full License Control: Duration (Days), Tier Selection, Device Limits
- Clipboard Support: Full Copy/Paste functionality for all fields
"""

import sys
import os
import re
import threading
from datetime import datetime, timedelta, timezone
import customtkinter as ctk
from tkinter import messagebox
from license_guard import generate_key
from utils import resource_path, add_context_menu, patch_ctk_scrollbar
from dotenv import load_dotenv

# Apply scrollbar patch to prevent RecursionError in CTkScrollableFrame
# This must be called before creating any scrollable widgets
patch_ctk_scrollbar()

# Load environment variables
load_dotenv()

# Import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase not available.")

# Supabase configuration - Use same credentials as main.py
# For security, credentials should be loaded from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Fallback values for development only - DO NOT USE IN PRODUCTION
if not SUPABASE_URL:
    SUPABASE_URL = "https://spfwfyjpexktgnusgyib.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "sb_publishable_tmwenU0VyOChNWKG90X_bw_HYf9X5kR"

# Suppress stdout/stderr for --noconsole mode with log file fallback
if hasattr(sys, 'frozen'):
    # Redirect to log file instead of complete suppression for debugging
    try:
        log_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'CourseSmithAI', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'admin_keygen_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        sys.stdout = open(log_file, 'w', encoding='utf-8')
        sys.stderr = sys.stdout
    except:
        # If log file creation fails, suppress completely
        sys.stdout = None
        sys.stderr = None


# Midnight Forge color scheme (matching main.py)
COLORS = {
    'background': '#0B0E14',
    'sidebar': '#151921',
    'accent': '#7F5AF0',
    'accent_hover': '#9D7BF5',
    'text': '#E0E0E0',
    'text_dim': '#808080'
}

# Duration mapping for days to duration strings
DURATION_MAP = {
    '3': '3_day',
    '30': '1_month',
    '90': '3_month',
    '180': '6_month',
    '365': '1_year',
    'lifetime': 'lifetime'
}

# Lazy loading configuration
LAZY_LOAD_BATCH_SIZE = 50  # Number of license rows to render per batch

# HWID display truncation length
HWID_TRUNCATE_LENGTH = 25


def get_supabase_client():
    """Get Supabase client instance."""
    if not SUPABASE_AVAILABLE or not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to create Supabase client: {e}")
        return None



class AdminKeygenApp(ctk.CTk):
    """Admin Keygen GUI Application with Full License Management."""
    
    def __init__(self):
        """Initialize the admin keygen application."""
        super().__init__()
        
        # Set widget scaling for High-DPI support
        # Default is 1.0. Adjust manually if needed for specific DPI requirements:
        # - Set to 1.25 for 125% scaling
        # - Set to 1.5 for 150% scaling
        # This can be customized based on user preferences or system detection
        ctk.set_widget_scaling(1.0)
        
        # Configure window - larger for Global Key Explorer
        self.title("CourseSmith License Management Suite")
        self.minsize(1280, 720)
        self.resizable(True, True)
        
        # Set appearance
        self.configure(fg_color=COLORS['background'])
        
        # GLOBAL HOTKEY OVERRIDE - Bind keyboard shortcuts at root window level
        # This ensures shortcuts work regardless of widget focus issues
        from utils import setup_global_window_shortcuts
        setup_global_window_shortcuts(self)
        
        # Set icon if available
        try:
            icon_path = resource_path("resources/admin_keygen.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
        
        # State
        self.last_license_key = None
        self.all_licenses = []  # Store all licenses for global view
        self.filtered_licenses = []  # Store filtered licenses for search
        self.is_loading = False  # Track loading state
        self.search_thread = None  # Track search thread
        self._search_after_id = None  # Track scheduled search callbacks
        self.displayed_count = 0  # Track how many licenses are currently displayed (for lazy loading)
        self.total_licenses = []  # Store licenses to be displayed in batches
        self.current_offset = 0  # Track current pagination offset for database queries
        self.has_more_licenses = False  # Track if more licenses are available in database
        
        # Create UI
        self._create_ui()
        
        # Load all licenses on startup (non-blocking)
        self.after(500, self._load_all_licenses_async)
        
        # Finalize window setup after UI is created (prevents recursion issues)
        self.after(200, self._finalize_init)
    
    def _finalize_init(self):
        """
        Finalize window initialization by maximizing the window.
        Called via self.after() to prevent recursion issues with scrollbar calculations.
        """
        # Maximize window (cross-platform compatible)
        try:
            # Try Windows-specific zoomed state
            self.state('zoomed')
        except:
            # Fallback for other platforms
            try:
                # Try macOS
                self.attributes('-zoomed', True)
            except:
                # Fallback: set large geometry
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                self.geometry(f"{screen_width}x{screen_height}+0+0")
        
    def _create_ui(self):
        """Create the main UI with Global Key Explorer and Search."""
        # Main container with two columns
        main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS['background'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=0, minsize=350)  # Sidebar (fixed)
        main_frame.grid_columnconfigure(1, weight=1)  # Explorer (expandable)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left column - Key Generator
        left_column = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=COLORS['sidebar'])
        left_column.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        
        # Header
        header_frame = ctk.CTkFrame(left_column, corner_radius=10, fg_color=COLORS['background'])
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔑 License Generator",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['accent']
        )
        title_label.pack(pady=15)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Vendor Tool - DO NOT DISTRIBUTE",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_dim']
        )
        subtitle_label.pack(pady=(0, 15))
        
        # Scrollable input section
        input_scroll = ctk.CTkScrollableFrame(left_column, corner_radius=0, fg_color="transparent")
        input_scroll.pack(fill="both", expand=True, pady=(0, 10))
        
        # Email input
        email_label = ctk.CTkLabel(
            input_scroll,
            text="Buyer Email:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        )
        email_label.pack(pady=(15, 5), padx=20, anchor="w")
        
        self.email_entry = ctk.CTkEntry(
            input_scroll,
            placeholder_text="buyer@example.com",
            font=ctk.CTkFont(size=12),
            height=38,
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.email_entry.pack(fill="x", padx=20, pady=(0, 15))
        self.email_entry.bind("<Return>", lambda e: self._on_generate())
        
        # Add clipboard support (includes all shortcuts: Ctrl+C/V/A)
        add_context_menu(self.email_entry)
        
        # Tier selection
        tier_label = ctk.CTkLabel(
            input_scroll,
            text="License Tier:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        )
        tier_label.pack(pady=(5, 5), padx=20, anchor="w")
        
        self.tier_var = ctk.StringVar(value="standard")
        
        tier_options = ctk.CTkFrame(input_scroll, fg_color="transparent")
        tier_options.pack(fill="x", padx=20, pady=(0, 15))
        
        tier_radio1 = ctk.CTkRadioButton(
            tier_options,
            text="Standard - Basic Features",
            variable=self.tier_var,
            value="standard",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover']
        )
        tier_radio1.pack(anchor="w", pady=4)
        
        tier_radio2 = ctk.CTkRadioButton(
            tier_options,
            text="Extended - Full Branding",
            variable=self.tier_var,
            value="extended",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover']
        )
        tier_radio2.pack(anchor="w", pady=4)
        
        tier_radio3 = ctk.CTkRadioButton(
            tier_options,
            text="Professional - Premium Support",
            variable=self.tier_var,
            value="professional",
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover']
        )
        tier_radio3.pack(anchor="w", pady=4)
        
        # Duration input
        duration_label = ctk.CTkLabel(
            input_scroll,
            text="Duration (Days):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        )
        duration_label.pack(pady=(5, 5), padx=20, anchor="w")
        
        duration_help = ctk.CTkLabel(
            input_scroll,
            text="Enter days (3, 30, 90, 180, 365) or 'lifetime' (case-insensitive)",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_dim']
        )
        duration_help.pack(pady=(0, 5), padx=20, anchor="w")
        
        self.duration_entry = ctk.CTkEntry(
            input_scroll,
            placeholder_text="lifetime",
            font=ctk.CTkFont(size=12),
            height=38,
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.duration_entry.pack(fill="x", padx=20, pady=(0, 15))
        self.duration_entry.insert(0, "lifetime")
        
        # Add clipboard support
        add_context_menu(self.duration_entry)
        
        # Device Limit input
        device_label = ctk.CTkLabel(
            input_scroll,
            text="Max Devices (HWID Limit):",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        )
        device_label.pack(pady=(5, 5), padx=20, anchor="w")
        
        device_help = ctk.CTkLabel(
            input_scroll,
            text="Number of devices that can use this license",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_dim']
        )
        device_help.pack(pady=(0, 5), padx=20, anchor="w")
        
        self.device_limit_entry = ctk.CTkEntry(
            input_scroll,
            placeholder_text="3",
            font=ctk.CTkFont(size=12),
            height=38,
            width=120,
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.device_limit_entry.pack(padx=20, pady=(0, 15), anchor="w")
        self.device_limit_entry.insert(0, "3")
        
        # Add clipboard support
        add_context_menu(self.device_limit_entry)
        
        # Initial Credits input (NEW - Credit System)
        credits_label = ctk.CTkLabel(
            input_scroll,
            text="Initial Credits:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        )
        credits_label.pack(pady=(5, 5), padx=20, anchor="w")
        
        credits_help = ctk.CTkLabel(
            input_scroll,
            text="Number of generation credits for this license (e.g., 10, 50, 100)",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_dim']
        )
        credits_help.pack(pady=(0, 5), padx=20, anchor="w")
        
        self.credits_entry = ctk.CTkEntry(
            input_scroll,
            placeholder_text="10",
            font=ctk.CTkFont(size=12),
            height=38,
            width=120,
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.credits_entry.pack(padx=20, pady=(0, 15), anchor="w")
        self.credits_entry.insert(0, "10")
        
        # Add clipboard support (includes all shortcuts: Ctrl+C/V/A)
        add_context_menu(self.credits_entry)
        
        # Generate button
        self.generate_btn = ctk.CTkButton(
            input_scroll,
            text="⚡ Generate License Key",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=self._on_generate
        )
        self.generate_btn.pack(fill="x", padx=20, pady=(5, 15))
        
        # Output textbox
        output_label = ctk.CTkLabel(
            input_scroll,
            text="Generated License:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        )
        output_label.pack(pady=(10, 5), padx=20, anchor="w")
        
        self.output_text = ctk.CTkTextbox(
            input_scroll,
            font=ctk.CTkFont(family="Courier New", size=11),
            wrap="word",
            state="disabled",
            height=120,
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.output_text.pack(fill="x", padx=20, pady=(0, 10))
        
        # Add clipboard support (includes all shortcuts: Ctrl+C/V/A)
        add_context_menu(self.output_text)
        
        # Copy button
        self.copy_btn = ctk.CTkButton(
            input_scroll,
            text="📋 Copy License Key",
            font=ctk.CTkFont(size=12),
            height=35,
            fg_color=COLORS['sidebar'],
            hover_color=COLORS['accent'],
            command=self._on_copy,
            state="disabled"
        )
        self.copy_btn.pack(fill="x", padx=20, pady=(0, 15))
        
        # Edit/Manage Key button
        self.manage_key_btn = ctk.CTkButton(
            input_scroll,
            text="✏️ Edit/Manage Key",
            font=ctk.CTkFont(size=12),
            height=35,
            fg_color=COLORS['sidebar'],
            hover_color=COLORS['accent'],
            command=self._on_manage_key
        )
        self.manage_key_btn.pack(fill="x", padx=20, pady=(0, 15))
        
        # Refill Key button (NEW - Credit System)
        self.refill_key_btn = ctk.CTkButton(
            input_scroll,
            text="💰 Refill Key",
            font=ctk.CTkFont(size=12),
            height=35,
            fg_color=COLORS['sidebar'],
            hover_color=COLORS['accent'],
            command=self._on_refill_key
        )
        self.refill_key_btn.pack(fill="x", padx=20, pady=(0, 15))
        
        # Status bar
        self.status_label = ctk.CTkLabel(
            left_column,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_dim']
        )
        self.status_label.pack(pady=(5, 15))
        
        # Right column - Global Key Explorer with Search
        right_column = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=COLORS['sidebar'])
        right_column.grid(row=0, column=1, padx=(15, 0), sticky="nsew")
        
        # Explorer Header
        explorer_header = ctk.CTkFrame(right_column, corner_radius=10, fg_color=COLORS['background'])
        explorer_header.pack(fill="x", pady=(0, 15))
        
        explorer_title = ctk.CTkLabel(
            explorer_header,
            text="🌐 Global Key Explorer",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS['accent']
        )
        explorer_title.pack(pady=15)
        
        # Search Bar (NEW - POWERFUL SEARCH)
        search_frame = ctk.CTkFrame(right_column, corner_radius=8, fg_color=COLORS['background'])
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        search_label = ctk.CTkLabel(
            search_frame,
            text="🔍 Search:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS['text']
        )
        search_label.pack(side="left", padx=(15, 10), pady=12)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search by Email, HWID, License Key, Tier, or Date",
            font=ctk.CTkFont(size=12),
            height=38,
            fg_color=COLORS['sidebar'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=12)
        
        # Add clipboard support for search (includes all shortcuts: Ctrl+C/V/A)
        add_context_menu(self.search_entry)
        
        # Bind real-time search (with debouncing)
        self.search_entry.bind("<KeyRelease>", self._on_search_keypress)
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="Search",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=100,
            height=38,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=self._perform_search
        )
        search_btn.pack(side="left", padx=(0, 15), pady=12)
        
        # Control buttons
        control_frame = ctk.CTkFrame(right_column, corner_radius=8, fg_color="transparent")
        control_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.refresh_db_btn = ctk.CTkButton(
            control_frame,
            text="🔄 Refresh Database",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=self._load_all_licenses_async
        )
        self.refresh_db_btn.pack(side="left", padx=(0, 10))
        
        self.loading_label = ctk.CTkLabel(
            control_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['accent']
        )
        self.loading_label.pack(side="left", padx=(10, 0))
        
        # Global Key Explorer with grid weight configuration for proper expansion
        self.explorer_frame = ctk.CTkScrollableFrame(
            right_column,
            corner_radius=0,
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.explorer_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        # Configure grid weights for proper scrolling behavior and content expansion
        self.explorer_frame.grid_columnconfigure(0, weight=1)
        
    def _on_search_keypress(self, event):
        """Handle search keypress with debouncing."""
        # Cancel previous scheduled search if any
        if hasattr(self, '_search_after_id') and self._search_after_id:
            self.after_cancel(self._search_after_id)
        
        # Schedule new search after short delay (debouncing)
        self._search_after_id = self.after(300, self._perform_search)
    
    def _perform_search(self):
        """Perform search in a background thread to avoid UI freezing."""
        search_term = self.search_entry.get().strip().lower()
        
        if not search_term:
            # If search is empty, show all licenses
            self.filtered_licenses = self.all_licenses.copy()
            self._display_licenses(self.filtered_licenses)
            return
        
        # Run search in background thread
        if self.search_thread and self.search_thread.is_alive():
            return  # Prevent multiple simultaneous searches
        
        self.search_thread = threading.Thread(target=self._search_licenses, args=(search_term,), daemon=True)
        self.search_thread.start()
    
    def _search_licenses(self, search_term):
        """Search licenses by Email, HWID, License Key, Tier, or Creation Date (runs in background thread)."""
        # Create a local copy to avoid race conditions
        licenses_to_search = list(self.all_licenses)
        filtered = []
        
        for license_record in licenses_to_search:
            email = str(license_record.get('email', '')).lower()
            key = str(license_record.get('license_key', '')).lower()
            hwid = str(license_record.get('hwid', '') or '').lower()
            tier = str(license_record.get('tier', '')).lower()
            created = str(license_record.get('created_at', '')).lower()
            
            # Check if search term matches any field
            matches = any([
                search_term in email,
                search_term in key,
                search_term in hwid,
                search_term in tier,
                search_term in created
            ])
            
            if matches:
                filtered.append(license_record)
        
        self.filtered_licenses = filtered
        
        # Update UI on main thread
        self.after(0, lambda: self._display_licenses(self.filtered_licenses))
        self.after(0, lambda: self._update_search_status(len(filtered)))
    
    def _update_search_status(self, count):
        """Update search status label."""
        search_term = self.search_entry.get().strip()
        if search_term:
            self.loading_label.configure(text=f"✓ Found {count} match(es)")
        else:
            self.loading_label.configure(text=f"✓ Loaded {len(self.all_licenses)} license(s)")
    
    def _on_generate(self):
        """Handle generate button click with Supabase sync (Full Schema with Credits)."""
        # Prevent double-click by disabling the button during generation
        if hasattr(self, '_generating') and self._generating:
            return
        self._generating = True
        self.generate_btn.configure(state="disabled", text="⏳ Generating...")
        
        try:
            self._do_generate()
        finally:
            # Re-enable button after generation
            self._generating = False
            self.generate_btn.configure(state="normal", text="⚡ Generate License Key")
    
    def _do_generate(self):
        """Actual generation logic (called from _on_generate)."""
        email_input = self.email_entry.get().strip()
        credits_input = self.credits_entry.get().strip()
        duration_input = self.duration_entry.get().strip().lower()
        device_limit_input = self.device_limit_entry.get().strip()
        
        if not email_input:
            messagebox.showerror("Error", "Please enter a buyer email.")
            return
        
        # Validate email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email_input):
            messagebox.showerror("Error", "Please enter a valid email address.")
            return
        
        # Validate credits
        try:
            credits = int(credits_input) if credits_input else 10
            if credits < 1:
                messagebox.showerror("Error", "Credits must be at least 1.")
                return
        except ValueError:
            messagebox.showerror("Error", "Credits must be a valid number.")
            return
        
        # Validate device limit
        try:
            device_limit = int(device_limit_input) if device_limit_input else 3
            if device_limit < 1 or device_limit > 100:
                messagebox.showerror("Error", "Device limit must be between 1 and 100.")
                return
        except ValueError:
            messagebox.showerror("Error", "Device limit must be a valid number.")
            return
        
        # Parse duration input
        duration_code = 'lifetime'
        if duration_input in DURATION_MAP:
            duration_code = DURATION_MAP[duration_input]
        elif duration_input.isdigit():
            days = int(duration_input)
            # Map custom days to closest duration
            if days <= 3:
                duration_code = '3_day'
            elif days <= 30:
                duration_code = '1_month'
            elif days <= 90:
                duration_code = '3_month'
            elif days <= 180:
                duration_code = '6_month'
            elif days <= 365:
                duration_code = '1_year'
            else:
                duration_code = 'lifetime'
        else:
            # Invalid input - show warning and default to lifetime
            messagebox.showwarning(
                "Invalid Duration",
                f"'{duration_input}' is not a valid duration. Defaulting to 'lifetime'.\n\n"
                "Valid inputs: 3, 30, 90, 180, 365, or 'lifetime'"
            )
        
        # Get tier
        tier = self.tier_var.get()
        
        # Generate license key using the actual generate_key function
        try:
            license_key, expires_at = generate_key(email_input, tier, duration_code)
            
            # Sync to Supabase database with ALL fields including credits
            sync_success = self._sync_to_supabase(email_input, license_key, tier, expires_at, device_limit, credits)
            
            # Display the license
            self._display_license(email_input, tier, license_key, device_limit, credits, duration_input, sync_success)
            
            # Update status
            sync_status = "✓ Synced to Supabase" if sync_success else "⚠ Local only (Supabase unavailable)"
            self.status_label.configure(
                text=f"License generated for {email_input} - {sync_status}",
                text_color=COLORS['accent']
            )
            
            # Refresh global explorer after generation (only if sync was successful)
            if sync_success:
                self.after(1000, self._load_all_licenses_async)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate license: {str(e)}")
            self.status_label.configure(text="Generation failed", text_color="red")
    
    def _sync_to_supabase(self, email, license_key, tier, expires_at, device_limit, credits):
        """
        Sync generated license to Supabase database (Full Schema with Credits).
        
        Full Schema:
        - license_key (Text, Unique)
        - credits (int4, NEW)
        - email (text)
        - is_banned (bool)
        - hwid (text)
        - used_hwids (jsonb)
        - max_devices (int4)
        - valid_until (timestamptz)
        - created_at (timestamptz)
        - tier (text)
        - page_limit (int4)
        
        Args:
            email: Buyer email
            license_key: Generated license key
            tier: License tier (standard/extended/professional)
            expires_at: Expiration date (ISO format) or None for lifetime
            device_limit: Maximum number of devices
            credits: Initial credits for this license
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        client = get_supabase_client()
        if not client:
            print("Supabase client not available")
            return False
        
        try:
            # Check if license key already exists
            existing = client.table("licenses").select("license_key").eq("license_key", license_key).execute()
            if existing.data and len(existing.data) > 0:
                messagebox.showwarning(
                    "Duplicate Key",
                    f"License key {license_key} already exists in database. This should not happen - "
                    "please contact support."
                )
                return False
            
            # Determine page limit based on tier
            page_limit_map = {
                'standard': 50,
                'extended': 150,
                'professional': 300
            }
            page_limit = page_limit_map.get(tier, 50)
            
            # Prepare license data with FULL schema + credits
            license_data = {
                'license_key': license_key,
                'email': email,
                'tier': tier,
                'valid_until': expires_at,
                'is_banned': False,
                'hwid': None,  # Single device HWID - set on first activation
                'used_hwids': [],  # Empty array for multi-device support
                'max_devices': device_limit,
                'credits': credits,  # NEW - Credit system
                'page_limit': page_limit,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert into Supabase
            response = client.table("licenses").insert(license_data).execute()
            
            if response.data:
                print(f"Successfully synced license {license_key} to Supabase with {credits} credits, tier={tier}")
                return True
            else:
                print("Failed to sync to Supabase: No data returned")
                return False
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error syncing to Supabase: {error_msg}")
            
            # Show user-friendly error
            messagebox.showerror(
                "Database Sync Error",
                f"Failed to sync license to database:\n{error_msg}\n\n"
                "The license key was generated but not saved to the cloud database."
            )
            return False
    
    def _load_all_licenses_async(self):
        """Load licenses from Supabase asynchronously (non-blocking). Resets pagination."""
        if self.is_loading:
            return  # Prevent multiple simultaneous loads
        
        self.is_loading = True
        self.current_offset = 0  # Reset pagination offset
        self.all_licenses = []  # Clear existing licenses
        self.loading_label.configure(text="⏳ Loading...")
        self.refresh_db_btn.configure(state="disabled")
        
        # Run database fetch in separate thread
        thread = threading.Thread(target=self._fetch_all_licenses, daemon=True)
        thread.start()
    
    def _fetch_all_licenses(self):
        """Fetch licenses from Supabase (runs in background thread)."""
        client = get_supabase_client()
        
        if not client:
            self.after(0, lambda: self._display_error("⚠ Supabase not available"))
            self.after(0, lambda: self._finish_loading())
            return
        
        try:
            # Order by created_at (most recent first)
            response = client.table("licenses").select("*").order("created_at", desc=True).limit(50).execute()
            
            if response.data:
                self.all_licenses = response.data
                self.current_offset = len(response.data)
                # Track if there might be more licenses
                self.has_more_licenses = len(response.data) >= 50
                self.filtered_licenses = self.all_licenses.copy()
                # Update UI on main thread - display ALL licenses from response
                self.after(0, lambda: self._display_licenses(self.filtered_licenses))
            else:
                self.all_licenses = []
                self.filtered_licenses = []
                self.has_more_licenses = False
                self.after(0, lambda: self._display_error("No licenses found in database."))
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error fetching all licenses: {error_msg}")
            self.after(0, lambda: self._display_error(f"Error loading licenses:\n{error_msg}"))
        
        finally:
            self.after(0, lambda: self._finish_loading())
    
    def _load_more_licenses_async(self):
        """Load more licenses from Supabase (pagination - next 50 rows)."""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.loading_label.configure(text="⏳ Loading more...")
        
        # Run database fetch in separate thread
        thread = threading.Thread(target=self._fetch_more_licenses, daemon=True)
        thread.start()
    
    def _fetch_more_licenses(self):
        """Fetch next batch of 50 licenses from Supabase (runs in background thread)."""
        client = get_supabase_client()
        
        if not client:
            self.after(0, lambda: self._finish_loading())
            return
        
        try:
            # Fetch next 50 licenses starting from current offset
            # .range(start, end) is inclusive, so end = start + 49 for 50 records
            end_offset = self.current_offset + 49
            response = client.table("licenses").select("*").order("created_at", desc=True).range(self.current_offset, end_offset).execute()
            
            if response.data:
                # Append to existing licenses
                self.all_licenses.extend(response.data)
                self.current_offset += len(response.data)
                # Track if there might be more licenses
                self.has_more_licenses = len(response.data) >= 50
                self.filtered_licenses = self.all_licenses.copy()
                # Update UI on main thread (re-display all)
                self.after(0, lambda: self._display_licenses(self.filtered_licenses))
            else:
                # No more licenses available
                self.has_more_licenses = False
                self.after(0, lambda: self._display_licenses(self.filtered_licenses))
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error fetching more licenses: {error_msg}")
        
        finally:
            self.after(0, lambda: self._finish_loading())
    
    def _finish_loading(self):
        """Clean up after loading completes."""
        self.is_loading = False
        self.loading_label.configure(text=f"✓ Loaded {len(self.all_licenses)} license(s)")
        self.refresh_db_btn.configure(state="normal")
    
    def _display_error(self, message):
        """Display error message in explorer frame."""
        # Clear existing widgets
        for widget in self.explorer_frame.winfo_children():
            widget.destroy()
        
        error_label = ctk.CTkLabel(
            self.explorer_frame,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_dim']
        )
        error_label.pack(pady=50)
    
    def _display_licenses(self, licenses):
        """Display licenses in the Global Key Explorer with lazy loading (first 50 rows)."""
        # Clear existing widgets
        for widget in self.explorer_frame.winfo_children():
            widget.destroy()
        
        if not licenses:
            self._display_error("No licenses match your search criteria.")
            return
        
        # Update loading label with count
        count = len(licenses)
        search_term = self.search_entry.get().strip()
        if search_term:
            self.loading_label.configure(text=f"✓ Found {count} match(es)")
        else:
            self.loading_label.configure(text=f"✓ Loaded {count} license(s)")
        
        # Create header row (FULL SCHEMA: Email, Key, Tier, Credits, Devices, Valid Until, Actions)
        header_frame = ctk.CTkFrame(
            self.explorer_frame,
            corner_radius=6,
            fg_color=COLORS['accent'],
            height=45
        )
        header_frame.pack(fill="x", pady=(0, 10), padx=2)
        header_frame.grid_columnconfigure(0, weight=2, minsize=180)  # Email
        header_frame.grid_columnconfigure(1, weight=2, minsize=240)  # License Key
        header_frame.grid_columnconfigure(2, weight=1)  # Tier
        header_frame.grid_columnconfigure(3, weight=1)  # Credits
        header_frame.grid_columnconfigure(4, weight=1)  # Devices
        header_frame.grid_columnconfigure(5, weight=1, minsize=120)  # Valid Until
        header_frame.grid_columnconfigure(6, weight=0)  # Actions
        
        headers = ["Email", "License Key", "Tier", "Credits", "Devices", "Valid Until", "Actions"]
        for idx, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS['background']
            )
            header_label.grid(row=0, column=idx, padx=10, pady=10, sticky="ew")
        
        # LAZY LOADING: Render first 50 rows initially
        self.displayed_count = 0
        self.total_licenses = licenses
        self._render_next_batch()
    
    def _render_next_batch(self):
        """
        Render the next batch of licenses using lazy loading.
        
        This method implements pagination by rendering licenses in batches of
        LAZY_LOAD_BATCH_SIZE (default: 50) to improve performance when dealing
        with large numbers of licenses (e.g., 165+ rows). After each batch,
        a "Load More" button appears to load the next batch on demand.
        
        This approach prevents UI freezing that would occur if all licenses
        were rendered simultaneously.
        """
        batch_size = LAZY_LOAD_BATCH_SIZE
        start_idx = self.displayed_count
        end_idx = min(start_idx + batch_size, len(self.total_licenses))
        
        # Create row for each license in this batch
        for idx in range(start_idx, end_idx):
            license_record = self.total_licenses[idx]
            self._create_license_row(license_record, idx)
        
        self.displayed_count = end_idx
        
        # Add "Load More" button if there are more licenses in local cache
        if self.displayed_count < len(self.total_licenses):
            if not hasattr(self, 'load_more_btn') or not self.load_more_btn.winfo_exists():
                self.load_more_btn = ctk.CTkButton(
                    self.explorer_frame,
                    text=f"📥 Load More ({len(self.total_licenses) - self.displayed_count} remaining)",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    height=45,
                    corner_radius=10,
                    fg_color=COLORS['accent'],
                    hover_color=COLORS['accent_hover'],
                    command=self._render_next_batch
                )
                self.load_more_btn.pack(fill="x", pady=(20, 10), padx=2)
            else:
                # Update button text
                self.load_more_btn.configure(
                    text=f"📥 Load More ({len(self.total_licenses) - self.displayed_count} remaining)"
                )
        else:
            # All cached licenses displayed, remove the render more button
            if hasattr(self, 'load_more_btn') and self.load_more_btn.winfo_exists():
                self.load_more_btn.pack_forget()
            
            # Remove old "Load More from Database" button if it exists
            if hasattr(self, 'load_more_db_btn') and self.load_more_db_btn.winfo_exists():
                self.load_more_db_btn.pack_forget()
            
            # Add "Load More from Database" button only if there are more licenses available
            if self.has_more_licenses:
                self.load_more_db_btn = ctk.CTkButton(
                    self.explorer_frame,
                    text="📥 Load More from Database",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    height=45,
                    corner_radius=10,
                    fg_color=COLORS['sidebar'],
                    hover_color=COLORS['accent'],
                    command=self._load_more_licenses_async
                )
                self.load_more_db_btn.pack(fill="x", pady=(20, 10), padx=2)
    
    def _create_selectable_text_widget(self, parent, text, font, text_color, row_color, width=None, height=25):
        """
        Create a read-only, selectable text widget that allows copying.
        Uses CTkTextbox configured to look like a label but allow text selection.
        
        Args:
            parent: Parent widget
            text: Text to display
            font: Font to use
            text_color: Text color
            row_color: Background color to match row
            width: Optional width
            height: Height in pixels
            
        Returns:
            CTkTextbox: The created selectable text widget
        """
        textbox = ctk.CTkTextbox(
            parent,
            font=font,
            text_color=text_color,
            fg_color=row_color,
            border_width=0,
            height=height,
            width=width if width else 100,
            wrap="none",
            activate_scrollbars=False
        )
        textbox.insert("1.0", text)
        # Note: NOT setting to disabled to allow text selection
        # Text is effectively read-only due to blocking insert/delete operations
        
        # Prevent text modification while allowing selection and clipboard operations
        def block_modification(event):
            # Allow clipboard shortcuts to pass through
            if event.keysym in ['c', 'C', 'v', 'V', 'a', 'A'] and (event.state & 0x4):  # Ctrl key
                return None  # Let the binding continue
            # Block all other key presses that would modify content
            if event.char or event.keysym in ['BackSpace', 'Delete', 'Return', 'Tab']:
                return "break"
            return None
        
        tk_widget = textbox._textbox if hasattr(textbox, '_textbox') else textbox
        tk_widget.bind("<Key>", block_modification)
        
        # Add right-click context menu for copy functionality AFTER blocking modifications
        # This ensures shortcuts are bound after the blocking handler
        add_context_menu(textbox)
        
        return textbox
    
    def _create_license_row(self, license_record, idx):
        """Create a row for a single license in the explorer (FULL SCHEMA with Credits)."""
        email = license_record.get('email', 'N/A')
        key = license_record.get('license_key', 'N/A')
        tier = license_record.get('tier', 'N/A')
        credits = license_record.get('credits', 0)
        device_limit = license_record.get('max_devices', 1)
        hwid = license_record.get('hwid', None)
        valid_until = license_record.get('valid_until', None)
        
        # Determine device usage
        if hwid:
            device_usage = f"1/{device_limit}"
        else:
            device_usage = f"0/{device_limit}"
        
        # Format valid_until
        try:
            if valid_until:
                dt = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
                valid_str = dt.strftime("%Y-%m-%d")
            else:
                valid_str = "Lifetime"
        except (ValueError, TypeError):
            valid_str = "N/A"
        
        # Row background (alternating)
        row_color = COLORS['sidebar'] if idx % 2 == 0 else COLORS['background']
        
        row_frame = ctk.CTkFrame(
            self.explorer_frame,
            corner_radius=6,
            fg_color=row_color,
            height=50
        )
        row_frame.pack(fill="x", pady=3, padx=2)
        row_frame.grid_columnconfigure(0, weight=2, minsize=180)  # Email
        row_frame.grid_columnconfigure(1, weight=2, minsize=240)  # License Key
        row_frame.grid_columnconfigure(2, weight=1)  # Tier
        row_frame.grid_columnconfigure(3, weight=1)  # Credits
        row_frame.grid_columnconfigure(4, weight=1)  # Devices
        row_frame.grid_columnconfigure(5, weight=1, minsize=120)  # Valid Until
        row_frame.grid_columnconfigure(6, weight=0)  # Actions
        
        # Email - selectable textbox
        email_display = email[:30] + "..." if len(email) > 30 else email
        email_textbox = self._create_selectable_text_widget(
            row_frame,
            email_display,
            ctk.CTkFont(size=11),
            COLORS['text'],
            row_color
        )
        email_textbox.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        # License Key - selectable textbox
        key_textbox = self._create_selectable_text_widget(
            row_frame,
            key,
            ctk.CTkFont(family="Courier New", size=10),
            COLORS['accent'],
            row_color
        )
        key_textbox.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Tier - with color coding
        tier_color = "#FFD700" if tier == "professional" else ("#FFA500" if tier == "extended" else "#A0A0A0")
        tier_textbox = self._create_selectable_text_widget(
            row_frame,
            tier.upper() if tier != 'N/A' else tier,
            ctk.CTkFont(size=10, weight="bold"),
            tier_color,
            row_color
        )
        tier_textbox.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        
        # Credits - with color coding
        credits_color = "#00FF00" if credits > 10 else ("#FFA500" if credits > 0 else "#FF0000")
        credits_textbox = self._create_selectable_text_widget(
            row_frame,
            str(credits),
            ctk.CTkFont(size=11, weight="bold"),
            credits_color,
            row_color
        )
        credits_textbox.grid(row=0, column=3, padx=10, pady=5, sticky="ew")
        
        # Devices
        device_textbox = self._create_selectable_text_widget(
            row_frame,
            device_usage,
            ctk.CTkFont(size=10),
            COLORS['text'],
            row_color
        )
        device_textbox.grid(row=0, column=4, padx=10, pady=5, sticky="ew")
        
        # Valid Until
        valid_textbox = self._create_selectable_text_widget(
            row_frame,
            valid_str,
            ctk.CTkFont(size=10),
            COLORS['text_dim'],
            row_color
        )
        valid_textbox.grid(row=0, column=5, padx=10, pady=5, sticky="ew")
        
        # Action buttons frame
        action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        action_frame.grid(row=0, column=6, padx=10, pady=10)
        
        # Copy Email button
        copy_email_btn = ctk.CTkButton(
            action_frame,
            text="📧",
            font=ctk.CTkFont(size=10),
            width=35,
            height=30,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=lambda e=email: self._copy_to_clipboard(e, "Email")
        )
        copy_email_btn.pack(side="left", padx=2)
        
        # Copy Key button
        copy_key_btn = ctk.CTkButton(
            action_frame,
            text="🔑",
            font=ctk.CTkFont(size=10),
            width=35,
            height=30,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=lambda k=key: self._copy_to_clipboard(k, "License Key")
        )
        copy_key_btn.pack(side="left", padx=2)
        
        # Copy HWID button (copy first HWID if available)
        if hwid:
            copy_hwid_btn = ctk.CTkButton(
                action_frame,
                text="💻",
                font=ctk.CTkFont(size=10),
                width=35,
                height=30,
                fg_color=COLORS['accent'],
                hover_color=COLORS['accent_hover'],
                command=lambda h=hwid: self._copy_to_clipboard(h, "HWID")
            )
            copy_hwid_btn.pack(side="left", padx=2)
    
    def _add_hwid_context_menu(self, widget, license_record):
        """
        Add right-click context menu to HWID widget with "Reset HWID" option.
        
        Args:
            widget: The HWID textbox widget
            license_record: The license record containing HWID data
        """
        from tkinter import Menu
        
        # Get underlying Tk widget
        tk_widget = widget._textbox if hasattr(widget, '_textbox') else widget
        
        # Create context menu
        context_menu = Menu(tk_widget, tearoff=0)
        context_menu.add_command(
            label="Reset HWID",
            command=lambda: self._reset_hwid(license_record)
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="Copy HWID",
            command=lambda: self._copy_first_hwid(license_record)
        )
        
        # Bind right-click to show menu
        def show_context_menu(event):
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
            return "break"
        
        tk_widget.bind("<Button-3>", show_context_menu)
    
    def _reset_hwid(self, license_record):
        """
        Reset (clear) HWID for a license - sets hwid to NULL in Supabase.
        This allows the user to re-bind their device.
        
        Args:
            license_record: The license record to reset
        """
        email = license_record.get('email', 'N/A')
        license_key = license_record.get('license_key', 'N/A')
        current_hwid = license_record.get('hwid', 'None')
        
        # Confirm with user
        if not messagebox.askyesno(
            "Confirm Reset HWID",
            f"Are you sure you want to reset HWID for:\n\n"
            f"Email: {email}\n"
            f"License: {license_key}\n\n"
            f"Current HWID: {current_hwid if current_hwid else 'None'}\n\n"
            f"This will allow the license to be re-activated on a new device."
        ):
            return
        
        # Update Supabase
        client = get_supabase_client()
        if not client:
            messagebox.showerror("Error", "Supabase client not available.")
            return
        
        try:
            # Set hwid to NULL
            client.table("licenses").update({
                "hwid": None
            }).eq("license_key", license_key).execute()
            
            messagebox.showinfo(
                "Success",
                f"HWID reset successfully for license:\n{license_key}\n\n"
                f"The license can now be activated on a new device."
            )
            
            # Refresh the license list
            self._load_all_licenses_async()
            
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror(
                "Reset Failed",
                f"Failed to reset HWID:\n{error_msg}"
            )
    
    def _copy_first_hwid(self, license_record):
        """
        Copy the HWID to clipboard.
        
        Args:
            license_record: The license record
        """
        hwid = license_record.get('hwid', None)
        if hwid:
            self._copy_to_clipboard(hwid, "HWID")
        else:
            messagebox.showinfo("No HWID", "No HWID registered for this license.")
    
    def _copy_to_clipboard(self, text, label):
        """Copy text to clipboard with feedback."""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.loading_label.configure(text=f"✓ Copied {label}: {text[:30]}...")
        # Clear message after 3 seconds
        self.after(3000, lambda: self.loading_label.configure(
            text=f"✓ Loaded {len(self.all_licenses)} license(s)" if not self.search_entry.get().strip()
            else f"✓ Found {len(self.filtered_licenses)} match(es)"
        ))
    
    def _display_license(self, email, tier, license_key, device_limit, credits, duration, sync_success):
        """Display the generated license (Full Schema with Credits)."""
        tier_label = tier.capitalize()
        sync_status = "✓ Synced to Supabase" if sync_success else "⚠ Local only"
        
        output = f"""
{'=' * 65}
✓ License Generated Successfully!
{'=' * 65}

Email:         {email}
Tier:          {tier_label}
Duration:      {duration}
Key:           {license_key}
Device Limit:  {device_limit} device(s)
Credits:       {credits}
Status:        {sync_status}

Send this key to the buyer for activation.
{'=' * 65}
"""
        
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", output.strip())
        self.output_text.configure(state="disabled")
        
        self.copy_btn.configure(state="normal")
        self.last_license_key = license_key
    
    def _on_copy(self):
        """Copy the license key to clipboard."""
        if hasattr(self, 'last_license_key') and self.last_license_key:
            try:
                # Clear and set clipboard
                self.clipboard_clear()
                self.clipboard_append(self.last_license_key)
                # Force update to ensure clipboard is set
                self.update()
                
                # Show visual feedback without blocking messagebox
                self.status_label.configure(
                    text="✓ License key copied to clipboard!",
                    text_color="#2ECC71"  # Darker green for better contrast
                )
                # Reset status after 3 seconds
                self.after(3000, lambda: self.status_label.configure(
                    text="Ready",
                    text_color=COLORS['text_dim']
                ))
            except Exception as e:
                self.status_label.configure(
                    text=f"Copy failed: {str(e)}",
                    text_color="#E74C3C"
                )
        else:
            self.status_label.configure(
                text="No license key to copy",
                text_color="#E74C3C"
            )
    
    def _on_refill_key(self):
        """Handle Refill Key button click - adds credits to an existing license."""
        # Ask for license key
        key_dialog = ctk.CTkInputDialog(
            text="Enter the License Key to refill:",
            title="Refill Key - Step 1"
        )
        license_key = key_dialog.get_input()
        
        if not license_key or not license_key.strip():
            return
        
        license_key = license_key.strip()
        
        # Look up the key in the database
        client = get_supabase_client()
        if not client:
            messagebox.showerror("Error", "Supabase client not available.")
            return
        
        try:
            response = client.table("licenses").select("*").eq("license_key", license_key).execute()
            
            if not response.data or len(response.data) == 0:
                messagebox.showerror("Not Found", f"License key not found:\n{license_key}")
                return
            
            license_record = response.data[0]
            current_credits = license_record.get('credits', 0)
            email = license_record.get('email', 'N/A')
            
            # Ask for amount to add
            amount_dialog = ctk.CTkInputDialog(
                text=f"Current credits: {current_credits}\nEmail: {email}\n\nEnter amount to ADD:",
                title="Refill Key - Step 2"
            )
            amount_str = amount_dialog.get_input()
            
            if not amount_str or not amount_str.strip():
                return
            
            try:
                amount = int(amount_str.strip())
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be a positive number.")
                    return
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number.")
                return
            
            # Execute: UPDATE licenses SET credits = credits + X WHERE license_key = ...
            # Re-fetch current credits to minimize race condition window
            fresh_response = client.table("licenses").select("credits").eq("license_key", license_key).execute()
            if fresh_response.data and len(fresh_response.data) > 0:
                fresh_credits = fresh_response.data[0].get('credits', 0)
            else:
                fresh_credits = current_credits
            
            new_credits = fresh_credits + amount
            client.table("licenses").update({
                "credits": new_credits
            }).eq("license_key", license_key).execute()
            
            messagebox.showinfo(
                "Success",
                f"Credits refilled successfully!\n\n"
                f"Key: {license_key}\n"
                f"Previous credits: {fresh_credits}\n"
                f"Added: +{amount}\n"
                f"New total: {new_credits}"
            )
            
            self.status_label.configure(
                text=f"Refilled {amount} credits to {email}",
                text_color=COLORS['accent']
            )
            
            # Refresh the explorer
            self._load_all_licenses_async()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refill credits:\n{str(e)}")
    
    def _on_manage_key(self):
        """Handle Edit/Manage Key button click - opens dialog to enter existing key."""
        # Create a dialog window to enter existing license key
        dialog = ctk.CTkInputDialog(
            text="Enter the License Key to manage:",
            title="Edit/Manage Key"
        )
        license_key = dialog.get_input()
        
        if not license_key or not license_key.strip():
            return
        
        license_key = license_key.strip()
        
        # Look up the key in the database
        client = get_supabase_client()
        if not client:
            messagebox.showerror("Error", "Supabase client not available.")
            return
        
        try:
            response = client.table("licenses").select("*").eq("license_key", license_key).execute()
            
            if not response.data or len(response.data) == 0:
                messagebox.showerror("Not Found", f"License key not found:\n{license_key}")
                return
            
            license_record = response.data[0]
            
            # Show the management sub-menu dialog
            self._show_manage_key_menu(license_record)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to look up license:\n{str(e)}")
    
    def _show_manage_key_menu(self, license_record):
        """
        Show sub-menu dialog for managing an existing key (Full Schema with Credits).
        
        Args:
            license_record: The license record from the database
        """
        license_key = license_record.get('license_key', 'N/A')
        email = license_record.get('email', 'N/A')
        tier = license_record.get('tier', 'N/A')
        credits = license_record.get('credits', 0)
        max_devices = license_record.get('max_devices', 1)
        hwid = license_record.get('hwid', None)
        is_banned = license_record.get('is_banned', False)
        valid_until = license_record.get('valid_until', None)
        
        # Format valid_until
        try:
            if valid_until:
                dt = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
                valid_str = dt.strftime("%Y-%m-%d")
            else:
                valid_str = "Lifetime"
        except (ValueError, TypeError):
            valid_str = "N/A"
        
        # Create management dialog window
        manage_window = ctk.CTkToplevel(self)
        manage_window.title(f"Manage Key: {license_key}")
        manage_window.geometry("500x550")
        manage_window.resizable(False, False)
        manage_window.configure(fg_color=COLORS['background'])
        
        # Make dialog modal
        manage_window.transient(self)
        manage_window.grab_set()
        
        # Center the dialog on the parent window
        manage_window.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (500 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (550 // 2)
        manage_window.geometry(f"+{x}+{y}")
        
        # Header
        header_label = ctk.CTkLabel(
            manage_window,
            text="🔧 Manage License Key",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['accent']
        )
        header_label.pack(pady=(20, 10))
        
        # Key info (full schema)
        info_frame = ctk.CTkFrame(manage_window, corner_radius=8, fg_color=COLORS['sidebar'])
        info_frame.pack(fill="x", padx=20, pady=10)
        
        hwid_display = hwid[:HWID_TRUNCATE_LENGTH] + "..." if hwid and len(hwid) > HWID_TRUNCATE_LENGTH else (hwid or "Not Bound")
        device_usage = "1" if hwid else "0"
        key_info = ctk.CTkLabel(
            info_frame,
            text=f"Key: {license_key}\nEmail: {email}\nTier: {tier.upper() if tier != 'N/A' else tier}\nCredits: {credits}\nDevices: {device_usage}/{max_devices}\nValid Until: {valid_str}\nHWID: {hwid_display}\nBanned: {'Yes' if is_banned else 'No'}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text'],
            justify="left"
        )
        key_info.pack(pady=15, padx=15)
        
        # Option buttons
        btn_frame = ctk.CTkFrame(manage_window, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        # 1. Set Credits
        credits_btn = ctk.CTkButton(
            btn_frame,
            text="💰 Set Credits",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=45,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=lambda: self._set_credits(license_record, manage_window)
        )
        credits_btn.pack(fill="x", pady=5)
        
        # 2. Toggle Ban Status
        ban_text = "✅ Unban Key" if is_banned else "🚫 Ban Key"
        ban_btn = ctk.CTkButton(
            btn_frame,
            text=ban_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=45,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=lambda: self._toggle_ban(license_record, manage_window)
        )
        ban_btn.pack(fill="x", pady=5)
        
        # 3. Reset HWID
        reset_hwid_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Reset HWID",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=45,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=lambda: self._reset_hwid_from_menu(license_record, manage_window)
        )
        reset_hwid_btn.pack(fill="x", pady=5)
        
        # 4. Delete Key
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ Delete Key",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=45,
            fg_color="#8B0000",  # Dark red
            hover_color="#B22222",  # Lighter red on hover
            command=lambda: self._delete_key(license_record, manage_window)
        )
        delete_btn.pack(fill="x", pady=5)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(size=12),
            height=35,
            fg_color=COLORS['sidebar'],
            hover_color=COLORS['accent'],
            command=manage_window.destroy
        )
        cancel_btn.pack(fill="x", pady=(15, 5))
    
    def _set_credits(self, license_record, parent_window):
        """
        Set the credits value for a license key.
        
        Args:
            license_record: The license record from the database
            parent_window: The parent dialog window to close after completion
        """
        license_key = license_record.get('license_key')
        current_credits = license_record.get('credits', 0)
        
        # Ask for new credits value
        dialog = ctk.CTkInputDialog(
            text=f"Current credits: {current_credits}\n\nEnter new credits value:",
            title="Set Credits"
        )
        new_credits_str = dialog.get_input()
        
        if not new_credits_str or not new_credits_str.strip():
            return
        
        try:
            new_credits = int(new_credits_str.strip())
            if new_credits < 0:
                messagebox.showerror("Error", "Credits cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.")
            return
        
        # Update the database
        client = get_supabase_client()
        if not client:
            messagebox.showerror("Error", "Supabase client not available.")
            return
        
        try:
            client.table("licenses").update({
                "credits": new_credits
            }).eq("license_key", license_key).execute()
            
            messagebox.showinfo(
                "Success",
                f"Credits updated successfully!\n\n"
                f"Key: {license_key}\n"
                f"Previous: {current_credits}\n"
                f"New: {new_credits}"
            )
            
            parent_window.destroy()
            self._load_all_licenses_async()  # Refresh the explorer
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update credits:\n{str(e)}")
    
    def _toggle_ban(self, license_record, parent_window):
        """
        Toggle the ban status for a license key.
        
        Args:
            license_record: The license record from the database
            parent_window: The parent dialog window to close after completion
        """
        license_key = license_record.get('license_key')
        current_banned = license_record.get('is_banned', False)
        new_banned = not current_banned
        
        action = "ban" if new_banned else "unban"
        
        # Confirm action
        if not messagebox.askyesno(
            f"Confirm {action.title()}",
            f"Are you sure you want to {action} this license?\n\n"
            f"Key: {license_key}"
        ):
            return
        
        # Update the database
        client = get_supabase_client()
        if not client:
            messagebox.showerror("Error", "Supabase client not available.")
            return
        
        try:
            client.table("licenses").update({
                "is_banned": new_banned
            }).eq("license_key", license_key).execute()
            
            status = "banned" if new_banned else "unbanned"
            messagebox.showinfo(
                "Success",
                f"License key {status} successfully!\n\nKey: {license_key}"
            )
            
            parent_window.destroy()
            self._load_all_licenses_async()  # Refresh the explorer
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to {action} license:\n{str(e)}")
    
    def _reset_hwid_from_menu(self, license_record, parent_window):
        """
        Reset (clear) HWID for a license key from the management menu.
        
        Args:
            license_record: The license record from the database
            parent_window: The parent dialog window to close after completion
        """
        license_key = license_record.get('license_key')
        current_hwid = license_record.get('hwid', None)
        
        if not current_hwid:
            messagebox.showinfo("Info", "This license has no HWID bound yet.")
            return
        
        # Confirm reset
        if not messagebox.askyesno(
            "Confirm Reset HWID",
            f"Are you sure you want to reset the HWID for this license?\n\n"
            f"Key: {license_key}\n"
            f"Current HWID: {current_hwid[:HWID_TRUNCATE_LENGTH]}...\n\n"
            f"This will allow the license to be activated on a new device."
        ):
            return
        
        # Update the database
        client = get_supabase_client()
        if not client:
            messagebox.showerror("Error", "Supabase client not available.")
            return
        
        try:
            client.table("licenses").update({
                "hwid": None
            }).eq("license_key", license_key).execute()
            
            messagebox.showinfo(
                "Success",
                f"HWID reset successfully!\n\nKey: {license_key}\n\n"
                f"The license can now be activated on a new device."
            )
            
            parent_window.destroy()
            self._load_all_licenses_async()  # Refresh the explorer
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset HWID:\n{str(e)}")
    
    def _delete_key(self, license_record, parent_window):
        """
        Permanently delete a license key from the database.
        
        Args:
            license_record: The license record from the database
            parent_window: The parent dialog window to close after completion
        """
        license_key = license_record.get('license_key')
        email = license_record.get('email', 'N/A')
        
        # Confirm deletion
        if not messagebox.askyesno(
            "Confirm Delete",
            f"⚠️ WARNING: This action cannot be undone!\n\n"
            f"Are you sure you want to permanently delete:\n\n"
            f"Key: {license_key}\n"
            f"Email: {email}\n\n"
            f"This will remove all license data from the database."
        ):
            return
        
        # Double confirm for safety
        if not messagebox.askyesno(
            "Final Confirmation",
            f"This is your FINAL confirmation.\n\n"
            f"Delete license key?\n{license_key}"
        ):
            return
        
        # Delete from database
        client = get_supabase_client()
        if not client:
            messagebox.showerror("Error", "Supabase client not available.")
            return
        
        try:
            client.table("licenses").delete().eq("license_key", license_key).execute()
            
            messagebox.showinfo(
                "Deleted",
                f"License key deleted successfully!\n\nKey: {license_key}"
            )
            
            parent_window.destroy()
            self._load_all_licenses_async()  # Refresh the explorer
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete license:\n{str(e)}")


def main():
    """Main entry point for the admin keygen GUI."""
    # Set appearance mode
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # Create and run the application
    app = AdminKeygenApp()
    app.mainloop()


if __name__ == "__main__":
    main()
