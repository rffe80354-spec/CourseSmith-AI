"""
License Guard Module - DRM Security for Faleovad AI Enterprise.
Provides tiered license key generation and validation using SHA256 hashing.
Returns session tokens and tier info on successful validation for anti-tamper protection.

Tiers:
- Standard (STD-): Basic features, no branding customization
- Extended (EXT-): Full features, custom logo and website support
"""

import hashlib
import base64
import os
import json
import time

from utils import get_data_dir


# Secret salt for license key generation - DO NOT SHARE
SECRET_SALT = "FALEOVAD_2009_SECURE_A5432"

# License file name (hidden file)
LICENSE_FILE = ".license"


def generate_key(email, tier='standard'):
    """
    Generate a license key for the given email address and tier.
    
    Uses SHA256 hash of email + tier + secret salt to create a unique key.
    Prefixes the key with STD- or EXT- based on tier.
    
    Args:
        email: The buyer's email address.
        tier: The license tier ('standard' or 'extended').
        
    Returns:
        str: The generated license key with tier prefix.
    """
    email = email.strip().lower()
    tier = tier.lower() if tier else 'standard'
    
    # Validate tier
    if tier not in ('standard', 'extended'):
        tier = 'standard'
    
    # Create hash from email + tier + salt
    hash_input = f"{email}{tier}{SECRET_SALT}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    
    # Encode as base64 and take first 24 characters for cleaner key
    key = base64.b64encode(hash_bytes).decode('utf-8')[:24]
    
    # Format key with tier prefix (TIER-XXXX-XXXX-XXXX format)
    prefix = "EXT" if tier == 'extended' else "STD"
    formatted_key = f"{prefix}-{key[:8]}-{key[8:16]}-{key[16:24]}"
    
    return formatted_key


def _generate_session_token(email, tier):
    """
    Generate a session token for a validated license.
    
    Args:
        email: The validated user's email address.
        tier: The license tier.
        
    Returns:
        str: A unique session token.
    """
    timestamp = str(time.time())
    token_input = f"{email}{tier}{timestamp}{SECRET_SALT}"
    token_bytes = hashlib.sha256(token_input.encode('utf-8')).digest()
    return base64.b64encode(token_bytes).decode('utf-8')[:48]


def _extract_tier_from_key(key):
    """
    Extract the tier from a license key prefix.
    
    Args:
        key: The license key.
        
    Returns:
        str: 'standard' or 'extended', or None if invalid prefix.
    """
    if not key:
        return None
    
    key_upper = key.strip().upper()
    if key_upper.startswith('EXT-'):
        return 'extended'
    elif key_upper.startswith('STD-'):
        return 'standard'
    else:
        return None


def validate_license(email, key):
    """
    Validate a license key against an email address.
    
    Args:
        email: The user's email address.
        key: The license key to validate.
        
    Returns:
        dict or None: Dictionary with 'valid', 'tier', 'token' if valid, None if invalid.
    """
    if not email or not key:
        return None
    
    # Extract tier from key prefix
    tier = _extract_tier_from_key(key)
    if tier is None:
        return None
    
    # Generate expected key for this email and tier
    expected_key = generate_key(email, tier)
    
    # Compare keys (case-insensitive)
    if key.strip().upper() == expected_key.upper():
        # Valid! Return session info
        token = _generate_session_token(email, tier)
        return {
            'valid': True,
            'tier': tier,
            'token': token
        }
    
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
        
        # Extract tier from key
        tier = _extract_tier_from_key(key)
        
        license_data = {
            "email": email.strip().lower(),
            "key": key.strip(),
            "tier": tier or 'standard',
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
        tuple: (session_token, email, tier) - token/email/tier if valid (or None values).
    """
    try:
        license_path = get_license_path()
        
        if not os.path.exists(license_path):
            return None, None, None
        
        with open(license_path, 'r', encoding='utf-8') as f:
            license_data = json.load(f)
        
        email = license_data.get("email", "")
        key = license_data.get("key", "")
        
        # Validate and get session info
        result = validate_license(email, key)
        
        if result and result.get('valid'):
            return result['token'], email, result['tier']
        else:
            return None, None, None
            
    except (IOError, OSError, json.JSONDecodeError) as e:
        print(f"Failed to load license: {e}")
        return None, None, None


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
