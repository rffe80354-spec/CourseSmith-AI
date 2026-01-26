"""
CourseSmith ENTERPRISE - Entry Point
A commercial desktop application to generate educational PDF books using AI with DRM protection.
"""

import os
import sys
import json
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
    Check if the current HWID is authorized for license activation.
    Implements multi-device license support:
    - Checks if license has expired
    - Checks if license is banned
    - Validates device count against max_devices limit
    - Automatically registers new devices if room available
    - Uses 'used_hwids' JSONB array instead of single 'hwid' column
    
    If banned, expired, or device limit reached, shows error and exits.
    Allows offline usage by catching connection errors.
    """
    try:
        # Get current hardware ID
        current_hwid = get_hwid()
        
        # Connect to Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query licenses table for current HWID in used_hwids array
        # We need to check all licenses that contain this HWID OR have room for it
        response = supabase.table("licenses").select("*").execute()
        
        # Find license that matches this HWID or can accept it
        license_record = None
        for record in response.data if response.data else []:
            # Parse used_hwids (JSONB array)
            used_hwids = record.get("used_hwids", [])
            if used_hwids is None:
                used_hwids = []
            
            # Check if current HWID is already registered
            if current_hwid in used_hwids:
                license_record = record
                break
        
        # If no license found with this HWID, check if any license can accept a new device
        # This allows first-time activation with just a license key
        if license_record is None:
            # No license found with this HWID - user needs to enter license key
            # This is handled by the license_guard.py module during first run
            # For now, we just allow the app to continue (offline mode)
            return
        
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
                        "Your subscription for CourseSmith AI has expired. Please renew on Whop to continue."
                    )
                    sys.exit()
            except Exception:
                # If date parsing fails, allow access (fail-open for this check)
                pass
        
        # If we reach here, license is valid and HWID is authorized
        
    except Exception:
        # Allow offline usage - if connection fails, don't block the app
        pass


def validate_license_key(license_key: str) -> dict:
    """
    Validate a license key and register the current device if authorized.
    This function is called during first-time activation.
    
    Args:
        license_key: The license key to validate
        
    Returns:
        dict: License information with status
            {'valid': bool, 'message': str, 'license_data': dict or None}
    """
    try:
        # Get current hardware ID
        current_hwid = get_hwid()
        
        # Connect to Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query licenses table for the provided license key
        response = supabase.table("licenses").select("*").eq("license_key", license_key).execute()
        
        # Check if license key exists
        if not response.data or len(response.data) == 0:
            return {
                'valid': False,
                'message': 'Invalid license key.',
                'license_data': None
            }
        
        license_record = response.data[0]
        
        # Check if license is banned
        if license_record.get("is_banned") is True:
            return {
                'valid': False,
                'message': 'This license has been revoked.',
                'license_data': None
            }
        
        # Check if license has expired
        valid_until = license_record.get("valid_until")
        if valid_until:
            try:
                expiration_date = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                current_date = datetime.now(timezone.utc)
                
                if current_date > expiration_date:
                    return {
                        'valid': False,
                        'message': 'This license has expired.',
                        'license_data': None
                    }
            except Exception:
                pass
        
        # Parse used_hwids (JSONB array)
        used_hwids = license_record.get("used_hwids", [])
        if used_hwids is None:
            used_hwids = []
        
        max_devices = license_record.get("max_devices", 1)
        
        # Check if current HWID is already registered
        if current_hwid in used_hwids:
            # Already activated on this device
            return {
                'valid': True,
                'message': 'License is valid and already activated on this device.',
                'license_data': license_record
            }
        
        # Check if there's room for a new device
        if len(used_hwids) < max_devices:
            # Add current HWID to the list
            used_hwids.append(current_hwid)
            
            # Update Supabase with new HWID
            supabase.table("licenses").update({
                "used_hwids": used_hwids
            }).eq("license_key", license_key).execute()
            
            return {
                'valid': True,
                'message': f'License activated successfully! Device {len(used_hwids)}/{max_devices} registered.',
                'license_data': license_record
            }
        else:
            # Device limit reached
            return {
                'valid': False,
                'message': f'Device Limit Reached. Max: {max_devices}. Please deactivate a device or upgrade your license.',
                'license_data': None
            }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f'Error validating license: {str(e)}',
            'license_data': None
        }


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
