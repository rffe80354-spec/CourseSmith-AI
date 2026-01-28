"""
CourseSmith ENTERPRISE - Entry Point with UI Overhaul
A commercial desktop application to generate educational PDF books using AI with DRM protection.
Features enterprise sidebar navigation and modern animations.
"""

import os
import sys
import json
import threading
from datetime import datetime, timezone
import customtkinter as ctk
from tkinter import messagebox
from dotenv import load_dotenv
from supabase import create_client, Client

# Import HWID and license utilities from utils module
from utils import get_hwid, parse_hwids_array, check_license, add_context_menu


# Suppress stdout/stderr for --noconsole mode with log file fallback
if hasattr(sys, 'frozen'):
    # Redirect to log file instead of complete suppression for debugging
    try:
        log_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'CourseSmithAI', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'coursesmith_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        sys.stdout = open(log_file, 'w', encoding='utf-8')
        sys.stderr = sys.stdout
    except:
        # If log file creation fails, suppress completely
        sys.stdout = None
        sys.stderr = None


# Supabase configuration for remote kill switch
# Load from environment variables for security
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Fallback values for development only - DO NOT USE IN PRODUCTION
if not SUPABASE_URL:
    SUPABASE_URL = "https://spfwfyjpexktgnusgyib.supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "sb_publishable_tmwenU0VyOChNWKG90X_bw_HYf9X5kR"


# Enterprise color scheme
COLORS = {
    'background': '#0B0E14',
    'sidebar': '#151921',
    'accent': '#7F5AF0',
    'accent_hover': '#9D7BF5',
    'text': '#E0E0E0',
    'text_dim': '#808080'
}

# UI timing constants
UI_RENDER_DELAY_MS = 200  # Delay before initial UI rendering to prevent RecursionError
STEP_DELAY_SECONDS = 1.5  # Delay between simulated generation steps
PACKAGING_DELAY_SECONDS = 1.0  # Delay for packaging simulation
EMAIL_LOG_DELAY_MS = 500  # Delay before showing email log message
COMPLETION_DELAY_MS = 1000  # Delay before completion


def check_remote_ban():
    """
    Check if the current HWID is authorized for license activation.
    Implements device binding support:
    - Checks if license has expired
    - Checks if license is banned
    - Validates device HWID matches stored HWID
    - Uses single 'hwid' column instead of 'used_hwids' array
    
    If banned, expired, or HWID mismatch, shows error and exits.
    Allows offline usage by catching connection errors.
    """
    try:
        # Get current hardware ID
        current_hwid = get_hwid()
        
        if not current_hwid or current_hwid == "UNKNOWN_ID":
            # Cannot validate without valid HWID - allow offline use
            return
        
        # Connect to Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query licenses table - search for license with this HWID
        response = supabase.table("licenses").select("*").eq("hwid", current_hwid).execute()
        
        # If no license found with this HWID, allow app to continue
        # (First-time activation handled during login)
        if not response.data or len(response.data) == 0:
            return
        
        license_record = response.data[0]
        
        # Check if license is banned
        if license_record.get("is_banned") is True:
            messagebox.showerror(
                "Access Denied",
                "Access Denied. License Revoked."
            )
            sys.exit()
        
        # Check if license has expired
        valid_until = license_record.get("valid_until")
        if valid_until:
            try:
                expiration_date = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                current_date = datetime.now(timezone.utc)
                
                if current_date > expiration_date:
                    messagebox.showerror(
                        "Subscription Expired",
                        "Your subscription for CourseSmith AI has expired. Please renew to continue."
                    )
                    sys.exit()
            except Exception as e:
                # If date parsing fails, fail closed for security
                print(f"Error: Invalid expiration date format: {e}")
                messagebox.showerror(
                    "License Error",
                    "Invalid license expiration date. Please contact support."
                )
                sys.exit()
        
        # If we reach here, license is valid and HWID is authorized
        
    except Exception:
        # Allow offline usage - if connection fails, don't block the app
        pass


def validate_license_key(license_key: str, email: str) -> dict:
    """
    Validate a license key with email and register the current device if authorized.
    This function is called during first-time activation.
    
    Args:
        license_key: The license key to validate
        email: The email associated with the license
        
    Returns:
        dict: License information with status
            {'valid': bool, 'message': str, 'license_data': dict or None}
    """
    # Use the check_license function from utils module
    return check_license(license_key, email, SUPABASE_URL, SUPABASE_KEY)


