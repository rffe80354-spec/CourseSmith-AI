"""
Faleovad AI Enterprise - Main Application GUI.
A commercial desktop tool to generate educational PDF books using AI with DRM protection.
Uses session token system for anti-tamper protection.
Features tiered licensing: Standard ($59) vs Extended ($249).
"""

import os
import threading
import webbrowser
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog, Menu

from utils import resource_path, get_data_dir, clipboard_cut, clipboard_copy, clipboard_paste, clipboard_select_all, add_context_menu, get_underlying_tk_widget
from license_guard import validate_license
from session_manager import set_session, set_token, is_active, get_tier, is_extended, clear_session
from project_manager import CourseProject
from ai_worker import OutlineGenerator, ChapterWriter, CoverGenerator, AIWorkerBase
from pdf_engine import PDFBuilder


# Configure appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Upgrade URL for upsell
UPGRADE_URL = "https://www.codester.com"


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
    """Main application window for Faleovad AI Enterprise with DRM protection."""

    def __init__(self):
        """Initialize the application window and widgets."""
        super().__init__()

        # Window configuration
        self.title("Faleovad AI Enterprise - Educational PDF Generator")
        self.geometry("1000x700")
        self.minsize(900, 600)

        # Initialize project
        self.project = CourseProject()
        
        # Track state
        self.is_licensed = False
        self.licensed_email = None
        self.license_tier = None  # 'standard' or 'extended'
        self.is_generating = False
        self.current_chapter_index = 0
        self.total_chapters = 0

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Bind global keyboard shortcuts for clipboard operations
        self._bind_global_shortcuts()

        # Check license status
        self._check_license()

    def _check_license(self):
        """Initialize the application to require fresh authentication.
        
        Security: Always requires fresh login. No persistent sessions.
        The user must enter their email and license key every time the app starts.
        """
        # Security: Always start with no session - require fresh login every time
        self.is_licensed = False
        self.license_tier = None
        clear_session()
        self._create_activation_ui()

    def _create_activation_ui(self):
        """Create the license activation screen."""
        # Clear any existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Main activation frame
        self.activation_frame = ctk.CTkFrame(self, corner_radius=20)
        self.activation_frame.grid(row=0, column=0, padx=100, pady=100, sticky="nsew")
        self.activation_frame.grid_columnconfigure(0, weight=1)

        # Logo/Title
        title_label = ctk.CTkLabel(
            self.activation_frame,
            text="🔐 Faleovad AI Enterprise",
            font=ctk.CTkFont(size=32, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=40, pady=(40, 10))

        subtitle_label = ctk.CTkLabel(
            self.activation_frame,
            text="License Activation Required",
            font=ctk.CTkFont(size=16),
            text_color="gray",
        )
        subtitle_label.grid(row=1, column=0, padx=40, pady=(0, 30))

        # Email entry
        email_label = ctk.CTkLabel(
            self.activation_frame,
            text="Email Address:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        email_label.grid(row=2, column=0, padx=40, pady=(20, 5), sticky="w")

        self.email_entry = ctk.CTkEntry(
            self.activation_frame,
            placeholder_text="your.email@example.com",
            width=400,
            height=45,
            font=ctk.CTkFont(size=14),
        )
        self.email_entry.grid(row=3, column=0, padx=40, pady=(0, 15))
        bind_clipboard_menu(self.email_entry)

        # License key entry
        key_label = ctk.CTkLabel(
            self.activation_frame,
            text="License Key:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        key_label.grid(row=4, column=0, padx=40, pady=(10, 5), sticky="w")

        self.key_entry = ctk.CTkEntry(
            self.activation_frame,
            placeholder_text="XXXX-XXXX-XXXX-XXXX",
            width=400,
            height=45,
            font=ctk.CTkFont(size=14),
        )
        self.key_entry.grid(row=5, column=0, padx=40, pady=(0, 30))
        bind_clipboard_menu(self.key_entry)

        # Activate button
        self.activate_btn = ctk.CTkButton(
            self.activation_frame,
            text="🔓 ACTIVATE LICENSE",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            width=300,
            fg_color="#28a745",
            hover_color="#218838",
            command=self._on_activate_click,
        )
        self.activate_btn.grid(row=6, column=0, padx=40, pady=(10, 40))

    def _on_activate_click(self):
        """Handle license activation."""
        email = self.email_entry.get().strip()
        key = self.key_entry.get().strip()

        if not email:
            messagebox.showerror("Error", "Please enter your email address.")
            return

        if not key:
            messagebox.showerror("Error", "Please enter your license key.")
            return

        # Validate the license and get session info
        result = validate_license(email, key)
        
        if result and result.get('valid'):
            # Set the session with token, email, and tier for anti-tamper protection
            # Security: Session is volatile only - no persistence to disk
            tier = result.get('tier', 'standard')
            set_session(result['token'], email, tier)
            self.is_licensed = True
            self.licensed_email = email
            self.license_tier = tier
            
            tier_label = "Extended" if tier == 'extended' else "Standard"
            messagebox.showinfo(
                "Success",
                f"License activated successfully!\n\n"
                f"Tier: {tier_label}\n\n"
                f"Welcome to Faleovad AI Enterprise.",
            )
            self._create_main_ui()
        else:
            messagebox.showerror(
                "Invalid License",
                "The license key is not valid for this email address.\n\n"
                "Please check your email and key, or contact support.",
            )

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

    def _create_header(self):
        """Create the header bar with title, tier info, and settings."""
        header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Faleovad AI Enterprise",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Tier indicator
        if self.license_tier == 'extended':
            tier_label = ctk.CTkLabel(
                header_frame,
                text="✓ PRO Features Active",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#ffd700",  # Gold color for PRO
            )
        else:
            tier_label = ctk.CTkLabel(
                header_frame,
                text="Standard License",
                font=ctk.CTkFont(size=12),
                text_color="#888888",
            )
        tier_label.grid(row=0, column=1, padx=10, pady=15, sticky="w")

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
        settings_btn.grid(row=0, column=2, padx=10, pady=15, sticky="e")

        # User info
        if self.licensed_email:
            user_label = ctk.CTkLabel(
                header_frame,
                text=f"✓ {self.licensed_email}",
                font=ctk.CTkFont(size=12),
                text_color="#28a745",
            )
            user_label.grid(row=0, column=3, padx=20, pady=15, sticky="e")

    def _show_settings(self):
        """Show the settings dialog for API key configuration."""
        # Create modal dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 300) // 2
        dialog.geometry(f"+{x}+{y}")

        # Title
        ctk.CTkLabel(
            dialog,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(padx=20, pady=(20, 10))

        # API Key section
        ctk.CTkLabel(
            dialog,
            text="OpenAI API Key:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=20, pady=(20, 5), anchor="w")

        # Load current API key from environment
        current_key = os.getenv("OPENAI_API_KEY", "")
        
        api_key_entry = ctk.CTkEntry(
            dialog,
            placeholder_text="sk-...",
            width=450,
            height=40,
            show="*",
        )
        api_key_entry.pack(padx=20, pady=(0, 5))
        bind_clipboard_menu(api_key_entry)
        if current_key:
            api_key_entry.insert(0, current_key)

        # Help text
        ctk.CTkLabel(
            dialog,
            text="Your API key is stored in the .env file in the application directory.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(padx=20, pady=(0, 20))

        def save_api_key():
            api_key = api_key_entry.get().strip()
            if not api_key:
                messagebox.showerror("Error", "Please enter an API key.", parent=dialog)
                return
            
            # Save to .env file
            env_path = os.path.join(os.getcwd(), ".env")
            try:
                # Read existing content
                existing_lines = []
                if os.path.exists(env_path):
                    with open(env_path, 'r') as f:
                        for line in f:
                            stripped = line.strip()
                            if stripped and not stripped.startswith("OPENAI_API_KEY"):
                                existing_lines.append(line.rstrip())
                
                # Write with new API key
                with open(env_path, 'w') as f:
                    for line in existing_lines:
                        f.write(line + "\n")
                    f.write(f"OPENAI_API_KEY={api_key}\n")
                
                # Update environment variable
                os.environ["OPENAI_API_KEY"] = api_key
                
                # Reset the AI client to use new key
                AIWorkerBase.reset_client()
                
                messagebox.showinfo("Success", "API key saved successfully!", parent=dialog)
                dialog.destroy()
                
            except IOError as e:
                messagebox.showerror("Error", f"Failed to save API key: {e}", parent=dialog)

        # Save button
        ctk.CTkButton(
            dialog,
            text="💾 Save API Key",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=200,
            fg_color="#28a745",
            hover_color="#218838",
            command=save_api_key,
        ).pack(pady=20)

    # ==================== SETUP TAB ====================
    def _create_setup_tab(self):
        """Create the Setup tab content with tier-based branding restrictions."""
        self.tab_setup.grid_columnconfigure(0, weight=1)
        self.tab_setup.grid_columnconfigure(1, weight=1)

        # Left column - Course Info
        left_frame = ctk.CTkFrame(self.tab_setup)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            left_frame,
            text="📚 Course Information",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        # Topic
        ctk.CTkLabel(left_frame, text="Topic:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=1, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.topic_entry = ctk.CTkEntry(
            left_frame, placeholder_text="e.g., Bitcoin Trading Strategies", width=350, height=40
        )
        self.topic_entry.grid(row=2, column=0, padx=20, pady=(0, 15))
        bind_clipboard_menu(self.topic_entry)

        # Audience
        ctk.CTkLabel(left_frame, text="Target Audience:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=3, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.audience_entry = ctk.CTkEntry(
            left_frame, placeholder_text="e.g., Beginners with no trading experience", width=350, height=40
        )
        self.audience_entry.grid(row=4, column=0, padx=20, pady=(0, 20))
        bind_clipboard_menu(self.audience_entry)

        # Right column - Branding
        right_frame = ctk.CTkFrame(self.tab_setup)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Check if Extended tier for branding access
        is_extended_tier = is_extended()
        
        branding_title = "🎨 Branding (PRO)" if is_extended_tier else "🔒 Branding (Extended Only)"
        ctk.CTkLabel(
            right_frame,
            text=branding_title,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="w")

        # Logo path
        ctk.CTkLabel(right_frame, text="Logo Image:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=1, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        
        logo_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        logo_frame.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="w")
        
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
            row=3, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.website_entry = ctk.CTkEntry(
            right_frame, 
            placeholder_text="e.g., www.yourcompany.com" if is_extended_tier else "🔒 Extended License Required",
            width=350, 
            height=40,
            state="normal" if is_extended_tier else "disabled"
        )
        self.website_entry.grid(row=4, column=0, padx=20, pady=(0, 10))
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
            upgrade_btn.grid(row=5, column=0, padx=20, pady=(10, 20))

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

    def _open_upgrade_url(self):
        """Open the upgrade URL in the default browser."""
        webbrowser.open(UPGRADE_URL)

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

        # Switch to Blueprint tab
        self.tabview.set("📋 Blueprint")
        self._log_message("Setup saved. Ready to generate outline.")

    # ==================== BLUEPRINT TAB ====================
    def _create_blueprint_tab(self):
        """Create the Blueprint tab content."""
        self.tab_blueprint.grid_columnconfigure(0, weight=1)
        self.tab_blueprint.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.tab_blueprint, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

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

        # Editable outline textbox
        ctk.CTkLabel(
            self.tab_blueprint,
            text="Edit the chapter titles below (one per line):",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=1, column=0, padx=20, pady=(10, 5), sticky="nw")

        self.outline_textbox = ctk.CTkTextbox(
            self.tab_blueprint,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
        )
        self.outline_textbox.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.tab_blueprint.grid_rowconfigure(2, weight=1)
        bind_clipboard_menu(self.outline_textbox)

        # Confirm button
        ctk.CTkButton(
            self.tab_blueprint,
            text="✅ Confirm Outline & Continue to Drafting →",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            fg_color="#28a745",
            hover_color="#218838",
            command=self._confirm_outline,
        ).grid(row=3, column=0, padx=20, pady=(10, 20))

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
        # Configure grid for split view
        self.tab_drafting.grid_columnconfigure(0, weight=1)  # Left: Console
        self.tab_drafting.grid_columnconfigure(1, weight=1)  # Right: Preview
        self.tab_drafting.grid_rowconfigure(1, weight=1)

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
        left_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            left_frame,
            text="📋 Progress Console",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # Progress log
        self.drafting_log = ctk.CTkTextbox(
            left_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            state="disabled",
        )
        self.drafting_log.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        bind_clipboard_menu(self.drafting_log)

        # ========== RIGHT SIDE: Live Page Preview ==========
        right_frame = ctk.CTkFrame(self.tab_drafting)
        right_frame.grid(row=1, column=1, padx=(10, 20), pady=(0, 10), sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            right_frame,
            text="📄 Live Page Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # White "paper" frame for document preview (scrollable)
        self.preview_scroll = ctk.CTkScrollableFrame(
            right_frame,
            fg_color="white",
            corner_radius=5,
        )
        self.preview_scroll.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
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

        self.drafting_progress_label = ctk.CTkLabel(
            progress_frame, text="Ready to draft", font=ctk.CTkFont(size=13)
        )
        self.drafting_progress_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.drafting_progress = ctk.CTkProgressBar(progress_frame, height=15)
        self.drafting_progress.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.drafting_progress.set(0)
        progress_frame.grid_columnconfigure(0, weight=1)

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
        self.continue_export_btn.grid(row=3, column=0, columnspan=2, padx=20, pady=(10, 20))

        # Track current preview content for accumulation
        self._preview_accumulated_text = ""

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
        
        Args:
            text_chunk: The incremental text chunk to append.
        """
        self._preview_accumulated_text += text_chunk
        self.preview_content_label.configure(text=self._preview_accumulated_text)
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
        self._preview_accumulated_text = ""
        self.preview_content_label.configure(text="")

    def _set_preview_chapter_title(self, title, chapter_num):
        """Set the chapter title in the preview area."""
        self.preview_chapter_title.configure(text=f"Chapter {chapter_num}: {title}")

    def _start_drafting(self):
        """Start the chapter drafting process."""
        if not self.project.outline:
            messagebox.showerror("Error", "Please confirm an outline in the Blueprint tab first.")
            self.tabview.set("📋 Blueprint")
            return

        if self.is_generating:
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

        self._log_drafting("Starting chapter generation...")
        self._write_next_chapter()

    def _write_next_chapter(self):
        """Write the next chapter in the queue."""
        if self.current_chapter_index >= self.total_chapters:
            # All chapters done
            self.is_generating = False
            self.draft_btn.configure(state="normal", text="🚀 Start Writing Chapters")
            self.continue_export_btn.configure(state="normal")
            self._log_drafting("=" * 40)
            self._log_drafting("✓ All chapters written successfully!")
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

        self._log_drafting(f"Writing Chapter {chapter_num}: {chapter_title}...")

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
        self._log_drafting(f"✓ Chapter '{title}' complete ({len(content)} characters)")

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

        # Left - Cover generation
        cover_frame = ctk.CTkFrame(self.tab_export)
        cover_frame.grid(row=0, column=0, padx=10, pady=20, sticky="nsew")

        ctk.CTkLabel(
            cover_frame,
            text="🎨 Cover Image",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        self.cover_status = ctk.CTkLabel(
            cover_frame,
            text="No cover generated yet",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.cover_status.grid(row=1, column=0, padx=20, pady=(0, 15))

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

        # Right - PDF export
        pdf_frame = ctk.CTkFrame(self.tab_export)
        pdf_frame.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

        ctk.CTkLabel(
            pdf_frame,
            text="📄 PDF Export",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        self.pdf_status = ctk.CTkLabel(
            pdf_frame,
            text="Ready to build PDF",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.pdf_status.grid(row=1, column=0, padx=20, pady=(0, 15))

        self.build_pdf_btn = ctk.CTkButton(
            pdf_frame,
            text="📑 Build Final PDF",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            width=280,
            fg_color="#28a745",
            hover_color="#218838",
            command=self._build_pdf,
        )
        self.build_pdf_btn.grid(row=2, column=0, padx=20, pady=(0, 20))

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

    def _build_pdf(self):
        """Build the final PDF document."""
        if not self.project.is_complete():
            missing = []
            if not self.project.topic:
                missing.append("Topic (Setup tab)")
            if not self.project.outline:
                missing.append("Outline (Blueprint tab)")
            if len(self.project.chapters_content) < len(self.project.outline):
                missing.append("Chapter content (Drafting tab)")
            
            messagebox.showerror(
                "Incomplete Project",
                f"Please complete the following before building PDF:\n\n" + "\n".join(f"• {m}" for m in missing),
            )
            return

        # Ask for save location
        safe_topic = "".join(c if c.isalnum() or c == " " else "_" for c in self.project.topic)
        safe_topic = safe_topic.replace(" ", "_")[:30]
        default_name = f"CourseSmith_{safe_topic}.pdf"

        filepath = filedialog.asksaveasfilename(
            title="Save PDF As",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF Files", "*.pdf")],
        )

        if not filepath:
            return

        self._log_export("Building PDF document...")
        self.pdf_status.configure(text="Building PDF...")
        self.build_pdf_btn.configure(state="disabled", text="⏳ Building...")

        def build():
            try:
                builder = PDFBuilder(filepath)
                result = builder.build_pdf(self.project)
                self.after(0, lambda: self._on_pdf_built(result))
            except Exception as e:
                self.after(0, lambda: self._on_pdf_error(str(e)))

        thread = threading.Thread(target=build, daemon=True)
        thread.start()

    def _on_pdf_built(self, filepath):
        """Handle successful PDF build."""
        self.build_pdf_btn.configure(state="normal", text="📑 Build Final PDF")
        self.pdf_status.configure(text="✓ PDF exported!", text_color="#28a745")
        self._log_export(f"✓ PDF saved: {filepath}")
        self.project.output_pdf_path = filepath

        messagebox.showinfo(
            "Success",
            f"PDF generated successfully!\n\nFile saved as:\n{filepath}",
        )

    def _on_pdf_error(self, error):
        """Handle PDF build error."""
        self.build_pdf_btn.configure(state="normal", text="📑 Build Final PDF")
        self.pdf_status.configure(text="❌ Build failed", text_color="#e74c3c")
        self._log_export(f"❌ Error: {error}")
        messagebox.showerror("Error", f"Failed to build PDF:\n\n{error}")

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
        # Bind Ctrl+A for Select All (both uppercase and lowercase)
        self.bind("<Control-a>", self._on_select_all)
        self.bind("<Control-A>", self._on_select_all)
        
        # Bind Ctrl+C for Copy (both uppercase and lowercase)
        self.bind("<Control-c>", self._on_copy)
        self.bind("<Control-C>", self._on_copy)
        
        # Bind Ctrl+V for Paste (both uppercase and lowercase)
        self.bind("<Control-v>", self._on_paste)
        self.bind("<Control-V>", self._on_paste)
        
        # Bind Ctrl+X for Cut (both uppercase and lowercase)
        self.bind("<Control-x>", self._on_cut)
        self.bind("<Control-X>", self._on_cut)

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
        """Handle Ctrl+V (Paste) globally."""
        focused, tk_widget = self._get_focused_tk_widget()
        if tk_widget is None:
            return "break"
        
        try:
            # Check if widget is in normal state (can accept input)
            widget_state = str(tk_widget.cget("state")) if hasattr(tk_widget, "cget") else "normal"
            if widget_state == "disabled" or widget_state == "readonly":
                return "break"
            
            # Get clipboard content
            text = tk_widget.clipboard_get()
        except Exception:
            # Failed to access clipboard content (empty, unavailable, or permission issues)
            return "break"
        
        # Note: We manually delete selected text and insert instead of using
        # event_generate("<<Paste>>") to avoid double-paste issues with CustomTkinter.
        # Delete selected text first (if any)
        try:
            tk_widget.delete("sel.first", "sel.last")
        except Exception:
            # No selection exists, which is fine
            pass
        
        # Insert text at current cursor position
        try:
            tk_widget.insert("insert", text)
        except Exception:
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
