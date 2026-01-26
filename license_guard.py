"""
License Guard Module - Enterprise DRM Security for CourseSmith AI.
Provides enterprise-grade license key generation and validation with:
- HWID Locking (Hardware ID binding) - Enterprise tier and above
- Custom Key Format: CS-XXXX-XXXX (12 characters, 8 hex digits)
- Time-Bombing with NTP verification (anti-tamper)
- Persistent Session with encrypted tokens
- Cloud-based license validation with Supabase
- Four-tier system with cloud protection

Tiers:
- Trial: 3 days, 10 pages, cloud-protected
- Standard: 50 pages, cloud-protected, basic features
- Enterprise: 300 pages, all AI features, HWID binding, cloud-protected
- Lifetime: Enterprise features, no expiration, cloud-protected

Durations:
- 3 Days: Trial period
- 1 Month: 30 days from activation
- 3 Months: 90 days from activation
- 6 Months: 180 days from activation
- 1 Year: 365 days from activation
- Lifetime: No expiration
"""

import hashlib
import base64
import os
import json
import time
import platform
import subprocess
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet

from utils import get_data_dir

# Try to import database_manager for license validation
try:
    from database_manager import get_license_by_key, check_cloud_status, update_hwid
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("Warning: database_manager not available. Some features may not work.")

# Try to import NTP library for time verification
try:
    import ntplib
    NTP_AVAILABLE = True
except ImportError:
    NTP_AVAILABLE = False
    print("Warning: ntplib not available. NTP time verification disabled.")


# Secret salt for license key generation - DO NOT SHARE
SECRET_SALT = "FALEOVAD_2009_SECURE_A5432_ENTERPRISE_v2"

# Key format constants
KEY_FORMAT_LENGTH = 12  # CS-XXXX-XXXX = 12 characters
KEY_DASH_COUNT = 2      # 2 dashes in the format
KEY_PREFIX = "CS-"      # All keys start with CS-

# Session file for persistent login (encrypted)
SESSION_FILE = ".session_token"

# Encryption key for session storage (derived from machine ID)
_encryption_key_cache = None

# NTP servers for time verification
NTP_SERVERS = [
    'pool.ntp.org',
    'time.google.com',
    'time.windows.com',
    'time.cloudflare.com'
]

# Tier configuration - Four tiers with cloud protection
TIER_LIMITS = {
    'trial': {
        'max_pages': 10,
        'hwid_required': False,
        'ai_images': False,
        'quizzes': False,
        'translation': False,
        'custom_branding': False,
        'cloud_protected': True
    },
    'standard': {
        'max_pages': 50,
        'hwid_required': False,
        'ai_images': True,
        'quizzes': False,
        'translation': False,
        'custom_branding': False,
        'cloud_protected': True
    },
    'enterprise': {
        'max_pages': 300,
        'hwid_required': True,
        'ai_images': True,
        'quizzes': True,
        'translation': True,
        'custom_branding': True,
        'cloud_protected': True
    },
    'lifetime': {
        'max_pages': 300,
        'hwid_required': True,
        'ai_images': True,
        'quizzes': True,
        'translation': True,
        'custom_branding': True,
        'cloud_protected': True
    }
}

# Tier code mapping for license key generation
TIER_CODE_MAP = {
    'trial': 'TRL',
    'standard': 'STD', 
    'enterprise': 'ENT',
    'lifetime': 'LFT'
}

# Tier extraction mapping for license key parsing
TIER_EXTRACT_MAP = {
    'TRL': 'trial',
    'STD': 'standard',
    'ENT': 'enterprise',
    'LFT': 'lifetime',
    'EXT': 'enterprise'  # Legacy support
}


def get_ntp_time() -> Optional[datetime]:
    """
    Get current time from NTP server to prevent local clock tampering.
    Tries multiple NTP servers for reliability.
    
    Returns:
        datetime: Current time from NTP server, or None if all servers fail.
    """
    if not NTP_AVAILABLE:
        return None
    
    client = ntplib.NTPClient()
    
    for server in NTP_SERVERS:
        try:
            response = client.request(server, version=3, timeout=2)
            ntp_time = datetime.fromtimestamp(response.tx_time)
            return ntp_time
        except Exception as e:
            # Try next server
            continue
    
    return None


