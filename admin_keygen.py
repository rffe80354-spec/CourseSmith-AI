#!/usr/bin/env python3
"""
Admin Key Generator - Vendor Tool for Faleovad AI Enterprise.
GUI-based version for PyInstaller --noconsole mode compatibility.

This script is for the SELLER only to generate tiered license keys for buyers.

Tiers:
- Standard ($59): Basic features, no custom branding
- Extended ($249): Full features, custom logo and website support

Features:
- GUI Mode: Enter buyer email to instantly generate Standard license
- God Mode: Enter the master password to access tier selection
- Supabase Integration: Automatically syncs keys to cloud database
"""

import sys
import os
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox, scrolledtext
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
    """Admin Keygen GUI Application."""
    
    def __init__(self):
        """Initialize the admin keygen application."""
        super().__init__()
        
        # Configure window
        self.title("CourseSmith License Generator")
        self.geometry("900x700")
        self.resizable(False, False)
        
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"900x700+{x}+{y}")
        
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
        
        # Create UI
        self._create_ui()
        
        # Load key history on startup
        self.after(500, self._refresh_key_history)
        
    def _create_ui(self):
        """Create the main UI."""
        # Main container with two columns
        main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left column - Key Generator
        left_column = ctk.CTkFrame(main_frame, corner_radius=10)
        left_column.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        # Header
        header_frame = ctk.CTkFrame(left_column, corner_radius=10, fg_color=("#2b2b2b", "#1a1a1a"))
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔑 License Key Generator",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=15)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Vendor Tool - DO NOT DISTRIBUTE",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray50")
        )
        subtitle_label.pack(pady=(0, 15))
        
        # Input section
        input_frame = ctk.CTkFrame(left_column, corner_radius=10)
        input_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Email input
        email_label = ctk.CTkLabel(
            input_frame,
            text="Buyer Email:",
            font=ctk.CTkFont(size=14)
        )
        email_label.pack(pady=(15, 5), padx=15, anchor="w")
        
        self.email_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="buyer@example.com or God Mode Code",
            font=ctk.CTkFont(size=12),
            height=35
        )
        self.email_entry.pack(fill="x", padx=15, pady=(0, 10))
        self.email_entry.bind("<Return>", lambda e: self._on_generate())
        
        # Tier selection (initially hidden)
        self.tier_frame = ctk.CTkFrame(input_frame, corner_radius=10, fg_color="transparent")
        self.tier_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        tier_label = ctk.CTkLabel(
            self.tier_frame,
            text="License Tier (God Mode):",
            font=ctk.CTkFont(size=14)
        )
        tier_label.pack(pady=(0, 8), anchor="w")
        
        self.tier_var = ctk.StringVar(value="standard")
        
        tier_radio1 = ctk.CTkRadioButton(
            self.tier_frame,
            text="Standard ($59) - No Branding",
            variable=self.tier_var,
            value="standard",
            font=ctk.CTkFont(size=12)
        )
        tier_radio1.pack(anchor="w", pady=3)
        
        tier_radio2 = ctk.CTkRadioButton(
            self.tier_frame,
            text="Extended ($249) - Full Branding",
            variable=self.tier_var,
            value="extended",
            font=ctk.CTkFont(size=12)
        )
        tier_radio2.pack(anchor="w", pady=3)
        
        # Hide tier selection initially
        self.tier_frame.pack_forget()
        
        # Generate button
        self.generate_btn = ctk.CTkButton(
            input_frame,
            text="Generate License Key",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._on_generate
        )
        self.generate_btn.pack(fill="x", padx=15, pady=(0, 15))
        
        # Output textbox
        output_label = ctk.CTkLabel(
            input_frame,
            text="Generated License:",
            font=ctk.CTkFont(size=14)
        )
        output_label.pack(pady=(10, 5), padx=15, anchor="w")
        
        self.output_text = ctk.CTkTextbox(
            input_frame,
            font=ctk.CTkFont(family="Courier New", size=11),
            wrap="word",
            state="disabled",
            height=120
        )
        self.output_text.pack(fill="x", padx=15, pady=(0, 10))
        
        # Copy button
        self.copy_btn = ctk.CTkButton(
            input_frame,
            text="Copy License Key",
            font=ctk.CTkFont(size=12),
            height=30,
            command=self._on_copy,
            state="disabled"
        )
        self.copy_btn.pack(fill="x", padx=15, pady=(0, 15))
        
        # Status bar
        self.status_label = ctk.CTkLabel(
            left_column,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray50")
        )
        self.status_label.pack(pady=(5, 0))
        
        # Right column - Key History
        right_column = ctk.CTkFrame(main_frame, corner_radius=10)
        right_column.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        
        # Key History Header
        history_header = ctk.CTkFrame(right_column, corner_radius=10, fg_color=("#2b2b2b", "#1a1a1a"))
        history_header.pack(fill="x", pady=(0, 15))
        
        history_title = ctk.CTkLabel(
            history_header,
            text="📋 Key History (Last 10)",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        history_title.pack(pady=15)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            right_column,
            text="🔄 Refresh from Supabase",
            font=ctk.CTkFont(size=12),
            height=35,
            command=self._refresh_key_history
        )
        refresh_btn.pack(fill="x", padx=15, pady=(0, 10))
        
        # Key history textbox
        self.history_text = ctk.CTkTextbox(
            right_column,
            font=ctk.CTkFont(family="Courier New", size=10),
            wrap="word",
            state="disabled"
        )
        self.history_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
    def _on_generate(self):
        """Handle generate button click with Supabase sync."""
        email_input = self.email_entry.get().strip()
        
        if not email_input:
            messagebox.showerror("Error", "Please enter a buyer email or God Mode code.")
            return
        
        # Check for God Mode trigger
        if email_input == GOD_MODE_CODE:
            if not self.god_mode:
                self.god_mode = True
                self.tier_frame.pack(fill="x", padx=15, pady=(0, 10), before=self.generate_btn)
                self.status_label.configure(text="⚡ GOD MODE ACTIVATED ⚡", text_color=("#ff6600", "#ff8800"))
                messagebox.showinfo("God Mode", "God Mode Activated! You can now select license tiers.")
                self.email_entry.delete(0, "end")
                return
            else:
                messagebox.showwarning("God Mode", "God Mode is already active.")
                return
        
        # Validate email
        if '@' not in email_input or '.' not in email_input:
            messagebox.showerror("Error", "Please enter a valid email address.")
            return
        
        # Get tier (standard by default, or selected tier in god mode)
        tier = self.tier_var.get() if self.god_mode else 'standard'
        
        # Generate license key using the actual generate_key function
        try:
            # Default to lifetime duration
            duration = 'lifetime'
            license_key, expires_at = generate_key(email_input, tier, duration)
            
            # Sync to Supabase database
            sync_success = self._sync_to_supabase(email_input, license_key, tier, expires_at)
            
            # Display the license
            self._display_license(email_input, tier, license_key, sync_success)
            
            # Update status
            sync_status = "✓ Synced to Supabase" if sync_success else "⚠ Local only (Supabase unavailable)"
            self.status_label.configure(
                text=f"License generated for {email_input} - {sync_status}",
                text_color=("#1f6aa5", "#3b8ed0")
            )
            
            # Refresh key history after generation
            self.after(500, self._refresh_key_history)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate license: {str(e)}")
            self.status_label.configure(text="Generation failed", text_color=("red", "red"))
    
    def _sync_to_supabase(self, email, license_key, tier, expires_at):
        """
        Sync generated license to Supabase database.
        
        Args:
            email: Buyer email
            license_key: Generated license key
            tier: License tier
            expires_at: Expiration date (ISO format) or None for lifetime
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        client = get_supabase_client()
        if not client:
            print("Supabase client not available")
            return False
        
        try:
            # Prepare license data
            license_data = {
                'license_key': license_key,
                'email': email,
                'tier': tier,
                'valid_until': expires_at,
                'is_banned': False,
                'used_hwids': [],  # Empty array for new licenses
                'max_devices': 3,  # Default to 3 devices
                'created_at': datetime.now().isoformat()
            }
            
            # Insert into Supabase
            response = client.table("licenses").insert(license_data).execute()
            
            if response.data:
                print(f"Successfully synced license {license_key} to Supabase")
                return True
            else:
                print("Failed to sync to Supabase: No data returned")
                return False
                
        except Exception as e:
            print(f"Error syncing to Supabase: {e}")
            return False
    
    def _refresh_key_history(self):
        """Refresh the key history from Supabase."""
        client = get_supabase_client()
        
        if not client:
            self.history_text.configure(state="normal")
            self.history_text.delete("1.0", "end")
            self.history_text.insert("1.0", "⚠ Supabase not available\n\nCannot fetch key history.")
            self.history_text.configure(state="disabled")
            return
        
        try:
            # Fetch last 10 licenses from Supabase, ordered by creation date
            response = client.table("licenses").select("*").order("created_at", desc=True).limit(10).execute()
            
            if response.data:
                # Format the history
                history = "=" * 60 + "\n"
                history += "RECENT LICENSE KEYS (Last 10)\n"
                history += "=" * 60 + "\n\n"
                
                for idx, license_record in enumerate(response.data, 1):
                    email = license_record.get('email', 'N/A')
                    key = license_record.get('license_key', 'N/A')
                    tier = license_record.get('tier', 'N/A')
                    created = license_record.get('created_at', 'N/A')
                    
                    # Parse and format date
                    try:
                        if created != 'N/A':
                            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            created = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                    
                    history += f"#{idx}. {email}\n"
                    history += f"    Key:  {key}\n"
                    history += f"    Tier: {tier.upper()}\n"
                    history += f"    Date: {created}\n"
                    history += "-" * 60 + "\n\n"
                
                self.history_text.configure(state="normal")
                self.history_text.delete("1.0", "end")
                self.history_text.insert("1.0", history.strip())
                self.history_text.configure(state="disabled")
            else:
                self.history_text.configure(state="normal")
                self.history_text.delete("1.0", "end")
                self.history_text.insert("1.0", "No licenses found in database.")
                self.history_text.configure(state="disabled")
                
        except Exception as e:
            self.history_text.configure(state="normal")
            self.history_text.delete("1.0", "end")
            self.history_text.insert("1.0", f"Error fetching key history:\n\n{str(e)}")
            self.history_text.configure(state="disabled")
    
    def _display_license(self, email, tier, license_key, sync_success):
        """Display the generated license."""
        tier_label = "Extended ($249)" if tier == 'extended' else "Standard ($59)"
        sync_status = "✓ Synced to Supabase" if sync_success else "⚠ Local only"
        
        output = f"""
{'=' * 60}
✓ License Generated Successfully!
{'=' * 60}

Email:   {email}
Tier:    {tier_label}
Key:     {license_key}
Status:  {sync_status}

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
