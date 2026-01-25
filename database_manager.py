"""
Database Manager Module - Hybrid SQLite/Supabase License Management.
Manages license keys with cloud synchronization, HWID bindings, and tier-based features.
Supports dual-tier system: Standard (10 pages) vs Enterprise (300 pages, HWID, AI features).

Cloud Features:
- Supabase integration for remote license validation
- Remote revocation and status checking
- Real-time license updates
- Graceful offline fallback to local SQLite cache
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from dotenv import load_dotenv

from utils import get_data_dir

# Try to import Supabase, but don't fail if not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase not available. Using local-only mode.")


# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = "licenses"

# Database file name
DB_NAME = "licenses.db"

# Global Supabase client
_supabase_client: Optional['Client'] = None


def get_supabase_client() -> Optional['Client']:
    """
    Get or create Supabase client singleton.
    
    Returns:
        Client: Supabase client instance, or None if not configured/available.
    """
    global _supabase_client
    
    if not SUPABASE_AVAILABLE:
        return None
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    
    if _supabase_client is None:
        try:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Failed to initialize Supabase client: {e}")
            return None
    
    return _supabase_client


def is_cloud_enabled() -> bool:
    """
    Check if cloud (Supabase) features are available and configured.
    
    Returns:
        bool: True if Supabase is available and configured.
    """
    return get_supabase_client() is not None


def sync_to_cloud(license_data: Dict[str, Any]) -> bool:
    """
    Sync a license to Supabase cloud database.
    
    Args:
        license_data: License dictionary to sync.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Upsert to Supabase (insert or update)
        client.table(SUPABASE_TABLE).upsert(license_data).execute()
        return True
    except Exception as e:
        print(f"Failed to sync to cloud: {e}")
        return False


def fetch_from_cloud(key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a license from Supabase cloud database by key.
    
    Args:
        key: License key to fetch.
        
    Returns:
        dict: License data, or None if not found or error.
    """
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        response = client.table(SUPABASE_TABLE).select("*").eq("key", key).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Failed to fetch from cloud: {e}")
        return None


def check_cloud_status(key: str) -> Optional[str]:
    """
    Check the status of a license in the cloud (for remote revocation).
    
    Args:
        key: License key to check.
        
    Returns:
        str: Status ('Active', 'Banned', 'Expired'), or None if offline/not found.
    """
    license_data = fetch_from_cloud(key)
    if license_data:
        return license_data.get('status')
    return None


def get_db_path():
    """
    Get the path to the licenses database file.
    
    Returns:
        str: Full path to the database file.
    """
    data_dir = get_data_dir()
    return os.path.join(data_dir, DB_NAME)


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures proper connection handling and automatic commits/rollbacks.
    
    Yields:
        sqlite3.Connection: Database connection object.
    """
    conn = None
    try:
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def initialize_database():
    """
    Initialize the licenses database with required tables.
    Creates the licenses table if it doesn't exist.
    Safe to call multiple times - won't overwrite existing data.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create licenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                key TEXT NOT NULL UNIQUE,
                tier TEXT NOT NULL,
                duration TEXT NOT NULL,
                hwid TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                status TEXT NOT NULL DEFAULT 'Active',
                notes TEXT
            )
        """)
        
        # Create index on email for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email ON licenses(email)
        """)
        
        # Create index on key for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_key ON licenses(key)
        """)
        
        # Create index on status for filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON licenses(status)
        """)


def create_license(email: str, key: str, tier: str, duration: str, 
                  expires_at: Optional[str] = None, notes: Optional[str] = None) -> int:
    """
    Create a new license entry in the database.
    
    Args:
        email: Buyer's email address.
        key: Generated license key.
        tier: License tier ('standard' or 'extended').
        duration: License duration ('lifetime', '1_month', '1_year').
        expires_at: Expiration date in ISO format (optional, calculated if None).
        notes: Additional notes about this license (optional).
        
    Returns:
        int: The ID of the newly created license record.
        
    Raises:
        sqlite3.IntegrityError: If the key already exists in the database.
    """
    # Calculate expiration date if not provided
    if expires_at is None:
        if duration == 'lifetime':
            expires_at = None
        elif duration == '1_month' or duration == '3_day':
            days = 3 if duration == '3_day' else 30
            expires_at = (datetime.now() + timedelta(days=days)).isoformat()
        elif duration == '1_year':
            expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        else:
            expires_at = None
    
    created_at = datetime.now().isoformat()
    
    # Create license in local database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO licenses (email, key, tier, duration, hwid, created_at, expires_at, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, key, tier, duration, None, created_at, expires_at, 'Active', notes))
        
        license_id = cursor.lastrowid
    
    # Sync to cloud if available
    if is_cloud_enabled():
        license_data = {
            'id': license_id,
            'email': email,
            'key': key,
            'tier': tier,
            'duration': duration,
            'hwid': None,
            'created_at': created_at,
            'expires_at': expires_at,
            'status': 'Active',
            'notes': notes
        }
        sync_to_cloud(license_data)
    
    return license_id


def get_license_by_key(key: str, check_cloud: bool = True) -> Optional[Dict[str, Any]]:
    """
    Retrieve a license by its key.
    First checks cloud (if enabled), then falls back to local database.
    
    Args:
        key: The license key to search for.
        check_cloud: Whether to check cloud database first (default True).
        
    Returns:
        dict: License information, or None if not found.
    """
    # Try cloud first if enabled and requested
    if check_cloud and is_cloud_enabled():
        cloud_data = fetch_from_cloud(key)
        if cloud_data:
            # Cache in local database
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    # Upsert into local cache
                    cursor.execute("""
                        INSERT OR REPLACE INTO licenses 
                        (id, email, key, tier, duration, hwid, created_at, expires_at, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cloud_data.get('id'),
                        cloud_data.get('email'),
                        cloud_data.get('key'),
                        cloud_data.get('tier'),
                        cloud_data.get('duration'),
                        cloud_data.get('hwid'),
                        cloud_data.get('created_at'),
                        cloud_data.get('expires_at'),
                        cloud_data.get('status'),
                        cloud_data.get('notes')
                    ))
            except Exception as e:
                print(f"Failed to cache cloud data locally: {e}")
            
            return cloud_data
    
    # Fallback to local database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licenses WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None


