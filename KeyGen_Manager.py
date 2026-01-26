#!/usr/bin/env python3
"""
KeyGen Manager - Admin Panel for CourseSmith AI License Management.

This tool provides a comprehensive admin interface to manage licenses stored in Supabase.
Features include viewing all licenses, banning/unbanning, copying keys/HWIDs, and deleting licenses.

ADMIN USE ONLY - DO NOT DISTRIBUTE

Features:
- Interactive Treeview showing all licenses from Supabase
- Right-click context menu for quick actions
- Copy HWID/Key to clipboard
- Delete licenses from database
- Ban/Unban license toggle
- Refresh button to reload data

Supabase Connection:
- URL: https://spfwfyjpexktgnusgyib.supabase.co
- Uses supabase==2.25.1
"""

import os
import sys
import re
import customtkinter as ctk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from supabase import create_client, Client

# Try to import license_guard for key generation (preserving existing logic)
try:
    from license_guard import generate_key, get_hwid
    LICENSE_GUARD_AVAILABLE = True
except ImportError:
    LICENSE_GUARD_AVAILABLE = False
    print("Warning: license_guard not available. Key generation disabled.")


# Supabase configuration
SUPABASE_URL = "https://spfwfyjpexktgnusgyib.supabase.co"
SUPABASE_KEY = "sb_publishable_tmwenU0VyOChNWKG90X_bw_HYf9X5kR"


