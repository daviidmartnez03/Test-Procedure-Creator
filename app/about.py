import tkinter as tk
from tkinter import messagebox

def show_about():
    '''Displays a simple popup with the software version'''
    messagebox.showinfo("Version", "Version: 1.1")

def open_manual():
    '''Create a secondary window to display the user manual'''
    # Toplevel creates a new child window of the main application
    manual_window = tk.Toplevel()
    manual_window.title("Manual")

    # Setup a Text widget for the content and a Scrollbar for navigation
    text = tk.Text(manual_window, wrap="word")
    scroll = tk.Scrollbar(manual_window, command=text.yview)
    text.configure(yscrollcommand=scroll.set)

    # Layout: Text on the left (filling space), Scrollbar on the right
    text.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    manual_content = """
    How it works
    
    1. The tool takes an input file and a template and generates an output file.

    2. The tool generates a complete test depending on the input file and the template selected.

    How to use it

    1. Select your input file.

    2. Select the corresponding template.

    3. Select the output directory

    4. Press the button "Process Files".

    5. Find the output file generated in the selected directory.
    """
    # Insert text and then lock the widget so users cannot edit the manual
    text.insert(tk.END, manual_content)
    text.configure(state="disabled")  # Make the text widget read-only

def show_new_features():
    '''Create a secondary window specifically for update notes'''
    new_features_window = tk.Toplevel()
    new_features_window.title("New Features")
    
    # Initialize text and scrollbar components
    text = tk.Text(new_features_window, wrap="word")
    scroll = tk.Scrollbar(new_features_window, command=text.yview)
    text.configure(yscrollcommand=scroll.set)

    text.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    new_features_content = """
    New features:

    1. Click the 'Config' menu to configure and save your predefined directories or to modify/activate/deactivate a syntax model.
    2. Click 'Input File Creator' in the 'Tools' menu to create an input file with the chosen model syntax.
    """
    text.insert(tk.END, new_features_content)
    text.configure(state="disabled")  # Set to read-only