#!/usr/bin/env python3
"""
Admin Key Generator - Full License Management Suite for Faleovad AI Enterprise.
GUI-based version for PyInstaller --noconsole mode compatibility.

This script is for the SELLER only to generate tiered license keys for buyers.

Tiers:
- Standard ($59): Basic features, no custom branding
- Extended ($249): Full features, custom logo and website support

Features:
- GUI Mode: Enter buyer email to instantly generate Standard license
- God Mode: Enter the master password to access tier selection
- Supabase Integration: Automatically syncs keys to cloud database
- Global Key Explorer: View ALL licenses from database
- Device Limit Control: Set max devices per license
"""

import sys
import os
import threading
from datetime import datetime, timedelta, timezone
import customtkinter as ctk
from tkinter import messagebox
from license_guard import generate_key
from utils import resource_path
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
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://spfwfyjpexktgnusgyib.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_tmwenU0VyOChNWKG90X_bw_HYf9X5kR")

# Suppress stdout/stderr for --noconsole mode with log file fallback
if hasattr(sys, 'frozen'):
    # Redirect to log file instead of complete suppression for debugging
    try:
        log_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'FaleovadAI', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'admin_keygen_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        sys.stdout = open(log_file, 'w', encoding='utf-8')
        sys.stderr = sys.stdout
    except:
        # If log file creation fails, suppress completely
        sys.stdout = None
        sys.stderr = None

