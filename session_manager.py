"""
Session Manager Module - Singleton for secure session token management.
Acts as a bridge between license validation and protected features.
"""

import threading


class SessionManager:
    """
    Singleton class for managing the current session token.
    
    The session token is required by ai_worker and pdf_engine to function.
    If the license gate is bypassed, these modules will fail without a valid token.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._token = None
                    cls._instance._email = None
        return cls._instance
    
    def set_token(self, token, email=None):
        """
        Set the current session token.
        
        Args:
            token: The session token from license validation.
            email: The licensed email address (optional).
        """
        with self._lock:
            self._token = token
            self._email = email
    
    def get_token(self):
        """
        Get the current session token.
        
        Returns:
            str: The current session token, or None if not set.
        """
        with self._lock:
            return self._token
    
    def get_email(self):
        """
        Get the licensed email address.
        
        Returns:
            str: The licensed email, or None if not set.
        """
        with self._lock:
            return self._email
    
    def is_active(self):
        """
        Check if a valid session is active.
        
        Returns:
            bool: True if a session token is set, False otherwise.
        """
        with self._lock:
            return self._token is not None
    
    def clear(self):
        """Clear the current session token."""
        with self._lock:
            self._token = None
            self._email = None


# Global singleton instance
_session_manager = SessionManager()


def get_session_manager():
    """
    Get the global session manager instance.
    
    Returns:
        SessionManager: The singleton session manager.
    """
    return _session_manager


# Convenience functions for direct access
def set_token(token, email=None):
    """Set the session token."""
    _session_manager.set_token(token, email)


def get_token():
    """Get the session token."""
    return _session_manager.get_token()


def is_active():
    """Check if session is active."""
    return _session_manager.is_active()


def clear_session():
    """Clear the session."""
    _session_manager.clear()


class SecurityError(Exception):
    """Exception raised when security checks fail."""
    pass
