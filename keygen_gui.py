#!/usr/bin/env python3
"""
Admin Key Generator GUI - Enterprise Vendor Tool for Faleovad AI.

CustomTkinter-based graphical interface for generating and managing tiered license keys.
This tool is for SELLERS ONLY to generate license keys for buyers.

Enterprise Features:
- Dark mode professional interface with animations
- Email input validation
- License tier selection (Standard vs Extended)
- Duration selection (Lifetime / 1 Month / 1 Year)
- SQLite database integration for key tracking
- HWID binding support
- Key revocation/management tab
- Copy to clipboard functionality
- Responsive layout (no overflow bugs)

Tiers:
- Standard ($59): Basic features, no custom branding
- Extended ($249): Full features, custom logo and website support

Usage:
    python keygen_gui.py
"""

import os
import sys
import customtkinter as ctk
from tkinter import messagebox
import threading
import time
from datetime import datetime
from typing import Optional

from utils import resource_path
from license_guard import generate_key, get_hwid
from database_manager import (
    create_license, get_license_by_key, search_licenses,
    revoke_license, reactivate_license, list_all_licenses,
    get_license_stats, is_license_expired
)


class SplashScreen(ctk.CTkToplevel):
    """Splash screen with loading animation."""
    
    def __init__(self, parent):
        """Initialize splash screen."""
        super().__init__(parent)
        
        # Configure window
        self.title("")
        self.geometry("500x350")
        self.resizable(False, False)
        
        # Remove window decorations
        self.overrideredirect(True)
        
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (350 // 2)
        self.geometry(f"500x350+{x}+{y}")
        
        # Create UI
        self._create_ui()
        
        # Make sure it's on top
        self.lift()
        self.focus_force()
        
    def _create_ui(self):
        """Create splash screen UI."""
        # Main frame with depth
        main_frame = ctk.CTkFrame(self, corner_radius=20, border_width=3, border_color="#1f6aa5")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Logo/Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔐",
            font=ctk.CTkFont(size=80)
        )
        title_label.pack(pady=(50, 10))
        
        app_name_label = ctk.CTkLabel(
            main_frame,
            text="Faleovad AI Enterprise",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0")
        )
        app_name_label.pack(pady=(0, 5))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="License Key Generator",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(
            main_frame,
            width=350,
            height=15,
            corner_radius=10,
            mode="indeterminate"
        )
        self.progress.pack(pady=(0, 15))
        self.progress.start()
        
        # Status label
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Initializing...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(pady=(0, 30))
    
    def update_status(self, text):
        """Update status message."""
        self.status_label.configure(text=text)
        self.update()
    
    def close_splash(self):
        """Close splash screen with fade effect."""
        self.progress.stop()
        self.destroy()