def get_licenses_by_email(email: str) -> List[Dict[str, Any]]:
    """
    Retrieve all licenses for a given email address.
    
    Args:
        email: The email address to search for.
        
    Returns:
        list: List of license dictionaries.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM licenses WHERE email = ? ORDER BY created_at DESC", (email,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]


def update_hwid(key: str, hwid: str) -> bool:
    """
    Bind a license key to a hardware ID (HWID).
    This happens on first activation.
    
    Args:
        key: The license key.
        hwid: The hardware ID to bind to.
        
    Returns:
        bool: True if updated successfully, False otherwise.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE licenses SET hwid = ? WHERE key = ?", (hwid, key))
        return cursor.rowcount > 0


def revoke_license(key: str, reason: Optional[str] = None) -> bool:
    """
    Revoke/ban a license key.
    Sets the status to 'Banned' and optionally adds a note.
    
    Args:
        key: The license key to revoke.
        reason: Optional reason for revocation.
        
    Returns:
        bool: True if revoked successfully, False if key not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if reason:
            cursor.execute("""
                UPDATE licenses 
                SET status = 'Banned', notes = COALESCE(notes || ' | ', '') || ?
                WHERE key = ?
            """, (f"REVOKED: {reason}", key))
        else:
            cursor.execute("UPDATE licenses SET status = 'Banned' WHERE key = ?", (key,))
        
        return cursor.rowcount > 0


def reactivate_license(key: str) -> bool:
    """
    Reactivate a previously revoked license.
    
    Args:
        key: The license key to reactivate.
        
    Returns:
        bool: True if reactivated successfully, False if key not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE licenses SET status = 'Active' WHERE key = ?", (key,))
        return cursor.rowcount > 0


def list_all_licenses(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all licenses in the database.
    
    Args:
        status_filter: Optional filter by status ('Active', 'Banned', 'Expired').
        
    Returns:
        list: List of all license dictionaries.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if status_filter:
            cursor.execute("SELECT * FROM licenses WHERE status = ? ORDER BY created_at DESC", (status_filter,))
        else:
            cursor.execute("SELECT * FROM licenses ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def search_licenses(search_term: str) -> List[Dict[str, Any]]:
    """
    Search licenses by email or key (partial match).
    
    Args:
        search_term: The search term (email or key fragment).
        
    Returns:
        list: List of matching license dictionaries.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        search_pattern = f"%{search_term}%"
        cursor.execute("""
            SELECT * FROM licenses 
            WHERE email LIKE ? OR key LIKE ?
            ORDER BY created_at DESC
        """, (search_pattern, search_pattern))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def is_license_expired(license_data: Dict[str, Any]) -> bool:
    """
    Check if a license has expired based on its expires_at date.
    
    Args:
        license_data: License dictionary from database.
        
    Returns:
        bool: True if expired, False otherwise.
    """
    if not license_data.get('expires_at'):
        # No expiration date means lifetime license
        return False
    
    try:
        expires_at = datetime.fromisoformat(license_data['expires_at'])
        return datetime.now() > expires_at
    except (ValueError, TypeError):
        # Invalid date format, consider not expired
        return False


def get_license_stats() -> Dict[str, int]:
    """
    Get statistics about licenses in the database.
    
    Returns:
        dict: Statistics including total, active, banned, expired counts.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Total licenses
        cursor.execute("SELECT COUNT(*) FROM licenses")
        total = cursor.fetchone()[0]
        
        # Active licenses
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE status = 'Active'")
        active = cursor.fetchone()[0]
        
        # Banned licenses
        cursor.execute("SELECT COUNT(*) FROM licenses WHERE status = 'Banned'")
        banned = cursor.fetchone()[0]
        
        # Count expired licenses (active but past expiration)
        cursor.execute("""
            SELECT COUNT(*) FROM licenses 
            WHERE status = 'Active' AND expires_at IS NOT NULL AND expires_at < ?
        """, (datetime.now().isoformat(),))
        expired = cursor.fetchone()[0]
        
        return {
            'total': total,
            'active': active,
            'banned': banned,
            'expired': expired
        }


def delete_license(key: str) -> bool:
    """
    Permanently delete a license from the database.
    Use with caution - this cannot be undone.
    
    Args:
        key: The license key to delete.
        
    Returns:
        bool: True if deleted successfully, False if key not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM licenses WHERE key = ?", (key,))
        return cursor.rowcount > 0


# Initialize database on module import only if not in test mode
# This allows for controlled initialization in production
try:
    if __name__ != '__main__':
        # Only auto-initialize when imported, not when run directly
        initialize_database()
except Exception as e:
    print(f"Warning: Failed to auto-initialize database: {e}")
    print("Call initialize_database() explicitly if needed.")

