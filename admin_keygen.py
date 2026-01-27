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
from utils import resource_path, add_context_menu
from dotenv import load_dotenv

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
        self.state('zoomed')
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
        
        # Create UI
        self._create_ui()
        
        # Load all licenses on startup (non-blocking)
        self.after(500, self._load_all_licenses_async)
        
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
        input_scroll = ctk.CTkScrollableFrame(left_column, corner_radius=8, fg_color="transparent")
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
        
        # Tier selection (now always visible - no God Mode)
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
        
        # Duration input (NEW)
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
        
        # Add clipboard support (includes all shortcuts: Ctrl+C/V/A)
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
        
        # Add clipboard support (includes all shortcuts: Ctrl+C/V/A)
        add_context_menu(self.device_limit_entry)
        
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
            placeholder_text="Search by Email, HWID, License Key, or Creation Date (YYYY-MM-DD)",
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
            corner_radius=8,
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
        """Search licenses by Email, HWID, License Key, or Creation Date (runs in background thread)."""
        # Create a local copy to avoid race conditions
        licenses_to_search = list(self.all_licenses)
        filtered = []
        
        for license_record in licenses_to_search:
            email = str(license_record.get('email', '')).lower()
            key = str(license_record.get('license_key', '')).lower()
            created = str(license_record.get('created_at', '')).lower()
            used_hwids = license_record.get('used_hwids', [])
            
            # Check if search term matches any field (using any() for efficiency)
            matches = any([
                search_term in email,
                search_term in key,
                search_term in created,
                (isinstance(used_hwids, list) and 
                 any(search_term in str(hwid).lower() for hwid in used_hwids))
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
        """Handle generate button click with Supabase sync."""
        email_input = self.email_entry.get().strip()
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
            
            # Sync to Supabase database with device limit
            sync_success = self._sync_to_supabase(email_input, license_key, tier, expires_at, device_limit)
            
            # Display the license
            self._display_license(email_input, tier, license_key, device_limit, duration_input, sync_success)
            
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
    
    def _sync_to_supabase(self, email, license_key, tier, expires_at, device_limit=3):
        """
        Sync generated license to Supabase database.
        
        Args:
            email: Buyer email
            license_key: Generated license key
            tier: License tier
            expires_at: Expiration date (ISO format) or None for lifetime
            device_limit: Maximum number of devices (default: 3)
            
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
            
            # Prepare license data with device_limit
            from datetime import datetime, timezone
            license_data = {
                'license_key': license_key,
                'email': email,
                'tier': tier,  # Ensure tier is correctly set
                'valid_until': expires_at,
                'is_banned': False,
                'used_hwids': [],  # Empty array for new licenses
                'max_devices': device_limit,  # Use the specified device limit
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert into Supabase
            response = client.table("licenses").insert(license_data).execute()
            
            if response.data:
                print(f"Successfully synced license {license_key} to Supabase with {device_limit} device limit")
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
        """Load all licenses from Supabase asynchronously (non-blocking)."""
        if self.is_loading:
            return  # Prevent multiple simultaneous loads
        
        self.is_loading = True
        self.loading_label.configure(text="⏳ Loading...")
        self.refresh_db_btn.configure(state="disabled")
        
        # Run database fetch in separate thread
        thread = threading.Thread(target=self._fetch_all_licenses, daemon=True)
        thread.start()
    
    def _fetch_all_licenses(self):
        """Fetch all licenses from Supabase (runs in background thread)."""
        client = get_supabase_client()
        
        if not client:
            self.after(0, lambda: self._display_error("⚠ Supabase not available"))
            self.after(0, lambda: self._finish_loading())
            return
        
        try:
            # Fetch ALL licenses from Supabase, ordered by creation date
            response = client.table("licenses").select("*").order("created_at", desc=True).execute()
            
            if response.data:
                self.all_licenses = response.data
                self.filtered_licenses = self.all_licenses.copy()
                # Update UI on main thread
                self.after(0, lambda: self._display_licenses(self.filtered_licenses))
            else:
                self.all_licenses = []
                self.filtered_licenses = []
                self.after(0, lambda: self._display_error("No licenses found in database."))
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error fetching all licenses: {error_msg}")
            self.after(0, lambda: self._display_error(f"Error loading licenses:\n{error_msg}"))
        
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
        """Display licenses in the Global Key Explorer."""
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
        
        # Create header row
        header_frame = ctk.CTkFrame(
            self.explorer_frame,
            corner_radius=6,
            fg_color=COLORS['accent'],
            height=45
        )
        header_frame.pack(fill="x", pady=(0, 10), padx=2)
        header_frame.grid_columnconfigure(0, weight=2)  # Email
        header_frame.grid_columnconfigure(1, weight=2)  # Key
        header_frame.grid_columnconfigure(2, weight=1)  # Tier
        header_frame.grid_columnconfigure(3, weight=1)  # Devices
        header_frame.grid_columnconfigure(4, weight=1)  # Created
        header_frame.grid_columnconfigure(5, weight=1)  # HWIDs
        header_frame.grid_columnconfigure(6, weight=0)  # Actions
        
        headers = ["Email", "License Key", "Tier", "Devices", "Created", "HWIDs", "Actions"]
        for idx, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS['background']
            )
            header_label.grid(row=0, column=idx, padx=10, pady=10, sticky="ew")
        
        # Create row for each license
        for idx, license_record in enumerate(licenses):
            self._create_license_row(license_record, idx)
        
        # Force canvas update to prevent floating text during scrolling
        # This ensures all widgets are properly positioned before scrolling begins
        self.explorer_frame.update_idletasks()
    
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
        """Create a row for a single license in the explorer."""
        email = license_record.get('email', 'N/A')
        key = license_record.get('license_key', 'N/A')
        tier = license_record.get('tier', 'N/A')
        max_devices = license_record.get('max_devices', 'N/A')
        used_hwids = license_record.get('used_hwids', [])
        created = license_record.get('created_at', 'N/A')
        
        # Parse and format date
        try:
            from datetime import datetime
            if created != 'N/A':
                dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                created = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            created = 'Invalid Date'
        
        # Determine device usage
        if isinstance(used_hwids, list):
            device_usage = f"{len(used_hwids)}/{max_devices}"
            hwid_preview = ', '.join(used_hwids[:2]) if used_hwids else 'None'
            if len(used_hwids) > 2:
                hwid_preview += "..."
        else:
            device_usage = f"0/{max_devices}"
            hwid_preview = 'None'
        
        # Row background (alternating)
        row_color = COLORS['sidebar'] if idx % 2 == 0 else COLORS['background']
        
        row_frame = ctk.CTkFrame(
            self.explorer_frame,
            corner_radius=6,
            fg_color=row_color,
            height=50
        )
        row_frame.pack(fill="x", pady=3, padx=2)
        row_frame.grid_columnconfigure(0, weight=2)
        row_frame.grid_columnconfigure(1, weight=2)
        row_frame.grid_columnconfigure(2, weight=1)
        row_frame.grid_columnconfigure(3, weight=1)
        row_frame.grid_columnconfigure(4, weight=1)
        row_frame.grid_columnconfigure(5, weight=1)
        row_frame.grid_columnconfigure(6, weight=0)
        
        # Email - selectable textbox
        email_display = email[:35] + "..." if len(email) > 35 else email
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
            ctk.CTkFont(family="Courier New", size=11),
            COLORS['accent'],
            row_color
        )
        key_textbox.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Tier - selectable textbox
        tier_color = "#FFD700" if tier == "professional" else ("#FFA500" if tier == "extended" else "#A0A0A0")
        tier_textbox = self._create_selectable_text_widget(
            row_frame,
            tier.upper() if tier != 'N/A' else tier,
            ctk.CTkFont(size=11, weight="bold"),
            tier_color,
            row_color
        )
        tier_textbox.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        
        # Device usage - selectable textbox
        device_textbox = self._create_selectable_text_widget(
            row_frame,
            device_usage,
            ctk.CTkFont(size=11),
            COLORS['text'],
            row_color
        )
        device_textbox.grid(row=0, column=3, padx=10, pady=5, sticky="ew")
        
        # Created date - selectable textbox
        date_textbox = self._create_selectable_text_widget(
            row_frame,
            created,
            ctk.CTkFont(size=10),
            COLORS['text_dim'],
            row_color
        )
        date_textbox.grid(row=0, column=4, padx=10, pady=5, sticky="ew")
        
        # HWIDs preview - selectable textbox
        hwid_textbox = self._create_selectable_text_widget(
            row_frame,
            hwid_preview,
            ctk.CTkFont(size=9),
            COLORS['text_dim'],
            row_color,
            width=150
        )
        hwid_textbox.grid(row=0, column=5, padx=10, pady=5, sticky="ew")
        
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
        if used_hwids and len(used_hwids) > 0:
            copy_hwid_btn = ctk.CTkButton(
                action_frame,
                text="💻",
                font=ctk.CTkFont(size=10),
                width=35,
                height=30,
                fg_color=COLORS['accent'],
                hover_color=COLORS['accent_hover'],
                command=lambda h=used_hwids[0]: self._copy_to_clipboard(h, "HWID")
            )
            copy_hwid_btn.pack(side="left", padx=2)
    
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
    
    def _display_license(self, email, tier, license_key, device_limit, duration, sync_success):
        """Display the generated license."""
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
            self.clipboard_clear()
            self.clipboard_append(self.last_license_key)
            messagebox.showinfo("Copied", "License key copied to clipboard!")
            self.status_label.configure(text="License key copied to clipboard", text_color=COLORS['accent'])


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
