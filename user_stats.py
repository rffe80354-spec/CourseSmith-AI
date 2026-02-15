"""
User Statistics Module - Manages generation history and user statistics.
Provides thread-safe access to user stats with SQLite storage.
"""

import sqlite3
import threading
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from utils import get_data_dir

# Database file name for user statistics
STATS_DB_NAME = "user_stats.db"

# Thread lock for database operations
_db_lock = threading.Lock()


def get_stats_db_path() -> str:
    """
    Get the path to the user statistics database file.
    
    Returns:
        str: Full path to the database file.
    """
    data_dir = get_data_dir()
    return os.path.join(data_dir, STATS_DB_NAME)


@contextmanager
def get_stats_db_connection():
    """
    Context manager for user stats database connections.
    Ensures proper connection handling and automatic commits/rollbacks.
    
    Note: SQLite handles concurrent access internally. The _db_lock is only
    used for initialization flag protection, not for connection management.
    
    Yields:
        sqlite3.Connection: Database connection object.
    """
    conn = None
    try:
        conn = sqlite3.connect(get_stats_db_path())
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


def initialize_stats_database():
    """
    Initialize the user statistics database with required tables.
    Creates the generation_history and user_settings tables if they don't exist.
    Safe to call multiple times - won't overwrite existing data.
    
    This function must be called before any SELECT operations on these tables
    to prevent error 42P01 (relation does not exist).
    """
    with get_stats_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create generation_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                product_type TEXT NOT NULL,
                chapters_count INTEGER DEFAULT 0,
                export_format TEXT,
                credits_used INTEGER DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'Completed',
                created_at TEXT NOT NULL,
                license_key TEXT
            )
        """)
        
        # Create index on created_at for faster ordering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON generation_history(created_at DESC)
        """)
        
        # Create index on license_key for faster filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_license_key ON generation_history(license_key)
        """)
        
        # Create user_settings table for storing preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)


# Flag to track if database has been initialized (protected by _db_lock)
_db_initialized = False


def ensure_db_initialized():
    """
    Ensure the database is initialized before any operations.
    This function is idempotent and thread-safe - safe to call multiple times
    from multiple threads.
    
    Returns:
        bool: True if database is ready, False on initialization failure.
    """
    global _db_initialized
    
    # Fast path: already initialized (read is atomic for simple bool in CPython)
    if _db_initialized:
        return True
    
    # Slow path: need to initialize (use lock for thread safety)
    with _db_lock:
        # Double-check after acquiring lock
        if _db_initialized:
            return True
        
        try:
            initialize_stats_database()
            _db_initialized = True
            return True
        except Exception as e:
            print(f"Error initializing user stats database: {e}")
            return False


def record_generation(
    product_name: str,
    product_type: str,
    chapters_count: int = 0,
    export_format: str = 'pdf',
    credits_used: int = 1,
    status: str = 'Completed',
    license_key: Optional[str] = None
) -> int:
    """
    Record a generation event in the history.
    
    Args:
        product_name: Name/title of the generated product.
        product_type: Type of product (full_course, mini_course, etc.).
        chapters_count: Number of chapters/sections generated.
        export_format: Export format used (pdf, docx, etc.).
        credits_used: Number of credits consumed.
        status: Status of generation (Completed, Failed, etc.).
        license_key: Associated license key (optional).
        
    Returns:
        int: The ID of the newly created record.
    """
    # Ensure database tables exist before INSERT
    ensure_db_initialized()
    
    created_at = datetime.now().isoformat()
    
    with get_stats_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO generation_history 
            (product_name, product_type, chapters_count, export_format, credits_used, status, created_at, license_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_name, product_type, chapters_count, export_format, credits_used, status, created_at, license_key))
        
        return cursor.lastrowid


def get_generation_history(limit: int = 10, license_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get the generation history, optionally filtered by license key.
    
    Args:
        limit: Maximum number of records to return (default: 10).
        license_key: Filter by license key (optional).
        
    Returns:
        list: List of generation history records as dictionaries.
    """
    # Ensure database tables exist before SELECT
    ensure_db_initialized()
    
    with get_stats_db_connection() as conn:
        cursor = conn.cursor()
        
        if license_key:
            cursor.execute("""
                SELECT * FROM generation_history 
                WHERE license_key = ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (license_key, limit))
        else:
            cursor.execute("""
                SELECT * FROM generation_history 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_user_statistics(license_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get aggregated user statistics.
    
    Args:
        license_key: Filter by license key (optional).
        
    Returns:
        dict: Statistics including total_products, total_credits_spent, 
              last_activity, products_this_month.
    """
    # Ensure database tables exist before SELECT
    ensure_db_initialized()
    
    with get_stats_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build base query
        base_filter = "WHERE license_key = ?" if license_key else ""
        params = (license_key,) if license_key else ()
        
        # Total products
        cursor.execute(f"""
            SELECT COUNT(*) FROM generation_history 
            {base_filter}
        """, params)
        total_products = cursor.fetchone()[0]
        
        # Total credits spent
        cursor.execute(f"""
            SELECT COALESCE(SUM(credits_used), 0) FROM generation_history 
            {base_filter}
        """, params)
        total_credits_spent = cursor.fetchone()[0]
        
        # Last activity (most recent generation)
        cursor.execute(f"""
            SELECT created_at FROM generation_history 
            {base_filter}
            ORDER BY created_at DESC LIMIT 1
        """, params)
        last_row = cursor.fetchone()
        last_activity = last_row[0] if last_row else None
        
        # Products this month
        current_month = datetime.now().strftime('%Y-%m')
        if license_key:
            cursor.execute("""
                SELECT COUNT(*) FROM generation_history 
                WHERE license_key = ? AND created_at LIKE ?
            """, (license_key, f"{current_month}%"))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM generation_history 
                WHERE created_at LIKE ?
            """, (f"{current_month}%",))
        products_this_month = cursor.fetchone()[0]
        
        return {
            'total_products': total_products,
            'total_credits_spent': total_credits_spent,
            'last_activity': last_activity,
            'products_this_month': products_this_month
        }


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a user setting value.
    
    Args:
        key: Setting key name.
        default: Default value if not found.
        
    Returns:
        str: Setting value or default.
    """
    try:
        # Ensure database tables exist before SELECT
        ensure_db_initialized()
        
        with get_stats_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    except Exception:
        return default


def set_setting(key: str, value: str) -> bool:
    """
    Set a user setting value.
    
    Args:
        key: Setting key name.
        value: Setting value.
        
    Returns:
        bool: True if successful.
    """
    try:
        # Ensure database tables exist before INSERT/UPDATE
        ensure_db_initialized()
        
        with get_stats_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)
            """, (key, value))
            return True
    except Exception:
        return False


# Initialize database on module import
try:
    initialize_stats_database()
except Exception as e:
    print(f"Warning: Failed to initialize user stats database: {e}")
