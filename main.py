"""
CourseSmith ENTERPRISE - Entry Point
A commercial desktop application to generate educational PDF books using AI with DRM protection.
"""

import os
import sys
import subprocess
from datetime import datetime, timezone
import customtkinter as ctk
from tkinter import messagebox
from dotenv import load_dotenv
from supabase import create_client, Client


# Supabase configuration for remote kill switch
SUPABASE_URL = "https://spfwfyjpexktgnusgyib.supabase.co"
SUPABASE_KEY = "sb_publishable_tmwenU0VyOChNWKG90X_bw_HYf9X5kR"


def get_hwid():
    """
    Get the Windows Hardware ID (UUID) using wmic command.
    
    Returns:
        str: The hardware UUID or "UNKNOWN_ID" if an error occurs.
    """
    try:
        # Execute wmic command to get system UUID
        result = subprocess.run(
            ["wmic", "csproduct", "get", "uuid"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse output - UUID is on second line
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                uuid = lines[1].strip()
                if uuid and uuid != "UUID":
                    return uuid
        
        return "UNKNOWN_ID"
    except Exception:
        return "UNKNOWN_ID"


def check_remote_ban():
    """
    Check if the current HWID is banned in the remote Supabase database.
    Also check if the license has expired.
    If banned or expired, show error message and exit the application.
    Allows offline usage by catching connection errors.
    """
    try:
        # Get current hardware ID
        hwid = get_hwid()
        
        # Connect to Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query licenses table for current HWID (fetch is_banned and valid_until fields)
        response = supabase.table("licenses").select("is_banned, valid_until").eq("hwid", hwid).execute()
        
        # Check if HWID exists
        if response.data and len(response.data) > 0:
            license_record = response.data[0]
            
            # Check if license is banned
            if license_record.get("is_banned") is True:
                # Show error message (messagebox works without creating root window)
                messagebox.showerror(
                    "Access Denied",
                    "Access Denied. License Revoked."
                )
                
                # Exit immediately
                sys.exit()
            
            # Check if license has expired
            valid_until = license_record.get("valid_until")
            if valid_until:
                try:
                    # Parse the expiration date
                    expiration_date = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                    current_date = datetime.now(timezone.utc)
                    
                    # Check if expired
                    if current_date > expiration_date:
                        messagebox.showerror(
                            "Subscription Expired",
                            "Subscription expired. Please renew on Whop."
                        )
                        sys.exit()
                except Exception:
                    # If date parsing fails, allow access (fail-open for this check)
                    pass
        
        # If HWID not found or not banned/expired, allow app to continue
    except Exception:
        # Allow offline usage - if connection fails, don't block the app
        pass


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
    ctk.set_default_color_theme("blue")
    
    # Import app here after environment is loaded
    from app import App
    
    # Create and run the application
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
