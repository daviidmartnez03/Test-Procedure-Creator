import tkinter as tk
from ui import create_ui
import main_window_operations as mwo
import os
import ctypes

def main():
    """Run the app and create the user interface"""
    # Check/Create the shortcut immediately when app starts
    try:
        mwo.create_live_shortcut()
    except Exception as e:
        print(f"Could not create shortcut: {e}")

    try:
        # Create unique key so the system detects the app ass an independent process, this permits to set the icon
        myappid = 'airbus.test_procedure_creator.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    
    # Create the main window
    root = tk.Tk()
    root.title("Test Procedure Creator")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, "images", "MBT.ico")

    try:
        # Sets the icon in the app
        root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Warning: Application icon could not be loaded: {e}")

    # Create the window with the main user_interface
    create_ui(root)
    root.mainloop()

if __name__ == '__main__':
    main()