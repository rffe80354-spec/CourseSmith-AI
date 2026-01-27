"""
Screenshot script for the custom UI
"""
import os
import sys
import time

# Set up virtual display
os.environ['DISPLAY'] = ':99'
os.system('Xvfb :99 -screen 0 1280x1024x24 > /dev/null 2>&1 &')
time.sleep(2)

import customtkinter as ctk
from tkinter import messagebox

# Override messagebox for screenshot
messagebox.showwarning = lambda *args, **kwargs: None
messagebox.showinfo = lambda *args, **kwargs: None
messagebox.showerror = lambda *args, **kwargs: None

from app_custom_ui import CustomApp


def take_screenshot(app, filename):
    """Take a screenshot of the application window."""
    app.update()
    time.sleep(0.5)
    
    try:
        # Get window position and size
        x = app.winfo_rootx()
        y = app.winfo_rooty()
        w = app.winfo_width()
        h = app.winfo_height()
        
        # Try PIL screenshot
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
            img.save(filename)
            print(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            print(f"PIL screenshot failed: {e}")
            
        # Fallback to pyscreenshot
        try:
            import pyscreenshot as ImageGrab
            img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
            img.save(filename)
            print(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            print(f"pyscreenshot failed: {e}")
            
        # Last resort: scrot or imagemagick
        try:
            os.system(f'scrot -u "{filename}"')
            print(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            print(f"scrot failed: {e}")
            
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return False


def main():
    """Run the app and take screenshots."""
    print("Starting custom UI...")
    
    # Create app
    app = CustomApp()
    
    # Fill in some sample data
    app.topic_entry.insert(0, "Machine Learning Fundamentals")
    app.audience_entry.insert(0, "Beginners in Data Science")
    
    # Take initial screenshot after a delay
    def capture_initial():
        app.update()
        time.sleep(0.3)
        take_screenshot(app, 'custom_ui_forge.png')
        
        # Switch to settings page and capture
        def capture_settings():
            app._switch_page('settings')
            app.update()
            time.sleep(0.3)
            take_screenshot(app, 'custom_ui_settings.png')
            
            # Switch to library and capture
            def capture_library():
                app._switch_page('library')
                app.update()
                time.sleep(0.3)
                take_screenshot(app, 'custom_ui_library.png')
                
                # Back to forge
                def capture_forge_active():
                    app._switch_page('forge')
                    app.update()
                    time.sleep(0.3)
                    
                    # Fill in data and take screenshot
                    app.topic_entry.delete(0, 'end')
                    app.topic_entry.insert(0, "Introduction to Python Programming")
                    app.audience_entry.delete(0, 'end')
                    app.audience_entry.insert(0, "Aspiring Developers")
                    
                    take_screenshot(app, 'custom_ui_forge_filled.png')
                    
                    # Close app
                    app.after(500, app.quit)
                
                app.after(300, capture_forge_active)
            
            app.after(300, capture_library)
        
        app.after(300, capture_settings)
    
    app.after(500, capture_initial)
    
    # Start main loop
    app.mainloop()
    
    print("Screenshots completed!")


if __name__ == "__main__":
    main()
