"""
CourseSmith AI - Custom High-End UI Implementation
Premium design with custom theme, sidebar navigation, and smooth animations.
"""

import os
import sys
import threading
import time
import locale
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog

from utils import resource_path, get_data_dir
from license_guard import validate_license, load_license, save_license, remove_license
from session_manager import set_session, is_active, get_tier, clear_session
from project_manager import CourseProject
from ai_worker import OutlineGenerator, ChapterWriter, CoverGenerator
from pdf_engine import PDFBuilder


# Custom Premium Theme Colors
COLORS = {
    'background': '#0B0E14',      # Deep dark background
    'sidebar': '#151921',         # Slightly lighter sidebar
    'accent': '#7F5AF0',          # Purple accent
    'accent_hover': '#9D7BF2',    # Lighter purple for hover
    'text_primary': '#FFFFFF',    # White text
    'text_secondary': '#8B92A8',  # Muted text
    'success': '#39D98A',         # Green for success
    'error': '#FF6B6B',           # Red for errors
    'card': '#1A1F2E',            # Card background
    'border': '#2A3142',          # Border color
}

# Sidebar width constant
SIDEBAR_WIDTH = 200


class LanguageManager:
    """Manages multilingual support for EN/RU languages."""
    
    def __init__(self):
        """Initialize language manager with OS language detection."""
        self.current_lang = self._detect_os_language()
        
    def _detect_os_language(self):
        """Detect OS language, defaulting to EN."""
        try:
            system_lang = locale.getdefaultlocale()[0]
            if system_lang and system_lang.startswith('ru'):
                return 'RU'
        except:
            pass
        return 'EN'
    
    def toggle_language(self):
        """Toggle between EN and RU."""
        self.current_lang = 'RU' if self.current_lang == 'EN' else 'EN'
    
    def get(self, key):
        """Get translated text for key."""
        translations = {
            'EN': {
                'forge': 'Forge',
                'library': 'Library',
                'settings': 'Settings',
                'start_forge': 'Start Forge',
                'course_topic': 'Course Topic',
                'target_audience': 'Target Audience',
                'chapter_count': 'Chapters',
                'generating': 'Forging your course...',
                'complete': 'Course Complete!',
                'progress': 'Progress',
                'cancel': 'Cancel',
                'export': 'Export PDF',
                'chapters_label': 'Chapters Generated',
                'output_format': 'Output Format',
                'format_pdf': '📄 PDF',
                'format_docx': '📝 DOCX',
                'format_epub': '📖 EPUB',
                'format_desc_pdf': '📄 PDF - Universal format with professional styling',
                'format_desc_docx': '📝 DOCX - Editable document for Microsoft Word',
                'format_desc_epub': '📖 EPUB - E-book format for digital readers',
                'success_title': 'Success',
                'success_message': 'Course generated successfully with {chapters} chapters!\nOutput format: {format}',
            },
            'RU': {
                'forge': 'Создать',
                'library': 'Библиотека',
                'settings': 'Настройки',
                'start_forge': 'Начать создание',
                'course_topic': 'Тема курса',
                'target_audience': 'Целевая аудитория',
                'chapter_count': 'Главы',
                'generating': 'Создание вашего курса...',
                'complete': 'Курс готов!',
                'progress': 'Прогресс',
                'cancel': 'Отмена',
                'export': 'Экспорт PDF',
                'chapters_label': 'Создано глав',
                'output_format': 'Формат вывода',
                'format_pdf': '📄 PDF',
                'format_docx': '📝 DOCX',
                'format_epub': '📖 EPUB',
                'format_desc_pdf': '📄 PDF - Универсальный формат с профессиональным оформлением',
                'format_desc_docx': '📝 DOCX - Редактируемый документ для Microsoft Word',
                'format_desc_epub': '📖 EPUB - Формат электронных книг для читалок',
                'success_title': 'Успех',
                'success_message': 'Курс успешно создан с {chapters} главами!\nФормат вывода: {format}',
            }
        }
        return translations.get(self.current_lang, {}).get(key, key)


