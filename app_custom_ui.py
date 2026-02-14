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
                'account': 'Account',
                'start_forge': 'Generate Product',
                'course_topic': 'Topic',
                'target_audience': 'Target Audience',
                'chapter_count': 'Chapters',
                'generating': 'Generating your product...',
                'complete': 'Product Complete!',
                'progress': 'Progress',
                'cancel': 'Cancel',
                'export': 'Export',
                'chapters_label': 'Sections Generated',
                'product_type': 'Product Type',
                'export_formats': 'Export Formats',
                'credits_needed': 'Credits Required',
                'credits_available': 'Credits Available',
                'filter_by_type': 'Filter by Type',
                'all_types': 'All Types',
                'date': 'Date',
                'credits_used': 'Credits Used',
                'total_products': 'Total Products',
                'total_credits_spent': 'Total Credits Spent',
                'license_tier': 'License Tier',
                'products_this_month': 'Products This Month',
                'select_product_type': 'Select Product Type',
                'select_formats': 'Select Export Formats',
            },
            'RU': {
                'forge': 'Создать',
                'library': 'Библиотека',
                'settings': 'Настройки',
                'account': 'Аккаунт',
                'start_forge': 'Создать продукт',
                'course_topic': 'Тема',
                'target_audience': 'Целевая аудитория',
                'chapter_count': 'Главы',
                'generating': 'Создание вашего продукта...',
                'complete': 'Продукт готов!',
                'progress': 'Прогресс',
                'cancel': 'Отмена',
                'export': 'Экспорт',
                'chapters_label': 'Создано разделов',
                'product_type': 'Тип продукта',
                'export_formats': 'Форматы экспорта',
                'credits_needed': 'Требуется кредитов',
                'credits_available': 'Доступно кредитов',
                'filter_by_type': 'Фильтр по типу',
                'all_types': 'Все типы',
                'date': 'Дата',
                'credits_used': 'Использовано кредитов',
                'total_products': 'Всего продуктов',
                'total_credits_spent': 'Всего потрачено кредитов',
                'license_tier': 'Тип лицензии',
                'products_this_month': 'Продуктов за месяц',
                'select_product_type': 'Выберите тип продукта',
                'select_formats': 'Выберите форматы экспорта',
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
    """Custom high-end UI for CourseSmith AI - AI Digital Product Factory."""
    
    def __init__(self):
        """Initialize the custom application."""
        super().__init__()
        
        # Window configuration
        self.title("CourseSmith AI - Digital Product Factory")
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
        
        # Product type and export format selections
        self.selected_product_type = 'full_course'
        self.selected_export_formats = {'pdf': True, 'docx': False, 'markdown': False, 'html': False}
        
        # Load product templates
        try:
            from product_templates import get_all_templates, get_template_info_for_ui
            self.product_templates = get_template_info_for_ui()
        except ImportError:
            self.product_templates = []
        
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
            text="🏭",
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
        
        subtitle_label = ctk.CTkLabel(
            logo_frame,
            text="Product Factory",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        subtitle_label.pack()
        
        # Navigation buttons - now with Account page
        self.nav_buttons = {}
        
        nav_items = ['forge', 'library', 'account', 'settings']
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
        elif page == 'account':
            self._show_account_page()
        elif page == 'settings':
            self._show_settings_page()
    
    def _show_forge_page(self):
        """Show the Forge (Generator) page with product type selection."""
        # Highlight forge button
        self.nav_buttons['forge'].configure(
            fg_color=COLORS['accent'],
            text_color=COLORS['text_primary']
        )
        
        # Create scrollable content frame
        content = ctk.CTkScrollableFrame(
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
        
        # ===== PRODUCT TYPE SELECTION =====
        type_label = ctk.CTkLabel(
            input_inner,
            text=self.lang.get('select_product_type'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        type_label.pack(anchor='w', pady=(0, 12))
        
        # Product type cards container
        types_frame = ctk.CTkFrame(input_inner, fg_color='transparent')
        types_frame.pack(fill='x', pady=(0, 20))
        
        self.type_buttons = {}
        self.product_type_var = ctk.StringVar(value=self.selected_product_type)
        
        # Create grid of product type buttons
        for i, template in enumerate(self.product_templates):
            row = i // 3
            col = i % 3
            
            btn_frame = ctk.CTkFrame(
                types_frame,
                corner_radius=15,
                fg_color=COLORS['background'] if template['id'] != self.selected_product_type else COLORS['accent'],
                border_width=1,
                border_color=COLORS['border']
            )
            btn_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            types_frame.grid_columnconfigure(col, weight=1)
            
            btn_inner = ctk.CTkFrame(btn_frame, fg_color='transparent')
            btn_inner.pack(fill='both', expand=True, padx=12, pady=10)
            
            # Icon and name
            header = ctk.CTkLabel(
                btn_inner,
                text=f"{template['icon']} {template['name']}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=COLORS['text_primary']
            )
            header.pack(anchor='w')
            
            # Credits info
            credits_text = ctk.CTkLabel(
                btn_inner,
                text=f"{template['credits']} credit(s) • {template['chapters']} sections",
                font=ctk.CTkFont(size=10),
                text_color=COLORS['text_secondary']
            )
            credits_text.pack(anchor='w')
            
            # Make the frame clickable
            btn_frame.bind('<Button-1>', lambda e, t_id=template['id']: self._select_product_type(t_id))
            btn_inner.bind('<Button-1>', lambda e, t_id=template['id']: self._select_product_type(t_id))
            header.bind('<Button-1>', lambda e, t_id=template['id']: self._select_product_type(t_id))
            credits_text.bind('<Button-1>', lambda e, t_id=template['id']: self._select_product_type(t_id))
            
            self.type_buttons[template['id']] = btn_frame
        
        # ===== TOPIC INPUT =====
        topic_label = ctk.CTkLabel(
            input_inner,
            text=self.lang.get('course_topic'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        topic_label.pack(anchor='w', pady=(10, 8))
        
        self.topic_entry = ctk.CTkEntry(
            input_inner,
            height=45,
            corner_radius=15,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['background'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary'],
            placeholder_text="e.g., Python Programming, Digital Marketing, Personal Finance..."
        )
        self.topic_entry.pack(fill='x', pady=(0, 20))
        
        # ===== AUDIENCE INPUT =====
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
            text_color=COLORS['text_primary'],
            placeholder_text="e.g., Beginners, Business Owners, Students..."
        )
        self.audience_entry.pack(fill='x', pady=(0, 20))
        
        # ===== EXPORT FORMATS SELECTION =====
        formats_label = ctk.CTkLabel(
            input_inner,
            text=self.lang.get('select_formats'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        formats_label.pack(anchor='w', pady=(0, 12))
        
        formats_frame = ctk.CTkFrame(input_inner, fg_color='transparent')
        formats_frame.pack(fill='x', pady=(0, 20))
        
        self.format_checkboxes = {}
        export_formats = [
            {'id': 'pdf', 'name': 'PDF', 'icon': '📄'},
            {'id': 'docx', 'name': 'DOCX', 'icon': '📝'},
            {'id': 'markdown', 'name': 'Markdown', 'icon': '📋'},
            {'id': 'html', 'name': 'HTML', 'icon': '🌐'}
        ]
        
        for i, fmt in enumerate(export_formats):
            var = ctk.BooleanVar(value=self.selected_export_formats.get(fmt['id'], False))
            cb = ctk.CTkCheckBox(
                formats_frame,
                text=f"{fmt['icon']} {fmt['name']}",
                variable=var,
                font=ctk.CTkFont(size=13),
                fg_color=COLORS['accent'],
                hover_color=COLORS['accent_hover'],
                text_color=COLORS['text_primary'],
                command=lambda f_id=fmt['id'], v=var: self._toggle_format(f_id, v)
            )
            cb.grid(row=0, column=i, padx=10, pady=5, sticky='w')
            self.format_checkboxes[fmt['id']] = var
        
        # ===== CREDIT INFO =====
        credit_frame = ctk.CTkFrame(input_inner, fg_color=COLORS['background'], corner_radius=10)
        credit_frame.pack(fill='x', pady=(0, 20))
        
        credit_inner = ctk.CTkFrame(credit_frame, fg_color='transparent')
        credit_inner.pack(fill='x', padx=15, pady=10)
        
        self.credit_info_label = ctk.CTkLabel(
            credit_inner,
            text="💳 Credits Required: 3",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        self.credit_info_label.pack(side='left')
        
        # Update credit display
        self._update_credit_display()
        
        # ===== GENERATE BUTTON =====
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
        self.start_button.pack(fill='x', pady=(10, 0))
        
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
        """Show the Library page with filters and product list."""
        content = ctk.CTkFrame(
            self.main_area,
            fg_color='transparent'
        )
        content.pack(fill='both', expand=True, padx=40, pady=30)
        
        # Header with title and filter
        header_frame = ctk.CTkFrame(content, fg_color='transparent')
        header_frame.pack(fill='x', pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=self.lang.get('library'),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title_label.pack(side='left')
        
        # Filter dropdown
        filter_frame = ctk.CTkFrame(header_frame, fg_color='transparent')
        filter_frame.pack(side='right')
        
        filter_label = ctk.CTkLabel(
            filter_frame,
            text=self.lang.get('filter_by_type'),
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary']
        )
        filter_label.pack(side='left', padx=(0, 10))
        
        # Get product types for filter
        filter_options = [self.lang.get('all_types')]
        for t in self.product_templates:
            filter_options.append(f"{t['icon']} {t['name']}")
        
        self.library_filter = ctk.CTkComboBox(
            filter_frame,
            values=filter_options,
            width=180,
            fg_color=COLORS['card'],
            border_color=COLORS['border'],
            button_color=COLORS['accent'],
            dropdown_fg_color=COLORS['card'],
            dropdown_hover_color=COLORS['accent']
        )
        self.library_filter.set(filter_options[0])
        self.library_filter.pack(side='left')
        
        # Products list (scrollable)
        products_scroll = ctk.CTkScrollableFrame(
            content,
            fg_color='transparent'
        )
        products_scroll.pack(fill='both', expand=True)
        
        # Column headers
        headers_frame = ctk.CTkFrame(products_scroll, fg_color=COLORS['card'], corner_radius=10)
        headers_frame.pack(fill='x', pady=(0, 10))
        
        headers = [
            ("Topic", 3),
            ("Type", 1),
            ("Formats", 1),
            (self.lang.get('date'), 1),
            (self.lang.get('credits_used'), 1)
        ]
        
        headers_inner = ctk.CTkFrame(headers_frame, fg_color='transparent')
        headers_inner.pack(fill='x', padx=15, pady=10)
        
        for i, (header_text, weight) in enumerate(headers):
            lbl = ctk.CTkLabel(
                headers_inner,
                text=header_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COLORS['text_secondary']
            )
            lbl.grid(row=0, column=i, sticky='w', padx=10)
            headers_inner.grid_columnconfigure(i, weight=weight)
        
        # Placeholder for empty library
        placeholder = ctk.CTkLabel(
            products_scroll,
            text="📚 Your generated products will appear here\nStart creating in the Forge!",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_secondary'],
            justify='center'
        )
        placeholder.pack(pady=50)
    
    def _show_account_page(self):
        """Show the Account page with statistics."""
        content = ctk.CTkScrollableFrame(
            self.main_area,
            fg_color='transparent'
        )
        content.pack(fill='both', expand=True, padx=40, pady=30)
        
        title_label = ctk.CTkLabel(
            content,
            text=self.lang.get('account'),
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title_label.pack(anchor='w', pady=(0, 30))
        
        # Stats cards grid
        stats_frame = ctk.CTkFrame(content, fg_color='transparent')
        stats_frame.pack(fill='x', pady=(0, 30))
        
        # Get credit info
        try:
            from ai_worker import check_remaining_credits
            credit_info = check_remaining_credits()
            credits_available = credit_info.get('credits', 0)
        except:
            credits_available = 0
        
        # Get tier
        try:
            from session_manager import get_tier
            tier = get_tier() or 'trial'
        except:
            tier = 'trial'
        
        # Stats data
        stats = [
            {"icon": "💳", "label": self.lang.get('credits_available'), "value": str(credits_available)},
            {"icon": "⭐", "label": self.lang.get('license_tier'), "value": tier.title()},
            {"icon": "📦", "label": self.lang.get('total_products'), "value": "0"},
            {"icon": "📊", "label": self.lang.get('total_credits_spent'), "value": "0"},
        ]
        
        for i, stat in enumerate(stats):
            card = ctk.CTkFrame(
                stats_frame,
                corner_radius=15,
                fg_color=COLORS['card'],
                border_width=1,
                border_color=COLORS['border']
            )
            card.grid(row=0, column=i, padx=10, pady=10, sticky='nsew')
            stats_frame.grid_columnconfigure(i, weight=1)
            
            card_inner = ctk.CTkFrame(card, fg_color='transparent')
            card_inner.pack(fill='both', expand=True, padx=20, pady=20)
            
            icon_label = ctk.CTkLabel(
                card_inner,
                text=stat['icon'],
                font=ctk.CTkFont(size=32)
            )
            icon_label.pack()
            
            value_label = ctk.CTkLabel(
                card_inner,
                text=stat['value'],
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=COLORS['text_primary']
            )
            value_label.pack(pady=(5, 0))
            
            label_label = ctk.CTkLabel(
                card_inner,
                text=stat['label'],
                font=ctk.CTkFont(size=11),
                text_color=COLORS['text_secondary']
            )
            label_label.pack()
        
        # Credit costs info
        info_card = ctk.CTkFrame(
            content,
            corner_radius=20,
            fg_color=COLORS['card']
        )
        info_card.pack(fill='x', pady=(0, 20))
        
        info_inner = ctk.CTkFrame(info_card, fg_color='transparent')
        info_inner.pack(fill='both', padx=30, pady=30)
        
        info_title = ctk.CTkLabel(
            info_inner,
            text="💡 Credit Costs by Product Type",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        )
        info_title.pack(anchor='w', pady=(0, 15))
        
        for template in self.product_templates:
            cost_row = ctk.CTkFrame(info_inner, fg_color='transparent')
            cost_row.pack(fill='x', pady=3)
            
            name_label = ctk.CTkLabel(
                cost_row,
                text=f"{template['icon']} {template['name']}",
                font=ctk.CTkFont(size=13),
                text_color=COLORS['text_primary']
            )
            name_label.pack(side='left')
            
            cost_label = ctk.CTkLabel(
                cost_row,
                text=f"{template['credits']} credit(s)",
                font=ctk.CTkFont(size=13),
                text_color=COLORS['accent']
            )
            cost_label.pack(side='right')
    
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
        
        # Info section (API key is managed internally)
        info_label = ctk.CTkLabel(
            settings_inner,
            text="ℹ️ API Configuration",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        info_label.pack(anchor='w', pady=(0, 8))
        
        info_text = ctk.CTkLabel(
            settings_inner,
            text="API access is managed automatically. Credits are deducted from your license when generating courses.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_secondary'],
            wraplength=400,
            justify="left"
        )
        info_text.pack(anchor='w', pady=(0, 20))
    
    def _select_product_type(self, product_type_id):
        """Handle product type selection."""
        self.selected_product_type = product_type_id
        
        # Update button styles
        for t_id, btn_frame in self.type_buttons.items():
            if t_id == product_type_id:
                btn_frame.configure(fg_color=COLORS['accent'])
            else:
                btn_frame.configure(fg_color=COLORS['background'])
        
        # Update credit display
        self._update_credit_display()
        
        # Update total chapters based on template
        for template in self.product_templates:
            if template['id'] == product_type_id:
                self.total_chapters = template['chapters']
                break
    
    def _toggle_format(self, format_id, var):
        """Handle export format checkbox toggle."""
        self.selected_export_formats[format_id] = var.get()
        
        # Ensure at least one format is selected
        if not any(self.selected_export_formats.values()):
            self.selected_export_formats['pdf'] = True
            # Reset PDF checkbox to checked state
            if 'pdf' in self.format_checkboxes:
                self.format_checkboxes['pdf'].set(True)
    
    def _update_credit_display(self):
        """Update the credit cost display based on selected product type."""
        try:
            from product_templates import get_credit_cost
            credits_needed = get_credit_cost(self.selected_product_type)
        except ImportError:
            credits_needed = 3
        
        if hasattr(self, 'credit_info_label'):
            self.credit_info_label.configure(
                text=f"💳 Credits Required: {credits_needed}"
            )
    
    def _get_selected_formats(self):
        """Get list of selected export format IDs."""
        return [fmt_id for fmt_id, selected in self.selected_export_formats.items() if selected]
    
    def _toggle_language(self):
        """Toggle between EN and RU languages."""
        self.lang.toggle_language()
        self.lang_button.configure(text=f"🌐 {self.lang.current_lang}")
        
        # Refresh current page to update labels
        self._switch_page(self.current_page)
    
    def _start_generation(self):
        """Start product generation process with selected template and formats."""
        topic = self.topic_entry.get().strip()
        audience = self.audience_entry.get().strip()
        
        if not topic:
            messagebox.showwarning("Input Required", "Please enter a topic")
            return
        
        if not audience:
            messagebox.showwarning("Input Required", "Please enter a target audience")
            return
        
        # Get selected export formats
        export_formats = self._get_selected_formats()
        if not export_formats:
            export_formats = ['pdf']
        
        # Setup project with selected options
        self.project = CourseProject()
        self.project.set_topic(topic)
        self.project.set_audience(audience)
        self.project.set_product_type(self.selected_product_type)
        self.project.set_export_formats(export_formats)
        
        # Disable inputs
        self.is_generating = True
        self.topic_entry.configure(state='disabled')
        self.audience_entry.configure(state='disabled')
        self.start_button.configure(state='disabled')
        
        # Disable product type buttons
        for btn_frame in self.type_buttons.values():
            for child in btn_frame.winfo_children():
                try:
                    child.configure(state='disabled')
                except:
                    pass
        
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
        """Simulate product generation with progress updates."""
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
        self.start_button.configure(state='normal')
        
        # Re-enable product type buttons
        for btn_frame in self.type_buttons.values():
            for child in btn_frame.winfo_children():
                try:
                    child.configure(state='normal')
                except:
                    pass
        
        # Get product type name for message
        product_name = "Product"
        for template in self.product_templates:
            if template['id'] == self.selected_product_type:
                product_name = template['name']
                break
        
        # Get selected formats
        formats = self._get_selected_formats()
        formats_str = ", ".join([f.upper() for f in formats])
        
        # Show success message
        messagebox.showinfo(
            "Success",
            f"{product_name} generated successfully!\n\n"
            f"Sections: {self.total_chapters}\n"
            f"Export formats: {formats_str}"
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