def get_reliable_time() -> datetime:
    """
    Get reliable current time.
    Prefers NTP time but falls back to system time if NTP unavailable.
    
    Returns:
        datetime: Current time (NTP if available, system time otherwise).
    """
    ntp_time = get_ntp_time()
    if ntp_time:
        return ntp_time
    
    # Fallback to system time
    return datetime.now()


def get_tier_limits(tier: str) -> Dict[str, Any]:
    """
    Get the limits and features for a given license tier.
    
    Args:
        tier: License tier ('trial', 'standard', 'enterprise', or 'lifetime').
        
    Returns:
        dict: Tier configuration with limits and features.
    """
    return TIER_LIMITS.get(tier.lower() if tier else 'trial', TIER_LIMITS['trial'])


def get_hwid() -> str:
    """
    Get a unique hardware ID for this machine.
    Uses motherboard serial and CPU info to create a machine-specific identifier.
    
    Returns:
        str: Hardware ID unique to this machine.
    """
    hwid_components = []
    
    try:
        # Get system information
        system = platform.system()
        
        if system == "Windows":
            # Get motherboard serial on Windows
            try:
                result = subprocess.check_output(
                    "wmic baseboard get serialnumber",
                    shell=True,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                serial = result.strip().split('\n')[-1].strip()
                if serial and serial != "SerialNumber":
                    hwid_components.append(serial)
            except Exception:
                pass
            
            # Get CPU ID on Windows
            try:
                result = subprocess.check_output(
                    "wmic cpu get processorid",
                    shell=True,
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                cpu_id = result.strip().split('\n')[-1].strip()
                if cpu_id and cpu_id != "ProcessorId":
                    hwid_components.append(cpu_id)
            except Exception:
                pass
                
        elif system == "Linux":
            # Get machine ID on Linux
            try:
                with open("/etc/machine-id", "r") as f:
                    machine_id = f.read().strip()
                    if machine_id:
                        hwid_components.append(machine_id)
            except Exception:
                pass
            
            # Get CPU info on Linux
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "Serial" in line:
                            serial = line.split(":")[-1].strip()
                            if serial:
                                hwid_components.append(serial)
                            break
            except Exception:
                pass
                
        elif system == "Darwin":  # macOS
            # Get hardware UUID on macOS
            try:
                result = subprocess.check_output(
                    ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                for line in result.split('\n'):
                    if "IOPlatformUUID" in line:
                        uuid = line.split('"')[3]
                        if uuid:
                            hwid_components.append(uuid)
                        break
            except Exception:
                pass
        
        # Fallback to MAC address if no other identifiers found
        if not hwid_components:
            import uuid
            mac = uuid.getnode()
            hwid_components.append(str(mac))
            # Add more unique identifiers for better fallback
            import socket
            try:
                hwid_components.append(socket.gethostname())
                hwid_components.append(str(os.getpid()))
            except:
                pass
        
        # Add hostname as additional component
        hwid_components.append(platform.node())
        
    except Exception as e:
        # Ultimate fallback - use a combination of system info and process-specific data
        import uuid
        hwid_components = [
            platform.system(),
            platform.machine(),
            platform.node(),
            str(uuid.getnode()),  # MAC address
            str(os.getpid()),  # Process ID for uniqueness
            os.environ.get('USERNAME', os.environ.get('USER', 'unknown'))  # Username
        ]
    
    # Combine all components and hash
    hwid_string = "|".join(hwid_components)
    hwid_hash = hashlib.sha256(hwid_string.encode('utf-8')).hexdigest()[:32].upper()
    
    return hwid_hash


def _get_encryption_key() -> bytes:
    """
    Get or generate an encryption key for session storage.
    The key is derived from the hardware ID for machine-specific encryption.
    
    Returns:
        bytes: Fernet encryption key.
    """
    global _encryption_key_cache
    
    if _encryption_key_cache is not None:
        return _encryption_key_cache
    
    # Derive key from HWID
    hwid = get_hwid()
    key_material = f"{hwid}{SECRET_SALT}".encode('utf-8')
    key_hash = hashlib.sha256(key_material).digest()
    _encryption_key_cache = base64.urlsafe_b64encode(key_hash)
    
    return _encryption_key_cache


def _extract_email_prefix(email: str, length: int = 6) -> str:
    """
    Extract the email prefix (before @) for use in license keys.
    
    Args:
        email: Email address.
        length: Number of characters to extract (default 6).
        
    Returns:
        str: Email prefix in uppercase, alphanumeric only.
    """
    prefix = email.split('@')[0]
    # Remove all non-alphanumeric characters
    prefix = ''.join(c for c in prefix if c.isalnum())
    # Take first N chars, pad with X if too short
    prefix = prefix[:length].upper().ljust(length, 'X')
    return prefix


def _format_expiration_code(expires_at: Optional[str]) -> str:
    """
    Format expiration date as a code for the license key.
    
    Args:
        expires_at: ISO format date string, or None for lifetime.
        
    Returns:
        str: Expiration code (YYYYMMDD or 'LIFETIME').
    """
    if not expires_at:
        return "LIFETIME"
    
    try:
        dt = datetime.fromisoformat(expires_at)
        return dt.strftime("%Y%m%d")
    except (ValueError, TypeError):
        return "LIFETIME"


def _calculate_expiration(duration: str) -> Optional[str]:
    """
    Calculate expiration date based on duration.
    
    Args:
        duration: '3_day', '1_month', '3_month', '6_month', '1_year', or 'lifetime'.
        
    Returns:
        str: ISO format expiration date, or None for lifetime.
    """
    if duration == 'lifetime':
        return None
    elif duration == '3_day':
        return (datetime.now() + timedelta(days=3)).isoformat()
    elif duration == '1_month':
        return (datetime.now() + timedelta(days=30)).isoformat()
    elif duration == '3_month':
        return (datetime.now() + timedelta(days=90)).isoformat()
    elif duration == '6_month':
        return (datetime.now() + timedelta(days=180)).isoformat()
    elif duration == '1_year':
        return (datetime.now() + timedelta(days=365)).isoformat()
    else:
        return None


def generate_key(email: str, tier: str = 'trial', duration: str = 'lifetime') -> Tuple[str, Optional[str]]:
    """
    Generate a license key in CS-XXXX-XXXX format (standardized for all tiers).
    Format: CS-XXXX-XXXX where X is an uppercase hex character (8 hex chars total, 12 chars including prefix and dashes).
    
    Args:
        email: The buyer's email address.
        tier: The license tier ('trial', 'standard', 'enterprise', or 'lifetime').
        duration: License duration ('3_day', '1_month', '3_month', '6_month', '1_year', 'lifetime').
        
    Returns:
        tuple: (license_key, expiration_date_iso) where expiration_date_iso is None for lifetime.
    """
    email = email.strip().lower()
    tier = tier.lower() if tier else 'trial'
    duration = duration.lower() if duration else 'lifetime'
    
    # Validate tier - support legacy naming
    if tier == 'extended':
        tier = 'enterprise'
    if tier not in TIER_LIMITS:
        tier = 'trial'
    
    # Validate duration
    if duration not in ('3_day', '1_month', '3_month', '6_month', '1_year', 'lifetime'):
        duration = 'lifetime'
    
    # Calculate expiration
    expires_at = _calculate_expiration(duration)
    
    # Generate signature using HMAC for cryptographic security
    # Include all relevant data in the signature for validation
    signature_input = f"{email}{tier}{duration}{expires_at}{SECRET_SALT}"
    signature_bytes = hmac.new(
        SECRET_SALT.encode('utf-8'),
        signature_input.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # Convert to hex and take first 8 characters for CS-XXXX-XXXX format
    hex_signature = signature_bytes.hex().upper()[:8]
    
    # Format as CS-XXXX-XXXX (CS + 4 hex + dash + 4 hex = 12 chars total)
    license_key = f"CS-{hex_signature[:4]}-{hex_signature[4:]}"
    
    return license_key, expires_at


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


def _extract_tier_from_key(key: str) -> Optional[str]:
    """
    Extract the tier from a license key.
    Supports multiple formats: PREFIX-TRL/STD/ENT/LFT-...
    
    Args:
        key: The license key.
        
    Returns:
        str: 'trial', 'standard', 'enterprise', 'lifetime', or None if invalid.
    """
    if not key:
        return None
    
    key_upper = key.strip().upper()
    parts = key_upper.split('-')
    
    # New format: EMAILPREFIX-TIER-EXPIRATION-SIGNATURE (4 parts)
    if len(parts) >= 4:
        tier_part = parts[1]
        return TIER_EXTRACT_MAP.get(tier_part, 'trial')
    
    # Old format: TIER-XXXX-XXXX-XXXX (4 parts starting with tier)
    if len(parts) == 4:
        return TIER_EXTRACT_MAP.get(parts[0], 'trial')
    
    return None


def _parse_key_components(key: str) -> Optional[Dict[str, str]]:
    """
    Parse a license key into its components.
    Supports new format: EMAILPREFIX-TIER-EXPIRATION-SIGNATURE
    
    Args:
        key: The license key.
        
    Returns:
        dict: Dictionary with 'email_prefix', 'tier', 'expiration', 'signature', or None if invalid.
    """
    if not key:
        return None
    
    parts = key.strip().upper().split('-')
    
    # New format has 4 parts
    if len(parts) == 4:
        return {
            'email_prefix': parts[0],
            'tier': parts[1],
            'expiration': parts[2],
            'signature': parts[3]
        }
    
    return None


def validate_license(email: str, key: str, hwid: Optional[str] = None, 
                    check_expiration: bool = True) -> Optional[Dict[str, Any]]:
    """
    Validate a license key in CS-XXXX-XXXX format with multi-device support.
    Supports all tiers: Trial, Standard, Enterprise, Lifetime.
    
    Args:
        email: The user's email address.
        key: The license key to validate (CS-XXXX-XXXX format).
        hwid: Hardware ID to check (optional, auto-detected if None).
        check_expiration: Whether to check expiration date (default True).
        
    Returns:
        dict: Dictionary with validation result:
            - 'valid': bool - Whether the key is valid
            - 'tier': str - 'trial', 'standard', 'enterprise', or 'lifetime'
            - 'token': str - Session token
            - 'expires_at': str or None - Expiration date in ISO format
            - 'expired': bool - Whether the license has expired
            - 'hwid_match': bool or None - Whether HWID matches (None if not bound)
            - 'tier_limits': dict - Tier configuration with max_pages, etc.
            - 'message': str - Human-readable status message
        None if validation fails completely.
    """
    if not email or not key:
        return {
            'valid': False,
            'message': 'Email and license key are required.'
        }
    
    email = email.strip().lower()
    key = key.strip().upper()
    
    # Get current HWID if not provided
    if hwid is None:
        hwid = get_hwid()
    
    # Validate CS-XXXX-XXXX format using constants
    if not key.startswith(KEY_PREFIX) or len(key) != KEY_FORMAT_LENGTH or key.count('-') != KEY_DASH_COUNT:
        return {
            'valid': False,
            'message': f'Invalid license key format. Expected: {KEY_PREFIX}XXXX-XXXX'
        }
    
    # Check if database is available
    if not DATABASE_AVAILABLE:
        return {
            'valid': False,
            'message': 'License validation unavailable. Database module not loaded.'
        }
    
    # Use Supabase for validation (cloud-first approach)
    try:
        # Import Supabase at function level to avoid circular imports
        from supabase import create_client
        import os
        
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL", "https://spfwfyjpexktgnusgyib.supabase.co")
        supabase_key = os.getenv("SUPABASE_KEY", "sb_publishable_tmwenU0VyOChNWKG90X_bw_HYf9X5kR")
        
        # Connect to Supabase
        supabase = create_client(supabase_url, supabase_key)
        
        # Query licenses table for the provided license key
        response = supabase.table("licenses").select("*").eq("license_key", key).execute()
        
        # Check if license key exists
        if not response.data or len(response.data) == 0:
            return {
                'valid': False,
                'message': 'License key not found in database.'
            }
        
        license_data = response.data[0]
        
        # Verify email matches
        if license_data.get('email', '').lower() != email:
            return {
                'valid': False,
                'message': 'License key does not match the provided email address.'
            }
        
        # Check if license is banned
        if license_data.get('is_banned') is True:
            return {
                'valid': False,
                'tier': license_data.get('tier', 'trial'),
                'message': 'License has been revoked. Contact support.'
            }
        
        # Get tier and expiration
        tier = license_data.get('tier', 'Free Trial')
        # Map tier names to internal format
        tier_map = {
            'Free Trial': 'trial',
            'Standard': 'standard',
            'Extended': 'enterprise',
            'Lifetime': 'lifetime'
        }
        tier_internal = tier_map.get(tier, 'trial')
        
        # Check expiration using valid_until field
        expires_at = license_data.get('valid_until')
        expired = False
        if expires_at and check_expiration:
            try:
                expires_at_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                # Use NTP time if available for anti-tamper
                current_time = get_reliable_time()
                if current_time > expires_at_dt:
                    expired = True
                    return {
                        'valid': False,
                        'expired': True,
                        'tier': tier_internal,
                        'expires_at': expires_at,
                        'message': f'License expired on {expires_at_dt.strftime("%Y-%m-%d")}.'
                    }
            except (ValueError, TypeError):
                # Invalid date format, treat as not expired
                pass
        
        # Multi-device validation logic
        used_hwids = license_data.get("used_hwids", [])
        if used_hwids is None:
            used_hwids = []
        
        max_devices = license_data.get("max_devices", 1)
        
        # Check if current HWID is already registered
        if hwid in used_hwids:
            # Already activated on this device - allow access
            pass
        else:
            # Check if there's room for a new device
            if len(used_hwids) < max_devices:
                # Add current HWID to the list
                used_hwids.append(hwid)
                
                # Update Supabase with new HWID
                supabase.table("licenses").update({
                    "used_hwids": used_hwids
                }).eq("license_key", key).execute()
            else:
                # Device limit reached
                return {
                    'valid': False,
                    'tier': tier_internal,
                    'message': f'Device Limit Reached. Max: {max_devices}. This license is already activated on {max_devices} device(s).'
                }
        
        # Get tier limits (includes max_pages)
        tier_limits = get_tier_limits(tier_internal)
        
        # Valid! Generate session token
        token = _generate_session_token(email, tier_internal)
        
        return {
            'valid': True,
            'tier': tier_internal,
            'token': token,
            'expires_at': expires_at,
            'expired': False,
            'hwid_match': True,
            'tier_limits': tier_limits,
            'message': 'License activated successfully.'
        }
        
    except Exception as e:
        print(f"License validation error: {e}")
        # Fallback to local database if Supabase fails
        try:
            # Look up the license in the local database
            license_data = get_license_by_key(key, check_cloud=False)
            
            if not license_data:
                return {
                    'valid': False,
                    'message': 'License key not found in database.'
                }
            
            # Verify email matches
            if license_data.get('email', '').lower() != email:
                return {
                    'valid': False,
                    'message': 'License key does not match the provided email address.'
                }
            
            # Check if license is banned
            if license_data.get('status') == 'Banned':
                return {
                    'valid': False,
                    'tier': license_data.get('tier', 'trial'),
                    'message': 'License has been revoked. Contact support.'
                }
            
            # Get tier and expiration
            tier = license_data.get('tier', 'trial').lower()
            expires_at = license_data.get('expires_at')
            
            # Check expiration
            expired = False
            if expires_at and check_expiration:
                try:
                    expires_at_dt = datetime.fromisoformat(expires_at)
                    current_time = get_reliable_time()
                    if current_time > expires_at_dt:
                        expired = True
                        return {
                            'valid': False,
                            'expired': True,
                            'tier': tier,
                            'expires_at': expires_at,
                            'message': f'License expired on {expires_at_dt.strftime("%Y-%m-%d")}.'
                        }
                except (ValueError, TypeError):
                    pass
            
            # Get tier limits
            tier_limits = get_tier_limits(tier)
            
            # Check HWID binding for tiers that require it
            hwid_match = True
            if tier_limits['hwid_required']:
                stored_hwid = license_data.get('hwid')
                if stored_hwid:
                    if stored_hwid != hwid:
                        return {
                            'valid': False,
                            'tier': tier,
                            'message': 'License is bound to a different machine. Contact support to transfer.'
                        }
                else:
                    # First activation - bind HWID
                    try:
                        update_hwid(key, hwid)
                    except Exception as e:
                        print(f"Warning: Failed to bind HWID: {e}")
            
            # Valid! Generate session token
            token = _generate_session_token(email, tier)
            
            return {
                'valid': True,
                'tier': tier,
                'token': token,
                'expires_at': expires_at,
                'expired': False,
                'hwid_match': hwid_match,
                'tier_limits': tier_limits,
                'message': 'License activated successfully (offline mode).'
            }
        except Exception as e2:
            print(f"Local license validation error: {e2}")
            return {
                'valid': False,
                'message': f'License validation failed: {str(e)}'
            }


def check_hwid_binding(key: str, hwid: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Check if a license key has HWID binding and validate it.
    
    NOTE: This is a placeholder for database integration.
    In production, this should query the database to check if the key
    has an associated HWID and validate it matches the current machine.
    
    Args:
        key: The license key.
        hwid: Hardware ID to check (optional, auto-detected if None).
        
    Returns:
        tuple: (is_bound, bound_hwid) where:
            - is_bound: True if key has HWID binding
            - bound_hwid: The HWID it's bound to, or None if not bound
            
    TODO: Implement database integration:
        1. Query database for license by key
        2. Check if hwid column is populated
        3. If populated, compare with current HWID
        4. Return appropriate values
    """
    # DEVELOPMENT PLACEHOLDER: Always returns not bound to allow activation
    # In production, this queries the database and validates HWID
    return False, None


def get_license_path():
    """
    Get the path to the session file.
    
    Returns:
        str: Full path to the session file.
    """
    data_dir = get_data_dir()
    return os.path.join(data_dir, SESSION_FILE)


def save_license(email: str, key: str, tier: str, expires_at: Optional[str] = None) -> bool:
    """
    Save a validated license to persistent storage with encryption.
    Enables "Remember Me" functionality.
    
    Args:
        email: The user's email address.
        key: The validated license key.
        tier: The license tier.
        expires_at: Expiration date in ISO format (optional).
        
    Returns:
        bool: True if saved successfully, False otherwise.
    """
    try:
        # Create session data
        session_data = {
            'email': email,
            'key': key,
            'tier': tier,
            'expires_at': expires_at,
            'hwid': get_hwid(),
            'saved_at': datetime.now().isoformat()
        }
        
        # Encrypt session data
        cipher = Fernet(_get_encryption_key())
        encrypted_data = cipher.encrypt(json.dumps(session_data).encode('utf-8'))
        
        # Save to file
        session_path = get_license_path()
        with open(session_path, 'wb') as f:
            f.write(encrypted_data)
        
        return True
        
    except Exception as e:
        print(f"Failed to save session: {e}")
        return False


def load_license() -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Load and validate the stored license session.
    Returns session info if valid, otherwise requires fresh login.
    
    Returns:
        tuple: (session_token, email, tier, expires_at) where:
            - session_token: str or None - the session authentication token
            - email: str or None - the user's email address
            - tier: str or None - 'standard' or 'extended' license tier
            - expires_at: str or None - expiration date in ISO format
        Returns (None, None, None, None) if no valid session exists.
    """
    try:
        session_path = get_license_path()
        
        if not os.path.exists(session_path):
            return None, None, None, None
        
        # Read encrypted data
        with open(session_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Decrypt session data
        cipher = Fernet(_get_encryption_key())
        decrypted_data = cipher.decrypt(encrypted_data)
        session_data = json.loads(decrypted_data.decode('utf-8'))
        
        # Validate session data
        email = session_data.get('email')
        key = session_data.get('key')
        tier = session_data.get('tier')
        expires_at = session_data.get('expires_at')
        saved_hwid = session_data.get('hwid')
        
        if not email or not key or not tier:
            return None, None, None, None
        
        # Check HWID match
        current_hwid = get_hwid()
        if saved_hwid != current_hwid:
            # Hardware changed - invalidate session
            remove_license()
            return None, None, None, None
        
        # Validate the license
        result = validate_license(email, key, hwid=current_hwid, check_expiration=True)
        
        if result and result.get('valid'):
            # Session is valid
            return result['token'], email, tier, expires_at
        else:
            # Session is invalid (expired or revoked)
            remove_license()
            return None, None, None, None
            
    except Exception as e:
        print(f"Failed to load session: {e}")
        # Clean up corrupted session
        try:
            remove_license()
        except Exception:
            pass
        return None, None, None, None


def remove_license() -> bool:
    """
    Remove the stored license/session file.
    
    Returns:
        bool: True if removed successfully or file doesn't exist.
    """
    try:
        session_path = get_license_path()
        if os.path.exists(session_path):
            os.remove(session_path)
        return True
    except (IOError, OSError) as e:
        print(f"Failed to remove session: {e}")
        return False