# God Mode secret trigger - DO NOT SHARE
GOD_MODE_CODE = "A543278.B543278.Z12345_Faleovad2009"


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
        
        # Configure window - larger for Global Key Explorer
        self.title("CourseSmith License Management Suite")
        self.geometry("1400x800")
        self.resizable(True, True)
        
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.winfo_screenheight() // 2) - (800 // 2)
        self.geometry(f"1400x800+{x}+{y}")
        
        # Set icon if available
        try:
            icon_path = resource_path("resources/admin_keygen.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
        
        # State
        self.god_mode = False
        self.last_license_key = None
        self.all_licenses = []  # Store all licenses for global view
        self.is_loading = False  # Track loading state
        
        # Create UI
        self._create_ui()
        
        # Load all licenses on startup (non-blocking)
        self.after(500, self._load_all_licenses_async)
        
    def _create_ui(self):
        """Create the main UI with Global Key Explorer."""
        # Main container with three sections
        main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=0, minsize=380)  # Generator column (fixed)
        main_frame.grid_columnconfigure(1, weight=1)  # Global Explorer (expandable)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left column - Key Generator
        left_column = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=("#2b2b2b", "#1a1a1a"))
        left_column.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        # Header
        header_frame = ctk.CTkFrame(left_column, corner_radius=10, fg_color=("#1a1a1a", "#0d0d0d"))
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔑 License Generator",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#7F5AF0", "#9D7BF5")
        )
        title_label.pack(pady=12)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Vendor Tool - DO NOT DISTRIBUTE",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray50")
        )
        subtitle_label.pack(pady=(0, 12))
        
        # Scrollable input section
        input_scroll = ctk.CTkScrollableFrame(left_column, corner_radius=8, fg_color="transparent")
        input_scroll.pack(fill="both", expand=True, pady=(0, 10))
        
        # Email input
        email_label = ctk.CTkLabel(
            input_scroll,
            text="Buyer Email:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#E0E0E0", "#E0E0E0")
        )
        email_label.pack(pady=(10, 5), padx=15, anchor="w")
        
        self.email_entry = ctk.CTkEntry(
            input_scroll,
            placeholder_text="buyer@example.com or God Mode Code",
            font=ctk.CTkFont(size=11),
            height=32,
            fg_color=("#0B0E14", "#0B0E14"),
            border_color=("#7F5AF0", "#9D7BF5")
        )
        self.email_entry.pack(fill="x", padx=15, pady=(0, 10))
        self.email_entry.bind("<Return>", lambda e: self._on_generate())
        
        # Device Limit input (NEW)
        device_label = ctk.CTkLabel(
            input_scroll,
            text="Device Limit (Max HWIDs):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#E0E0E0", "#E0E0E0")
        )
        device_label.pack(pady=(5, 5), padx=15, anchor="w")
        
        device_help = ctk.CTkLabel(
            input_scroll,
            text="Number of devices that can use this license",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray50")
        )
        device_help.pack(pady=(0, 5), padx=15, anchor="w")
        
        self.device_limit_entry = ctk.CTkEntry(
            input_scroll,
            placeholder_text="3",
            font=ctk.CTkFont(size=11),
            height=32,
            width=100,
            fg_color=("#0B0E14", "#0B0E14"),
            border_color=("#7F5AF0", "#9D7BF5")
        )
        self.device_limit_entry.pack(padx=15, pady=(0, 10), anchor="w")
        self.device_limit_entry.insert(0, "3")  # Default value
        
        # Tier selection (initially hidden)
        self.tier_frame = ctk.CTkFrame(input_scroll, corner_radius=8, fg_color="transparent")
        self.tier_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        tier_label = ctk.CTkLabel(
            self.tier_frame,
            text="License Tier (God Mode):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#FF6600", "#FF8800")
        )
        tier_label.pack(pady=(0, 8), anchor="w")
        
        self.tier_var = ctk.StringVar(value="standard")
        
        tier_radio1 = ctk.CTkRadioButton(
            self.tier_frame,
            text="Standard ($59) - Basic Features",
            variable=self.tier_var,
            value="standard",
            font=ctk.CTkFont(size=11),
            fg_color=("#7F5AF0", "#9D7BF5"),
            hover_color=("#9D7BF5", "#7F5AF0")
        )
        tier_radio1.pack(anchor="w", pady=3)
        
        tier_radio2 = ctk.CTkRadioButton(
            self.tier_frame,
            text="Extended ($249) - Full Branding",
            variable=self.tier_var,
            value="extended",
            font=ctk.CTkFont(size=11),
            fg_color=("#7F5AF0", "#9D7BF5"),
            hover_color=("#9D7BF5", "#7F5AF0")
        )
        tier_radio2.pack(anchor="w", pady=3)
        
        # Hide tier selection initially
        self.tier_frame.pack_forget()
        
        # Generate button
        self.generate_btn = ctk.CTkButton(
            input_scroll,
            text="⚡ Generate License Key",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color=("#7F5AF0", "#9D7BF5"),
            hover_color=("#9D7BF5", "#7F5AF0"),
            command=self._on_generate
        )
        self.generate_btn.pack(fill="x", padx=15, pady=(0, 12))
        
        # Output textbox
        output_label = ctk.CTkLabel(
            input_scroll,
            text="Generated License:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#E0E0E0", "#E0E0E0")
        )
        output_label.pack(pady=(8, 5), padx=15, anchor="w")
        
        self.output_text = ctk.CTkTextbox(
            input_scroll,
            font=ctk.CTkFont(family="Courier New", size=10),
            wrap="word",
            state="disabled",
            height=110,
            fg_color=("#0B0E14", "#0B0E14"),
            border_color=("#7F5AF0", "#9D7BF5")
        )
        self.output_text.pack(fill="x", padx=15, pady=(0, 8))
        
        # Copy button
        self.copy_btn = ctk.CTkButton(
            input_scroll,
            text="📋 Copy License Key",
            font=ctk.CTkFont(size=11),
            height=28,
            fg_color=("#151921", "#151921"),
            hover_color=("#7F5AF0", "#9D7BF5"),
            command=self._on_copy,
            state="disabled"
        )
        self.copy_btn.pack(fill="x", padx=15, pady=(0, 12))
        
        # Status bar
        self.status_label = ctk.CTkLabel(
            left_column,
            text="Ready",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray50")
        )
        self.status_label.pack(pady=(5, 10))
        
        # Right column - Global Key Explorer
        right_column = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=("#2b2b2b", "#1a1a1a"))
        right_column.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        # Explorer Header
        explorer_header = ctk.CTkFrame(right_column, corner_radius=10, fg_color=("#1a1a1a", "#0d0d0d"))
        explorer_header.pack(fill="x", pady=(0, 10))
        
        explorer_title = ctk.CTkLabel(
            explorer_header,
            text="🌐 Global Key Explorer",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#7F5AF0", "#9D7BF5")
        )
        explorer_title.pack(pady=12)
        
        # Control buttons
        control_frame = ctk.CTkFrame(right_column, corner_radius=8, fg_color="transparent")
        control_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.refresh_db_btn = ctk.CTkButton(
            control_frame,
            text="🔄 Refresh Database",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35,
            fg_color=("#7F5AF0", "#9D7BF5"),
            hover_color=("#9D7BF5", "#7F5AF0"),
            command=self._load_all_licenses_async
        )
        self.refresh_db_btn.pack(side="left", padx=(0, 5))
        
        self.loading_label = ctk.CTkLabel(
            control_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#7F5AF0", "#9D7BF5")
        )
        self.loading_label.pack(side="left", padx=(10, 0))
        
        # Global Key Explorer (scrollable)
        self.explorer_frame = ctk.CTkScrollableFrame(
            right_column,
            corner_radius=8,
            fg_color=("#151921", "#151921"),
            border_color=("#7F5AF0", "#9D7BF5"),
            border_width=1
        )
        self.explorer_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
    def _on_generate(self):
        """Handle generate button click with Supabase sync."""
        email_input = self.email_entry.get().strip()
        device_limit_input = self.device_limit_entry.get().strip()
        
        if not email_input:
            messagebox.showerror("Error", "Please enter a buyer email or God Mode code.")
            return
        
        # Check for God Mode trigger
        if email_input == GOD_MODE_CODE:
            if not self.god_mode:
                self.god_mode = True
                self.tier_frame.pack(fill="x", padx=15, pady=(5, 10), before=self.generate_btn)
                self.status_label.configure(text="⚡ GOD MODE ACTIVATED ⚡", text_color=("#ff6600", "#ff8800"))
                messagebox.showinfo("God Mode", "God Mode Activated! You can now select license tiers.")
                self.email_entry.delete(0, "end")
                return
            else:
                messagebox.showwarning("God Mode", "God Mode is already active.")
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
        
        # Get tier (standard by default, or selected tier in god mode)
        tier = self.tier_var.get() if self.god_mode else 'standard'
        
        # Generate license key using the actual generate_key function
        try:
            # Default to lifetime duration
            duration = 'lifetime'
            license_key, expires_at = generate_key(email_input, tier, duration)
            
            # Sync to Supabase database with device limit
            sync_success = self._sync_to_supabase(email_input, license_key, tier, expires_at, device_limit)
            
            # Display the license
            self._display_license(email_input, tier, license_key, device_limit, sync_success)
            
            # Update status
            sync_status = "✓ Synced to Supabase" if sync_success else "⚠ Local only (Supabase unavailable)"
            self.status_label.configure(
                text=f"License generated for {email_input} - {sync_status}",
                text_color=("#1f6aa5", "#3b8ed0")
            )
            
            # Refresh global explorer after generation (only if sync was successful)
            if sync_success:
                self.after(1000, self._load_all_licenses_async)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate license: {str(e)}")
            self.status_label.configure(text="Generation failed", text_color=("red", "red"))
    
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
                'tier': tier,  # Ensure tier is correctly set (standard or extended)
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
                # Update UI on main thread
                self.after(0, lambda: self._display_all_licenses())
            else:
                self.all_licenses = []
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
        self.loading_label.configure(text="")
        self.refresh_db_btn.configure(state="normal")
    
    def _display_error(self, message):
        """Display error message in explorer frame."""
        # Clear existing widgets
        for widget in self.explorer_frame.winfo_children():
            widget.destroy()
        
        error_label = ctk.CTkLabel(
            self.explorer_frame,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray50")
        )
        error_label.pack(pady=50)
    
    def _display_all_licenses(self):
        """Display all licenses in the Global Key Explorer."""
        # Clear existing widgets
        for widget in self.explorer_frame.winfo_children():
            widget.destroy()
        
        if not self.all_licenses:
            self._display_error("No licenses found in database.")
            return
        
        # Update loading label with count
        count = len(self.all_licenses)
        self.loading_label.configure(text=f"✓ Loaded {count} license(s)")
        
        # Create header row
        header_frame = ctk.CTkFrame(
            self.explorer_frame,
            corner_radius=6,
            fg_color=("#7F5AF0", "#9D7BF5"),
            height=40
        )
        header_frame.pack(fill="x", pady=(0, 8), padx=2)
        header_frame.grid_columnconfigure(0, weight=2)  # Email
        header_frame.grid_columnconfigure(1, weight=2)  # Key
        header_frame.grid_columnconfigure(2, weight=1)  # Tier
        header_frame.grid_columnconfigure(3, weight=1)  # Devices
        header_frame.grid_columnconfigure(4, weight=1)  # Created
        header_frame.grid_columnconfigure(5, weight=0)  # Actions
        
        headers = ["Email", "License Key", "Tier", "Devices", "Created", ""]
        for idx, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#0B0E14", "#0B0E14")
            )
            header_label.grid(row=0, column=idx, padx=8, pady=8, sticky="w")
        
        # Create row for each license
        for idx, license_record in enumerate(self.all_licenses):
            self._create_license_row(license_record, idx)
    
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
        else:
            device_usage = f"0/{max_devices}"
        
        # Row background (alternating)
        row_color = ("#1a1a1a", "#1a1a1a") if idx % 2 == 0 else ("#0d0d0d", "#0d0d0d")
        
        row_frame = ctk.CTkFrame(
            self.explorer_frame,
            corner_radius=6,
            fg_color=row_color,
            height=45
        )
        row_frame.pack(fill="x", pady=2, padx=2)
        row_frame.grid_columnconfigure(0, weight=2)
        row_frame.grid_columnconfigure(1, weight=2)
        row_frame.grid_columnconfigure(2, weight=1)
        row_frame.grid_columnconfigure(3, weight=1)
        row_frame.grid_columnconfigure(4, weight=1)
        row_frame.grid_columnconfigure(5, weight=0)
        
        # Email
        email_label = ctk.CTkLabel(
            row_frame,
            text=email[:30] + "..." if len(email) > 30 else email,
            font=ctk.CTkFont(size=10),
            text_color=("#E0E0E0", "#E0E0E0"),
            anchor="w"
        )
        email_label.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        
        # License Key
        key_label = ctk.CTkLabel(
            row_frame,
            text=key,
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color=("#7F5AF0", "#9D7BF5"),
            anchor="w"
        )
        key_label.grid(row=0, column=1, padx=8, pady=8, sticky="w")
        
        # Tier
        tier_color = ("#FFD700", "#FFD700") if tier == "extended" else ("#A0A0A0", "#A0A0A0")
        tier_label = ctk.CTkLabel(
            row_frame,
            text=tier.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=tier_color,
            anchor="w"
        )
        tier_label.grid(row=0, column=2, padx=8, pady=8, sticky="w")
        
        # Device usage
        device_label = ctk.CTkLabel(
            row_frame,
            text=device_usage,
            font=ctk.CTkFont(size=10),
            text_color=("#E0E0E0", "#E0E0E0"),
            anchor="w"
        )
        device_label.grid(row=0, column=3, padx=8, pady=8, sticky="w")
        
        # Created date
        date_label = ctk.CTkLabel(
            row_frame,
            text=created,
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray50"),
            anchor="w"
        )
        date_label.grid(row=0, column=4, padx=8, pady=8, sticky="w")
        
        # Copy button
        copy_btn = ctk.CTkButton(
            row_frame,
            text="📋 Copy",
            font=ctk.CTkFont(size=9),
            width=70,
            height=26,
            fg_color=("#7F5AF0", "#9D7BF5"),
            hover_color=("#9D7BF5", "#7F5AF0"),
            command=lambda k=key: self._copy_key_from_explorer(k)
        )
        copy_btn.grid(row=0, column=5, padx=8, pady=8)
    
    def _copy_key_from_explorer(self, key):
        """Copy a license key from the explorer to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(key)
        self.loading_label.configure(text=f"✓ Copied: {key}")
        # Clear message after 3 seconds
        self.after(3000, lambda: self.loading_label.configure(text=f"✓ Loaded {len(self.all_licenses)} license(s)"))
    
    def _display_license(self, email, tier, license_key, device_limit, sync_success):
        """Display the generated license."""
        tier_label = "Extended ($249)" if tier == 'extended' else "Standard ($59)"
        sync_status = "✓ Synced to Supabase" if sync_success else "⚠ Local only"
        
        output = f"""
{'=' * 60}
✓ License Generated Successfully!
{'=' * 60}

Email:         {email}
Tier:          {tier_label}
Key:           {license_key}
Device Limit:  {device_limit} device(s)
Status:        {sync_status}

Send this key to the buyer for activation.
{'=' * 60}
"""
        
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", output.strip())
        self.output_text.configure(state="disabled")
        
        self.copy_btn.configure(state="normal")
        self.last_license_key = license_key
    
    def _on_copy(self):
        """Copy the license key to clipboard."""
        if hasattr(self, 'last_license_key'):
            self.clipboard_clear()
            self.clipboard_append(self.last_license_key)
            messagebox.showinfo("Copied", "License key copied to clipboard!")
            self.status_label.configure(text="License key copied to clipboard", text_color=("#1f6aa5", "#3b8ed0"))


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
