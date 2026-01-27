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
"""

import sys
import os
import customtkinter as ctk
from tkinter import messagebox
from license_guard import generate_key
from utils import resource_path

# Suppress stdout/stderr for --noconsole mode
if hasattr(sys, 'frozen'):
    sys.stdout = None
    sys.stderr = None

# God Mode secret trigger - DO NOT SHARE
GOD_MODE_CODE = "A543278.B543278.Z12345_Faleovad2009"


class AdminKeygenApp(ctk.CTk):
    """Admin Keygen GUI Application."""
    
    def __init__(self):
        """Initialize the admin keygen application."""
        super().__init__()
        
        # Configure window
        self.title("CourseSmith License Generator")
        self.geometry("700x600")
        self.resizable(False, False)
        
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"700x600+{x}+{y}")
        
        # Set icon if available
        try:
            icon_path = resource_path("resources/admin_keygen.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass
        
        # State
        self.god_mode = False
        
        # Create UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the main UI."""
        # Main container
        main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=("#2b2b2b", "#1a1a1a"))
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔑 License Key Generator",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=15)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Vendor Tool - DO NOT DISTRIBUTE",
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray50")
        )
        subtitle_label.pack(pady=(0, 15))
        
        # Input section
        input_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        input_frame.pack(fill="x", pady=(0, 15))
        
        # Email input
        email_label = ctk.CTkLabel(
            input_frame,
            text="Buyer Email:",
            font=ctk.CTkFont(size=16)
        )
        email_label.pack(pady=(20, 5), padx=20, anchor="w")
        
        self.email_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="buyer@example.com or God Mode Code",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.email_entry.pack(fill="x", padx=20, pady=(0, 15))
        self.email_entry.bind("<Return>", lambda e: self._on_generate())
        
        # Tier selection (initially hidden)
        self.tier_frame = ctk.CTkFrame(input_frame, corner_radius=10, fg_color="transparent")
        self.tier_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        tier_label = ctk.CTkLabel(
            self.tier_frame,
            text="License Tier (God Mode):",
            font=ctk.CTkFont(size=16)
        )
        tier_label.pack(pady=(0, 10), anchor="w")
        
        self.tier_var = ctk.StringVar(value="standard")
        
        tier_radio1 = ctk.CTkRadioButton(
            self.tier_frame,
            text="Standard ($59) - No Branding",
            variable=self.tier_var,
            value="standard",
            font=ctk.CTkFont(size=14)
        )
        tier_radio1.pack(anchor="w", pady=5)
        
        tier_radio2 = ctk.CTkRadioButton(
            self.tier_frame,
            text="Extended ($249) - Full Branding",
            variable=self.tier_var,
            value="extended",
            font=ctk.CTkFont(size=14)
        )
        tier_radio2.pack(anchor="w", pady=5)
        
        # Hide tier selection initially
        self.tier_frame.pack_forget()
        
        # Generate button
        self.generate_btn = ctk.CTkButton(
            input_frame,
            text="Generate License Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            command=self._on_generate
        )
        self.generate_btn.pack(fill="x", padx=20, pady=(0, 20))
        
        # Output section
        output_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        output_frame.pack(fill="both", expand=True)
        
        output_label = ctk.CTkLabel(
            output_frame,
            text="Generated License:",
            font=ctk.CTkFont(size=16)
        )
        output_label.pack(pady=(20, 10), padx=20, anchor="w")
        
        self.output_text = ctk.CTkTextbox(
            output_frame,
            font=ctk.CTkFont(family="Courier New", size=12),
            wrap="word",
            state="disabled"
        )
        self.output_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Copy button
        self.copy_btn = ctk.CTkButton(
            output_frame,
            text="Copy License Key",
            font=ctk.CTkFont(size=14),
            height=35,
            command=self._on_copy,
            state="disabled"
        )
        self.copy_btn.pack(fill="x", padx=20, pady=(0, 20))
        
        # Status bar
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray50")
        )
        self.status_label.pack(pady=(10, 0))
        
    def _on_generate(self):
        """Handle generate button click."""
        email_input = self.email_entry.get().strip()
        
        if not email_input:
            messagebox.showerror("Error", "Please enter a buyer email or God Mode code.")
            return
        
        # Check for God Mode trigger
        if email_input == GOD_MODE_CODE:
            if not self.god_mode:
                self.god_mode = True
                self.tier_frame.pack(fill="x", padx=20, pady=(0, 15), before=self.generate_btn)
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
        
        # Generate license key
        try:
            license_key = generate_key(email_input, tier)
            self._display_license(email_input, tier, license_key)
            self.status_label.configure(text=f"License generated for {email_input}", text_color=("#1f6aa5", "#3b8ed0"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate license: {str(e)}")
            self.status_label.configure(text="Generation failed", text_color=("red", "red"))
    
    def _display_license(self, email, tier, license_key):
        """Display the generated license."""
        tier_label = "Extended ($249)" if tier == 'extended' else "Standard ($59)"
        
        output = f"""
{'=' * 60}
✓ License Generated Successfully!
{'=' * 60}

Email:   {email}
Tier:    {tier_label}
Key:     {license_key}

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
