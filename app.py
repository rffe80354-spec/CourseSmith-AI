"""
CourseSmith ENTERPRISE - Main Application GUI.
A commercial desktop tool to generate educational PDF books using AI with DRM protection.
"""

import os
import threading
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog

from utils import resource_path, get_data_dir
from license_guard import load_license, save_license, validate_license
from project_manager import CourseProject
from ai_worker import OutlineGenerator, ChapterWriter, CoverGenerator
from pdf_engine import PDFBuilder


# Configure appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Main application window for CourseSmith ENTERPRISE with DRM protection."""

    def __init__(self):
        """Initialize the application window and widgets."""
        super().__init__()

        # Window configuration
        self.title("CourseSmith ENTERPRISE - Educational PDF Generator")
        self.geometry("1000x700")
        self.minsize(900, 600)

        # Initialize project
        self.project = CourseProject()
        
        # Track state
        self.is_licensed = False
        self.licensed_email = None
        self.is_generating = False
        self.current_chapter_index = 0
        self.total_chapters = 0

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Check license status
        self._check_license()

    def _check_license(self):
        """Check license status and show appropriate UI."""
        is_valid, email = load_license()
        
        if is_valid:
            self.is_licensed = True
            self.licensed_email = email
            self._create_main_ui()
        else:
            self.is_licensed = False
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
            text="🔐 CourseSmith ENTERPRISE",
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

        # Validate the license
        if validate_license(email, key):
            # Save the license
            if save_license(email, key):
                self.is_licensed = True
                self.licensed_email = email
                messagebox.showinfo(
                    "Success",
                    "License activated successfully!\n\nWelcome to CourseSmith ENTERPRISE.",
                )
                self._create_main_ui()
            else:
                messagebox.showerror("Error", "Failed to save license. Please try again.")
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
        """Create the header bar with title and user info."""
        header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="CourseSmith ENTERPRISE",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # User info
        if self.licensed_email:
            user_label = ctk.CTkLabel(
                header_frame,
                text=f"✓ Licensed to: {self.licensed_email}",
                font=ctk.CTkFont(size=12),
                text_color="#28a745",
            )
            user_label.grid(row=0, column=2, padx=20, pady=15, sticky="e")

    # ==================== SETUP TAB ====================
    def _create_setup_tab(self):
        """Create the Setup tab content."""
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

        # Audience
        ctk.CTkLabel(left_frame, text="Target Audience:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=3, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.audience_entry = ctk.CTkEntry(
            left_frame, placeholder_text="e.g., Beginners with no trading experience", width=350, height=40
        )
        self.audience_entry.grid(row=4, column=0, padx=20, pady=(0, 20))

        # Right column - Branding
        right_frame = ctk.CTkFrame(self.tab_setup)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(
            right_frame,
            text="🎨 Branding (Optional)",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="w")

        # Logo path
        ctk.CTkLabel(right_frame, text="Logo Image:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=1, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        
        logo_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        logo_frame.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="w")
        
        self.logo_entry = ctk.CTkEntry(logo_frame, placeholder_text="Path to logo image...", width=250, height=35)
        self.logo_entry.grid(row=0, column=0, padx=(0, 10))
        
        ctk.CTkButton(
            logo_frame, text="Browse", width=80, height=35, command=self._browse_logo
        ).grid(row=0, column=1)

        # Website URL
        ctk.CTkLabel(right_frame, text="Website URL:", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=3, column=0, padx=20, pady=(10, 5), sticky="w"
        )
        self.website_entry = ctk.CTkEntry(
            right_frame, placeholder_text="e.g., www.yourcompany.com", width=350, height=40
        )
        self.website_entry.grid(row=4, column=0, padx=20, pady=(0, 20))

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
        """Create the Drafting tab content."""
        self.tab_drafting.grid_columnconfigure(0, weight=1)
        self.tab_drafting.grid_rowconfigure(1, weight=1)

        # Header with button
        header_frame = ctk.CTkFrame(self.tab_drafting, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

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

        # Progress log
        self.drafting_log = ctk.CTkTextbox(
            self.tab_drafting,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            state="disabled",
        )
        self.drafting_log.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")

        # Progress bar
        progress_frame = ctk.CTkFrame(self.tab_drafting)
        progress_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.drafting_progress_label = ctk.CTkLabel(
            progress_frame, text="Ready to draft", font=ctk.CTkFont(size=13)
        )
        self.drafting_progress_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.drafting_progress = ctk.CTkProgressBar(progress_frame, height=15)
        self.drafting_progress.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.drafting_progress.set(0)
        progress_frame.grid_columnconfigure(0, weight=1)

        # Continue button
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
        self.continue_export_btn.grid(row=3, column=0, padx=20, pady=(10, 20))

    def _log_drafting(self, message):
        """Add message to drafting log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"

        self.drafting_log.configure(state="normal")
        self.drafting_log.insert("end", formatted_msg)
        self.drafting_log.see("end")
        self.drafting_log.configure(state="disabled")

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

        self._log_drafting(f"Writing Chapter {chapter_num}: {chapter_title}...")

        def on_success(title, content):
            self.after(0, lambda: self._on_chapter_written(title, content))

        def on_error(error):
            self.after(0, lambda: self._on_drafting_error(error))

        worker = ChapterWriter(
            self.project.topic,
            chapter_title,
            chapter_num,
            callback=on_success,
            error_callback=on_error,
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


if __name__ == "__main__":
    app = App()
    app.mainloop()