class KeygenApp(ctk.CTk):
    """Admin License Key Generator GUI Application with Enterprise Features."""
    
    def __init__(self):
        """Initialize the keygen application."""
        super().__init__()
        
        # Window configuration
        self.title("Faleovad AI Enterprise - License Key Generator")
        self.geometry("900x750")
        self.minsize(800, 650)
        
        # Set window icon if it exists (PyInstaller compatible)
        icon_path = resource_path("resources/admin_keygen.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass  # Icon not critical, continue without it
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Hide main window initially
        self.withdraw()
        
        # Show splash screen
        self._show_splash()
        
    def _show_splash(self):
        """Show splash screen with loading animation."""
        splash = SplashScreen(self)
        
        def load_app():
            """Simulate loading and initialize app."""
            time.sleep(0.5)
            splash.update_status("Loading database...")
            time.sleep(0.5)
            splash.update_status("Initializing UI components...")
            time.sleep(0.5)
            splash.update_status("Ready!")
            time.sleep(0.3)
            
            # Close splash and show main window
            self.after(0, lambda: self._finish_loading(splash))
        
        # Run loading in thread
        thread = threading.Thread(target=load_app, daemon=True)
        thread.start()
    
    def _finish_loading(self, splash):
        """Finish loading and show main window."""
        splash.close_splash()
        self.deiconify()
        self._create_ui()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"900x750+{x}+{y}")
        
    def _create_ui(self):
        """Create the main user interface with tabs."""
        # Create tab view
        self.tabview = ctk.CTkTabview(self, corner_radius=15)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Add tabs
        self.tabview.add("Generate Key")
        self.tabview.add("Manage Keys")
        self.tabview.add("Statistics")
        
        # Configure tab grids
        self.tabview.tab("Generate Key").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Manage Keys").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Statistics").grid_columnconfigure(0, weight=1)
        
        # Create tab contents
        self._create_generate_tab()
        self._create_manage_tab()
        self._create_stats_tab()
        
        # Set up tab change handler for auto-scroll to top
        self.tabview.configure(command=self._on_tab_change)
    
    def _on_tab_change(self):
        """Handle tab change to auto-scroll to top.
        
        Note: Uses _parent_canvas which is a private attribute of CTkScrollableFrame.
        This is the standard approach in CustomTkinter for programmatic scrolling.
        """
        current_tab = self.tabview.get()
        
        # Scroll to top of the current tab
        if current_tab == "Generate Key" and hasattr(self, 'generate_scroll_frame'):
            self.generate_scroll_frame._parent_canvas.yview_moveto(0)
        elif current_tab == "Manage Keys" and hasattr(self, 'manage_scroll_frame'):
            self.manage_scroll_frame._parent_canvas.yview_moveto(0)
        elif current_tab == "Statistics" and hasattr(self, 'stats_scroll_frame'):
            self.stats_scroll_frame._parent_canvas.yview_moveto(0)
        
    def _create_generate_tab(self):
        """Create the Generate Key tab."""
        tab = self.tabview.tab("Generate Key")
        
        # Scrollable frame for content
        scroll_frame = ctk.CTkScrollableFrame(tab, corner_radius=10)
        scroll_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(
            scroll_frame,
            text="🔑 Generate License Key",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0"),
        )
        header_label.grid(row=0, column=0, padx=20, pady=(20, 20))
        
        # Email input
        email_label = ctk.CTkLabel(
            scroll_frame,
            text="📧 Buyer Email Address:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        email_label.grid(row=1, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.email_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="buyer@example.com",
            height=45,
            font=ctk.CTkFont(size=13),
            border_width=2,
            corner_radius=8,
        )
        self.email_entry.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # License tier - Use dropdown instead of radio buttons
        tier_label = ctk.CTkLabel(
            scroll_frame,
            text="📋 License Tier:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        tier_label.grid(row=3, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.tier_combo = ctk.CTkComboBox(
            scroll_frame,
            values=["Trial (3 days, 10 pages)", "Standard (50 pages)", "Enterprise (300 pages, all features)", "Lifetime (Enterprise, no expiration)"],
            height=45,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            corner_radius=8,
            border_width=2,
            state="readonly"
        )
        self.tier_combo.set("Standard (50 pages)")
        self.tier_combo.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Duration selection - Updated with all durations
        duration_label = ctk.CTkLabel(
            scroll_frame,
            text="⏰ License Duration:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        duration_label.grid(row=5, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.duration_combo = ctk.CTkComboBox(
            scroll_frame,
            values=["3 Days", "1 Month", "3 Months", "6 Months", "1 Year", "Lifetime"],
            height=45,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            corner_radius=8,
            border_width=2,
            state="readonly"
        )
        self.duration_combo.set("Lifetime")
        self.duration_combo.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Notes (optional)
        notes_label = ctk.CTkLabel(
            scroll_frame,
            text="📝 Notes (Optional):",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        notes_label.grid(row=7, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.notes_entry = ctk.CTkEntry(
            scroll_frame,
            placeholder_text="Customer name, order number, etc.",
            height=45,
            font=ctk.CTkFont(size=13),
            border_width=2,
            corner_radius=8,
        )
        self.notes_entry.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Generate button
        self.generate_btn = ctk.CTkButton(
            scroll_frame,
            text="🚀 GENERATE LICENSE KEY",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=55,
            corner_radius=10,
            fg_color=("#1f6aa5", "#3b8ed0"),
            hover_color=("#1a5a8f", "#2f5ba0"),
            command=self._generate_key,
        )
        self.generate_btn.grid(row=9, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Result section
        result_label = ctk.CTkLabel(
            scroll_frame,
            text="🔐 Generated License Key:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        result_label.grid(row=10, column=0, padx=20, pady=(20, 5), sticky="w")
        
        # Use textbox instead of entry for better wrapping
        self.result_text = ctk.CTkTextbox(
            scroll_frame,
            height=80,
            font=ctk.CTkFont(family="Courier", size=12),
            border_width=2,
            corner_radius=8,
            wrap="word",
            state="disabled"
        )
        self.result_text.grid(row=11, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Copy button
        self.copy_btn = ctk.CTkButton(
            scroll_frame,
            text="📋 COPY TO CLIPBOARD",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            corner_radius=8,
            fg_color=("#28a745", "#20873a"),
            hover_color=("#218838", "#1a6d2e"),
            state="disabled",
            command=self._copy_to_clipboard,
        )
        self.copy_btn.grid(row=12, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Store reference for auto-scroll to top
        self.generate_scroll_frame = scroll_frame

        
    def _create_manage_tab(self):
        """Create the Manage Keys tab."""
        tab = self.tabview.tab("Manage Keys")
        
        # Scrollable frame for entire content
        scroll_frame = ctk.CTkScrollableFrame(tab, corner_radius=10)
        scroll_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        # Search frame
        search_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        search_frame.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)
        
        search_label = ctk.CTkLabel(
            search_frame,
            text="🔍 Search:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        search_label.grid(row=0, column=0, padx=(20, 10), pady=20)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Enter email or key fragment...",
            height=40,
            font=ctk.CTkFont(size=12),
            corner_radius=8
        )
        self.search_entry.grid(row=0, column=1, padx=(0, 10), pady=20, sticky="ew")
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="Search",
            width=100,
            height=40,
            corner_radius=8,
            command=self._search_keys
        )
        search_btn.grid(row=0, column=2, padx=(0, 10), pady=20)
        
        refresh_btn = ctk.CTkButton(
            search_frame,
            text="Refresh",
            width=100,
            height=40,
            corner_radius=8,
            command=self._refresh_keys
        )
        refresh_btn.grid(row=0, column=3, padx=(0, 20), pady=20)
        
        # Keys list frame
        list_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        list_frame.grid(row=1, column=0, padx=0, pady=(0, 20), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Create scrollable text area for keys
        self.keys_text = ctk.CTkTextbox(
            list_frame,
            font=ctk.CTkFont(family="Courier", size=11),
            corner_radius=8,
            wrap="none"
        )
        self.keys_text.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Action buttons frame
        actions_frame = ctk.CTkFrame(scroll_frame, corner_radius=10)
        actions_frame.grid(row=2, column=0, padx=0, pady=(0, 0), sticky="ew")
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.selected_key_var = ctk.StringVar()
        
        key_entry_label = ctk.CTkLabel(
            actions_frame,
            text="Selected Key:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        key_entry_label.grid(row=0, column=0, padx=(20, 5), pady=(20, 5), sticky="w")
        
        self.selected_key_entry = ctk.CTkEntry(
            actions_frame,
            textvariable=self.selected_key_var,
            placeholder_text="Paste or type key here...",
            height=40,
            font=ctk.CTkFont(size=11),
            corner_radius=8
        )
        self.selected_key_entry.grid(row=1, column=0, columnspan=3, padx=20, pady=(0, 20), sticky="ew")
        
        revoke_btn = ctk.CTkButton(
            actions_frame,
            text="🚫 Revoke Key",
            height=45,
            corner_radius=8,
            fg_color=("#dc3545", "#c82333"),
            hover_color=("#bd2130", "#a71d2a"),
            command=self._revoke_key
        )
        revoke_btn.grid(row=2, column=0, padx=(20, 5), pady=(0, 20), sticky="ew")
        
        reactivate_btn = ctk.CTkButton(
            actions_frame,
            text="✅ Reactivate Key",
            height=45,
            corner_radius=8,
            fg_color=("#28a745", "#20873a"),
            hover_color=("#218838", "#1a6d2e"),
            command=self._reactivate_key
        )
        reactivate_btn.grid(row=2, column=1, padx=5, pady=(0, 20), sticky="ew")
        
        view_btn = ctk.CTkButton(
            actions_frame,
            text="👁 View Details",
            height=45,
            corner_radius=8,
            command=self._view_key_details
        )
        view_btn.grid(row=2, column=2, padx=(5, 20), pady=(0, 20), sticky="ew")
        
        # Store reference for auto-scroll to top
        self.manage_scroll_frame = scroll_frame
        
        # Load keys initially
        self._refresh_keys()
    
    def _create_stats_tab(self):
        """Create the Statistics tab."""
        tab = self.tabview.tab("Statistics")
        
        # Scrollable frame for entire content
        scroll_frame = ctk.CTkScrollableFrame(tab, corner_radius=10)
        scroll_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        scroll_frame.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        # Stats frame
        stats_frame = ctk.CTkFrame(scroll_frame, corner_radius=15)
        stats_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        stats_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            stats_frame,
            text="📊 License Statistics",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(30, 40))
        
        # Get stats
        stats = get_license_stats()
        
        # Display stats in cards
        # Total
        total_card = ctk.CTkFrame(stats_frame, corner_radius=12, border_width=2, border_color="gray30")
        total_card.grid(row=1, column=0, padx=(20, 10), pady=20, sticky="ew")
        
        ctk.CTkLabel(
            total_card,
            text="📦 Total Licenses",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            total_card,
            text=str(stats['total']),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0")
        ).pack(pady=(0, 20))
        
        # Active
        active_card = ctk.CTkFrame(stats_frame, corner_radius=12, border_width=2, border_color="gray30")
        active_card.grid(row=1, column=1, padx=(10, 20), pady=20, sticky="ew")
        
        ctk.CTkLabel(
            active_card,
            text="✅ Active Licenses",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            active_card,
            text=str(stats['active']),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=("#28a745", "#20873a")
        ).pack(pady=(0, 20))
        
        # Banned
        banned_card = ctk.CTkFrame(stats_frame, corner_radius=12, border_width=2, border_color="gray30")
        banned_card.grid(row=2, column=0, padx=(20, 10), pady=20, sticky="ew")
        
        ctk.CTkLabel(
            banned_card,
            text="🚫 Banned Licenses",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            banned_card,
            text=str(stats['banned']),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=("#dc3545", "#c82333")
        ).pack(pady=(0, 20))
        
        # Expired
        expired_card = ctk.CTkFrame(stats_frame, corner_radius=12, border_width=2, border_color="gray30")
        expired_card.grid(row=2, column=1, padx=(10, 20), pady=20, sticky="ew")
        
        ctk.CTkLabel(
            expired_card,
            text="⏰ Expired Licenses",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            expired_card,
            text=str(stats['expired']),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=("#ffc107", "#ff9800")
        ).pack(pady=(0, 20))
        
        # Refresh button
        refresh_stats_btn = ctk.CTkButton(
            stats_frame,
            text="🔄 Refresh Statistics",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            corner_radius=10,
            command=lambda: self._create_stats_tab()
        )
        refresh_stats_btn.grid(row=3, column=0, columnspan=2, padx=20, pady=(30, 40), sticky="ew")
        
        # HWID info
        hwid_frame = ctk.CTkFrame(stats_frame, corner_radius=12, border_width=2, border_color="gray30")
        hwid_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=(20, 30), sticky="ew")
        
        ctk.CTkLabel(
            hwid_frame,
            text="🖥️ Current Machine HWID",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(20, 5))
        
        hwid_text = ctk.CTkTextbox(
            hwid_frame,
            height=60,
            font=ctk.CTkFont(family="Courier", size=11),
            corner_radius=8,
            wrap="word"
        )
        hwid_text.pack(padx=20, pady=(0, 20), fill="x")
        hwid_text.insert("1.0", get_hwid())
        hwid_text.configure(state="disabled")
        
        # Store reference for auto-scroll to top
        self.stats_scroll_frame = scroll_frame

        
    def _generate_key(self):
        """Generate a license key and save to database."""
        email = self.email_entry.get().strip()
        
        # Validate email
        if not email:
            messagebox.showerror("Error", "Please enter a buyer email address.")
            return
            
        if '@' not in email or '.' not in email.split('@')[-1]:
            messagebox.showerror("Error", "Please enter a valid email address.")
            return
        
        # Get selected tier and duration
        tier_display = self.tier_combo.get()
        duration_display = self.duration_combo.get()
        
        # Map display tier to internal format
        tier_map = {
            "Trial (3 days, 10 pages)": "trial",
            "Standard (50 pages)": "standard",
            "Enterprise (300 pages, all features)": "enterprise",
            "Lifetime (Enterprise, no expiration)": "lifetime"
        }
        tier = tier_map.get(tier_display, "trial")
        
        # Map display duration to internal format
        duration_map = {
            "3 Days": "3_day",
            "1 Month": "1_month",
            "3 Months": "3_month",
            "6 Months": "6_month",
            "1 Year": "1_year",
            "Lifetime": "lifetime"
        }
        duration = duration_map.get(duration_display, "lifetime")
        
        # Get notes
        notes = self.notes_entry.get().strip() or None
        
        try:
            # Generate license key
            license_key, expires_at = generate_key(email, tier, duration)
            
            # Save to database (sync to Supabase via postgrest)
            license_id = create_license(email, license_key, tier, duration, expires_at, notes)
            
            # Display result
            self.result_text.configure(state="normal")
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", license_key)
            self.result_text.configure(state="disabled")
            
            # Store for clipboard
            self.generated_key = license_key
            
            # Enable copy button
            self.copy_btn.configure(state="normal")
            
            # Show success message
            tier_name_map = {
                "trial": "Trial",
                "standard": "Standard",
                "enterprise": "Enterprise",
                "lifetime": "Lifetime"
            }
            tier_name = tier_name_map.get(tier, "Trial")
            duration_name = duration_display
            expires_msg = f"\nExpires: {datetime.fromisoformat(expires_at).strftime('%Y-%m-%d')}" if expires_at else "\nExpires: Never (Lifetime)"
            
            messagebox.showinfo(
                "Success",
                f"License key generated and saved to database!\n"
                f"Synced to Supabase cloud.\n\n"
                f"Email: {email}\n"
                f"Tier: {tier_name}\n"
                f"Duration: {duration_name}{expires_msg}\n"
                f"Database ID: {license_id}\n\n"
                f"Key: {license_key}\n\n"
                f"Send this key to the buyer for activation."
            )
            
            # Refresh manage tab
            self._refresh_keys()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate license key:\n{str(e)}")
    
    def _copy_to_clipboard(self):
        """Copy the generated license key to clipboard."""
        if hasattr(self, 'generated_key') and self.generated_key:
            self.clipboard_clear()
            self.clipboard_append(self.generated_key)
            messagebox.showinfo("Copied", "License key copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "No license key to copy. Generate a key first.")
    
    def _search_keys(self):
        """Search for keys by email or key fragment."""
        search_term = self.search_entry.get().strip()
        
        if not search_term:
            messagebox.showwarning("Warning", "Please enter a search term.")
            return
        
        try:
            results = search_licenses(search_term)
            self._display_keys(results)
        except Exception as e:
            messagebox.showerror("Error", f"Search failed:\n{str(e)}")
    
    def _refresh_keys(self):
        """Refresh the keys list."""
        try:
            all_keys = list_all_licenses()
            self._display_keys(all_keys)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load licenses:\n{str(e)}")
    
    def _display_keys(self, licenses):
        """Display licenses in the text area."""
        self.keys_text.configure(state="normal")
        self.keys_text.delete("1.0", "end")
        
        if not licenses:
            self.keys_text.insert("1.0", "No licenses found.")
        else:
            header = f"{'ID':<6} {'Email':<30} {'Tier':<10} {'Duration':<12} {'Status':<10} {'Key'}\n"
            self.keys_text.insert("end", header)
            self.keys_text.insert("end", "=" * 120 + "\n")
            
            for lic in licenses:
                lid = lic.get('id', 'N/A')
                email = lic.get('email', 'N/A')[:28]
                tier = lic.get('tier', 'N/A')[:8].capitalize()
                duration = lic.get('duration', 'N/A')[:10]
                status = lic.get('status', 'N/A')[:8]
                key = lic.get('key', 'N/A')
                
                # Check if expired
                if status == 'Active' and is_license_expired(lic):
                    status = 'Expired'
                
                line = f"{lid:<6} {email:<30} {tier:<10} {duration:<12} {status:<10} {key}\n"
                self.keys_text.insert("end", line)
        
        self.keys_text.configure(state="disabled")
    
    def _revoke_key(self):
        """Revoke a license key."""
        key = self.selected_key_var.get().strip()
        
        if not key:
            messagebox.showwarning("Warning", "Please enter a license key to revoke.")
            return
        
        # Confirm
        if not messagebox.askyesno("Confirm", f"Are you sure you want to revoke this license key?\n\n{key}"):
            return
        
        try:
            success = revoke_license(key, "Revoked by admin")
            if success:
                messagebox.showinfo("Success", "License key revoked successfully.")
                self._refresh_keys()
                self.selected_key_var.set("")
            else:
                messagebox.showerror("Error", "License key not found in database.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to revoke license:\n{str(e)}")
    
    def _reactivate_key(self):
        """Reactivate a revoked license key."""
        key = self.selected_key_var.get().strip()
        
        if not key:
            messagebox.showwarning("Warning", "Please enter a license key to reactivate.")
            return
        
        try:
            success = reactivate_license(key)
            if success:
                messagebox.showinfo("Success", "License key reactivated successfully.")
                self._refresh_keys()
                self.selected_key_var.set("")
            else:
                messagebox.showerror("Error", "License key not found in database.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reactivate license:\n{str(e)}")
    
    def _view_key_details(self):
        """View detailed information about a license key."""
        key = self.selected_key_var.get().strip()
        
        if not key:
            messagebox.showwarning("Warning", "Please enter a license key to view details.")
            return
        
        try:
            license_data = get_license_by_key(key)
            if not license_data:
                messagebox.showerror("Error", "License key not found in database.")
                return
            
            # Format details
            details = f"""License Key Details:
            
ID: {license_data.get('id', 'N/A')}
Email: {license_data.get('email', 'N/A')}
Key: {license_data.get('key', 'N/A')}
Tier: {license_data.get('tier', 'N/A').capitalize()}
Duration: {license_data.get('duration', 'N/A')}
Status: {license_data.get('status', 'N/A')}
HWID: {license_data.get('hwid') or 'Not activated yet'}
Created: {license_data.get('created_at', 'N/A')}
Expires: {license_data.get('expires_at') or 'Never (Lifetime)'}
Notes: {license_data.get('notes') or 'None'}
Expired: {'Yes' if is_license_expired(license_data) else 'No'}
"""
            
            messagebox.showinfo("License Details", details)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve license details:\n{str(e)}")


def main():
    """Run the keygen GUI application."""
    # Set appearance
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # Create and run app
    app = KeygenApp()
    app.mainloop()


if __name__ == "__main__":
    main()