class AnimatedBorderFrame(ctk.CTkFrame):
    """Frame with animated border glow effect."""
    
    def __init__(self, master, **kwargs):
        """Initialize animated border frame."""
        super().__init__(master, **kwargs)
        self.border_opacity = 0.3
        self.animation_direction = 1
        self.is_animating = False
        
    def start_animation(self):
        """Start border glow animation."""
        if not self.is_animating:
            self.is_animating = True
            self._animate_step()
    
    def stop_animation(self):
        """Stop border glow animation."""
        self.is_animating = False
        self.border_opacity = 0.3
        
    def _animate_step(self):
        """Perform one animation step."""
        if not self.is_animating:
            return
            
        # Update opacity
        self.border_opacity += 0.02 * self.animation_direction
        
        # Reverse direction at limits
        if self.border_opacity >= 1.0:
            self.border_opacity = 1.0
            self.animation_direction = -1
        elif self.border_opacity <= 0.3:
            self.border_opacity = 0.3
            self.animation_direction = 1
        
        # Calculate color with opacity
        base_color = int(COLORS['accent'][1:], 16)
        r = (base_color >> 16) & 0xFF
        g = (base_color >> 8) & 0xFF
        b = base_color & 0xFF
        
        # Apply opacity
        r = int(r * self.border_opacity)
        g = int(g * self.border_opacity)
        b = int(b * self.border_opacity)
        
        new_color = f'#{r:02x}{g:02x}{b:02x}'
        
        try:
            self.configure(border_color=new_color)
        except:
            pass
        
        # Schedule next step
        if self.is_animating:
            self.after(50, self._animate_step)


class SmoothProgressBar(ctk.CTkProgressBar):
    """Progress bar with smooth step animation."""
    
    def __init__(self, master, **kwargs):
        """Initialize smooth progress bar."""
        super().__init__(master, **kwargs)
        self.target_value = 0.0
        self.current_value = 0.0
        self.is_animating = False
        
    def set_target(self, value):
        """Set target progress value with smooth animation."""
        self.target_value = max(0.0, min(1.0, value))
        if not self.is_animating:
            self.is_animating = True
            self._animate_progress()
    
    def _animate_progress(self):
        """Animate progress toward target."""
        if not self.is_animating:
            return
        
        # Calculate step size
        diff = self.target_value - self.current_value
        step = diff * 0.15  # Smooth easing
        
        # Update current value
        if abs(diff) < 0.001:
            self.current_value = self.target_value
            self.is_animating = False
        else:
            self.current_value += step
        
        # Update UI
        self.set(self.current_value)
        
        # Continue animation
        if self.is_animating:
            self.after(30, self._animate_progress)


class PremiumButton(ctk.CTkButton):
    """Button with premium glow effect."""
    
    def __init__(self, master, glow=False, **kwargs):
        """Initialize premium button."""
        super().__init__(master, **kwargs)
        self.has_glow = glow
        self.glow_opacity = 0.5
        self.glow_direction = 1
        
        if self.has_glow:
            self._start_glow()
    
    def _start_glow(self):
        """Start glow animation."""
        self._animate_glow()
    
    def _animate_glow(self):
        """Animate button glow."""
        if not self.has_glow:
            return
        
        # Update glow opacity
        self.glow_opacity += 0.03 * self.glow_direction
        
        # Reverse at limits
        if self.glow_opacity >= 1.0:
            self.glow_opacity = 1.0
            self.glow_direction = -1
        elif self.glow_opacity <= 0.5:
            self.glow_opacity = 0.5
            self.glow_direction = 1
        
        # Calculate glow color
        base = int(COLORS['accent'][1:], 16)
        r = (base >> 16) & 0xFF
        g = (base >> 8) & 0xFF
        b = base & 0xFF
        
        # Apply glow
        r = int(r * self.glow_opacity)
        g = int(g * self.glow_opacity)
        b = int(b * self.glow_opacity)
        
        glow_color = f'#{r:02x}{g:02x}{b:02x}'
        
        try:
            self.configure(fg_color=glow_color)
        except:
            pass
        
        # Continue animation
        if self.has_glow:
            self.after(50, self._animate_glow)


