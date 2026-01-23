"""
CourseSmith AI - Main Application GUI.
A desktop tool to generate educational PDF books using AI.
"""

import os
import threading
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from ai_manager import AIGenerator
from pdf_engine import PDFBuilder


# Configure appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Main application window for CourseSmith AI."""

    def __init__(self):
        """Initialize the application window and widgets."""
        super().__init__()

        # Window configuration
        self.title("CourseSmith AI - Educational PDF Generator")
        self.geometry("900x600")
        self.minsize(800, 500)

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Track generation state
        self.is_generating = False

        # Create UI components
        self._create_sidebar()
        self._create_main_area()

    def _create_sidebar(self):
        """Create the left sidebar with inputs and generate button."""
        # Sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        # Title label
        self.title_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="CourseSmith AI",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(30, 10))

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Generate Educational PDFs",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 30))

        # Topic label
        self.topic_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Topic:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.topic_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

        # Topic entry
        self.topic_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text="e.g., Bitcoin Trading",
            width=240,
            height=40,
        )
        self.topic_entry.grid(row=3, column=0, padx=20, pady=(0, 15))

        # Audience label
        self.audience_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Target Audience:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self.audience_label.grid(row=4, column=0, padx=20, pady=(10, 5), sticky="w")

        # Audience entry
        self.audience_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text="e.g., Beginners",
            width=240,
            height=40,
        )
        self.audience_entry.grid(row=5, column=0, padx=20, pady=(0, 30))

        # Generate button
        self.generate_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🚀 GENERATE COURSE",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            width=240,
            fg_color="#28a745",
            hover_color="#218838",
            command=self._on_generate_click,
        )
        self.generate_btn.grid(row=7, column=0, padx=20, pady=(20, 30))

        # Version label at bottom
        self.version_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="v1.0.0",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.version_label.grid(row=8, column=0, padx=20, pady=(0, 10))

    def _create_main_area(self):
        """Create the main area with console log and progress bar."""
        # Main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Console header
        self.console_header = ctk.CTkLabel(
            self.main_frame,
            text="📋 Generation Log",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        )
        self.console_header.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="w")

        # Console log (read-only textbox)
        self.console_log = ctk.CTkTextbox(
            self.main_frame,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            state="disabled",
        )
        self.console_log.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")

        # Progress frame
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        # Progress label
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Ready to generate",
            font=ctk.CTkFont(size=13),
            anchor="w",
        )
        self.progress_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=15)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        # Initial welcome message
        self._log_message("Welcome to CourseSmith AI!")
        self._log_message("Enter a topic and target audience, then click 'Generate Course'.")
        self._log_message("-" * 50)

    def _log_message(self, message):
        """
        Add a message to the console log (thread-safe).

        Args:
            message: The message to log.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"

        self.console_log.configure(state="normal")
        self.console_log.insert("end", formatted_msg)
        self.console_log.see("end")
        self.console_log.configure(state="disabled")

    def _update_progress(self, value, label_text):
        """
        Update the progress bar and label (thread-safe).

        Args:
            value: Progress value (0.0 to 1.0).
            label_text: Text to display in progress label.
        """
        self.progress_bar.set(value)
        self.progress_label.configure(text=label_text)

    def _on_generate_click(self):
        """Handle the generate button click."""
        if self.is_generating:
            messagebox.showwarning(
                "In Progress", "A course is already being generated. Please wait."
            )
            return

        # Get input values
        topic = self.topic_entry.get().strip()
        audience = self.audience_entry.get().strip()

        # Validate inputs
        if not topic:
            messagebox.showerror("Error", "Please enter a topic.")
            return

        if not audience:
            messagebox.showerror("Error", "Please enter a target audience.")
            return

        # Start generation in background thread
        self.is_generating = True
        self.generate_btn.configure(state="disabled", text="⏳ Generating...")

        thread = threading.Thread(
            target=self._generation_worker, args=(topic, audience), daemon=True
        )
        thread.start()

    def _generation_worker(self, topic, audience):
        """
        Background worker for course generation.

        Args:
            topic: The course topic.
            audience: The target audience.
        """
        cover_image_path = None

        try:
            # Initialize AI Generator
            self.after(0, lambda: self._log_message("Initializing AI Generator..."))
            self.after(0, lambda: self._update_progress(0.05, "Initializing..."))

            ai_generator = AIGenerator()

            # Step 1: Generate outline (20%)
            self.after(0, lambda: self._log_message("Generating course outline..."))
            self.after(0, lambda: self._update_progress(0.1, "Creating outline..."))

            chapters = ai_generator.generate_outline(topic, audience)

            self.after(0, lambda: self._log_message(f"✓ Generated {len(chapters)} chapter titles:"))
            for i, title in enumerate(chapters, 1):
                self.after(0, lambda t=title, n=i: self._log_message(f"  {n}. {t}"))

            self.after(0, lambda: self._update_progress(0.2, "Outline complete"))

            # Step 2: Generate cover image (35%)
            self.after(0, lambda: self._log_message("Generating cover image with DALL-E 3..."))
            self.after(0, lambda: self._update_progress(0.25, "Creating cover image..."))

            cover_image_path = ai_generator.generate_cover(topic)

            self.after(0, lambda: self._log_message("✓ Cover image generated successfully"))
            self.after(0, lambda: self._update_progress(0.35, "Cover image complete"))

            # Step 3: Generate chapter content (35% -> 80%)
            self.after(0, lambda: self._log_message("Generating chapter content..."))

            chapters_data = []
            for i, chapter_title in enumerate(chapters):
                progress = 0.35 + (i * 0.09)  # 0.35 to 0.80
                self.after(
                    0,
                    lambda p=progress, n=i + 1: self._update_progress(
                        p, f"Writing chapter {n}/5..."
                    ),
                )
                self.after(
                    0, lambda t=chapter_title: self._log_message(f"Writing: {t}...")
                )

                content = ai_generator.generate_chapter(topic, chapter_title)
                chapters_data.append({"title": chapter_title, "content": content})

                self.after(0, lambda n=i + 1: self._log_message(f"✓ Chapter {n} complete"))

            self.after(0, lambda: self._update_progress(0.8, "All chapters written"))

            # Step 4: Build PDF (80% -> 100%)
            self.after(0, lambda: self._log_message("Building PDF document..."))
            self.after(0, lambda: self._update_progress(0.9, "Creating PDF..."))

            # Generate filename
            safe_topic = "".join(c if c.isalnum() or c == " " else "_" for c in topic)
            safe_topic = safe_topic.replace(" ", "_")[:30]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"CourseSmith_{safe_topic}_{timestamp}.pdf"

            # Build the PDF
            pdf_builder = PDFBuilder(filename)
            pdf_path = pdf_builder.build_pdf(topic, audience, cover_image_path, chapters_data)

            self.after(0, lambda: self._update_progress(1.0, "Complete!"))
            self.after(0, lambda: self._log_message("=" * 50))
            self.after(0, lambda p=pdf_path: self._log_message(f"✓ PDF generated: {p}"))
            self.after(0, lambda: self._log_message("🎉 Course generation complete!"))

            # Show success message
            self.after(
                0,
                lambda: messagebox.showinfo(
                    "Success",
                    f"Course PDF generated successfully!\n\nFile saved as:\n{pdf_path}",
                ),
            )

        except ValueError as e:
            # API key not found
            self.after(0, lambda e=e: self._log_message(f"❌ Configuration Error: {str(e)}"))
            self.after(0, lambda: self._update_progress(0, "Error - Check API Key"))
            self.after(
                0,
                lambda: messagebox.showerror(
                    "Configuration Error",
                    "OpenAI API key not found.\n\nPlease create a .env file with:\n"
                    "OPENAI_API_KEY=your_api_key_here",
                ),
            )

        except Exception as e:
            # General error
            self.after(0, lambda e=e: self._log_message(f"❌ Error: {str(e)}"))
            self.after(0, lambda: self._update_progress(0, "Error occurred"))
            self.after(
                0,
                lambda e=e: messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}"),
            )

        finally:
            # Cleanup temp cover image
            if cover_image_path and os.path.exists(cover_image_path):
                try:
                    os.remove(cover_image_path)
                except OSError:
                    pass

            # Reset UI state
            self.after(0, self._reset_ui_state)

    def _reset_ui_state(self):
        """Reset the UI state after generation completes or fails."""
        self.is_generating = False
        self.generate_btn.configure(state="normal", text="🚀 GENERATE COURSE")


if __name__ == "__main__":
    app = App()
    app.mainloop()
