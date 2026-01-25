"""
Simple test script to launch the UI and take screenshots.
"""
import os
import sys
import time

# Set up virtual display for headless environment
os.environ['DISPLAY'] = ':99'

# Start Xvfb
os.system('Xvfb :99 -screen 0 1280x1024x24 > /dev/null 2>&1 &')
time.sleep(2)

import customtkinter as ctk
from tkinter import messagebox

# Override messagebox for testing
original_showerror = messagebox.showerror
original_showinfo = messagebox.showinfo
messagebox.showerror = lambda *args, **kwargs: print(f"ERROR: {args}")
messagebox.showinfo = lambda *args, **kwargs: print(f"INFO: {args}")

from app import App

def take_screenshot(app, filename):
    """Take a screenshot of the application window."""
    try:
        import pyscreenshot as ImageGrab
        im = ImageGrab.grab()
        im.save(filename)
        print(f"Screenshot saved: {filename}")
    except:
        # Alternative method
        import subprocess
        subprocess.run(['import', '-window', 'root', filename])
        print(f"Screenshot saved: {filename}")

def main():
    """Run the app and take screenshots."""
    print("Starting application...")
    
    # Set appearance mode
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # Create app
    app = App()
    
    # Wait a moment for UI to render
    app.after(1000, lambda: take_screenshot_and_close(app))
    
    # Start main loop
    app.mainloop()

def take_screenshot_and_close(app):
    """Take screenshot and close the app."""
    try:
        # Try to save a screenshot using PIL
        x = app.winfo_rootx()
        y = app.winfo_rooty()
        w = app.winfo_width()
        h = app.winfo_height()
        
        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
        img.save('/home/runner/work/CourseSmith-AI/CourseSmith-AI/ui_screenshot_login.png')
        print("Screenshot saved: ui_screenshot_login.png")
    except Exception as e:
        print(f"Screenshot failed: {e}")
    
    # Close the app
    app.after(500, app.quit)

if __name__ == "__main__":
    main()