class CustomApp(ctk.CTk):
    """Custom high-end UI for CourseSmith AI."""
    
    def __init__(self):
        """Initialize the custom application."""
        super().__init__()
        
        # Window configuration
        self.title("CourseSmith AI - Premium Edition")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Set custom background
        self.configure(fg_color=COLORS['background'])
        
        # Initialize language manager
        self.lang = LanguageManager()
        
        # Initialize project and state
        self.project = CourseProject()
        self.is_generating = False
        self.current_page = 'forge'
        self.chapter_count = 0
        self.total_chapters = 10
        
        # Create UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the main UI layout."""
        # Create sidebar
        self._create_sidebar()
        
        # Create main content area
        self._create_main_area()
        
        # Show forge page by default
        self._show_forge_page()
    
    def _create_sidebar(self):
        """Create fixed sidebar with navigation."""
        self.sidebar = ctk.CTkFrame(
            self,
            width=SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=COLORS['sidebar']
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        
        # Logo/Title
        logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color='transparent'
        )
        logo_frame.pack(pady=(30, 40))
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="📚",
            font=ctk.CTkFont(size=48)
        )
        logo_label.pack()
        
        title_label = ctk.CTkLabel(
            logo_frame,
            text="CourseSmith",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title_label.pack(pady=(5, 0))
        
        # Navigation buttons
        self.nav_buttons = {}
        
        nav_items = ['forge', 'library', 'settings']
        for item in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=self.lang.get(item),
                corner_radius=20,
                height=50,
                font=ctk.CTkFont(size=14),
                fg_color='transparent',
                text_color=COLORS['text_secondary'],
                hover_color=COLORS['card'],
                anchor='w',
                command=lambda p=item: self._switch_page(p)
            )
            btn.pack(padx=15, pady=5, fill='x')
            self.nav_buttons[item] = btn
        
        # Language toggle at bottom
        lang_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color='transparent'
        )
        lang_frame.pack(side='bottom', pady=20)
        
        self.lang_button = ctk.CTkButton(
            lang_frame,
            text=f"🌐 {self.lang.current_lang}",
            corner_radius=20,
            height=35,
            width=100,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS['card'],
            text_color=COLORS['text_secondary'],
            hover_color=COLORS['accent'],
            command=self._toggle_language
        )
        self.lang_button.pack()
        
    def _create_main_area(self):
        """Create main content area."""
        self.main_area = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=COLORS['background']
        )
        self.main_area.grid(row=0, column=1, sticky="nsew")
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _switch_page(self, page):
        """Switch to a different page."""
        self.current_page = page
        
        # Update button colors
        for name, btn in self.nav_buttons.items():
            if name == page:
                btn.configure(
                    fg_color=COLORS['accent'],
                    text_color=COLORS['text_primary']
                )
            else:
                btn.configure(
                    fg_color='transparent',
                    text_color=COLORS['text_secondary']
                )
        
        # Clear main area
        for widget in self.main_area.winfo_children():
            widget.destroy()
        
        # Show appropriate page
        if page == 'forge':
            self._show_forge_page()
        elif page == 'library':
            self._show_library_page()
        elif page == 'settings':
            self._show_settings_page()
    
    def _show_forge_page(self):
        """Show the Forge (Generator) page."""
        # Highlight forge button
        self.nav_buttons['forge'].configure(
            fg_color=COLORS['accent'],
            text_color=COLORS['text_primary']
        )
        
        # Create content frame with padding
        content = ctk.CTkFrame(
            self.main_area,
            fg_color='transparent'
        )
        content.pack(fill='both', expand=True, padx=40, pady=30)
        
        # Page title
        title_label = ctk.CTkLabel(
            content,
            text=self.lang.get('forge'),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title_label.pack(anchor='w', pady=(0, 30))
        
        # Input card
        input_card = ctk.CTkFrame(
            content,
            corner_radius=20,
            fg_color=COLORS['card'],
            border_width=2,
            border_color=COLORS['border']
        )
        input_card.pack(fill='x', pady=(0, 20))
        
        # Make it an animated border frame
        self.input_border_frame = AnimatedBorderFrame(
            content,
            corner_radius=20,
            fg_color=COLORS['card'],
            border_width=2,
            border_color=COLORS['border']
        )
        self.input_border_frame.pack(fill='x', pady=(0, 20))
        
        input_inner = ctk.CTkFrame(
            self.input_border_frame,
            fg_color='transparent'
        )
        input_inner.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Course topic
        topic_label = ctk.CTkLabel(
            input_inner,
            text=self.lang.get('course_topic'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        topic_label.pack(anchor='w', pady=(0, 8))
        
        self.topic_entry = ctk.CTkEntry(
            input_inner,
            height=45,
            corner_radius=15,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['background'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary']
        )
        self.topic_entry.pack(fill='x', pady=(0, 20))
        
        # Target audience
        audience_label = ctk.CTkLabel(
            input_inner,
            text=self.lang.get('target_audience'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        audience_label.pack(anchor='w', pady=(0, 8))
        
        self.audience_entry = ctk.CTkEntry(
            input_inner,
            height=45,
            corner_radius=15,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['background'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary']
        )
        self.audience_entry.pack(fill='x', pady=(0, 20))
        
        # Chapter count
        chapters_label = ctk.CTkLabel(
            input_inner,
            text=self.lang.get('chapter_count'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        chapters_label.pack(anchor='w', pady=(0, 8))
        
        self.chapters_slider = ctk.CTkSlider(
            input_inner,
            from_=5,
            to=15,
            number_of_steps=10,
            height=20,
            button_color=COLORS['accent'],
            button_hover_color=COLORS['accent_hover'],
            progress_color=COLORS['accent'],
            fg_color=COLORS['background']
        )
        self.chapters_slider.set(10)
        self.chapters_slider.pack(fill='x', pady=(0, 10))
        
        self.chapters_value_label = ctk.CTkLabel(
            input_inner,
            text="10",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        self.chapters_value_label.pack(anchor='w')
        
        # Update chapter count display
        def update_chapter_label(value):
            self.chapters_value_label.configure(text=str(int(value)))
            self.total_chapters = int(value)
        
        self.chapters_slider.configure(command=update_chapter_label)
        
        # Output Format selector
        format_label = ctk.CTkLabel(
            input_inner,
            text=self.lang.get('output_format'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        format_label.pack(anchor='w', pady=(20, 8))
        
        # Format buttons frame
        format_buttons_frame = ctk.CTkFrame(
            input_inner,
            fg_color='transparent'
        )
        format_buttons_frame.pack(fill='x', pady=(0, 10))
        
        # Store selected format
        self.selected_format = ctk.StringVar(value='PDF')
        
        # Create format toggle buttons using translations
        self.format_buttons = {}
        formats = ['PDF', 'DOCX', 'EPUB']
        
        for idx, fmt in enumerate(formats):
            btn = ctk.CTkButton(
                format_buttons_frame,
                text=self.lang.get(f'format_{fmt.lower()}'),
                corner_radius=15,
                height=45,
                width=100,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=COLORS['accent'] if fmt == 'PDF' else COLORS['background'],
                text_color=COLORS['text_primary'] if fmt == 'PDF' else COLORS['text_secondary'],
                hover_color=COLORS['accent_hover'],
                border_width=2,
                border_color=COLORS['accent'] if fmt == 'PDF' else COLORS['border'],
                command=lambda f=fmt: self._select_format(f)
            )
            btn.pack(side='left', padx=(0 if idx == 0 else 10, 0))
            self.format_buttons[fmt] = btn
        
        # Format description label using translation
        self.format_description_label = ctk.CTkLabel(
            input_inner,
            text=self.lang.get('format_desc_pdf'),
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        self.format_description_label.pack(anchor='w', pady=(0, 10))
        
        # Start Forge button with glow
        self.start_button = PremiumButton(
            input_inner,
            text=self.lang.get('start_forge'),
            height=60,
            corner_radius=20,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color=COLORS['text_primary'],
            glow=True,
            command=self._start_generation
        )
        self.start_button.pack(fill='x', pady=(20, 0))
        
        # Progress section (initially hidden)
        self.progress_frame = ctk.CTkFrame(
            content,
            corner_radius=20,
            fg_color=COLORS['card']
        )
        # Don't pack yet
        
        progress_inner = ctk.CTkFrame(
            self.progress_frame,
            fg_color='transparent'
        )
        progress_inner.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Progress title
        self.progress_title = ctk.CTkLabel(
            progress_inner,
            text=self.lang.get('generating'),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        self.progress_title.pack(anchor='w', pady=(0, 20))
        
        # Smooth progress bar
        self.progress_bar = SmoothProgressBar(
            progress_inner,
            height=25,
            corner_radius=15,
            progress_color=COLORS['accent'],
            fg_color=COLORS['background']
        )
        self.progress_bar.pack(fill='x', pady=(0, 15))
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            progress_inner,
            text=f"{self.lang.get('chapters_label')}: 0/10",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_secondary']
        )
        self.progress_label.pack(anchor='w')
    
    def _show_library_page(self):
        """Show the Library page."""
        content = ctk.CTkFrame(
            self.main_area,
            fg_color='transparent'
        )
        content.pack(fill='both', expand=True, padx=40, pady=30)
        
        title_label = ctk.CTkLabel(
            content,
            text=self.lang.get('library'),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title_label.pack(anchor='w', pady=(0, 30))
        
        # Placeholder for library content
        placeholder = ctk.CTkLabel(
            content,
            text="📚 Your generated courses will appear here",
            font=ctk.CTkFont(size=16),
            text_color=COLORS['text_secondary']
        )
        placeholder.pack(pady=50)
    
    def _show_settings_page(self):
        """Show the Settings page."""
        content = ctk.CTkFrame(
            self.main_area,
            fg_color='transparent'
        )
        content.pack(fill='both', expand=True, padx=40, pady=30)
        
        title_label = ctk.CTkLabel(
            content,
            text=self.lang.get('settings'),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title_label.pack(anchor='w', pady=(0, 30))
        
        # Settings card
        settings_card = ctk.CTkFrame(
            content,
            corner_radius=20,
            fg_color=COLORS['card']
        )
        settings_card.pack(fill='x')
        
        settings_inner = ctk.CTkFrame(
            settings_card,
            fg_color='transparent'
        )
        settings_inner.pack(fill='both', expand=True, padx=30, pady=30)
        
        # API Key setting
        api_label = ctk.CTkLabel(
            settings_inner,
            text="OpenAI API Key",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        api_label.pack(anchor='w', pady=(0, 8))
        
        api_entry = ctk.CTkEntry(
            settings_inner,
            height=45,
            corner_radius=15,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['background'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary'],
            show="*"
        )
        api_entry.pack(fill='x', pady=(0, 20))
        
        save_btn = ctk.CTkButton(
            settings_inner,
            text="Save Settings",
            height=45,
            corner_radius=20,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color=COLORS['text_primary']
        )
        save_btn.pack(fill='x')
    
    def _select_format(self, format_name):
        """Handle format selection button click."""
        self.selected_format.set(format_name)
        
        # Update button styles to show selection
        for fmt, btn in self.format_buttons.items():
            if fmt == format_name:
                btn.configure(
                    fg_color=COLORS['accent'],
                    text_color=COLORS['text_primary'],
                    border_color=COLORS['accent']
                )
            else:
                btn.configure(
                    fg_color=COLORS['background'],
                    text_color=COLORS['text_secondary'],
                    border_color=COLORS['border']
                )
        
        # Update format description using translation system
        description_key = f'format_desc_{format_name.lower()}'
        if hasattr(self, 'format_description_label'):
            self.format_description_label.configure(text=self.lang.get(description_key))
    
    def _toggle_language(self):
        """Toggle between EN and RU languages."""
        self.lang.toggle_language()
        self.lang_button.configure(text=f"🌐 {self.lang.current_lang}")
        
        # Refresh current page to update labels
        self._switch_page(self.current_page)
    
    def _start_generation(self):
        """Start course generation process."""
        topic = self.topic_entry.get().strip()
        audience = self.audience_entry.get().strip()
        
        if not topic:
            messagebox.showwarning("Input Required", "Please enter a course topic")
            return
        
        if not audience:
            messagebox.showwarning("Input Required", "Please enter a target audience")
            return
        
        # Disable inputs
        self.is_generating = True
        self.topic_entry.configure(state='disabled')
        self.audience_entry.configure(state='disabled')
        self.chapters_slider.configure(state='disabled')
        self.start_button.configure(state='disabled')
        
        # Disable format buttons
        for btn in self.format_buttons.values():
            btn.configure(state='disabled')
        
        # Start border animation
        self.input_border_frame.start_animation()
        
        # Show progress frame
        self.progress_frame.pack(fill='x', pady=(20, 0))
        
        # Reset progress
        self.chapter_count = 0
        self.progress_bar.set_target(0.0)
        self.progress_label.configure(
            text=f"{self.lang.get('chapters_label')}: 0/{self.total_chapters}"
        )
        
        # Simulate generation (replace with actual generation)
        self._simulate_generation()
    
    def _simulate_generation(self):
        """Simulate course generation with progress updates."""
        def generate():
            for i in range(self.total_chapters):
                time.sleep(1.5)  # Simulate chapter generation time
                
                # Update progress on main thread
                self.after(0, self._update_progress, i + 1)
            
            # Complete
            self.after(0, self._generation_complete)
        
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
    
    def _update_progress(self, chapter_num):
        """Update progress display."""
        self.chapter_count = chapter_num
        progress_value = chapter_num / self.total_chapters
        
        self.progress_bar.set_target(progress_value)
        self.progress_label.configure(
            text=f"{self.lang.get('chapters_label')}: {chapter_num}/{self.total_chapters}"
        )
    
    def _generation_complete(self):
        """Handle generation completion."""
        self.is_generating = False
        
        # Stop animations
        self.input_border_frame.stop_animation()
        
        # Update UI
        self.progress_title.configure(text=self.lang.get('complete'))
        
        # Re-enable controls
        self.topic_entry.configure(state='normal')
        self.audience_entry.configure(state='normal')
        self.chapters_slider.configure(state='normal')
        self.start_button.configure(state='normal')
        
        # Re-enable format buttons
        for btn in self.format_buttons.values():
            btn.configure(state='normal')
        
        # Show success message with format info using translation
        selected_format = self.selected_format.get()
        success_message = self.lang.get('success_message').format(
            chapters=self.total_chapters,
            format=selected_format
        )
        messagebox.showinfo(
            self.lang.get('success_title'),
            success_message
        )


def main():
    """Main entry point."""
    # Set appearance
    ctk.set_appearance_mode("Dark")
    
    # Create and run app
    app = CustomApp()
    app.mainloop()


if __name__ == "__main__":
    main()
