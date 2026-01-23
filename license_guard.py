"""
License Guard Module - DRM Security for CourseSmith ENTERPRISE.
Provides license key generation and validation using SHA256 hashing.
"""

import hashlib
import base64
import os
import json

from utils import get_data_dir


# Secret salt for license key generation - DO NOT SHARE
SECRET_SALT = "CourseSmith_2026_ULTIMATE_SECURE_SALT"

# License file name (hidden file)
LICENSE_FILE = ".license"


def generate_key(email):
    """
    Generate a license key for the given email address.
    
    Uses SHA256 hash of email + secret salt to create a unique key.
    
    Args:
        email: The buyer's email address.
        
    Returns:
        str: The generated license key (base64 encoded).
    """
    email = email.strip().lower()
    
    # Create hash from email + salt
    hash_input = f"{email}{SECRET_SALT}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    
    # Encode as base64 and take first 32 characters for cleaner key
    key = base64.b64encode(hash_bytes).decode('utf-8')[:32]
    
    # Format key with dashes for readability (8-8-8-8 format)
    formatted_key = f"{key[:8]}-{key[8:16]}-{key[16:24]}-{key[24:32]}"
    
    return formatted_key


def validate_license(email, key):
    """
    Validate a license key against an email address.
    
    Args:
        email: The user's email address.
        key: The license key to validate.
        
    Returns:
        bool: True if the key is valid for the email, False otherwise.
    """
    if not email or not key:
        return False
    
    # Generate expected key for this email
    expected_key = generate_key(email)
    
    # Compare keys (case-insensitive)
    return key.strip().upper() == expected_key.upper()


def get_license_path():
    """
    Get the path to the license file.
    
    Returns:
        str: Full path to the license file.
    """
    data_dir = get_data_dir()
    return os.path.join(data_dir, LICENSE_FILE)


def save_license(email, key):
    """
    Save a valid license to the license file.
    
    Args:
        email: The user's email address.
        key: The validated license key.
        
    Returns:
        bool: True if saved successfully, False otherwise.
    """
    try:
        license_path = get_license_path()
        
        license_data = {
            "email": email.strip().lower(),
            "key": key.strip(),
            "version": "1.0"
        }
        
        with open(license_path, 'w', encoding='utf-8') as f:
            json.dump(license_data, f)
        
        return True
    except (IOError, OSError) as e:
        print(f"Failed to save license: {e}")
        return False


def load_license():
    """
    Load and validate the stored license.
    
    Returns:
        tuple: (is_valid, email) - is_valid is True if license is valid,
               email is the registered email or None.
    """
    try:
        license_path = get_license_path()
        
        if not os.path.exists(license_path):
            return False, None
        
        with open(license_path, 'r', encoding='utf-8') as f:
            license_data = json.load(f)
        
        email = license_data.get("email", "")
        key = license_data.get("key", "")
        
        if validate_license(email, key):
            return True, email
        else:
            return False, None
            
    except (IOError, OSError, json.JSONDecodeError) as e:
        print(f"Failed to load license: {e}")
        return False, None


def remove_license():
    """
    Remove the stored license file.
    
    Returns:
        bool: True if removed successfully or file doesn't exist.
    """
    try:
        license_path = get_license_path()
        if os.path.exists(license_path):
            os.remove(license_path)
        return True
    except (IOError, OSError) as e:
        print(f"Failed to remove license: {e}")
        return False
