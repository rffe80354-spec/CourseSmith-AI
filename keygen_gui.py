#!/usr/bin/env python3
"""
Admin Key Generator GUI - Vendor Tool for Faleovad AI Enterprise.

CustomTkinter-based graphical interface for generating tiered license keys.
This tool is for SELLERS ONLY to generate license keys for buyers.

Features:
- Dark mode professional interface
- Email input validation
- License tier selection (Standard vs Extended)
- One-click key generation
- Copy to clipboard functionality
- Mock key generation (connect real logic later)

Tiers:
- Standard ($59): Basic features, no custom branding
- Extended ($249): Full features, custom logo and website support

Usage:
    python keygen_gui.py
"""

import customtkinter as ctk
from tkinter import messagebox
import hashlib
from datetime import datetime


class KeygenApp(ctk.CTk):
    """Admin License Key Generator GUI Application."""
    
    def __init__(self):
        """Initialize the keygen application."""
        super().__init__()
        
        # Window configuration
        self.title("Faleovad AI Enterprise - License Key Generator")
        self.geometry("700x600")
        self.minsize(600, 500)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create main UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the main user interface."""
        # Main container frame with generous padding
        main_frame = ctk.CTkFrame(self, corner_radius=15, border_width=2, border_color="gray30")
        main_frame.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header section
        header_label = ctk.CTkLabel(
            main_frame,
            text="🔑 License Key Generator",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#1f6aa5", "#3b8ed0"),
        )
        header_label.grid(row=0, column=0, padx=30, pady=(35, 10))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Admin Tool - Vendor Use Only",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        subtitle_label.grid(row=1, column=0, padx=30, pady=(0, 30))
        
        # Email input section
        email_label = ctk.CTkLabel(
            main_frame,
            text="📧 Buyer Email Address:",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        email_label.grid(row=2, column=0, padx=30, pady=(15, 8), sticky="w")
        
        self.email_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="buyer@example.com",
            height=50,
            font=ctk.CTkFont(size=14),
            border_width=2,
            corner_radius=10,
        )
        self.email_entry.grid(row=3, column=0, padx=30, pady=(0, 25), sticky="ew")
        
        # License tier section
        tier_label = ctk.CTkLabel(
            main_frame,
            text="📋 License Tier:",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        tier_label.grid(row=4, column=0, padx=30, pady=(15, 15), sticky="w")
        
        # Radio button frame
        radio_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        radio_frame.grid(row=5, column=0, padx=30, pady=(0, 25), sticky="ew")
        radio_frame.grid_columnconfigure(0, weight=1)
        radio_frame.grid_columnconfigure(1, weight=1)
        
        self.tier_var = ctk.StringVar(value="standard")
        
        standard_radio = ctk.CTkRadioButton(
            radio_frame,
            text="Standard ($59)\nBasic Features",
            variable=self.tier_var,
            value="standard",
            font=ctk.CTkFont(size=14),
            radiobutton_width=25,
            radiobutton_height=25,
        )
        standard_radio.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        extended_radio = ctk.CTkRadioButton(
            radio_frame,
            text="Extended ($249)\nFull Features + Branding",
            variable=self.tier_var,
            value="extended",
            font=ctk.CTkFont(size=14),
            radiobutton_width=25,
            radiobutton_height=25,
        )
        extended_radio.grid(row=0, column=1, padx=15, pady=10, sticky="w")
        
        # Generate button
        self.generate_btn = ctk.CTkButton(
            main_frame,
            text="🚀 GENERATE LICENSE KEY",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            corner_radius=12,
            fg_color=("#1f6aa5", "#3b8ed0"),
            hover_color=("#1a5a8f", "#2f5ba0"),
            command=self._generate_key,
        )
        self.generate_btn.grid(row=6, column=0, padx=30, pady=(20, 20), sticky="ew")
        
        # Result section
        result_label = ctk.CTkLabel(
            main_frame,
            text="🔐 Generated License Key:",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        result_label.grid(row=7, column=0, padx=30, pady=(20, 8), sticky="w")
        
        self.result_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Key will appear here after generation...",
            height=50,
            font=ctk.CTkFont(family="Courier", size=13),
            border_width=2,
            corner_radius=10,
            state="readonly",
        )
        self.result_entry.grid(row=8, column=0, padx=30, pady=(0, 15), sticky="ew")
        
        # Copy button
        self.copy_btn = ctk.CTkButton(
            main_frame,
            text="📋 COPY TO CLIPBOARD",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=("#28a745", "#20873a"),
            hover_color=("#218838", "#1a6d2e"),
            state="disabled",
            command=self._copy_to_clipboard,
        )
        self.copy_btn.grid(row=9, column=0, padx=30, pady=(0, 35), sticky="ew")
        
    def _generate_key(self):
        """Generate a license key based on email and tier selection."""
        email = self.email_entry.get().strip()
        
        # Validate email
        if not email:
            messagebox.showerror("Error", "Please enter a buyer email address.")
            return
            
        if '@' not in email or '.' not in email:
            messagebox.showerror("Error", "Please enter a valid email address.")
            return
        
        # Get selected tier
        tier = self.tier_var.get()
        
        # Generate mock license key
        license_key = self._mock_generate_key(email, tier)
        
        # Display result
        self.result_entry.configure(state="normal")
        self.result_entry.delete(0, "end")
        self.result_entry.insert(0, license_key)
        self.result_entry.configure(state="readonly")
        
        # Enable copy button
        self.copy_btn.configure(state="normal")
        
        # Show success message
        tier_name = "Extended" if tier == "extended" else "Standard"
        messagebox.showinfo(
            "Success",
            f"License key generated successfully!\n\n"
            f"Email: {email}\n"
            f"Tier: {tier_name}\n\n"
            f"Key: {license_key}\n\n"
            f"Send this key to the buyer for activation."
        )
        
    def _mock_generate_key(self, email, tier):
        """
        Mock license key generation function.
        
        TODO: Replace this with real license generation logic from license_guard module.
        
        Args:
            email: Buyer's email address
            tier: License tier ('standard' or 'extended')
            
        Returns:
            str: Generated license key
        """
        # Create a deterministic but unique key based on email and tier
        hash_input = f"{email}|{tier}|{datetime.now().year}"
        hash_obj = hashlib.sha256(hash_input.encode())
        hash_hex = hash_obj.hexdigest()[:16].upper()
        
        # Format as license key
        tier_prefix = "FALEOVAD-EXT" if tier == "extended" else "FALEOVAD-STD"
        year = datetime.now().year
        
        # Split hash into parts for readability
        part1 = hash_hex[:4]
        part2 = hash_hex[4:8]
        part3 = hash_hex[8:12]
        
        license_key = f"{tier_prefix}-{part1}-{part2}-{year}"
        
        return license_key
    
    def _copy_to_clipboard(self):
        """Copy the generated license key to clipboard."""
        license_key = self.result_entry.get()
        
        if license_key and not license_key.startswith("Key will appear"):
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(license_key)
            
            # Show confirmation
            messagebox.showinfo("Copied", "License key copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "No license key to copy. Generate a key first.")


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