class EnterpriseApp(ctk.CTk):
    """Enterprise UI with sidebar navigation and license authentication."""
    
    def __init__(self):
        """Initialize the enterprise application."""
        super().__init__()
        
        # Set widget scaling for High-DPI support
        # Default is 1.0. Adjust manually if needed for specific DPI requirements:
        # - Set to 1.25 for 125% scaling
        # - Set to 1.5 for 150% scaling
        # This can be customized based on user preferences or system detection
        ctk.set_widget_scaling(1.0)
        
        # Configure window
        self.title("CourseSmith AI Enterprise")
        self.geometry("1200x800")
        self.minsize(1000, 600)
        
        # Configure colors
        self.configure(fg_color=COLORS['background'])
        
        # GLOBAL HOTKEY OVERRIDE - Bind keyboard shortcuts at root window level
        # This ensures shortcuts work regardless of widget focus issues
        from utils import setup_global_window_shortcuts
        setup_global_window_shortcuts(self)
        
        # State
        self.current_tab = "forge"
        self.progress_animation_running = False
        self.license_valid = False  # Track license validation state
        self.license_data = None  # Store validated license data
        
        # Initialize coursesmith_engine
        self.coursesmith_engine = None
        self._init_coursesmith_engine()
        
        # Check if license is already activated
        if self._check_existing_license():
            # License already validated, show main UI
            self._create_main_ui()
        else:
            # Show login/activation screen
            self._create_activation_ui()
    
    def _check_existing_license(self):
        """Check if a license is already activated on this device."""
        try:
            current_hwid = get_hwid()
            if not current_hwid or current_hwid == "UNKNOWN_ID":
                return False
            
            # Connect to Supabase
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Query licenses table for this HWID
            response = supabase.table("licenses").select("*").limit(100).execute()
            
            # Find license that matches this HWID
            for record in response.data if response.data else []:
                used_hwids = parse_hwids_array(record.get("used_hwids"))
                
                if current_hwid in used_hwids:
                    # Found matching license, validate it
                    if self._validate_license_record(record):
                        self.license_valid = True
                        self.license_data = record
                        return True
                    else:
                        # License found but invalid (expired/banned)
                        return False
            
            return False
            
        except Exception as e:
            print(f"Error checking existing license: {e}")
            # On error, allow offline usage
            return False
    
    def _validate_license_record(self, record):
        """Validate a license record (check expiration and ban status)."""
        # Check if license is banned
        if record.get("is_banned") is True:
            return False
        
        # Check if license has expired
        valid_until = record.get("valid_until")
        if valid_until:
            try:
                expiration_date = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                current_date = datetime.now(timezone.utc)
                
                if current_date > expiration_date:
                    return False
            except Exception as e:
                # If date parsing fails, fail closed for security
                print(f"Warning: Failed to parse expiration date: {e}")
                return False
        
        return True
    
    def _create_activation_ui(self):
        """Create the license activation screen with expanded 550x850 geometry."""
        # Set window size for login screen (expanded to ensure Activate button is fully visible)
        self.geometry("550x850")
        self.minsize(550, 850)
        self.resizable(False, False)
        
        # Main container
        container = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS['background'])
        container.pack(fill="both", expand=True)
        
        # Center frame
        center_frame = ctk.CTkFrame(container, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Logo/Title
        title_label = ctk.CTkLabel(
            center_frame,
            text="⚡ CourseSmith AI",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color=COLORS['accent']
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ctk.CTkLabel(
            center_frame,
            text="Enterprise Edition",
            font=ctk.CTkFont(size=20),
            text_color=COLORS['text']
        )
        subtitle_label.pack(pady=(0, 50))
        
        # Activation frame - expanded height to 500 to fit Email + Key + Button with generous padding
        activation_frame = ctk.CTkFrame(
            center_frame,
            corner_radius=15,
            fg_color=COLORS['sidebar'],
            width=500,
            height=500
        )
        activation_frame.pack(padx=40, pady=20)
        activation_frame.pack_propagate(False)
        
        # Activation title
        activation_title = ctk.CTkLabel(
            activation_frame,
            text="License Activation Required",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS['text']
        )
        activation_title.pack(pady=(30, 10))
        
        # Instructions
        instructions = ctk.CTkLabel(
            activation_frame,
            text="Please enter your email and license key to activate CourseSmith AI",
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_dim']
        )
        instructions.pack(pady=(0, 25))
        
        # Email entry field
        email_label = ctk.CTkLabel(
            activation_frame,
            text="Email Address",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text']
        )
        email_label.pack(pady=(0, 5), anchor="w", padx=50)
        
        self.activation_email_entry = ctk.CTkEntry(
            activation_frame,
            placeholder_text="your@email.com",
            font=ctk.CTkFont(size=16),
            height=50,
            width=400,
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.activation_email_entry.pack(pady=(0, 15))
        self.activation_email_entry.bind("<Return>", lambda e: self._on_activate())
        
        # License key entry field
        key_label = ctk.CTkLabel(
            activation_frame,
            text="License Key",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text']
        )
        key_label.pack(pady=(0, 5), anchor="w", padx=50)
        
        self.activation_entry = ctk.CTkEntry(
            activation_frame,
            placeholder_text="CS-XXXX-XXXX",
            font=ctk.CTkFont(size=16),
            height=50,
            width=400,
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.activation_entry.pack(pady=(0, 20))
        self.activation_entry.bind("<Return>", lambda e: self._on_activate())
        
        # Set focus to email entry field for better UX
        self.after(0, lambda: self.activation_email_entry.focus())
        
        # Add clipboard support (includes all shortcuts: Ctrl+C/V/A)
        add_context_menu(self.activation_email_entry)
        add_context_menu(self.activation_entry)
        
        # Status label (placed before button so button stays at bottom)
        self.activation_status = ctk.CTkLabel(
            activation_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_dim']
        )
        self.activation_status.pack(pady=(10, 10))
        
        # Activate button - Green button packed at bottom with side="bottom" and pady=40
        # Specs: height=60, width=400, color=#28a745
        activate_btn = ctk.CTkButton(
            activation_frame,
            text="🔓 Activate License",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=60,
            width=400,
            fg_color="#28a745",  # Green color for activate button
            hover_color="#218838",  # Darker green on hover
            command=self._on_activate
        )
        activate_btn.pack(side="bottom", pady=40)
    
    def _on_activate(self):
        """Handle license activation."""
        email = self.activation_email_entry.get().strip()
        license_key = self.activation_entry.get().strip()
        
        if not email:
            self.activation_status.configure(text="Please enter your email address", text_color="red")
            return
        
        # Basic email format validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            self.activation_status.configure(text="Please enter a valid email address", text_color="red")
            return
        
        if not license_key:
            self.activation_status.configure(text="Please enter a license key", text_color="red")
            return
        
        # Disable button during validation
        self.activation_status.configure(text="Validating license...", text_color=COLORS['accent'])
        self.update()
        
        # Validate license key with email
        result = validate_license_key(license_key, email)
        
        if result['valid']:
            self.license_valid = True
            self.license_data = result['license_data']
            
            # Show success message
            messagebox.showinfo("Success", result['message'])
            
            # Clear activation UI and show main UI
            for widget in self.winfo_children():
                widget.destroy()
            
            # Restore window to main app size (1200x800) after login
            self.geometry("1200x800")
            self.minsize(1000, 600)
            self.resizable(True, True)
            
            self._create_main_ui()
        else:
            self.activation_status.configure(text=result['message'], text_color="red")
    
    def _init_coursesmith_engine(self):
        """Initialize the CourseSmith Engine with API key from environment."""
        try:
            from coursesmith_engine import CourseSmithEngine
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.coursesmith_engine = CourseSmithEngine(api_key=api_key)
            else:
                # Initialize without API key - user can add it later in Settings
                self.coursesmith_engine = CourseSmithEngine(api_key=None, require_api_key=False)
        except Exception as e:
            print(f"Warning: Could not initialize coursesmith_engine: {e}")
            self.coursesmith_engine = None
        
    def _create_main_ui(self):
        """
        Create the main enterprise UI with sidebar (after license validation).
        Uses delayed rendering to prevent RecursionError during initialization.
        """
        # Maximize the window immediately on main UI creation
        self._maximize_window()
        
        # Use after() for initial rendering to prevent RecursionError
        self.after(UI_RENDER_DELAY_MS, self._render_main_ui)
    
    def _maximize_window(self):
        """
        Maximize the window (cross-platform compatible).
        Uses self.state('zoomed') for Windows, with fallbacks for other platforms.
        """
        try:
            # Try Windows-specific zoomed state
            self.state('zoomed')
        except Exception:
            # Fallback for other platforms
            try:
                # Try macOS
                self.attributes('-zoomed', True)
            except Exception:
                # Fallback: set large geometry
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                self.geometry(f"{screen_width}x{screen_height}+0+0")
    
    def _render_main_ui(self):
        """
        Render the main UI with responsive grid layout.
        Called after a delay from _create_main_ui to ensure proper initialization.
        The delay prevents recursion issues that can occur when scrollbar calculations
        trigger geometry updates during initial widget creation.
        """
        # Main container with grid layout for responsive design
        main_container = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS['background'])
        main_container.pack(fill="both", expand=True)
        
        # Configure grid: sidebar column (fixed), content column (expand)
        main_container.grid_columnconfigure(0, weight=0, minsize=200)  # Sidebar fixed
        main_container.grid_columnconfigure(1, weight=1)  # Content expands
        main_container.grid_rowconfigure(0, weight=1)
        
        # Sidebar (200px fixed width)
        self.sidebar = ctk.CTkFrame(
            main_container,
            width=200,
            corner_radius=0,
            fg_color=COLORS['sidebar']
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Logo/Header in sidebar
        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="⚡ CourseSmith",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['accent']
        )
        logo_label.pack(pady=(30, 20))
        
        # License Info Frame - Display Tier and Expiration in Sidebar
        license_info_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORS['background'],
            corner_radius=10
        )
        license_info_frame.pack(fill="x", padx=15, pady=(0, 30))
        
        # Get license tier and expiration from license_data
        tier_text = "Unknown"
        expiry_text = "N/A"
        if self.license_data and isinstance(self.license_data, dict):
            tier_text = self.license_data.get('tier', 'standard').upper()
            valid_until = self.license_data.get('valid_until')
            if valid_until:
                try:
                    expiry_date = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                    expiry_text = expiry_date.strftime("%Y-%m-%d")
                except Exception:
                    expiry_text = "Lifetime"
            else:
                expiry_text = "Lifetime"
        
        # Determine tier color based on tier level
        tier_colors = {
            "PROFESSIONAL": "#FFD700",  # Gold
            "EXTENDED": "#FFA500",       # Orange
            "STANDARD": "#A0A0A0"        # Gray/Silver
        }
        tier_color = tier_colors.get(tier_text, COLORS['accent'])
        
        # Tier label
        tier_label = ctk.CTkLabel(
            license_info_frame,
            text=f"🎫 Tier: {tier_text}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=tier_color
        )
        tier_label.pack(pady=(10, 5), padx=10, anchor="w")
        
        # Expiration label
        expiry_label = ctk.CTkLabel(
            license_info_frame,
            text=f"📅 Expires: {expiry_text}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS['text_dim']
        )
        expiry_label.pack(pady=(0, 10), padx=10, anchor="w")
        
        # Navigation buttons
        self.nav_buttons = {}
        
        self.nav_buttons['forge'] = self._create_nav_button("🔥 Forge", "forge")
        self.nav_buttons['library'] = self._create_nav_button("📚 Library", "library")
        self.nav_buttons['settings'] = self._create_nav_button("⚙️ Settings", "settings")
        
        # Spacer
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=20)
        spacer.pack(fill="both", expand=True)
        
        # Version label at bottom
        version_label = ctk.CTkLabel(
            self.sidebar,
            text="v2.0 Enterprise",
            font=ctk.CTkFont(size=10),
            text_color=COLORS['text_dim']
        )
        version_label.pack(pady=(0, 20))
        
        # Main content area
        self.content_frame = ctk.CTkFrame(
            main_container,
            corner_radius=0,
            fg_color=COLORS['background']
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # Show default tab
        self._switch_tab("forge")
    
    def _create_nav_button(self, text, tab_id):
        """Create a navigation button with hover effects."""
        btn = ctk.CTkButton(
            self.sidebar,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            corner_radius=10,
            fg_color="transparent",
            text_color=COLORS['text'],
            hover_color=COLORS['accent'],
            anchor="w",
            command=lambda: self._switch_tab(tab_id)
        )
        btn.pack(fill="x", padx=15, pady=5)
        
        # Bind hover events for glow effect
        btn.bind("<Enter>", lambda e: self._on_button_hover(btn, True))
        btn.bind("<Leave>", lambda e: self._on_button_hover(btn, False))
        
        return btn
    
    def _on_button_hover(self, button, is_entering):
        """Handle button hover for glow effect."""
        if is_entering:
            button.configure(
                text_color=COLORS['background'],
                fg_color=COLORS['accent_hover']
            )
        else:
            # Check if this is the active tab
            if button == self.nav_buttons.get(self.current_tab):
                button.configure(
                    text_color=COLORS['background'],
                    fg_color=COLORS['accent']
                )
            else:
                button.configure(
                    text_color=COLORS['text'],
                    fg_color="transparent"
                )
    
    def _switch_tab(self, tab_id):
        """Switch to a different tab."""
        self.current_tab = tab_id
        
        # Update button states
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == tab_id:
                btn.configure(
                    fg_color=COLORS['accent'],
                    text_color=COLORS['background']
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS['text']
                )
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show appropriate content
        if tab_id == "forge":
            self._create_forge_tab()
        elif tab_id == "library":
            self._create_library_tab()
        elif tab_id == "settings":
            self._create_settings_tab()
    
    def _create_forge_tab(self):
        """Create the Forge tab - main course generation interface."""
        # Main container with padding
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Title
        title_label = ctk.CTkLabel(
            container,
            text="Forge Your Course",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS['text']
        )
        title_label.pack(anchor="w", pady=(0, 10))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            container,
            text="Enter your master instruction below to generate an educational course",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_dim']
        )
        subtitle_label.pack(anchor="w", pady=(0, 30))
        
        # Input frame
        input_frame = ctk.CTkFrame(container, fg_color=COLORS['sidebar'], corner_radius=15)
        input_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Input label
        input_label = ctk.CTkLabel(
            input_frame,
            text="Master Instruction",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text']
        )
        input_label.pack(anchor="w", padx=25, pady=(25, 10))
        
        # Large text input
        self.instruction_textbox = ctk.CTkTextbox(
            input_frame,
            font=ctk.CTkFont(size=14),
            wrap="word",
            height=300,
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2
        )
        self.instruction_textbox.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        # Add clipboard support (includes all shortcuts: Ctrl+C/V/A)
        from utils import add_context_menu
        add_context_menu(self.instruction_textbox)
        
        # Settings Panel Frame (above Generate button)
        settings_panel = ctk.CTkFrame(container, fg_color=COLORS['sidebar'], corner_radius=15)
        settings_panel.pack(fill="x", pady=(0, 20))
        
        # Page Count slider with dynamic label
        page_count_frame = ctk.CTkFrame(settings_panel, fg_color="transparent")
        page_count_frame.pack(fill="x", padx=25, pady=20)
        
        # Initialize page count variable (default: 10 pages)
        self.page_count_var = ctk.IntVar(value=10)
        
        # Dynamic label that updates with slider
        self.page_count_label = ctk.CTkLabel(
            page_count_frame,
            text="Target: 10 Pages",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS['text']
        )
        self.page_count_label.pack(anchor="w", pady=(0, 10))
        
        # Page Count slider (Range: 5 to 50)
        self.page_count_slider = ctk.CTkSlider(
            page_count_frame,
            from_=5,
            to=50,
            number_of_steps=45,
            variable=self.page_count_var,
            width=400,
            height=20,
            progress_color=COLORS['accent'],
            button_color=COLORS['accent'],
            button_hover_color=COLORS['accent_hover'],
            command=self._on_page_count_change
        )
        self.page_count_slider.pack(anchor="w")
        
        # Action buttons frame
        action_frame = ctk.CTkFrame(container, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 20))
        
        # Generate button
        self.generate_btn = ctk.CTkButton(
            action_frame,
            text="⚡ Generate Course",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=self._start_generation
        )
        self.generate_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Clear button
        clear_btn = ctk.CTkButton(
            action_frame,
            text="Clear",
            font=ctk.CTkFont(size=14),
            height=50,
            corner_radius=10,
            fg_color=COLORS['sidebar'],
            hover_color=COLORS['accent'],
            command=self._clear_instruction
        )
        clear_btn.pack(side="left", padx=(0, 0))
        
        # Logging console frame
        log_frame = ctk.CTkFrame(container, fg_color=COLORS['sidebar'], corner_radius=15)
        log_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        log_label = ctk.CTkLabel(
            log_frame,
            text="Generation Log",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS['text']
        )
        log_label.pack(anchor="w", padx=25, pady=(25, 10))
        
        # Logging console text widget - Matrix-style (Black bg/Green text)
        self.log_console = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            height=200,
            fg_color="#000000",  # Matrix-style black background
            text_color="#00FF00",  # Matrix-style green text
            border_color=COLORS['accent'],
            border_width=2,
            state="disabled"  # Read-only
        )
        self.log_console.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        # Progress frame (initially hidden)
        self.progress_frame = ctk.CTkFrame(container, fg_color=COLORS['sidebar'], corner_radius=15)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Generating your course...",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text']
        )
        self.progress_label.pack(pady=(20, 10))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=400,
            height=20,
            corner_radius=10,
            progress_color=COLORS['accent']
        )
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.set(0)
    
    def _create_library_tab(self):
        """Create the Library tab."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        title_label = ctk.CTkLabel(
            container,
            text="Course Library",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS['text']
        )
        title_label.pack(anchor="w", pady=(0, 10))
        
        subtitle_label = ctk.CTkLabel(
            container,
            text="View and manage your generated courses",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_dim']
        )
        subtitle_label.pack(anchor="w", pady=(0, 30))
        
        # Placeholder for library content
        placeholder_frame = ctk.CTkFrame(container, fg_color=COLORS['sidebar'], corner_radius=15)
        placeholder_frame.pack(fill="both", expand=True)
        
        placeholder_label = ctk.CTkLabel(
            placeholder_frame,
            text="📚 Your course library will appear here",
            font=ctk.CTkFont(size=16),
            text_color=COLORS['text_dim']
        )
        placeholder_label.pack(expand=True)
    
    def _create_settings_tab(self):
        """Create the Settings tab."""
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=40)
        
        title_label = ctk.CTkLabel(
            container,
            text="Settings",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS['text']
        )
        title_label.pack(anchor="w", pady=(0, 10))
        
        subtitle_label = ctk.CTkLabel(
            container,
            text="Configure your CourseSmith preferences",
            font=ctk.CTkFont(size=14),
            text_color=COLORS['text_dim']
        )
        subtitle_label.pack(anchor="w", pady=(0, 30))
        
        # Settings frame
        settings_frame = ctk.CTkFrame(container, fg_color=COLORS['sidebar'], corner_radius=15)
        settings_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # API Key section
        api_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        api_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        api_label = ctk.CTkLabel(
            api_frame,
            text="OpenAI API Key",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS['text']
        )
        api_label.pack(anchor="w", pady=(0, 10))
        
        api_help_label = ctk.CTkLabel(
            api_frame,
            text="Your API key is stored in the .env file in the application directory.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS['text_dim']
        )
        api_help_label.pack(anchor="w", pady=(0, 15))
        
        # Load current API key from environment
        current_key = os.getenv("OPENAI_API_KEY", "")
        
        # API Key entry with show/hide button
        entry_frame = ctk.CTkFrame(api_frame, fg_color="transparent")
        entry_frame.pack(fill="x", pady=(0, 10))
        
        self.api_key_entry = ctk.CTkEntry(
            entry_frame,
            placeholder_text="sk-...",
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS['background'],
            border_color=COLORS['accent'],
            border_width=2,
            show="*"
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        if current_key:
            self.api_key_entry.insert(0, current_key)
        
        # Add clipboard support (includes all shortcuts: Ctrl+C/V/A)
        from utils import add_context_menu
        add_context_menu(self.api_key_entry)
        
        # Show/Hide button
        self.api_key_visible = False
        self.show_hide_btn = ctk.CTkButton(
            entry_frame,
            text="👁",
            width=45,
            height=45,
            font=ctk.CTkFont(size=18),
            fg_color=COLORS['sidebar'],
            hover_color=COLORS['accent'],
            command=self._toggle_api_key_visibility
        )
        self.show_hide_btn.pack(side="right")
        
        # Save button
        save_btn = ctk.CTkButton(
            api_frame,
            text="💾 Save API Key",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            corner_radius=10,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_hover'],
            command=self._save_api_key
        )
        save_btn.pack(pady=(20, 0))
    
    def _toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        self.api_key_visible = not self.api_key_visible
        if self.api_key_visible:
            self.api_key_entry.configure(show="")
            self.show_hide_btn.configure(text="👁‍🗨")
        else:
            self.api_key_entry.configure(show="*")
            self.show_hide_btn.configure(text="👁")
    
    def _save_api_key(self):
        """Save the API key to .env file and update environment."""
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key.")
            return
        
        # Validate OpenAI API key format
        if not api_key.startswith("sk-"):
            result = messagebox.askyesno(
                "Invalid API Key Format",
                "The API key doesn't start with 'sk-' which is the expected format for OpenAI API keys.\n\n"
                "Do you want to save it anyway?"
            )
            if not result:
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
            
            # Update coursesmith_engine instance if it exists
            if hasattr(self, 'coursesmith_engine'):
                try:
                    from coursesmith_engine import CourseSmithEngine
                    self.coursesmith_engine = CourseSmithEngine(api_key=api_key)
                except Exception as e:
                    print(f"Warning: Could not reinitialize coursesmith_engine: {e}")
                    messagebox.showwarning(
                        "Partial Success",
                        f"API key saved, but engine reinitialization failed:\n{str(e)}\n\n"
                        "Please restart the application."
                    )
                    return
            
            messagebox.showinfo("Success", "API key saved successfully!")
            
        except IOError as e:
            messagebox.showerror("Error", f"Failed to save API key: {e}")
    
    def _on_page_count_change(self, value):
        """
        Handle page count slider change - update the dynamic label.
        
        Args:
            value: The new slider value (float, will be converted to int)
        """
        page_count = int(value)
        self.page_count_label.configure(text=f"Target: {page_count} Pages")
    
    def _log_message(self, message: str):
        """
        Add a timestamped message to the logging console.
        
        Args:
            message: The message to log
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update log console on main thread
        self.log_console.configure(state="normal")
        self.log_console.insert("end", log_entry)
        self.log_console.see("end")  # Scroll to bottom
        self.log_console.configure(state="disabled")
    
    def _generate_pdf_file(self, course_data: dict) -> str:
        """
        Generate a real PDF file from course data and save to Downloads folder.
        Uses the shared generate_pdf utility function from utils module.
        
        Args:
            course_data: Dictionary containing 'title' and 'chapters' list
            
        Returns:
            str: Path to the generated PDF file
        """
        from utils import generate_pdf
        # Get page count from slider (default to 10 if not set)
        page_count = getattr(self, 'page_count_var', None)
        target_pages = page_count.get() if page_count else 10
        return generate_pdf(course_data, page_count=target_pages)
    
    def _start_generation(self):
        """Start course generation with animated progress and detailed logging."""
        instruction = self.instruction_textbox.get("1.0", "end-1c").strip()
        
        if not instruction:
            messagebox.showwarning("Input Required", "Please enter a master instruction.")
            return
        
        # Get the target page count from slider
        target_page_count = getattr(self, 'page_count_var', None)
        target_pages = target_page_count.get() if target_page_count else 10
        
        # Clear log console
        self.log_console.configure(state="normal")
        self.log_console.delete("1.0", "end")
        self.log_console.configure(state="disabled")
        
        # Log generation start with page count
        self._log_message("🔥 Starting course generation...")
        self._log_message(f"📝 Instruction: {instruction[:100]}...")
        self._log_message(f"📄 Target Pages: {target_pages}")
        
        # Check if coursesmith_engine is available
        has_api_key = self.coursesmith_engine is not None and self.coursesmith_engine.client is not None
        
        if not has_api_key:
            self._log_message("⚠️  API key not configured - using simulated generation mode")
        
        # Show progress frame
        self.progress_frame.pack(fill="x", pady=(20, 0))
        self.generate_btn.configure(state="disabled")
        
        # Start progress animation
        self._animate_progress()
        
        # Store generated course data
        self.generated_course_data = None
        self.generated_pdf_path = None  # Initialize PDF path for consistency
        
        # Determine if using real or simulated generation
        if has_api_key:
            # Real course generation using coursesmith_engine
            def run_generation():
                try:
                    # Progress callback to update UI
                    def progress_callback(step, total, message):
                        # Update progress label on main thread (explicit value capture)
                        self.after(0, lambda msg=message: self._log_message(msg))
                        self.after(0, lambda msg=message: self.progress_label.configure(text=msg))
                    
                    # Generate the full course
                    course_data = self.coursesmith_engine.generate_full_course(
                        user_instruction=instruction,
                        progress_callback=progress_callback
                    )
                    
                    # Store the result
                    self.generated_course_data = course_data
                    
                    # Add email notification log - use actual user email from login
                    user_email = "user@example.com"
                    if self.license_data and isinstance(self.license_data, dict):
                        user_email = self.license_data.get('email', user_email)
                    self.after(0, lambda: self._log_message("📦 Packaging course..."))
                    self.after(EMAIL_LOG_DELAY_MS, lambda email=user_email: self._log_message(f"📧 Sending copy to {email}..."))
                    
                    # Notify completion on main thread
                    self.after(COMPLETION_DELAY_MS, lambda: self._finish_generation(success=True))
                    
                except Exception as e:
                    # Handle errors on main thread (explicit value capture)
                    error_msg = str(e)
                    self.after(0, lambda err=error_msg: self._log_message(f"❌ Error: {err}"))
                    self.after(0, lambda err=error_msg: self._finish_generation(success=False, error=err))
            
            # Run generation in background thread
            thread = threading.Thread(target=run_generation, daemon=True)
            thread.start()
        else:
            # Simulated generation with detailed step logging and PDF output
            # Uses sequential delays to provide realistic user feedback ("Matrix effect")
            # Smart Generation: Thinking time scales with page_count selection
            def run_simulated_generation():
                import time
                
                try:
                    # Calculate dynamic delay based on page count (smart generation)
                    # More pages = longer thinking time
                    base_delay = STEP_DELAY_SECONDS
                    page_multiplier = target_pages / 10.0  # Scale based on pages
                    smart_delay = base_delay * max(0.5, min(page_multiplier, 3.0))  # Clamp between 0.5x and 3x
                    
                    # Step 1: Initializing AI Engine (Matrix effect log sequence)
                    self.after(0, lambda: self._log_message("[System]: Initializing AI Engine..."))
                    self.after(0, lambda: self.progress_label.configure(text="Initializing AI Engine..."))
                    self.after(0, lambda: self.update_idletasks())  # Force UI refresh
                    time.sleep(smart_delay)
                    
                    # Step 2: Structuring Course Content
                    self.after(0, lambda: self._log_message("[AI]: Structuring Course Content..."))
                    self.after(0, lambda: self.progress_label.configure(text="Structuring Course Content..."))
                    self.after(0, lambda: self.update_idletasks())  # Force UI refresh
                    time.sleep(smart_delay)
                    
                    # Generate dynamic number of modules based on page count
                    num_modules = max(3, target_pages // 10)  # At least 3 modules, more for higher page counts
                    
                    # Write modules dynamically
                    for module_num in range(1, num_modules + 1):
                        self.after(0, lambda m=module_num: self._log_message(f"[Generative]: Writing Module {m}..."))
                        self.after(0, lambda m=module_num: self.progress_label.configure(text=f"Writing Module {m}..."))
                        self.after(0, lambda: self.update_idletasks())  # Force UI refresh
                        time.sleep(smart_delay)
                    
                    # Step N+1: Rendering PDF document
                    self.after(0, lambda: self._log_message("[PDF]: Rendering document..."))
                    self.after(0, lambda: self.progress_label.configure(text="Rendering PDF document..."))
                    self.after(0, lambda: self.update_idletasks())  # Force UI refresh
                    time.sleep(PACKAGING_DELAY_SECONDS)
                    
                    # Create simulated course data - modules scale with page count
                    chapters = []
                    for i in range(num_modules):
                        module_titles = ['Introduction', 'Core Concepts', 'Advanced Topics', 'Practical Applications', 'Case Studies', 'Best Practices', 'Future Trends']
                        title = f"Module {i+1}: {module_titles[i % len(module_titles)]}"
                        content = f"This is the {module_titles[i % len(module_titles)].lower()} module content.\n\n[VIDEO/IMAGE PLACEHOLDER]\n\nSimulated educational content for Module {i+1}. This module covers important aspects of the topic and provides detailed explanations."
                        chapters.append({'title': title, 'content': content})
                    
                    course_data = {
                        'title': f"Course: {instruction[:50]}",
                        'chapters': chapters,
                        'language': 'en'
                    }
                    
                    self.generated_course_data = course_data
                    
                    # Generate real PDF file to Downloads folder
                    pdf_path = self._generate_pdf_file(course_data)
                    
                    # Step N+2: File saved to Downloads (include filename)
                    pdf_filename = os.path.basename(pdf_path)
                    self.after(0, lambda fn=pdf_filename: self._log_message(f"[System]: File saved to Downloads: {fn}"))
                    self.after(0, lambda: self.update_idletasks())  # Force UI refresh
                    
                    # Store PDF path for success message
                    self.generated_pdf_path = pdf_path
                    
                    # Notify completion on main thread
                    self.after(0, lambda: self._finish_generation(success=True))
                    
                except Exception as e:
                    # Handle errors on main thread (explicit value capture)
                    error_msg = str(e)
                    self.after(0, lambda err=error_msg: self._log_message(f"❌ Error: {err}"))
                    self.after(0, lambda err=error_msg: self._finish_generation(success=False, error=err))
            
            # Run simulated generation in background thread
            thread = threading.Thread(target=run_simulated_generation, daemon=True)
            thread.start()
    
    def _animate_progress(self):
        """Animate progress bar smoothly."""
        if not self.progress_animation_running:
            self.progress_animation_running = True
            self.progress_bar.set(0)
            self._update_progress_animation(0)
    
    def _update_progress_animation(self, value):
        """Update progress bar animation."""
        if self.progress_animation_running and self.winfo_exists():
            # Increment progress
            value = min(value + 0.01, 0.95)  # Max at 95% until complete
            self.progress_bar.set(value)
            
            # Update label with different messages
            if value < 0.3:
                self.progress_label.configure(text="Analyzing your instruction...")
            elif value < 0.6:
                self.progress_label.configure(text="Generating course structure...")
            elif value < 0.9:
                self.progress_label.configure(text="Creating content...")
            else:
                self.progress_label.configure(text="Finalizing your course...")
            
            # Continue animation
            self.after(50, lambda: self._update_progress_animation(value))
    
    def _stop_progress_animation(self):
        """Stop progress bar animation."""
        self.progress_animation_running = False
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Course generation complete!")
    
    def _finish_generation(self, success=True, error=None):
        """
        Finish generation and show result.
        
        Args:
            success: Whether generation succeeded.
            error: Error message if generation failed.
        """
        self._stop_progress_animation()
        
        # Show completion for a moment
        def complete_generation():
            self.progress_frame.pack_forget()
            self.generate_btn.configure(state="normal")
            
            if success and self.generated_course_data:
                # Save generated course to data directory
                try:
                    from utils import get_data_dir
                    data_dir = get_data_dir()
                    courses_dir = os.path.join(data_dir, "generated_courses")
                    os.makedirs(courses_dir, exist_ok=True)
                    
                    # Create filename from title and timestamp
                    title = self.generated_course_data.get('title', 'Untitled Course')
                    # Sanitize filename
                    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_title = safe_title[:50]  # Limit length
                    # Ensure filename is not empty after sanitization
                    if not safe_title:
                        safe_title = "Course"
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{safe_title}_{timestamp}.json"
                    filepath = os.path.join(courses_dir, filename)
                    
                    # Save course data to JSON
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(self.generated_course_data, f, indent=2, ensure_ascii=False)
                    
                    # Show success message with course info (include PDF path if generated)
                    course_title = self.generated_course_data.get('title', 'Course')
                    chapter_count = len(self.generated_course_data.get('chapters', []))
                    
                    # Include PDF path in message if available
                    pdf_info = ""
                    if hasattr(self, 'generated_pdf_path') and self.generated_pdf_path:
                        pdf_info = f"\n\nPDF saved to:\n{self.generated_pdf_path}"
                    
                    messagebox.showinfo(
                        "Success", 
                        f"Course generated successfully!\n\n"
                        f"Title: {course_title}\n"
                        f"Chapters: {chapter_count}\n"
                        f"Language: {self.generated_course_data.get('language', 'en')}"
                        f"{pdf_info}"
                    )
                except Exception as save_error:
                    # Still show success but mention save error
                    messagebox.showwarning(
                        "Partial Success",
                        f"Course generated successfully but failed to save:\n{save_error}"
                    )
            elif success:
                # Success but no data (shouldn't happen)
                messagebox.showwarning("Warning", "Course generation completed but no data was returned.")
            else:
                # Generation failed
                messagebox.showerror(
                    "Generation Failed", 
                    f"Failed to generate course:\n\n{error}\n\n"
                    "Please check your API key and internet connection."
                )
        
        self.after(1000, complete_generation)
    
    def _clear_instruction(self):
        """Clear the instruction textbox."""
        self.instruction_textbox.delete("1.0", "end")


def main():
    """Initialize and run the CourseSmith ENTERPRISE application."""
    # Check for remote ban before starting the application
    check_remote_ban()
    
    # Load environment variables with PyInstaller support
    # Try to find .env in the executable directory (works for both dev and EXE)
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in development mode
        base_path = os.path.abspath(".")
    
    env_path = os.path.join(base_path, ".env")
    
    # Load .env if it exists
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        # Fallback to current directory for development
        load_dotenv()
    
    # Set appearance mode
    ctk.set_appearance_mode("Dark")
    
    # Create custom theme with enterprise colors
    ctk.set_default_color_theme("blue")
    
    # Import app here after environment is loaded
    # Note: The EnterpriseApp is the new main UI
    # The original App class is still available via: from app import App
    
    # Create and run the enterprise application
    app = EnterpriseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
