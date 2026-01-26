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
import secrets
import customtkinter as ctk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from supabase import create_client, Client


# Supabase configuration
SUPABASE_URL = "https://spfwfyjpexktgnusgyib.supabase.co"
SUPABASE_KEY = "sb_publishable_tmwenU0VyOChNWKG90X_bw_HYf9X5kR"

# Tier configuration for the new system
TIER_CONFIG = {
    "Free Trial": {
        "days": 3,
        "page_limit": 10
    },
    "Standard": {
        "days": 30,
        "page_limit": 50
    },
    "Extended": {
        "days": 30,
        "page_limit": 100
    },
    "Lifetime": {
        "days": 36135,  # 99 years (99 * 365.25 accounting for leap years)
        "page_limit": 999999
    }
}


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
        
        # Create License Form Frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Form Title
        form_title = ctk.CTkLabel(
            form_frame,
            text="➕ Create License",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0")
        )
        form_title.grid(row=0, column=0, columnspan=4, pady=(10, 15), sticky="w", padx=10)
        
        # Email Input
        email_label = ctk.CTkLabel(
            form_frame,
            text="User Email:",
            font=ctk.CTkFont(size=12)
        )
        email_label.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="e")
        
        self.email_entry = ctk.CTkEntry(
            form_frame,
            width=250,
            placeholder_text="user@example.com"
        )
        self.email_entry.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        
        # Tier Dropdown
        tier_label = ctk.CTkLabel(
            form_frame,
            text="License Tier:",
            font=ctk.CTkFont(size=12)
        )
        tier_label.grid(row=1, column=2, padx=(20, 5), pady=10, sticky="e")
        
        self.tier_dropdown = ctk.CTkComboBox(
            form_frame,
            width=150,
            values=["Free Trial", "Standard", "Extended", "Lifetime"],
            state="readonly"
        )
        self.tier_dropdown.set("Free Trial")  # Default selection
        self.tier_dropdown.grid(row=1, column=3, padx=5, pady=10, sticky="w")
        
        # Generate Button
        self.generate_btn = ctk.CTkButton(
            form_frame,
            text="🔑 Generate & Save Key",
            command=self._generate_and_add_license,
            width=200,
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
            columns=("id", "email", "key", "tier", "limit", "valid_until", "created_at"),
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
            ("email", "Email", 200),
            ("key", "License Key", 180),
            ("tier", "Tier", 120),
            ("limit", "Page Limit", 100),
            ("valid_until", "Valid Until", 150),
            ("created_at", "Created", 150)
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
    
    def _create_context_menu(self):
        """Create right-click context menu."""
        self.context_menu = ctk.CTkFrame(self, fg_color="#2b2b2b", border_width=2, border_color="#1f6aa5")
        self.context_menu.withdraw = lambda: self.context_menu.place_forget()
        
        # Menu items (updated for new schema)
        menu_items = [
            ("🔑 Copy Key", self._copy_key),
            ("📅 Extend +30 Days", self._set_expiration_30days),
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
        
        # Map values back to license dict (updated for new schema)
        license_data = {
            "id": values[0],
            "email": values[1],
            "license_key": values[2],
            "key": values[2],  # Alias for compatibility
            "tier": values[3],
            "page_limit": values[4],
            "valid_until": values[5],
            "created_at": values[6]
        }
        
        return license_data
    
    def _copy_key(self):
        """Copy selected license key to clipboard."""
        license_data = self._get_selected_license()
        if license_data:
            key = license_data["license_key"]
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
        expiration_date = datetime.now(timezone.utc) + timedelta(days=30)
        expiration_iso = expiration_date.isoformat()
        
        # Confirm action
        confirm = messagebox.askyesno(
            "Set Expiration Date",
            f"Set expiration date for {license_data['email']}?\n\nKey: {license_data['license_key']}\n\nExpires: {expiration_date.strftime('%Y-%m-%d %H:%M')} UTC\n\n(+30 days from now)"
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
    
    def _delete_license(self):
        """Delete the selected license from Supabase."""
        license_data = self._get_selected_license()
        if not license_data:
            return
        
        # Confirm action
        confirm = messagebox.askyesno(
            "Delete License",
            f"PERMANENTLY DELETE this license?\n\nEmail: {license_data['email']}\nKey: {license_data['license_key']}\n\n⚠️ This action cannot be undone!"
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
    
    def _generate_and_add_license(self):
        """Generate a new license key and add it to the database with tier-based logic."""
        # Get input values
        email = self.email_entry.get().strip()
        tier = self.tier_dropdown.get()
        
        # Validate email
        if not email:
            messagebox.showerror("Validation Error", "Please enter an email address.")
            return
        
        # Simple email validation pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            messagebox.showerror("Validation Error", "Please enter a valid email address.")
            return
        
        # Validate tier selection
        if tier not in TIER_CONFIG:
            messagebox.showerror("Validation Error", "Please select a valid license tier.")
            return
        
        try:
            # Disable button during generation
            self.generate_btn.configure(state="disabled")
            self.status_label.configure(text="Generating license...")
            
            # Generate a secure license key using secrets module
            # Format: CS-[32 random hex characters]
            license_key = f"CS-{secrets.token_hex(16)}"
            
            # Get tier configuration
            tier_settings = TIER_CONFIG[tier]
            days = tier_settings["days"]
            page_limit = tier_settings["page_limit"]
            
            # Calculate valid_until based on tier
            valid_until = datetime.now(timezone.utc) + timedelta(days=days)
            valid_until_iso = valid_until.isoformat()
            
            # Get current timestamp for created_at
            created_at = datetime.now(timezone.utc).isoformat()
            
            # Prepare license data for insertion (new schema - NO duration column)
            license_data = {
                'email': email,
                'license_key': license_key,
                'tier': tier,
                'page_limit': page_limit,
                'valid_until': valid_until_iso,
                'created_at': created_at
            }
            
            # Insert into Supabase
            response = self.supabase.table("licenses").insert(license_data).execute()
            
            # Clear input fields
            self.email_entry.delete(0, 'end')
            self.tier_dropdown.set("Free Trial")  # Reset to default
            
            # Show success message (truncate key at 35 chars for display readability)
            key_display = license_key if len(license_key) <= 35 else license_key[:35] + "..."
            messagebox.showinfo(
                "Success",
                f"License generated successfully!\n\n"
                f"Email: {email}\n"
                f"Tier: {tier}\n"
                f"Page Limit: {page_limit}\n"
                f"Valid Until: {valid_until.strftime('%Y-%m-%d %H:%M')} UTC\n"
                f"License Key: {key_display}\n\n"
                f"The full license key has been copied to clipboard."
            )
            
            # Copy key to clipboard
            self.clipboard_clear()
            self.clipboard_append(license_key)
            
            self.status_label.configure(text=f"✓ License created for: {email}")
            
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
            # Format data for display (new schema)
            license_id = license_data.get("id", "")
            email = license_data.get("email", "N/A")
            # Try both 'license_key' and 'key' columns for compatibility
            key = license_data.get("license_key") or license_data.get("key", "N/A")
            tier = license_data.get("tier", "N/A")
            page_limit = license_data.get("page_limit", "N/A")
            
            # Format valid_until timestamp
            valid_until = license_data.get("valid_until", "N/A")
            if valid_until and valid_until != "N/A":
                try:
                    dt = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                    valid_until = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            # Format created_at timestamp
            created_at = license_data.get("created_at", "N/A")
            if created_at not in (None, "", "N/A"):
                try:
                    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            # Insert into treeview with new column structure
            self.tree.insert(
                "",
                "end",
                values=(license_id, email, key, tier, page_limit, valid_until, created_at)
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