class LicenseManagerApp(ctk.CTk):
    """Admin Panel for managing licenses in Supabase."""
    
    def __init__(self):
        """Initialize the License Manager application."""
        super().__init__()
        
        # Window configuration
        self.title("CourseSmith AI - License Manager (Admin Panel)")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        
        # Set icon
        try:
            self.iconbitmap("resources/admin_keygen.ico")
        except Exception as e:
            print(f"Warning: Could not load icon: {e}")
        
        # Set appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize Supabase client
        self.supabase: Optional[Client] = None
        self.connect_to_supabase()
        
        # Data storage
        self.licenses: List[Dict[str, Any]] = []
        
        # Create UI
        self._create_ui()
        
        # Load initial data
        self.refresh_licenses()
    
    def connect_to_supabase(self):
        """Connect to Supabase database."""
        try:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("✓ Connected to Supabase successfully")
        except Exception as e:
            messagebox.showerror(
                "Connection Error",
                f"Failed to connect to Supabase:\n{str(e)}"
            )
            print(f"✗ Supabase connection failed: {e}")
    
    def _create_ui(self):
        """Create the main UI layout."""
        # Header Frame
        header_frame = ctk.CTkFrame(self, height=80, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔐 CourseSmith AI - License Manager",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0")
        )
        title_label.pack(pady=15)
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Admin Panel - Manage Licenses in Supabase",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack()
        
        # Control Panel Frame
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Refresh Button
        self.refresh_btn = ctk.CTkButton(
            control_frame,
            text="🔄 Refresh Licenses",
            command=self.refresh_licenses,
            width=150,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.refresh_btn.pack(side="left", padx=5)
        
        # Status Label
        self.status_label = ctk.CTkLabel(
            control_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=20)
        
        # Count Label
        self.count_label = ctk.CTkLabel(
            control_frame,
            text="Total Licenses: 0",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.count_label.pack(side="right", padx=5)
        
        # Add License Form Frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Form Title
        form_title = ctk.CTkLabel(
            form_frame,
            text="➕ Add New License",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0")
        )
        form_title.grid(row=0, column=0, columnspan=4, pady=(10, 15), sticky="w", padx=10)
        
        # Email Input
        email_label = ctk.CTkLabel(
            form_frame,
            text="Email:",
            font=ctk.CTkFont(size=12)
        )
        email_label.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="e")
        
        self.email_entry = ctk.CTkEntry(
            form_frame,
            width=250,
            placeholder_text="user@example.com"
        )
        self.email_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        
        # Duration Input
        duration_label = ctk.CTkLabel(
            form_frame,
            text="Duration (days):",
            font=ctk.CTkFont(size=12)
        )
        duration_label.grid(row=1, column=2, padx=(20, 5), pady=10, sticky="e")
        
        self.duration_entry = ctk.CTkEntry(
            form_frame,
            width=120,
            placeholder_text="30"
        )
        self.duration_entry.grid(row=1, column=3, padx=5, pady=10, sticky="w")
        
        # Generate Button
        self.generate_btn = ctk.CTkButton(
            form_frame,
            text="🔑 Generate & Add to Database",
            command=self._generate_and_add_license,
            width=250,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#2fa572", "#2fa572"),
            hover_color=("#248a5c", "#248a5c")
        )
        self.generate_btn.grid(row=1, column=4, padx=20, pady=10)
        
        # Table Frame
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create Treeview for licenses
        self._create_treeview(table_frame)
        
        # Context Menu
        self._create_context_menu()
    
    def _create_treeview(self, parent):
        """Create the Treeview widget for displaying licenses."""
        # Create frame for treeview and scrollbar
        tree_container = ctk.CTkFrame(parent)
        tree_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Style for Treeview (native tkinter widget styled for dark mode)
        style = ttk.Style()
        style.theme_use("default")
        
        # Configure Treeview colors for dark mode
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            borderwidth=0
        )
        style.configure("Treeview.Heading", background="#1f6aa5", foreground="white", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#1f6aa5")])
        
        # Create scrollbars
        vsb = ttk.Scrollbar(tree_container, orient="vertical")
        hsb = ttk.Scrollbar(tree_container, orient="horizontal")
        
        # Create Treeview
        self.tree = ttk.Treeview(
            tree_container,
            columns=("id", "email", "key", "hwid", "tier", "duration", "is_banned", "valid_until", "subscription_id", "created_at"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        # Configure scrollbars
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Define columns
        columns_config = [
            ("id", "ID", 60),
            ("email", "Email", 180),
            ("key", "License Key", 150),
            ("hwid", "HWID", 130),
            ("tier", "Tier", 80),
            ("duration", "Duration", 90),
            ("is_banned", "Banned", 70),
            ("valid_until", "Expires", 140),
            ("subscription_id", "Sub ID", 100),
            ("created_at", "Created", 130)
        ]
        
        for col, heading, width in columns_config:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, minwidth=50)
        
        # Pack widgets
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Bind right-click event
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        # Bind double-click for quick ban toggle
        self.tree.bind("<Double-1>", self._toggle_ban_quick)
    
    def _create_context_menu(self):
        """Create right-click context menu."""
        self.context_menu = ctk.CTkFrame(self, fg_color="#2b2b2b", border_width=2, border_color="#1f6aa5")
        self.context_menu.withdraw = lambda: self.context_menu.place_forget()
        
        # Menu items
        menu_items = [
            ("📋 Copy HWID", self._copy_hwid),
            ("🔑 Copy Key", self._copy_key),
            ("📅 Extend +30 Days", self._set_expiration_30days),
            ("🚫 Ban License", self._ban_license),
            ("✅ Unban License", self._unban_license),
            ("❌ Delete License", self._delete_license),
        ]
        
        for text, command in menu_items:
            btn = ctk.CTkButton(
                self.context_menu,
                text=text,
                command=command,
                fg_color="transparent",
                hover_color="#1f6aa5",
                anchor="w",
                height=30,
                font=ctk.CTkFont(size=12)
            )
            btn.pack(fill="x", padx=5, pady=2)
        
        # Hide menu when clicking elsewhere
        self.bind("<Button-1>", lambda e: self.context_menu.place_forget())
    
    def _show_context_menu(self, event):
        """Show context menu at cursor position."""
        # Select item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty())
    
    def _get_selected_license(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected license data."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a license first.")
            return None
        
        item = selection[0]
        values = self.tree.item(item, "values")
        
        if not values:
            return None
        
        # Map values back to license dict
        license_data = {
            "id": values[0],
            "email": values[1],
            "key": values[2],  # This will work for both 'key' and 'license_key'
            "license_key": values[2],  # Add for compatibility
            "hwid": values[3],
            "tier": values[4],
            "duration": values[5],
            "is_banned": str(values[6]).lower() == "yes",  # Robust boolean conversion
            "valid_until": values[7],
            "subscription_id": values[8],
            "created_at": values[9]
        }
        
        return license_data
    
    def _copy_hwid(self):
        """Copy selected HWID to clipboard."""
        license_data = self._get_selected_license()
        if license_data:
            hwid = license_data["hwid"]
            self.clipboard_clear()
            self.clipboard_append(hwid)
            self.status_label.configure(text=f"✓ HWID copied: {hwid[:20]}...")
            self.context_menu.place_forget()
    
    def _copy_key(self):
        """Copy selected license key to clipboard."""
        license_data = self._get_selected_license()
        if license_data:
            key = license_data["key"]
            self.clipboard_clear()
            self.clipboard_append(key)
            self.status_label.configure(text=f"✓ Key copied: {key}")
            self.context_menu.place_forget()
    
    def _set_expiration_30days(self):
        """Set expiration date to +30 days from now for the selected license."""
        license_data = self._get_selected_license()
        if not license_data:
            return
        
        # Calculate expiration date (30 days from now in UTC)
        from datetime import timezone
        expiration_date = datetime.now(timezone.utc) + timedelta(days=30)
        expiration_iso = expiration_date.isoformat()
        
        # Confirm action
        confirm = messagebox.askyesno(
            "Set Expiration Date",
            f"Set expiration date for {license_data['email']}?\n\nKey: {license_data['key']}\n\nExpires: {expiration_date.strftime('%Y-%m-%d %H:%M')} UTC\n\n(+30 days from now)"
        )
        
        if confirm:
            try:
                # Update in Supabase
                self.supabase.table("licenses").update({"valid_until": expiration_iso}).eq("id", license_data["id"]).execute()
                messagebox.showinfo("Success", f"Expiration date set to {expiration_date.strftime('%Y-%m-%d %H:%M')} UTC")
                self.status_label.configure(text=f"✓ Expiration set for: {license_data['email']}")
                self.refresh_licenses()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set expiration date:\n{str(e)}")
        
        self.context_menu.place_forget()
    
    def _update_ban_status(self, license_id: str, email: str, is_banned: bool) -> bool:
        """
        Update the ban status of a license in Supabase.
        
        Args:
            license_id: The ID of the license to update
            email: The email associated with the license (for status message)
            is_banned: True to ban, False to unban
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.supabase.table("licenses").update({"is_banned": is_banned}).eq("id", license_id).execute()
            action = "banned" if is_banned else "unbanned"
            self.status_label.configure(text=f"✓ {action.capitalize()}: {email}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update ban status:\n{str(e)}")
            return False
    
    def _ban_license(self):
        """Ban the selected license."""
        license_data = self._get_selected_license()
        if not license_data:
            return
        
        if license_data["is_banned"]:
            messagebox.showinfo("Already Banned", "This license is already banned.")
            return
        
        # Confirm action
        confirm = messagebox.askyesno(
            "Ban License",
            f"Ban license for {license_data['email']}?\n\nKey: {license_data['key']}\n\nThe user will be blocked from using the app."
        )
        
        if confirm:
            if self._update_ban_status(license_data["id"], license_data["email"], True):
                messagebox.showinfo("Success", "License banned successfully.")
                self.refresh_licenses()
        
        self.context_menu.place_forget()
    
    def _unban_license(self):
        """Unban the selected license."""
        license_data = self._get_selected_license()
        if not license_data:
            return
        
        if not license_data["is_banned"]:
            messagebox.showinfo("Not Banned", "This license is not banned.")
            return
        
        # Confirm action
        confirm = messagebox.askyesno(
            "Unban License",
            f"Unban license for {license_data['email']}?\n\nKey: {license_data['key']}\n\nThe user will regain access to the app."
        )
        
        if confirm:
            if self._update_ban_status(license_data["id"], license_data["email"], False):
                messagebox.showinfo("Success", "License unbanned successfully.")
                self.refresh_licenses()
        
        self.context_menu.place_forget()
    
    def _delete_license(self):
        """Delete the selected license from Supabase."""
        license_data = self._get_selected_license()
        if not license_data:
            return
        
        # Confirm action
        confirm = messagebox.askyesno(
            "Delete License",
            f"PERMANENTLY DELETE this license?\n\nEmail: {license_data['email']}\nKey: {license_data['key']}\n\n⚠️ This action cannot be undone!"
        )
        
        if confirm:
            try:
                # Delete from Supabase
                self.supabase.table("licenses").delete().eq("id", license_data["id"]).execute()
                messagebox.showinfo("Success", "License deleted successfully.")
                self.status_label.configure(text=f"✓ Deleted: {license_data['email']}")
                self.refresh_licenses()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete license:\n{str(e)}")
        
        self.context_menu.place_forget()
    
    def _toggle_ban_quick(self, event):
        """Quick toggle ban status on double-click."""
        license_data = self._get_selected_license()
        if not license_data:
            return
        
        new_status = not license_data["is_banned"]
        if self._update_ban_status(license_data["id"], license_data["email"], new_status):
            self.refresh_licenses()
    
    def _generate_and_add_license(self):
        """Generate a new license key and add it to the database."""
        # Get input values
        email = self.email_entry.get().strip()
        duration_str = self.duration_entry.get().strip()
        
        # Validate email
        if not email:
            messagebox.showerror("Validation Error", "Please enter an email address.")
            return
        
        # Simple email validation pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            messagebox.showerror("Validation Error", "Please enter a valid email address.")
            return
        
        # Validate duration
        try:
            duration_days = int(duration_str)
            if duration_days <= 0:
                raise ValueError("Duration must be positive")
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid duration (positive integer).")
            return
        
        # Check if license_guard is available
        if not LICENSE_GUARD_AVAILABLE:
            messagebox.showerror(
                "Error",
                "License generation is not available.\nlicense_guard module not found."
            )
            return
        
        try:
            # Disable button during generation
            self.generate_btn.configure(state="disabled")
            self.status_label.configure(text="Generating license...")
            
            # Generate license key using license_guard
            # Note: We use 'trial' tier and calculate custom expiration based on user input
            license_key, _ = generate_key(email, tier='trial', duration='lifetime')
            
            # Calculate valid_until based on duration_days (overrides generate_key's expiration)
            valid_until = datetime.now(timezone.utc) + timedelta(days=duration_days)
            valid_until_iso = valid_until.isoformat()
            
            # Insert into Supabase with new schema columns
            license_data = {
                'email': email,
                'license_key': license_key,  # Using 'license_key' column
                'hwid': None,  # No HWID initially
                'is_banned': False,  # Not banned by default
                'valid_until': valid_until_iso,  # Expiration date
                'whop_user_id': None,  # No Whop user ID initially
                'tier': 'trial',  # Default tier
                'duration': f"{duration_days}_days",  # Duration as string
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert into Supabase
            response = self.supabase.table("licenses").insert(license_data).execute()
            
            # Clear input fields
            self.email_entry.delete(0, 'end')
            self.duration_entry.delete(0, 'end')
            
            # Show success message
            messagebox.showinfo(
                "Success",
                f"License generated successfully!\n\n"
                f"Email: {email}\n"
                f"License Key: {license_key}\n"
                f"Valid Until: {valid_until.strftime('%Y-%m-%d %H:%M')} UTC\n\n"
                f"The license key has been copied to clipboard."
            )
            
            # Copy key to clipboard
            self.clipboard_clear()
            self.clipboard_append(license_key)
            
            self.status_label.configure(text=f"✓ License created: {license_key}")
            
            # Refresh the list
            self.refresh_licenses()
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to generate license:\n{str(e)}\n\nPlease check Supabase configuration and table schema."
            )
            self.status_label.configure(text=f"✗ Failed to generate license")
        finally:
            self.generate_btn.configure(state="normal")
    
    def refresh_licenses(self):
        """Refresh the license list from Supabase."""
        self.status_label.configure(text="Loading licenses...")
        self.refresh_btn.configure(state="disabled")
        
        # Run in thread to prevent UI freeze
        thread = threading.Thread(target=self._fetch_licenses_thread, daemon=True)
        thread.start()
    
    def _fetch_licenses_thread(self):
        """Fetch licenses from Supabase (runs in background thread)."""
        try:
            if not self.supabase:
                raise Exception("Not connected to Supabase")
            
            # Query all licenses
            response = self.supabase.table("licenses").select("*").order("created_at", desc=True).execute()
            
            self.licenses = response.data if response.data else []
            
            # Update UI on main thread
            self.after(0, self._update_treeview)
            self.after(0, lambda: self.status_label.configure(text=f"✓ Loaded {len(self.licenses)} licenses"))
            
        except Exception as e:
            error_msg = f"Failed to load licenses: {str(e)}"
            self.after(0, lambda: self.status_label.configure(text=f"✗ {error_msg}"))
            self.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.after(0, lambda: self.refresh_btn.configure(state="normal"))
    
    def _update_treeview(self):
        """Update the Treeview with fetched licenses."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert licenses
        for license_data in self.licenses:
            # Format data for display
            license_id = license_data.get("id", "")
            email = license_data.get("email", "N/A")
            # Try both 'license_key' and 'key' columns for compatibility
            key = license_data.get("license_key") or license_data.get("key", "N/A")
            hwid = license_data.get("hwid", "N/A")
            tier = license_data.get("tier", "N/A")
            duration = license_data.get("duration", "N/A")
            is_banned = "Yes" if license_data.get("is_banned", False) else "No"
            
            # Format valid_until timestamp
            valid_until = license_data.get("valid_until", "N/A")
            if valid_until and valid_until != "N/A":
                try:
                    dt = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                    valid_until = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            # Get subscription_id or whop_user_id
            subscription_id = license_data.get("subscription_id") or license_data.get("whop_user_id", "N/A")
            
            # Format created_at timestamp
            created_at = license_data.get("created_at", "N/A")
            if created_at != "N/A":
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            # Insert into treeview
            self.tree.insert(
                "",
                "end",
                values=(license_id, email, key, hwid, tier, duration, is_banned, valid_until, subscription_id, created_at)
            )
        
        # Update count
        self.count_label.configure(text=f"Total Licenses: {len(self.licenses)}")


def main():
    """Main entry point for the License Manager."""
    print("=" * 70)
    print("  CourseSmith AI - License Manager (Admin Panel)")
    print("  Version 1.0.0")
    print("  ADMIN USE ONLY - DO NOT DISTRIBUTE")
    print("=" * 70)
    print()
    
    # Create and run the application
    app = LicenseManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
