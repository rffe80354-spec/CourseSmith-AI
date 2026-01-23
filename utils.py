"""
Utils Module - Helper functions for PyInstaller EXE compilation.
Provides resource path resolution for bundled applications.
"""

import os
import sys


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    When running as a PyInstaller bundle, files are extracted to a 
    temporary folder (sys._MEIPASS). When running in development,
    files are in the current working directory.
    
    Args:
        relative_path: The relative path to the resource file.
        
    Returns:
        str: The absolute path to the resource.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in development mode
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_data_dir():
    """
    Get the application data directory for storing user files.
    
    Returns:
        str: Path to the application data directory.
    """
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        data_dir = os.path.join(app_data, "CourseSmith")
    else:
        data_dir = os.path.join(os.path.expanduser("~"), ".coursesmith")
    
    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    return data_dir


def ensure_dir(path):
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The directory path to ensure exists.
        
    Returns:
        str: The path that was ensured.
    """
    os.makedirs(path, exist_ok=True)
    return path
