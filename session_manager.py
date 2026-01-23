"""
Session Manager Module - Singleton for secure session token and tier management.
Acts as a bridge between license validation and protected features.
Supports tiered licensing (Standard vs Extended).
"""

import threading


class SessionManager:
    """
    Singleton class for managing the current session token and license tier.
    
    The session token is required by ai_worker and pdf_engine to function.
    The tier determines feature access (standard vs extended branding).
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
                    cls._instance._tier = None  # 'standard' or 'extended'
        return cls._instance
    
    def set_session(self, token, email=None, tier=None):
        """
        Set the current session with token, email, and tier.
        
        Args:
            token: The session token from license validation.
            email: The licensed email address (optional).
            tier: The license tier ('standard' or 'extended').
        """
        with self._lock:
            self._token = token
            self._email = email
            self._tier = tier if tier in ('standard', 'extended') else 'standard'
    
    def set_token(self, token, email=None):
        """
        Set the current session token (legacy compatibility).
        
        Args:
            token: The session token from license validation.
            email: The licensed email address (optional).
        """
        with self._lock:
            self._token = token
            self._email = email
            # Keep existing tier if set
            if self._tier is None:
                self._tier = 'standard'
    
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
    
    def get_tier(self):
        """
        Get the current license tier.
        
        Returns:
            str: 'standard' or 'extended', or None if not set.
        """
        with self._lock:
            return self._tier
    
    def is_active(self):
        """
        Check if a valid session is active.
        
        Returns:
            bool: True if a session token is set, False otherwise.
        """
        with self._lock:
            return self._token is not None
    
    def is_extended(self):
        """
        Check if the current license is Extended tier.
        
        Returns:
            bool: True if Extended license, False otherwise.
        """
        with self._lock:
            return self._tier == 'extended'
    
    def is_standard(self):
        """
        Check if the current license is Standard tier.
        
        Returns:
            bool: True if Standard license, False otherwise.
        """
        with self._lock:
            return self._tier == 'standard'
    
    def clear(self):
        """Clear the current session token and tier."""
        with self._lock:
            self._token = None
            self._email = None
            self._tier = None


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
def set_session(token, email=None, tier=None):
    """Set the session with token, email, and tier."""
    _session_manager.set_session(token, email, tier)


def set_token(token, email=None):
    """Set the session token (legacy)."""
    _session_manager.set_token(token, email)


def get_token():
    """Get the session token."""
    return _session_manager.get_token()


def get_tier():
    """Get the license tier."""
    return _session_manager.get_tier()


def is_active():
    """Check if session is active."""
    return _session_manager.is_active()


def is_extended():
    """Check if Extended license."""
    return _session_manager.is_extended()


def is_standard():
    """Check if Standard license."""
    return _session_manager.is_standard()


def clear_session():
    """Clear the session."""
    _session_manager.clear()


class SecurityError(Exception):
    """Exception raised when security checks fail."""
    pass
