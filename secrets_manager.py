"""
Secrets Manager Module - Secure API key retrieval from Supabase.

This module handles fetching sensitive API keys (like OpenAI API key) from 
a Supabase database table called 'secrets'. This approach keeps API keys 
secure and out of the source code.

Supabase Table Structure:
    Table name: 'secrets'
    Columns:
        - id: Primary key (auto-increment)
        - name: The secret name (e.g., 'OPENAI_API_KEY')
        - value: The actual secret value

Usage:
    from secrets_manager import get_openai_api_key
    
    api_key = get_openai_api_key()
    if api_key:
        # Use the API key
        client = OpenAI(api_key=api_key)
    else:
        # Handle error - key not available

Error Handling:
    - Returns None if Supabase is not configured
    - Returns None if the key is not found in the database
    - Returns None if there's a connection error
    - Logs detailed error messages for debugging
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

# Load environment variables with PyInstaller support
# PyInstaller creates a temp folder and stores path in _MEIPASS
try:
    base_path = sys._MEIPASS
except AttributeError:
    # Running in development mode
    base_path = os.path.abspath(".")

env_path = os.path.join(base_path, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Fallback to current directory for development
    load_dotenv()

# Try to import Supabase, but don't fail if not available
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase-py not installed. Run: pip install supabase")

# ============================================================================
# SUPABASE CONFIGURATION
# These values should be set in your .env file:
#   SUPABASE_URL=https://your-project.supabase.co
#   SUPABASE_KEY=your-anon-or-service-key
# ============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Table and column names for secrets storage in Supabase
SECRETS_TABLE = "secrets"
SECRET_NAME_COLUMN = "name"
SECRET_VALUE_COLUMN = "value"

# Global Supabase client (singleton pattern)
_supabase_client: Optional['Client'] = None


class SecretsManagerError(Exception):
    """Exception raised when secrets retrieval fails."""
    pass


def _get_supabase_client() -> Optional['Client']:
    """
    Get or create a Supabase client singleton.
    
    This function implements the singleton pattern to avoid creating
    multiple client instances, which improves performance.
    
    Returns:
        Client: Supabase client instance, or None if not configured/available.
    """
    global _supabase_client
    
    # Check if supabase-py library is installed
    if not SUPABASE_AVAILABLE:
        print("Error: Supabase library not available.")
        return None
    
    # Check if Supabase credentials are configured
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Supabase URL or KEY not configured in .env file.")
        print("Required environment variables: SUPABASE_URL, SUPABASE_KEY")
        return None
    
    # Create client if not already created
    if _supabase_client is None:
        try:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Error: Failed to initialize Supabase client: {e}")
            return None
    
    return _supabase_client


def is_supabase_configured() -> bool:
    """
    Check if Supabase is properly configured and available.
    
    Returns:
        bool: True if Supabase is available and configured.
    """
    return _get_supabase_client() is not None


def get_secret(secret_name: str) -> Optional[str]:
    """
    Fetch a secret value from the Supabase 'secrets' table.
    
    This function queries the Supabase database to retrieve a secret
    by its name. The secrets table should have columns: id, name, value.
    
    Args:
        secret_name: The name of the secret to retrieve (e.g., 'OPENAI_API_KEY').
    
    Returns:
        str: The secret value if found, None otherwise.
    
    Example:
        >>> api_key = get_secret("OPENAI_API_KEY")
        >>> if api_key:
        ...     print("Key retrieved successfully")
    """
    client = _get_supabase_client()
    if not client:
        return None
    
    try:
        # Query the secrets table for the specified secret name
        # Supabase query: SELECT value FROM secrets WHERE name = 'secret_name' LIMIT 1
        response = client.table(SECRETS_TABLE).select(SECRET_VALUE_COLUMN).eq(
            SECRET_NAME_COLUMN, secret_name
        ).limit(1).execute()
        
        # Check if we got a result
        if response.data and len(response.data) > 0:
            secret_value = response.data[0].get(SECRET_VALUE_COLUMN)
            if secret_value:
                return secret_value
            else:
                print(f"Warning: Secret '{secret_name}' found but value is empty.")
                return None
        else:
            print(f"Warning: Secret '{secret_name}' not found in Supabase.")
            return None
            
    except Exception as e:
        print(f"Error: Failed to fetch secret '{secret_name}' from Supabase: {e}")
        return None


def get_openai_api_key() -> Optional[str]:
    """
    Fetch the OpenAI API key from Supabase.
    
    This is a convenience function that retrieves the OpenAI API key
    specifically. It looks for a secret named 'OPENAI_API_KEY' in the
    Supabase secrets table.
    
    Returns:
        str: The OpenAI API key if found, None otherwise.
    
    Raises:
        SecretsManagerError: If Supabase is not configured or key not found
                            (only in strict mode - currently returns None).
    
    Example:
        >>> from secrets_manager import get_openai_api_key
        >>> api_key = get_openai_api_key()
        >>> if api_key:
        ...     from openai import OpenAI
        ...     client = OpenAI(api_key=api_key)
    """
    return get_secret("OPENAI_API_KEY")


def validate_api_key(api_key: str) -> bool:
    """
    Validate that an API key has the expected format.
    
    This performs basic validation on the API key format.
    It does not verify that the key is actually valid with OpenAI.
    
    Args:
        api_key: The API key to validate.
    
    Returns:
        bool: True if the key format appears valid.
    """
    if not api_key:
        return False
    
    # OpenAI API keys typically start with 'sk-' and have a certain length
    # This is a basic format check, not authentication
    if not api_key.startswith("sk-"):
        return False
    
    # Check minimum length (OpenAI keys are typically 50+ characters)
    if len(api_key) < 40:
        return False
    
    return True


def get_validated_openai_key() -> Optional[str]:
    """
    Fetch and validate the OpenAI API key from Supabase.
    
    This function combines fetching and validation into one step.
    It returns the key only if it passes basic format validation.
    
    Returns:
        str: The validated OpenAI API key, or None if not found/invalid.
    """
    api_key = get_openai_api_key()
    
    if api_key and validate_api_key(api_key):
        return api_key
    
    if api_key:
        print("Warning: Retrieved API key does not appear to be valid format.")
    
    return None


# ============================================================================
# DIAGNOSTIC FUNCTIONS
# These can be used to debug Supabase connectivity issues
# ============================================================================

def test_supabase_connection() -> bool:
    """
    Test the connection to Supabase.
    
    This function attempts to connect to Supabase and query the secrets table.
    Useful for diagnosing connection issues.
    
    Returns:
        bool: True if connection successful, False otherwise.
    """
    client = _get_supabase_client()
    if not client:
        print("Supabase client not available.")
        return False
    
    try:
        # Try a simple query to test connectivity
        response = client.table(SECRETS_TABLE).select("*").limit(1).execute()
        print("Supabase connection successful!")
        print(f"Secrets table accessible: {len(response.data) >= 0}")
        return True
    except Exception as e:
        print(f"Supabase connection failed: {e}")
        return False


def print_config_status():
    """
    Print the current configuration status for debugging.
    
    This function prints information about the current Supabase
    configuration without revealing sensitive values.
    """
    print("=" * 50)
    print("Secrets Manager Configuration Status")
    print("=" * 50)
    print(f"Supabase library installed: {SUPABASE_AVAILABLE}")
    print(f"SUPABASE_URL configured: {'Yes' if SUPABASE_URL else 'No'}")
    print(f"SUPABASE_KEY configured: {'Yes' if SUPABASE_KEY else 'No'}")
    print(f"Supabase client ready: {is_supabase_configured()}")
    print("=" * 50)


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # When run directly, print diagnostic information
    print_config_status()
    
    if is_supabase_configured():
        print("\nTesting Supabase connection...")
        test_supabase_connection()
        
        print("\nTrying to fetch OPENAI_API_KEY...")
        key = get_openai_api_key()
        if key:
            # Only show first few characters for security
            print(f"API key retrieved: {key[:10]}...")
            print(f"Key format valid: {validate_api_key(key)}")
        else:
            print("API key not found or error occurred.")
