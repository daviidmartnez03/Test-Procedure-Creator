import tkinter as tk
from tkinter import messagebox

def show_about():
    '''Displays a simple popup with the software version and basic info'''
    about_text = (
        "Test Procedure Creator\n"
        "Version: 2.0\n\n"
        "Automated test generation tool using Jinja2 and textX (DSL)."
    )
    messagebox.showinfo("About", about_text)

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
    How it works:
    This tool automates test script generation by separating data dictionaries (Parameter Files) from validation logic (Templates), using Jinja2 and a custom Domain-Specific Language (DSL).

    Workflow / How to use it:

    1. Configuration (Config Menu):
    - 'Default Paths': Set your default directories for inputs, templates, and outputs.
    - 'Model Syntax': Define the syntax rules for your data dictionaries.

    2. Preparation (Tools Menu):
    - 'Parameter File Editor': Create and save your data dictionaries in a grid-based interface.
    - 'Template Editor' / 'Humanized Syntax Template Editor': Write your test logic using standard Jinja2 or the humanized DSL syntax. 

    3. Processing (Main Interface):
    - Step 1: Select one or multiple Parameter Files.
    - Step 2: Select the Template File.
    - Choose the processing method: 'Normal Processing' (Jinja2 only) or 'Humanized Syntax Processing' (Jinja2 + textX DSL).
    - Step 0: Select the Output Directory.
    - Click 'Process Files'.

    4. Review:
    - Use the 'Processed File Viewer' in the Tools menu to verify your generated scripts.
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

    • Multi-flow Processing: Choose between standard Jinja2 rendering or the new Advanced Humanized Syntax processing (DSL translation via textX).
    • Specialized Specialized Editors: 
        - Grid-based Parameter File Editor for easy data definition.
        - Advanced Template Editors with real-time syntax highlighting, variable autocompletion, and code injection shortcuts.
    • Dynamic Route Resolution: Automatic mapping and resolution of message/signal paths via XML parsing.
    • Modernized UI: Fully upgraded graphical interface using CustomTkinter for a smoother user experience.
    • Smart Assistance: Compatible with the external Gemini AI Assistant to help you draft test logic, validate syntax, and resolve coding doubts.
    """
    text.insert(tk.END, new_features_content)
    text.configure(state="disabled")  # Set to read-only