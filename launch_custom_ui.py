#!/usr/bin/env python3
"""
Launcher for CourseSmith AI Custom UI
Run this to see the new premium design.
"""

import sys
import os

# Ensure we're in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set display for headless environment
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':99'
    # Start Xvfb if needed
    os.system('Xvfb :99 -screen 0 1280x1024x24 > /dev/null 2>&1 &')
    import time
    time.sleep(2)

# Import and run the custom UI
from app_custom_ui import main

if __name__ == "__main__":
    main()
