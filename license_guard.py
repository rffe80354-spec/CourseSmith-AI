"""
License Guard Module - DRM Security for CourseSmith ENTERPRISE.
Provides license key generation and validation using SHA256 hashing.
Returns session tokens on successful validation for anti-tamper protection.
"""

import hashlib
import base64
import os
import json
import time

from utils import get_data_dir


# Secret salt for license key generation - DO NOT SHARE
SECRET_SALT = "CS_2026_SECURE_SALT"

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


def _generate_session_token(email):
    """
    Generate a session token for a validated license.
    
    Args:
        email: The validated user's email address.
        
    Returns:
        str: A unique session token.
    """
    timestamp = str(time.time())
    token_input = f"{email}{timestamp}{SECRET_SALT}"
    token_bytes = hashlib.sha256(token_input.encode('utf-8')).digest()
    return base64.b64encode(token_bytes).decode('utf-8')[:48]


def validate_license(email, key):
    """
    Validate a license key against an email address.
    
    Args:
        email: The user's email address.
        key: The license key to validate.
        
    Returns:
        str or None: A session token if valid, None if invalid.
    """
    if not email or not key:
        return None
    
    # Generate expected key for this email
    expected_key = generate_key(email)
    
    # Compare keys (case-insensitive)
    if key.strip().upper() == expected_key.upper():
        # Valid! Return a session token
        return _generate_session_token(email)
    
    return None


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
            "version": "2.0"
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
        tuple: (session_token, email) - session_token is the token if valid (or None),
               email is the registered email or None.
    """
    try:
        license_path = get_license_path()
        
        if not os.path.exists(license_path):
            return None, None
        
        with open(license_path, 'r', encoding='utf-8') as f:
            license_data = json.load(f)
        
        email = license_data.get("email", "")
        key = license_data.get("key", "")
        
        # Validate and get session token
        session_token = validate_license(email, key)
        
        if session_token:
            return session_token, email
        else:
            return None, None
            
    except (IOError, OSError, json.JSONDecodeError) as e:
        print(f"Failed to load license: {e}")
        return None, None


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
