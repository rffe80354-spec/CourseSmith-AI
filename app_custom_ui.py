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

from utils import resource_path, get_data_dir, patch_ctk_scrollbar, generate_pdf
from license_guard import validate_license, load_license, save_license, remove_license
from session_manager import set_session, is_active, get_tier, clear_session, get_user_email, get_license_key
from project_manager import CourseProject
from ai_worker import OutlineGenerator, ChapterWriter, CoverGenerator
from pdf_engine import PDFBuilder
from docx_exporter import DOCXExporter
from html_exporter import HTMLExporter
from epub_exporter import EPUBExporter
from markdown_exporter import MarkdownExporter

# Apply scrollbar patch to prevent RecursionError in CTkScrollableFrame
patch_ctk_scrollbar()


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

# Button color constants for format selector - selected vs unselected states
FORMAT_BTN_SELECTED = {"fg": "#7F5AF0", "hover": "#9D7BF5", "border": "#9D7BF5"}
FORMAT_BTN_UNSELECTED = {"fg": "#2A3142", "hover": "#3A4152", "border": "#3A4152"}

# Sidebar width constant
SIDEBAR_WIDTH = 200

# Max length for prompt text in log messages
MAX_PROMPT_LOG_LENGTH = 50


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
                'prompt_label': 'Generation Instructions (Prompt)',
                'login_title': 'Login',
                'email': 'Email',
                'license_key': 'License Key',
                'login_button': 'Login',
                'login_error': 'Login Error',
                'login_required': 'Please enter email and license key',
                'user_header': 'User Profile',
                'credit_balance': 'Credit Balance',
                'upgrade_plan': 'Upgrade Plan',
                'topup_credits': 'Top Up Credits',
                'statistics': 'Statistics',
                'last_activity': 'Last Activity',
                'current_model': 'AI Model',
                'api_status': 'API Status',
                'generation_history': 'Generation History',
                'product_name': 'Product Name',
                'status': 'Status',
                'no_history': 'No generation history yet',
                'api_online': 'Online',
                'api_offline': 'Offline',
                'checking': 'Checking...',
                'never': 'Never',
                'logout': 'Logout',
                'reset_session': 'Reset Session',
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
                'prompt_label': 'Инструкция для генерации (Промт)',
                'login_title': 'Вход',
                'email': 'Email',
                'license_key': 'Лицензионный ключ',
                'login_button': 'Войти',
                'login_error': 'Ошибка входа',
                'login_required': 'Пожалуйста, введите email и лицензионный ключ',
                'user_header': 'Профиль пользователя',
                'credit_balance': 'Баланс кредитов',
                'upgrade_plan': 'Улучшить план',
                'topup_credits': 'Пополнить баланс',
                'statistics': 'Статистика',
                'last_activity': 'Последняя активность',
                'current_model': 'AI Модель',
                'api_status': 'Статус API',
                'generation_history': 'История генераций',
                'product_name': 'Название продукта',
                'status': 'Статус',
                'no_history': 'История генераций пуста',
                'api_online': 'Онлайн',
                'api_offline': 'Офлайн',
                'checking': 'Проверка...',
                'never': 'Никогда',
                'logout': 'Выход',
                'reset_session': 'Сбросить сессию',
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
        self.selected_export_formats = {'pdf': True, 'docx': False, 'html': False, 'epub': False, 'markdown': False}
        
        # Load product templates
        try:
            from product_templates import get_all_templates, get_template_info_for_ui
            self.product_templates = get_template_info_for_ui()
        except ImportError:
            self.product_templates = []
        
        # DRM: Always show login screen (force user to click Login each time)
        # but auto-fill saved credentials for convenience
        self._show_login_screen()
        
        # Setup keyboard shortcuts for EN/RU layouts
        self._setup_keyboard_shortcuts()
    
    def _show_login_screen(self):
        """Show the login screen for license validation."""
        # Clear any existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Create login container centered on screen
        login_container = ctk.CTkFrame(
            self,
            fg_color=COLORS['card'],
            corner_radius=20,
            border_width=2,
            border_color=COLORS['border']
        )
        login_container.place(relx=0.5, rely=0.5, anchor='center')
        
        login_inner = ctk.CTkFrame(login_container, fg_color='transparent')
        login_inner.pack(padx=50, pady=40)
        
        # Logo/Title
        logo_label = ctk.CTkLabel(
            login_inner,
            text="🏭",
            font=ctk.CTkFont(size=64)
        )
        logo_label.pack(pady=(0, 10))
        
        title_label = ctk.CTkLabel(
            login_inner,
            text="CourseSmith AI",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS['text_primary']
        )
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ctk.CTkLabel(
            login_inner,
            text="Digital Product Factory",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_secondary']
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Login title
        login_title = ctk.CTkLabel(
            login_inner,
            text=self.lang.get('login_title'),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['text_primary']
        )
        login_title.pack(anchor='w', pady=(0, 20))
        
        # Email field
        email_label = ctk.CTkLabel(
            login_inner,
            text=self.lang.get('email'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        email_label.pack(anchor='w', pady=(0, 5))
        
        self.login_email_entry = ctk.CTkEntry(
            login_inner,
            width=350,
            height=45,
            corner_radius=15,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['background'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary'],
            placeholder_text="your@email.com"
        )
        self.login_email_entry.pack(pady=(0, 15))
        
        # License Key field
        key_label = ctk.CTkLabel(
            login_inner,
            text=self.lang.get('license_key'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        key_label.pack(anchor='w', pady=(0, 5))
        
        self.login_key_entry = ctk.CTkEntry(
            login_inner,
            width=350,
            height=45,
            corner_radius=15,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['background'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary'],
            placeholder_text="CS-XXXX-XXXX-XXXX..."
        )
        self.login_key_entry.pack(pady=(0, 25))
        
        # Auto-fill saved credentials for convenience
        _, saved_email, _, _, saved_key = load_license()
        if saved_email:
            self.login_email_entry.insert(0, saved_email)
        if saved_key:
            self.login_key_entry.insert(0, saved_key)
        
        # Login button with premium styling
        self.login_button = PremiumButton(
            login_inner,
            text=self.lang.get('login_button'),
            width=350,
            height=50,
            corner_radius=20,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            text_color=COLORS['text_primary'],
            glow=True,
            command=self._handle_login
        )
        self.login_button.pack(pady=(0, 10))
        
        # Error message label (hidden initially)
        self.login_error_label = ctk.CTkLabel(
            login_inner,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['error']
        )
        self.login_error_label.pack(pady=(10, 0))
    
    def _handle_login(self):
        """Handle login button click and validate credentials."""
        email = self.login_email_entry.get().strip()
        license_key = self.login_key_entry.get().strip()
        
        if not email or not license_key:
            self.login_error_label.configure(text=self.lang.get('login_required'))
            return
        
        # Validate with license_guard
        result = validate_license(email, license_key)
        
        if result and result.get('valid'):
            # Successful validation
            tier = result.get('tier', 'standard')
            expires_at = result.get('expires_at')
            token = result.get('token', '')
            
            # Save license for persistent session
            save_license(email, license_key, tier, expires_at)
            
            # Set session with license key for product generation
            set_session(token, email, tier, license_key=license_key)
            
            # Clear login screen and create main UI
            for widget in self.winfo_children():
                widget.destroy()
            
            self._create_ui()
        else:
            # Failed validation
            error_msg = result.get('message', self.lang.get('login_error')) if result else self.lang.get('login_error')
            self.login_error_label.configure(text=error_msg)
    
    def _setup_keyboard_shortcuts(self):
        """
        Setup keyboard shortcuts for Russian Cyrillic keyboard layout only.
        
        NOTE: English Ctrl+C/V/X/A are handled natively by CustomTkinter.
        Adding custom bindings for English keys causes DOUBLE copy/paste actions.
        Only bind Russian Cyrillic equivalents for users with Russian keyboard layouts.
        """
        def select_all(event):
            widget = self.focus_get()
            if isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)):
                if hasattr(widget, 'select_range'):  # For Entry
                    widget.select_range(0, 'end')
                    widget.icursor('end')
                elif hasattr(widget, 'tag_add'):  # For Textbox
                    widget.tag_add('sel', '1.0', 'end')
            return "break"
        
        def copy_text(event):
            widget = self.focus_get()
            if widget:
                widget.event_generate("<<Copy>>")
            return "break"
        
        def paste_text(event):
            widget = self.focus_get()
            if widget:
                widget.event_generate("<<Paste>>")
            return "break"
        
        def cut_text(event):
            widget = self.focus_get()
            if widget:
                widget.event_generate("<<Cut>>")
            return "break"
        
        # Only bind Russian Cyrillic equivalents (same key positions on keyboard)
        # English Ctrl+C/V/X/A are already handled natively by CustomTkinter
        # ф = a, с = c, м = v, ч = x
        self.bind_all("<Control-Cyrillic_ef>", select_all)  # ф (Ctrl+A position)
        self.bind_all("<Control-Cyrillic_EF>", select_all)
        self.bind_all("<Control-Cyrillic_es>", copy_text)   # с (Ctrl+C position)
        self.bind_all("<Control-Cyrillic_ES>", copy_text)
        self.bind_all("<Control-Cyrillic_em>", paste_text)  # м (Ctrl+V position)
        self.bind_all("<Control-Cyrillic_EM>", paste_text)
        self.bind_all("<Control-Cyrillic_che>", cut_text)   # ч (Ctrl+X position)
        self.bind_all("<Control-Cyrillic_CHE>", cut_text)
        
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
        
        # ===== MASTER PROMPT INPUT =====
        prompt_label = ctk.CTkLabel(
            input_inner,
            text=self.lang.get('prompt_label'),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text_primary']
        )
        prompt_label.pack(anchor='w', pady=(10, 8))
        
        self.prompt_textbox = ctk.CTkTextbox(
            input_inner,
            height=150,
            corner_radius=15,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['background'],
            border_color=COLORS['border'],
            text_color=COLORS['text_primary'],
            border_width=1
        )
        self.prompt_textbox.pack(fill='x', pady=(0, 20))
        
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
        
        # Format buttons with visual feedback (replaces checkboxes)
        # All export formats: PDF, DOCX, HTML, EPUB, Markdown
        self.format_buttons = {}
        export_formats = [
            {'id': 'pdf', 'name': 'PDF', 'icon': '📄'},
            {'id': 'docx', 'name': 'DOCX', 'icon': '📝'},
            {'id': 'html', 'name': 'HTML', 'icon': '🌐'},
            {'id': 'epub', 'name': 'EPUB', 'icon': '📚'},
            {'id': 'markdown', 'name': 'Markdown', 'icon': '📋'}
        ]
        
        for i, fmt in enumerate(export_formats):
            is_selected = self.selected_export_formats.get(fmt['id'], False)
            colors = FORMAT_BTN_SELECTED if is_selected else FORMAT_BTN_UNSELECTED
            
            # Arrange in 2 rows: first 3 on row 0, next 2 on row 1
            row = 0 if i < 3 else 1
            col = i if i < 3 else i - 3
            
            btn = ctk.CTkButton(
                formats_frame,
                text=f"{fmt['icon']} {fmt['name']}",
                font=ctk.CTkFont(size=13, weight="bold" if is_selected else "normal"),
                width=90,
                height=40,
                corner_radius=8,
                fg_color=colors["fg"],
                hover_color=colors["hover"],
                border_width=2,
                border_color=colors["border"],
                command=lambda f_id=fmt['id']: self._toggle_format_btn(f_id)
            )
            btn.grid(row=row, column=col, padx=(0, 10), pady=5)
            self.format_buttons[fmt['id']] = btn
        
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
        """
        Show the enhanced Account page with user statistics, credit tracker,
        and generation history. Implements thread-safe data loading.
        """
        # Store reference for updates from background threads
        self._account_content = ctk.CTkScrollableFrame(
            self.main_area,
            fg_color='transparent'
        )
        self._account_content.pack(fill='both', expand=True, padx=40, pady=30)
        
        # ===== HEADER SECTION: User Profile =====
        self._create_account_header(self._account_content)
        
        # ===== CREDIT TRACKER SECTION =====
        self._create_credit_tracker(self._account_content)
        
        # ===== STATISTICS GRID: 4 Cards =====
        self._create_statistics_grid(self._account_content)
        
        # ===== GENERATION HISTORY TABLE =====
        self._create_history_table(self._account_content)
        
        # ===== SESSION INFO & LOGOUT =====
        self._create_session_section(self._account_content)
        
        # Start background thread to check API status
        self._check_api_status_async()
    
    def _create_account_header(self, parent):
        """Create the header section with user info and tier."""
        header_card = ctk.CTkFrame(
            parent,
            corner_radius=20,
            fg_color=COLORS['card'],
            border_width=1,
            border_color=COLORS['border']
        )
        header_card.pack(fill='x', pady=(0, 20))
        
        header_inner = ctk.CTkFrame(header_card, fg_color='transparent')
        header_inner.pack(fill='both', padx=30, pady=25)
        
        # Left side: User info
        user_frame = ctk.CTkFrame(header_inner, fg_color='transparent')
        user_frame.pack(side='left', fill='x', expand=True)
        
        # User icon and name
        user_icon = ctk.CTkLabel(
            user_frame,
            text="👤",
            font=ctk.CTkFont(size=42)
        )
        user_icon.pack(side='left', padx=(0, 15))
        
        user_info = ctk.CTkFrame(user_frame, fg_color='transparent')
        user_info.pack(side='left', fill='y')
        
        # Get user email
        email = get_user_email() or 'Unknown User'
        # Mask email for display
        if '@' in email:
            masked_email = email[:3] + '***' + email[email.find('@'):]
        else:
            masked_email = email
        
        user_name_label = ctk.CTkLabel(
            user_info,
            text=masked_email,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        user_name_label.pack(anchor='w')
        
        # Get tier
        tier = get_tier() or 'trial'
        tier_display = {
            'trial': '🆓 Starter Pack',
            'standard': '⭐ Standard',
            'enterprise': '🚀 Pro / Enterprise',
            'lifetime': '💎 Lifetime Pro'
        }.get(tier, f'⭐ {tier.title()}')
        
        tier_label = ctk.CTkLabel(
            user_info,
            text=tier_display,
            font=ctk.CTkFont(size=14),
            text_color=COLORS['accent']
        )
        tier_label.pack(anchor='w', pady=(5, 0))
    
    def _create_credit_tracker(self, parent):
        """Create the credit tracker section with progress bar."""
        credit_card = ctk.CTkFrame(
            parent,
            corner_radius=20,
            fg_color=COLORS['card'],
            border_width=1,
            border_color=COLORS['border']
        )
        credit_card.pack(fill='x', pady=(0, 20))
        
        credit_inner = ctk.CTkFrame(credit_card, fg_color='transparent')
        credit_inner.pack(fill='both', padx=30, pady=25)
        
        # Title row
        title_row = ctk.CTkFrame(credit_inner, fg_color='transparent')
        title_row.pack(fill='x', pady=(0, 15))
        
        credit_title = ctk.CTkLabel(
            title_row,
            text=f"💳 {self.lang.get('credit_balance')}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        )
        credit_title.pack(side='left')
        
        # Get credit info
        try:
            from ai_worker import check_remaining_credits
            credit_info = check_remaining_credits()
            credits_available = credit_info.get('credits', 0)
        except Exception:
            credits_available = 0
        
        # Determine total credits based on tier
        tier = get_tier() or 'trial'
        tier_credit_limits = {
            'trial': 3,
            'standard': 50,
            'enterprise': 300,
            'lifetime': 999
        }
        total_credits = tier_credit_limits.get(tier, 10)
        
        # Calculate progress
        progress_value = min(credits_available / max(total_credits, 1), 1.0)
        
        # Credits display
        credits_label = ctk.CTkLabel(
            title_row,
            text=f"{credits_available} / {total_credits}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['success'] if credits_available > 0 else COLORS['error']
        )
        credits_label.pack(side='right')
        
        # Progress bar
        progress_bar = SmoothProgressBar(
            credit_inner,
            height=20,
            corner_radius=10,
            fg_color=COLORS['background'],
            progress_color=COLORS['accent']
        )
        progress_bar.pack(fill='x', pady=(0, 15))
        progress_bar.set(progress_value)
        
        # Upgrade/Top-up button
        upgrade_btn = PremiumButton(
            credit_inner,
            text=f"🚀 {self.lang.get('topup_credits')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            corner_radius=15,
            height=45,
            glow=True,
            command=self._open_upgrade_url
        )
        upgrade_btn.pack(anchor='w')
    
    def _create_statistics_grid(self, parent):
        """Create the 4-card statistics grid."""
        stats_title = ctk.CTkLabel(
            parent,
            text=f"📊 {self.lang.get('statistics')}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text_primary']
        )
        stats_title.pack(anchor='w', pady=(0, 15))
        
        stats_frame = ctk.CTkFrame(parent, fg_color='transparent')
        stats_frame.pack(fill='x', pady=(0, 25))
        
        # Get user statistics from database
        try:
            from user_stats import get_user_statistics
            user_stats = get_user_statistics(get_license_key())
        except Exception:
            user_stats = {
                'total_products': 0,
                'total_credits_spent': 0,
                'last_activity': None,
                'products_this_month': 0
            }
        
        # Format last activity date
        last_activity = user_stats.get('last_activity')
        if last_activity:
            try:
                dt = datetime.fromisoformat(last_activity)
                last_activity_str = dt.strftime('%Y-%m-%d %H:%M')
            except Exception:
                last_activity_str = self.lang.get('never')
        else:
            last_activity_str = self.lang.get('never')
        
        # Stats data for 4 cards
        stats = [
            {
                "icon": "📦",
                "label": self.lang.get('total_products'),
                "value": str(user_stats.get('total_products', 0))
            },
            {
                "icon": "📅",
                "label": self.lang.get('last_activity'),
                "value": last_activity_str
            },
            {
                "icon": "🤖",
                "label": self.lang.get('current_model'),
                "value": "gpt-4o"
            },
            {
                "icon": "🌐",
                "label": self.lang.get('api_status'),
                "value": self.lang.get('checking'),
                "id": "api_status_value"
            },
        ]
        
        self._stat_value_labels = {}
        
        for i, stat in enumerate(stats):
            card = ctk.CTkFrame(
                stats_frame,
                corner_radius=15,
                fg_color=COLORS['card'],
                border_width=1,
                border_color=COLORS['border']
            )
            card.grid(row=0, column=i, padx=8, pady=8, sticky='nsew')
            stats_frame.grid_columnconfigure(i, weight=1)
            
            card_inner = ctk.CTkFrame(card, fg_color='transparent')
            card_inner.pack(fill='both', expand=True, padx=15, pady=18)
            
            icon_label = ctk.CTkLabel(
                card_inner,
                text=stat['icon'],
                font=ctk.CTkFont(size=28)
            )
            icon_label.pack()
            
            value_label = ctk.CTkLabel(
                card_inner,
                text=stat['value'],
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS['text_primary']
            )
            value_label.pack(pady=(5, 0))
            
            # Store reference for API status updates
            if stat.get('id'):
                self._stat_value_labels[stat['id']] = value_label
            
            label_label = ctk.CTkLabel(
                card_inner,
                text=stat['label'],
                font=ctk.CTkFont(size=10),
                text_color=COLORS['text_secondary']
            )
            label_label.pack()
    
    def _create_history_table(self, parent):
        """Create the generation history table."""
        history_card = ctk.CTkFrame(
            parent,
            corner_radius=20,
            fg_color=COLORS['card'],
            border_width=1,
            border_color=COLORS['border']
        )
        history_card.pack(fill='x', pady=(0, 20))
        
        history_inner = ctk.CTkFrame(history_card, fg_color='transparent')
        history_inner.pack(fill='both', padx=30, pady=25)
        
        history_title = ctk.CTkLabel(
            history_inner,
            text=f"📜 {self.lang.get('generation_history')}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text_primary']
        )
        history_title.pack(anchor='w', pady=(0, 15))
        
        # Get generation history
        try:
            from user_stats import get_generation_history
            history = get_generation_history(limit=10, license_key=get_license_key())
        except Exception:
            history = []
        
        if not history:
            # No history message
            no_history_label = ctk.CTkLabel(
                history_inner,
                text=f"📭 {self.lang.get('no_history')}",
                font=ctk.CTkFont(size=13),
                text_color=COLORS['text_secondary']
            )
            no_history_label.pack(pady=20)
        else:
            # Create table header
            header_frame = ctk.CTkFrame(history_inner, fg_color=COLORS['background'], corner_radius=8)
            header_frame.pack(fill='x', pady=(0, 5))
            
            header_inner = ctk.CTkFrame(header_frame, fg_color='transparent')
            header_inner.pack(fill='x', padx=15, pady=10)
            
            # Header columns
            headers = [
                (self.lang.get('product_name'), 0.4),
                (self.lang.get('date'), 0.3),
                (self.lang.get('status'), 0.3)
            ]
            
            for header_text, weight in headers:
                header_label = ctk.CTkLabel(
                    header_inner,
                    text=header_text,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=COLORS['text_secondary']
                )
                header_label.pack(side='left', expand=True, fill='x')
            
            # Table rows
            for i, record in enumerate(history[:10]):
                row_bg = COLORS['card'] if i % 2 == 0 else COLORS['background']
                row_frame = ctk.CTkFrame(history_inner, fg_color=row_bg, corner_radius=5)
                row_frame.pack(fill='x', pady=2)
                
                row_inner = ctk.CTkFrame(row_frame, fg_color='transparent')
                row_inner.pack(fill='x', padx=15, pady=8)
                
                # Product name
                product_name = record.get('product_name', 'Unknown')
                if len(product_name) > 30:
                    product_name = product_name[:27] + '...'
                name_label = ctk.CTkLabel(
                    row_inner,
                    text=product_name,
                    font=ctk.CTkFont(size=12),
                    text_color=COLORS['text_primary']
                )
                name_label.pack(side='left', expand=True, fill='x')
                
                # Date
                created_at = record.get('created_at', '')
                try:
                    dt = datetime.fromisoformat(created_at)
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                except Exception:
                    date_str = created_at[:16] if created_at else ''
                date_label = ctk.CTkLabel(
                    row_inner,
                    text=date_str,
                    font=ctk.CTkFont(size=12),
                    text_color=COLORS['text_secondary']
                )
                date_label.pack(side='left', expand=True, fill='x')
                
                # Status with color
                status = record.get('status', 'Unknown')
                status_color = COLORS['success'] if status == 'Completed' else COLORS['error']
                status_label = ctk.CTkLabel(
                    row_inner,
                    text=status,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=status_color
                )
                status_label.pack(side='left', expand=True, fill='x')
    
    def _create_session_section(self, parent):
        """Create session info and logout section."""
        # Session info (masked credentials)
        email = get_user_email() or ''
        license_key = get_license_key() or ''
        
        # Mask email: show first 3 chars and domain
        if email and '@' in email:
            masked_email = email[:3] + '***' + email[email.find('@'):]
        else:
            masked_email = email
        
        # Mask license key: show only last 4 characters
        if license_key and len(license_key) >= 4:
            masked_key = '***' + license_key[-4:]
        else:
            masked_key = license_key
        
        session_label = ctk.CTkLabel(
            parent,
            text=f"🔐 Session: {masked_email} | Key: {masked_key}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_secondary']
        )
        session_label.pack(anchor='w', pady=(10, 15))
        
        # Logout button
        logout_btn = ctk.CTkButton(
            parent,
            text=f"🚪 {self.lang.get('logout')} / {self.lang.get('reset_session')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS['error'],
            hover_color='#D9534F',
            corner_radius=12,
            height=42,
            command=self._logout
        )
        logout_btn.pack(anchor='w', pady=(0, 20))
    
    def _check_api_status_async(self):
        """Check API status in a background thread to avoid blocking GUI."""
        def check_status():
            try:
                from ai_worker import fetch_openai_api_key
                # Try to fetch API key as connectivity test
                api_key = fetch_openai_api_key()
                is_online = api_key is not None and api_key.startswith('sk-')
            except Exception:
                is_online = False
            
            # Update UI from main thread
            self.after(0, lambda: self._update_api_status(is_online))
        
        # Start background thread
        api_thread = threading.Thread(target=check_status, daemon=True)
        api_thread.start()
    
    def _update_api_status(self, is_online: bool):
        """Update the API status label in the UI (called from main thread)."""
        try:
            if hasattr(self, '_stat_value_labels') and 'api_status_value' in self._stat_value_labels:
                status_label = self._stat_value_labels['api_status_value']
                if is_online:
                    status_label.configure(
                        text=f"✅ {self.lang.get('api_online')}",
                        text_color=COLORS['success']
                    )
                else:
                    status_label.configure(
                        text=f"❌ {self.lang.get('api_offline')}",
                        text_color=COLORS['error']
                    )
        except Exception:
            pass  # Widget may have been destroyed
    
    def _open_upgrade_url(self):
        """Open the upgrade/top-up URL in the default browser."""
        import webbrowser
        # Default upgrade URL - can be configured
        upgrade_url = "https://coursesmith.ai/upgrade"
        try:
            webbrowser.open(upgrade_url)
        except Exception:
            messagebox.showinfo("Upgrade", f"Visit: {upgrade_url}")
    
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
    
    def _logout(self):
        """Logout and reset the session, clearing all stored credentials."""
        # Clear the session manager
        clear_session()
        
        # Physically delete the token file
        if os.path.exists('.session_token'):
            os.remove('.session_token')
        
        # Destroy all widgets
        for w in self.winfo_children():
            w.destroy()
        
        # Show login screen
        self._show_login_screen()
    
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
    
    def _toggle_format_btn(self, format_id):
        """Handle export format button click with radio-button behavior (only one format at a time)."""
        # Deselect all formats first
        for fmt in self.selected_export_formats:
            self.selected_export_formats[fmt] = False
        
        # Select only the clicked format
        self.selected_export_formats[format_id] = True
        
        # Update all button visual states
        self._update_format_buttons()
        
        # Log format change with emoji prefix
        print(f"📋 Format selection changed: {format_id.upper()}")
    
    def _update_format_buttons(self):
        """Update format button visual states based on selection."""
        format_icons = {'pdf': '📄', 'docx': '📝', 'html': '🌐', 'epub': '📚', 'markdown': '📋'}
        format_names = {'pdf': 'PDF', 'docx': 'DOCX', 'html': 'HTML', 'epub': 'EPUB', 'markdown': 'Markdown'}
        
        for fmt_id, btn in self.format_buttons.items():
            is_selected = self.selected_export_formats.get(fmt_id, False)
            colors = FORMAT_BTN_SELECTED if is_selected else FORMAT_BTN_UNSELECTED
            icon = format_icons.get(fmt_id, '📄')
            name = format_names.get(fmt_id, fmt_id.upper())
            
            btn.configure(
                fg_color=colors["fg"],
                hover_color=colors["hover"],
                border_color=colors["border"],
                font=ctk.CTkFont(size=13, weight="bold" if is_selected else "normal"),
                text=f"{icon} {name}"
            )
    
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
    
    def _generate_document_by_format(self, format_type: str) -> str:
        """
        Generate a document in the specified format from the current project data.
        Routes to the appropriate exporter based on format_type.
        
        Args:
            format_type: The export format (pdf, docx, html, epub, markdown)
            
        Returns:
            str: Path to the generated document file
        """
        format_type_upper = format_type.upper()
        print(f"📄 Rendering {format_type_upper} document...")
        
        if format_type_upper == "PDF":
            return self._build_pdf()
        elif format_type_upper == "DOCX":
            return self._build_docx()
        elif format_type_upper == "HTML":
            return self._build_html()
        elif format_type_upper == "EPUB":
            return self._build_epub()
        elif format_type_upper == "MARKDOWN":
            return self._build_markdown()
        else:
            # Fallback to PDF for unknown formats
            print(f"⚠️  Unknown format '{format_type}', falling back to PDF")
            return self._build_pdf()
    
    def _get_downloads_dir(self) -> str:
        """
        Get the downloads directory path and ensure it exists.
        
        Returns:
            str: Path to the downloads directory
        """
        import os
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        return downloads_dir
    
    def _build_pdf(self) -> str:
        """Generate a PDF file from the current project."""
        self._get_downloads_dir()  # Ensure downloads directory exists
        
        # Create course data structure from project
        course_data = self._create_course_data_from_project()
        
        # Use the shared generate_pdf utility
        return generate_pdf(course_data, page_count=self.total_chapters, media_files=None)
    
    def _build_docx(self) -> str:
        """Generate a DOCX file from the current project."""
        downloads_dir = self._get_downloads_dir()
        
        exporter = DOCXExporter(self.project)
        output_path = exporter.generate_output_path(downloads_dir)
        exporter.output_path = output_path
        
        return exporter.export()
    
    def _build_html(self) -> str:
        """Generate an HTML file from the current project."""
        downloads_dir = self._get_downloads_dir()
        
        exporter = HTMLExporter(self.project)
        output_path = exporter.generate_output_path(downloads_dir)
        exporter.output_path = output_path
        
        return exporter.export()
    
    def _build_epub(self) -> str:
        """Generate an EPUB file from the current project."""
        downloads_dir = self._get_downloads_dir()
        
        exporter = EPUBExporter(self.project)
        output_path = exporter.generate_output_path(downloads_dir)
        exporter.output_path = output_path
        
        return exporter.export()
    
    def _build_markdown(self) -> str:
        """Generate a Markdown file from the current project."""
        downloads_dir = self._get_downloads_dir()
        
        exporter = MarkdownExporter(self.project)
        output_path = exporter.generate_output_path(downloads_dir)
        exporter.output_path = output_path
        
        return exporter.export()
    
    def _create_course_data_from_project(self) -> dict:
        """
        Create course data structure from the current project for PDF generation.
        
        Returns:
            dict: Course data with 'title' and 'chapters' list
        """
        chapters = []
        for chapter_title in self.project.outline:
            content = self.project.chapters_content.get(chapter_title, '')
            chapters.append({
                'title': chapter_title,
                'content': content
            })
        
        return {
            'title': self.project.topic,
            'chapters': chapters
        }
    
    def _toggle_language(self):
        """Toggle between EN and RU languages."""
        self.lang.toggle_language()
        self.lang_button.configure(text=f"🌐 {self.lang.current_lang}")
        
        # Refresh current page to update labels
        self._switch_page(self.current_page)
    
    def _start_generation(self):
        """Start product generation process with selected template and formats."""
        # Get prompt text from the master prompt textbox
        prompt_text = self.prompt_textbox.get("1.0", "end-1c").strip()
        
        if not prompt_text:
            messagebox.showwarning("Input Required", "Please enter generation instructions (prompt)")
            return
        
        # Get selected export formats
        export_formats = self._get_selected_formats()
        if not export_formats:
            export_formats = ['pdf']
        
        # Log generation start with emoji prefix and context
        formats_str = ', '.join([f.upper() for f in export_formats])
        print(f"🚀 Starting generation: Prompt='{prompt_text[:MAX_PROMPT_LOG_LENGTH]}...', Chapters={self.total_chapters}, Formats={formats_str}")
        
        # Setup project with selected options
        # Use prompt_text as the topic for AI generation (audience is now part of prompt)
        self.project = CourseProject()
        self.project.set_topic(prompt_text)
        self.project.set_product_type(self.selected_product_type)
        self.project.set_export_formats(export_formats)
        
        # Disable inputs
        self.is_generating = True
        self.prompt_textbox.configure(state='disabled')
        self.start_button.configure(state='disabled')
        
        # Disable product type buttons
        for btn_frame in self.type_buttons.values():
            for child in btn_frame.winfo_children():
                try:
                    child.configure(state='disabled')
                except:
                    pass
        
        # Disable format buttons during generation
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
        
        # Start real AI generation with workers
        self._run_real_generation()
    
    def _run_real_generation(self):
        """
        Run real AI-powered product generation using OutlineGenerator and ChapterWriter.
        
        This method:
        1. Initializes OutlineGenerator with the selected product template
        2. Loops through the generated outline and calls ChapterWriter for each chapter
        3. Updates UI progress bar and labels in real-time (thread-safe via self.after)
        4. Calls _generation_complete() only after all AI operations are successful
        """
        def generate():
            try:
                topic = self.project.topic
                audience = self.project.audience
                product_type = self.selected_product_type
                
                # Step 1: Generate outline using OutlineGenerator
                self.after(0, lambda: self.progress_title.configure(
                    text=self.lang.get('generating') + " (Creating outline...)"
                ))
                
                outline_result = []
                outline_error = None
                outline_done = threading.Event()
                
                def on_outline_complete(chapters):
                    nonlocal outline_result
                    outline_result = chapters
                    outline_done.set()
                
                def on_outline_error(error):
                    nonlocal outline_error
                    outline_error = error
                    outline_done.set()
                
                outline_gen = OutlineGenerator(
                    topic=topic,
                    audience=audience,
                    callback=on_outline_complete,
                    error_callback=on_outline_error,
                    product_type=product_type
                )
                outline_gen.start()
                
                # Wait for outline generation to complete
                outline_done.wait()
                
                if outline_error:
                    self.after(0, lambda e=outline_error: self._handle_generation_error(e))
                    return
                
                if not outline_result:
                    self.after(0, lambda: self._handle_generation_error("Failed to generate outline"))
                    return
                
                # Update project outline
                self.project.set_outline(outline_result)
                
                # Adjust total_chapters to match actual outline
                actual_chapters = len(outline_result)
                self.after(0, lambda: self._update_total_chapters(actual_chapters))
                
                # Step 2: Generate each chapter using ChapterWriter
                for i, chapter_title in enumerate(outline_result):
                    chapter_num = i + 1
                    
                    # Update progress label with current chapter
                    truncated_title = (chapter_title[:30] + '...') if len(chapter_title) > 30 else chapter_title
                    self.after(0, lambda cn=chapter_num, tt=truncated_title: self.progress_title.configure(
                        text=f"{self.lang.get('generating')} ({cn}/{actual_chapters}: {tt})"
                    ))
                    
                    chapter_content = None
                    chapter_error = None
                    chapter_done = threading.Event()
                    
                    def on_chapter_complete(title, content):
                        nonlocal chapter_content
                        chapter_content = content
                        chapter_done.set()
                    
                    def on_chapter_error(error):
                        nonlocal chapter_error
                        chapter_error = error
                        chapter_done.set()
                    
                    chapter_writer = ChapterWriter(
                        topic=topic,
                        chapter_title=chapter_title,
                        chapter_num=chapter_num,
                        callback=on_chapter_complete,
                        error_callback=on_chapter_error,
                        product_type=product_type
                    )
                    chapter_writer.start()
                    
                    # Wait for chapter generation to complete
                    chapter_done.wait()
                    
                    if chapter_error:
                        self.after(0, lambda e=chapter_error: self._handle_generation_error(e))
                        return
                    
                    # Store chapter content in project
                    if chapter_content:
                        self.project.set_chapter_content(chapter_title, chapter_content)
                    
                    # Update progress on main thread
                    self.after(0, self._update_progress, chapter_num)
                
                # All chapters generated successfully
                self.after(0, self._generation_complete)
                
            except Exception as e:
                self.after(0, lambda err=str(e): self._handle_generation_error(err))
        
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
    
    def _update_total_chapters(self, count):
        """Update the total chapters count to match actual outline."""
        self.total_chapters = count
        self.progress_label.configure(
            text=f"{self.lang.get('chapters_label')}: 0/{self.total_chapters}"
        )
    
    def _handle_generation_error(self, error_message):
        """Handle errors during AI generation."""
        self.is_generating = False
        
        # Stop animations
        self.input_border_frame.stop_animation()
        
        # Re-enable controls
        self.prompt_textbox.configure(state='normal')
        self.start_button.configure(state='normal')
        
        # Re-enable product type buttons
        for btn_frame in self.type_buttons.values():
            for child in btn_frame.winfo_children():
                try:
                    child.configure(state='normal')
                except Exception:
                    pass
        
        # Re-enable format buttons
        for btn in self.format_buttons.values():
            btn.configure(state='normal')
        
        # Hide progress frame
        self.progress_frame.pack_forget()
        
        # Show error message
        print(f"❌ Generation error: {error_message}")
        messagebox.showerror("Generation Error", f"An error occurred during generation:\n\n{error_message}")
    
    def _update_progress(self, chapter_num):
        """Update progress display."""
        self.chapter_count = chapter_num
        progress_value = chapter_num / self.total_chapters
        
        self.progress_bar.set_target(progress_value)
        self.progress_label.configure(
            text=f"{self.lang.get('chapters_label')}: {chapter_num}/{self.total_chapters}"
        )
    
    def _generation_complete(self):
        """Handle generation completion and export documents in selected formats."""
        self.is_generating = False
        
        # Stop animations
        self.input_border_frame.stop_animation()
        
        # Update UI
        self.progress_title.configure(text=self.lang.get('complete'))
        
        # Get selected formats
        formats = self._get_selected_formats()
        if not formats:
            formats = ['pdf']
        formats_str = ", ".join([f.upper() for f in formats])
        
        # Export documents in selected formats
        exported_files = []
        export_errors = []
        
        for fmt in formats:
            try:
                output_path = self._generate_document_by_format(fmt)
                exported_files.append((fmt.upper(), output_path))
                print(f"✅ {fmt.upper()} exported: {output_path}")
            except Exception as e:
                error_msg = f"Failed to export {fmt.upper()}: {str(e)}"
                print(f"❌ {error_msg}")
                export_errors.append(error_msg)
        
        # Re-enable controls
        self.prompt_textbox.configure(state='normal')
        self.start_button.configure(state='normal')
        
        # Re-enable product type buttons
        for btn_frame in self.type_buttons.values():
            for child in btn_frame.winfo_children():
                try:
                    child.configure(state='normal')
                except:
                    pass
        
        # Re-enable format buttons
        for btn in self.format_buttons.values():
            btn.configure(state='normal')
        
        # Get product type name for message
        product_name = "Product"
        for template in self.product_templates:
            if template['id'] == self.selected_product_type:
                product_name = template['name']
                break
        
        # Log success with emoji prefix and context
        prompt_text = self.prompt_textbox.get("1.0", "end-1c").strip()[:MAX_PROMPT_LOG_LENGTH] if hasattr(self, 'prompt_textbox') else "Unknown"
        print(f"✅ Generation complete: Prompt='{prompt_text}...', Chapters={self.total_chapters}, Formats={formats_str}")
        
        # Record generation in history database
        try:
            from user_stats import record_generation
            from product_templates import get_credit_cost
            credits_used = get_credit_cost(self.selected_product_type)
            record_generation(
                product_name=prompt_text[:100] if prompt_text else product_name,
                product_type=self.selected_product_type,
                chapters_count=self.total_chapters,
                export_format=formats_str,
                credits_used=credits_used,
                status='Completed' if exported_files else 'Failed',
                license_key=get_license_key()
            )
        except Exception as e:
            print(f"⚠️ Failed to record generation history: {e}")
        
        # Build success message
        if exported_files:
            files_msg = "\n".join([f"  • {fmt}: {path}" for fmt, path in exported_files])
            success_msg = f"{product_name} generated successfully!\n\nSections: {self.total_chapters}\nExported files:\n{files_msg}"
        else:
            success_msg = f"{product_name} content generated but export failed.\n\nExport formats: {formats_str}"
        
        # Add any errors to the message
        if export_errors:
            success_msg += "\n\nExport errors:\n" + "\n".join([f"  • {err}" for err in export_errors])
        
        # Show success message
        messagebox.showinfo("Success", success_msg)


def main():
    """Main entry point."""
    # Set appearance
    ctk.set_appearance_mode("Dark")
    
    # Create and run app
    app = CustomApp()
    app.mainloop()


if __name__ == "__main__":
    main()
