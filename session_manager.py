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
                    cls._instance._tier = None  # 'trial', 'standard', 'enterprise', or 'lifetime'
                    cls._instance._license_key = None
        return cls._instance
    
    def set_session(self, token, email=None, tier=None, license_key=None):
        """
        Set the current session with token, email, tier, and license key.
        
        Args:
            token: The session token from license validation.
            email: The licensed email address (optional).
            tier: The license tier ('trial', 'standard', 'enterprise', or 'lifetime').
            license_key: The license key string (optional).
        """
        with self._lock:
            self._token = token
            self._email = email
            self._license_key = license_key
            # Support all tiers, with 'extended' as legacy alias for 'enterprise'
            if tier == 'extended':
                tier = 'enterprise'
            self._tier = tier if tier in ('trial', 'standard', 'enterprise', 'lifetime') else 'standard'
    
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
    
    def get_license_key(self):
        """
        Get the license key.
        
        Returns:
            str: The license key, or None if not set.
        """
        with self._lock:
            return self._license_key
    
    def get_tier(self):
        """
        Get the current license tier.
        
        Returns:
            str: 'trial', 'standard', 'enterprise', or 'lifetime', or None if not set.
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
        Check if the current license is Extended/Enterprise tier or higher.
        Supports both 'extended' (legacy) and 'enterprise' naming.
        
        Returns:
            bool: True if Enterprise/Extended/Lifetime license, False otherwise.
        """
        with self._lock:
            return self._tier in ('extended', 'enterprise', 'lifetime')
    
    def is_standard(self):
        """
        Check if the current license is Standard tier.
        
        Returns:
            bool: True if Standard license, False otherwise.
        """
        with self._lock:
            return self._tier == 'standard'
    
    def is_trial(self):
        """
        Check if the current license is Trial tier.
        
        Returns:
            bool: True if Trial license, False otherwise.
        """
        with self._lock:
            return self._tier == 'trial'
    
    def is_enterprise(self):
        """
        Check if the current license is Enterprise tier.
        
        Returns:
            bool: True if Enterprise license, False otherwise.
        """
        with self._lock:
            return self._tier in ('enterprise', 'extended')
    
    def is_lifetime(self):
        """
        Check if the current license is Lifetime tier.
        
        Returns:
            bool: True if Lifetime license, False otherwise.
        """
        with self._lock:
            return self._tier == 'lifetime'
    
    def get_max_pages(self):
        """
        Get the maximum pages allowed for the current tier.
        
        Returns:
            int: Max pages (10 for trial, 50 for standard, 300 for enterprise/lifetime).
        """
        with self._lock:
            tier_page_limits = {
                'trial': 10,
                'standard': 50,
                'enterprise': 300,
                'extended': 300,  # Legacy support
                'lifetime': 300
            }
            return tier_page_limits.get(self._tier, 10)
    
    def clear(self):
        """Clear the current session token, license key, and tier."""
        with self._lock:
            self._token = None
            self._email = None
            self._license_key = None
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
def set_session(token, email=None, tier=None, license_key=None):
    """Set the session with token, email, tier, and license key."""
    _session_manager.set_session(token, email, tier, license_key)


def set_token(token, email=None):
    """Set the session token (legacy)."""
    _session_manager.set_token(token, email)


def get_token():
    """Get the session token."""
    return _session_manager.get_token()


def get_tier():
    """Get the license tier."""
    return _session_manager.get_tier()


def get_user_email():
    """Get the user's email from session."""
    return _session_manager.get_email()


def get_license_key():
    """Get the license key from session."""
    return _session_manager.get_license_key()


def is_active():
    """Check if session is active."""
    return _session_manager.is_active()


def is_extended():
    """Check if Extended license."""
    return _session_manager.is_extended()


def is_standard():
    """Check if Standard license."""
    return _session_manager.is_standard()


def is_trial():
    """Check if Trial license."""
    return _session_manager.is_trial()


def is_enterprise():
    """Check if Enterprise license."""
    return _session_manager.is_enterprise()


def is_lifetime():
    """Check if Lifetime license."""
    return _session_manager.is_lifetime()


def get_max_pages():
    """Get max pages for current tier."""
    return _session_manager.get_max_pages()


def clear_session():
    """Clear the session."""
    _session_manager.clear()


class SecurityError(Exception):
    """Exception raised when security checks fail."""
    pass
