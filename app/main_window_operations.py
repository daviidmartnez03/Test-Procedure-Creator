import json
import os
import sys
import winshell
from win32com.client import Dispatch
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk

from jinja2 import StrictUndefined, Environment, FileSystemLoader

from param_file_editor import ParamFileEditorWindow
from template_editor import TemplateEditor
from humanized_syntax_template_editor import HumanizedSyntaxTemplateEditor, HumanizedSyntaxProcessFeatures
from output_file_viewer import ProcessedFileViewer


# ==== CONSTANTS ====

CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT_DIR = os.path.dirname(CURRENT_SCRIPT_DIR)
MODELS_DIR = os.path.join(PROJECT_ROOT_DIR, "models")

CONFIG_DIR = os.path.join(CURRENT_SCRIPT_DIR, "user_config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
ACTIVE_SYNTAX_FILE = os.path.join(CONFIG_DIR, "active_syntax.json")

# Global Variables used across file selection and processing
input_files = []
template_path = ""
output_path = "" 
project_name = ""


# ==== INITIALIZATION ====

def create_live_shortcut():
    """Creates a shortcut on the Windows Desktop that runs the main application"""
    desktop = winshell.desktop() # find desktop path
    path = os.path.join(desktop, "Test Procedure Creator.lnk")
    
    # Only create it if it does not exist yet
    if not os.path.exists(path):
        shell = Dispatch('WScript.Shell') # create a windows assistant with permits to create shortcuts
        shortcut = shell.CreateShortCut(path) # initialize the creation of a direct access at the path
        
        # search python interpreter
        python_dir = os.path.dirname(sys.executable)
        python_exe = os.path.join(python_dir, 'python.exe')  # Shows console ('pythonw.exe' hides it)
        shortcut.Targetpath = python_exe 
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(current_dir, "main.py")
        shortcut.Arguments = f'"{main_script}"'

        shortcut.WorkingDirectory = os.path.dirname(main_script) # define the working directory for the app
        
        icon_path = os.path.join(os.path.dirname(main_script), "images", "MBT.ico")
        if os.path.exists(icon_path):
            shortcut.IconLocation = icon_path
            
        shortcut.save()
        print("Shortcut created on Desktop!")

def initialize_output_folders():
    """Checks if model directories exist and ensures they have an output folder"""
    target_folders = sorted([f for f in os.listdir(MODELS_DIR) if os.path.isdir(os.path.join(MODELS_DIR, f))]) # sort and check models/folders
    for folder_name in target_folders:
        model_dir = os.path.join(MODELS_DIR, folder_name)

        if os.path.exists(model_dir):
            output_dir = os.path.join(model_dir, "output")
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    print(f"[Init] Created Folder: {output_dir}")
                except OSError as e:
                    print(f"[Init] Error creating folder {output_dir}: {e}")


# ==== PREDEFINED PATHS and SYNTAX CONFIGURATION MANAGEMENT ====

def ensure_config_exists():
    """Ensures that user_config directory exists and predefined paths and syntax are set"""
    if not os.path.exists(CONFIG_DIR):
        try:
            os.makedirs(CONFIG_DIR)
        except OSError:
            pass 
    
    default_models = MODELS_DIR
    
    # Check if models folder exist at the root, and if not try to create it
    if not os.path.exists(default_models):
        try:
            os.makedirs(default_models)
        except:
            pass

    # Create default config.json if not exist
    if not os.path.exists(CONFIG_FILE):
        default_data = {
            "default_input_dir": default_models,
            "default_template_dir": default_models,
            "default_output_dir": default_models
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default_data, f, indent=4)
        except:
            pass
    
    # Ensure Syntax Config exist
    ensure_syntax_config_exists()

def ensure_syntax_config_exists():
    """Scans the models folder. Keeps existing indices, and assigns new indices to new folders"""
    if not os.path.exists(MODELS_DIR):
        try: os.makedirs(MODELS_DIR)
        except OSError: pass

    try:
        folders = sorted([f for f in os.listdir(MODELS_DIR) if os.path.isdir(os.path.join(MODELS_DIR, f))]) # sort projects_name
    except Exception:
        folders = []

    # Find the highest existing index to prevent duplicates
    max_index = 0
    configs_to_create = []

    for folder in folders:
        target_dir = os.path.join(MODELS_DIR, folder, "syntax")
        filename = f"{folder.lower()}_config.json"
        filepath = os.path.join(target_dir, filename)

        # check if syntax config.json exists for each project and if not add to the configs_to_create to create the syntax_config
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f: data = json.load(f)
                idx = data.get("index") # open the config and get de index
                if isinstance(idx, int):
                    max_index = max(max_index, idx) # save the highest index
                else:
                    configs_to_create.append((target_dir, filename, data)) # Needs an index added
            except:
                configs_to_create.append((target_dir, filename, {}))
        else:
            configs_to_create.append((target_dir, filename, None)) # Store the info to create new folder

    # Create or update configs for new folders
    for target_dir, filename, existing_data in configs_to_create:
        # check if syntax folder exists if not create it
        if not os.path.exists(target_dir):
            try: os.makedirs(target_dir)
            except OSError: continue

        max_index += 1  # Assign the next available number
        filepath = os.path.join(target_dir, filename)

        # assign the predefined content
        new_data = existing_data if existing_data else {
            "list_start": "{", "list_end": "}", "separator": ";",
            "state_separator": "|", "list_separator": ","
        }
        new_data["index"] = max_index

        try:
            with open(filepath, 'w') as f: json.dump(new_data, f, indent=4)
        except Exception as e:
            print(f"Error creating syntax config {filename}: {e}")

    # Create active_syntax.json using 0 (initialized in deactivated)
    if not os.path.exists(ACTIVE_SYNTAX_FILE):
        if not os.path.exists(CONFIG_DIR):
            try: os.makedirs(CONFIG_DIR)
            except OSError: pass

        try:
            with open(ACTIVE_SYNTAX_FILE, 'w') as f:
                json.dump({"current_index": 0}, f, indent=4)
        except Exception as e:
            print(f"Error creating active syntax file: {e}")

def load_config():
    """Loads and returns the general user configuration dictionary"""
    ensure_config_exists()
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(new_config):
    """Saves new data into the general user configuration"""
    ensure_config_exists()
    try:
        current_config = load_config()
        current_config.update(new_config)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current_config, f, indent=4)
    except Exception as e:
        messagebox.showerror("Config Error", f"Could not save settings: {e}")

def get_dynamic_model_mapping():
    """Scans MODELS_DIR and returns a dictionary mapped by the model INDEX, to display names at the syntax configuration window"""
    mapping = {}
    if not os.path.exists(MODELS_DIR):
        return mapping
        
    for folder in os.listdir(MODELS_DIR):
        folder_path = os.path.join(MODELS_DIR, folder)
        if os.path.isdir(folder_path):
            filename = f"{folder.lower()}_config.json"
            filepath = os.path.join(folder_path, "syntax", filename)
            
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        idx = data.get("index")
                        if isinstance(idx, int):
                            mapping[idx] = {
                                "filename": filename,
                                "folder": folder,
                                "display_name": folder.replace("_", " ").upper()
                            }
                except: pass
    return mapping

def get_syntax_config():
    """Loads the syntax configuration for the currently active model index"""
    ensure_syntax_config_exists()
    
    current_index = 0
    try:
        with open(ACTIVE_SYNTAX_FILE, 'r') as f:
            current_index = json.load(f).get("current_index", 0)
    except Exception: pass 

    mapping = get_dynamic_model_mapping()
    if current_index in mapping:
        folder_name = mapping[current_index]["folder"]
        filename = mapping[current_index]["filename"]
        full_path = os.path.join(MODELS_DIR, folder_name, "syntax", filename)
        try:
            with open(full_path, 'r') as f: return json.load(f)
        except: pass
        
    # Fallback if no valid config is found
    return {"list_start": "{", "list_end": "}", "separator": ";", "state_separator": "|", "list_separator": ",", "index": 0}

def get_active_model_name():
    """Returns the display name of the active model based on the active index"""
    ensure_syntax_config_exists()
    
    try:
        with open(ACTIVE_SYNTAX_FILE, 'r') as f:
            current_index = json.load(f).get("current_index", 0)

        if current_index == 0: return None
            
        mapping = get_dynamic_model_mapping()
        if current_index in mapping:
            return mapping[current_index]["display_name"]
    except Exception: pass
    
    return "Unknown Configuration"


# ==== UI DIALOGS and LAUNCHERS ====

def open_parameters_file_editor(root):
    """Validates that a syntax model is active and launch the Param File Editor"""
    active_model = get_active_model_name()
    
    if active_model is None:
        messagebox.showwarning(
            "No Syntax Active", 
            "You currently have no syntax model selected.\n\n"
            "Please go to 'Config -> Model Syntax' and activate a model first."
        )
        return

    ParamFileEditorWindow(root)

def open_humanized_syntax_template_editor(root):
    """Validates syntax state, ask to load a parameter file and launches the Template Editor"""
    from ui import LoadParametersChoiceDialog

    active_model = get_active_model_name()
    
    if active_model is None:
        messagebox.showwarning(
            "No Syntax Active", 
            "You currently have no syntax model selected.\n\n"
            "Please go to 'Config -> Model Syntax' and activate a model first."
        )
        return

    dialog = LoadParametersChoiceDialog(root)
    result = dialog.get_choice() # freeze the code until the user select an option

    if result == "Load Parameters from file":
        config = load_config()
        initial_dir = config.get("default_input_dir", os.getcwd())

        parameters_filepath = filedialog.askopenfilename(
            parent=root,
            title="Select a Parameters File to Load Variables",
            initialdir=initial_dir,
            filetypes=(("All Files", "*.*"), ("CSV Files", "*.csv"), ("Text Files", "*.txt"))
        )

        if not parameters_filepath:
            return 
    elif result == "Continue without preloading":
        parameters_filepath=None
    else:
        return
    
    editor_win = ctk.CTkToplevel(root)
    editor_win.title("New Template")
    editor_win.geometry("1100x700")
    editor_win.focus_force()

    editor_pro = HumanizedSyntaxTemplateEditor(editor_win, parameters_filepath=parameters_filepath)
    editor_pro.pack(fill="both", expand=True, padx=0, pady=0) # fill="both" to expand in x, y directions and expand=True to maintain responsive behaviour


def open_template_editor(root):
    """Validates syntax state, ask to load a parameter file and launches the Template Editor"""
    from ui import LoadParametersChoiceDialog

    active_model = get_active_model_name()
    
    if active_model is None:
        messagebox.showwarning(
            "No Syntax Active", 
            "You currently have no syntax model selected.\n\n"
            "Please go to 'Config -> Model Syntax' and activate a model first."
        )
        return
    
    dialog = LoadParametersChoiceDialog(root)
    result = dialog.get_choice()

    if result == "Load Parameters from file":
        config = load_config()
        initial_dir = config.get("default_input_dir", os.getcwd())

        parameters_filepath = filedialog.askopenfilename(
            parent=root,
            title="Select a Parameters File to Load Variables",
            initialdir=initial_dir,
            filetypes=(("All Files", "*.*"), ("CSV Files", "*.csv"), ("Text Files", "*.txt"))
        )

        if not parameters_filepath:
            return 
    elif result == "Continue without preloading":
        parameters_filepath=None
    else:
        return

    editor_win = ctk.CTkToplevel(root)
    editor_win.title("New Template")
    editor_win.geometry("1100x700")
    editor_win.focus_force()

    editor_pro = TemplateEditor(editor_win, parameters_filepath=parameters_filepath)
    editor_pro.pack(fill="both", expand=True, padx=0, pady=0)

def open_processed_file_viewer(root):
    """Open a processed file in read-only"""
    active_model = get_active_model_name()
    
    if active_model is None:
        messagebox.showwarning(
            "No Syntax Active", 
            "You currently have no syntax model selected.\n\n"
            "Please go to 'Config -> Model Syntax' and activate a model first."
        )
        return 

    output_win = ctk.CTkToplevel(root)
    output_win.title("Processed File Viewer")
    output_win.geometry("1100x700")
    output_win.focus_force()

    editor_pro = ProcessedFileViewer(output_win)
    editor_pro.pack(fill="both", expand=True, padx=0, pady=0)

def open_paths_configuration_window(root):
    """Opens the configuration window to manage default default paths"""
    settings_window = tk.Toplevel(root)
    settings_window.title("Configure Default Paths")
    settings_window.geometry("750x230")
    
    settings_window.transient(root) # maintains settings_window always at the front
    settings_window.grab_set()             
    settings_window.focus_force()          

    config = load_config()
    models_fallback = MODELS_DIR
    
    var_input = tk.StringVar(value=config.get("default_input_dir", models_fallback))
    var_template = tk.StringVar(value=config.get("default_template_dir", models_fallback))
    var_output = tk.StringVar(value=config.get("default_output_dir", models_fallback))

    def browse_dir(target_var):
        current_dir = target_var.get()
        if not os.path.exists(current_dir): current_dir = os.getcwd()
        
        d = filedialog.askdirectory(parent=settings_window, initialdir=current_dir)
        if d: 
            target_var.set(d)
            settings_window.focus_force() 

    tk.Label(settings_window, text="Default Input Directory:").grid(row=0, column=0, sticky="e", padx=5, pady=10)
    tk.Entry(settings_window, textvariable=var_input, width=80).grid(row=0, column=1, padx=5, pady=10)
    tk.Button(settings_window, text="Browse", command=lambda: browse_dir(var_input)).grid(row=0, column=2, padx=5, pady=10)

    tk.Label(settings_window, text="Default Template Directory:").grid(row=1, column=0, sticky="e", padx=5, pady=10)
    tk.Entry(settings_window, textvariable=var_template, width=80).grid(row=1, column=1, padx=5, pady=10)
    tk.Button(settings_window, text="Browse", command=lambda: browse_dir(var_template)).grid(row=1, column=2, padx=5, pady=10)

    tk.Label(settings_window, text="Default Output Directory:").grid(row=2, column=0, sticky="e", padx=5, pady=10)
    tk.Entry(settings_window, textvariable=var_output, width=80).grid(row=2, column=1, padx=5, pady=10)
    tk.Button(settings_window, text="Browse", command=lambda: browse_dir(var_output)).grid(row=2, column=2, padx=5, pady=10)

    def save_and_close():
        new_settings = {
            "default_input_dir": var_input.get(),
            "default_template_dir": var_template.get(),
            "default_output_dir": var_output.get()
        }
        save_config(new_settings)
        messagebox.showinfo("Saved", "Configuration updated successfully!", parent=settings_window)
        settings_window.destroy()

    tk.Button(
        settings_window, text="Save Configuration", bg="#e1e1e1", 
        height=2, width=20, command=save_and_close
    ).grid(row=3, column=1, pady=20)
    
    root.wait_window(settings_window)

def open_model_syntax_settings_window(root):
    """Opens the syntax configuration window, mapping models to specific syntactic rules"""
    ensure_syntax_config_exists()
    
    win = tk.Toplevel(root)
    win.title("Syntax Configuration")
    win.geometry("550x450")
    win.transient(root)
    win.grab_set()
    win.focus_force()

    mapping = get_dynamic_model_mapping()
    
    name_to_index = {}
    for idx, details in mapping.items():
        display_name = details["display_name"]
        name_to_index[display_name] = idx
            
    display_names = sorted(list(name_to_index.keys()))

    # Load current active index
    try:
        with open(ACTIVE_SYNTAX_FILE, 'r') as f:
            current_active_index = json.load(f).get("current_index", 0)
    except: 
        current_active_index = 0

    is_active = (current_active_index != 0 and current_active_index in mapping)
    
    if is_active:
        current_active_display = mapping[current_active_index]["display_name"]
    else:
        current_active_display = display_names[0] if display_names else ""

    # UI variables 
    active_toggle_var = tk.BooleanVar(value=is_active)
    selected_model_var = tk.StringVar(value=current_active_display)
    sep_var, list_start_var, list_end_var, state_sep_var, list_sep_var = [tk.StringVar() for _ in range(5)]

    # Helper functions
    def toggle_state():
        if active_toggle_var.get():
            model_dropdown.config(state="readonly")
            load_selected_model_data() 
        else:
            model_dropdown.config(state="disabled")
            sep_var.set(""); list_start_var.set(""); list_end_var.set("")
            state_sep_var.set(""); list_sep_var.set("")

    def load_selected_model_data(*args):
        if not active_toggle_var.get(): return

        display_name = selected_model_var.get()
        if not display_name or display_name not in name_to_index: return
        
        idx = name_to_index[display_name]
        folder_name = mapping[idx]["folder"]
        target_file = mapping[idx]["filename"]
        path = os.path.join(MODELS_DIR, folder_name, "syntax", target_file)
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                sep_var.set(data.get("separator", ";"))
                list_start_var.set(data.get("list_start", "{"))
                list_end_var.set(data.get("list_end", "}"))
                state_sep_var.set(data.get("state_separator", "|"))
                list_sep_var.set(data.get("list_separator", ","))
        except Exception as e: 
            print(f"Error: {e}")

    def save_new_syntax_with_confirmation():
        """Asks for confirmation before proceeding with the save operation"""
        
        # Show the confirmation dialog
        response = messagebox.askokcancel(
            title="Syntax Mismatch Warning",
            message="Changing the global syntax will restrict the 'Process Files' feature to the new format. Existing parameter files with different syntax will no longer be compatible for processing. \n\nAre you sure you want to apply these changes?",
            icon="question" # Adds a question mark icon
        )

        # Handle the response
        if response:
            save_changes() 
        else:
            return 

    def save_changes():
        try:
            if not active_toggle_var.get():
                save_idx = 0
            else:
                display_name = selected_model_var.get()
                if display_name not in name_to_index: 
                    messagebox.showwarning("Warning", "Please select a model to activate.")
                    return
                save_idx = name_to_index[display_name]

            # Save the integer index to user_config/active_syntax.json
            with open(ACTIVE_SYNTAX_FILE, 'w') as f:
                json.dump({"current_index": save_idx}, f, indent=4)
            
            # Save the rules to the specific model's config
            if active_toggle_var.get() and save_idx != 0:
                folder_name = mapping[save_idx]["folder"]
                target_file = mapping[save_idx]["filename"]
                path = os.path.join(MODELS_DIR, folder_name, "syntax", target_file)
                
                new_data = {
                    "separator": sep_var.get(), "list_start": list_start_var.get(),
                    "list_end": list_end_var.get(), "state_separator": state_sep_var.get(),
                    "list_separator": list_sep_var.get(), "index": save_idx
                }
                
                with open(path, 'w') as f: json.dump(new_data, f, indent=4)
            
            state_msg = "Active" if active_toggle_var.get() else "Deactivated"
            messagebox.showinfo("Success", f"Configuration updated.\nSyntax Status: {state_msg}")
            win.destroy()
        except Exception as e: 
            messagebox.showerror("Error", str(e))

    top_frame = tk.Frame(win)
    top_frame.pack(pady=(15, 10))
    
    chk_active = tk.Checkbutton(
        top_frame, text="Click to Activate/Deactivate Syntax", variable=active_toggle_var, 
        font=("Helvetica", 12, "bold"), command=toggle_state
    )
    chk_active.pack()
    
    tk.Label(win, text="Select Model:", font=("Helvetica", 10)).pack(pady=(0, 5))
    model_dropdown = ttk.Combobox(win, textvariable=selected_model_var, values=display_names, state="readonly", width=35, font=("Helvetica", 11))
    model_dropdown.pack(pady=5, ipady=3) # ipady = intern pady
    model_dropdown.bind("<<ComboboxSelected>>", load_selected_model_data)
    
    frame = tk.LabelFrame(win, text=" Syntax Rules ", font=("Helvetica", 11, "bold"), padx=15, pady=10)
    frame.pack(fill="both", expand=True, padx=20, pady=15)
    
    def add_row(label_text, var, row):
        tk.Label(frame, text=label_text, font=("Helvetica", 11)).grid(row=row, column=0, sticky="e", padx=5, pady=8)
        tk.Entry(frame, textvariable=var, width=8, font=("Helvetica", 11), justify="center").grid(row=row, column=1, sticky="w", padx=5, pady=8)
        
    add_row("Main Separator:", sep_var, 0)
    add_row("List Start:", list_start_var, 1)
    add_row("List End:", list_end_var, 2)
    add_row("State Separator:", state_sep_var, 3)
    add_row("List Separator:", list_sep_var, 4)
    
    tk.Button(
        win, text="Save", bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"), 
        width=18, command=save_new_syntax_with_confirmation
    ).pack(pady=(0, 20), ipady=5)
    
    toggle_state()


# ==== GLOBAL FILE SELECTION FUNCTIONS ====

def select_files():
    """Prompts user to select input parameter files and updates global state"""
    global input_files
    global output_path
    
    config = load_config()
    default_models = MODELS_DIR
    
    initial_dir = config.get("default_input_dir", default_models)
    if not os.path.exists(initial_dir): initial_dir = default_models

    new_files = filedialog.askopenfilenames(
        title="Select parameter files",
        initialdir=initial_dir,
        filetypes=(("All files", "*.*"),)
    )

    if new_files:
        input_files = new_files
        messagebox.showinfo("Info", f"{len(input_files)} files selected.")
        
        configured_output = config.get("default_output_dir", "")
        if configured_output and os.path.exists(configured_output):
            output_path = configured_output
        else:
            output_path = "" 

def select_template(root):
    """Prompts user to select a template file and updates global state"""
    from ui import SyntaxChoiceDialog
    global input_files, template_path, project_name
    
    config = load_config()
    default_models = MODELS_DIR
    
    initial_dir = config.get("default_template_dir", default_models)
    if not os.path.exists(initial_dir): initial_dir = default_models
    
    selected_temp = filedialog.askopenfilename(
        title="Select a template file",
        initialdir=initial_dir,
        filetypes=(("Jinja2 files", "*.j2"), ("Text files", "*.txt"), ("All files", "*.*"))
    )

    if selected_temp:
        template_path = os.path.normpath(selected_temp)
        template_name = os.path.basename(template_path)
        # ask the user to select the processing method
        dialog = SyntaxChoiceDialog(root)
        result = dialog.get_choice()
        
        if result == "Humanized Syntax":
            if not input_files:
                messagebox.showerror("Error", f"Select an input file first")
            else:
                humanized_syntax_process_features_class = HumanizedSyntaxProcessFeatures(input_files[0], selected_temp)
                try:
                    humanized_syntax_process_features_class.process_humanized_syntax_template() # process the selected_template to see if there are errors
                    project_name = "HumanizedSyntax"
                    messagebox.showinfo("Info", f"Template processing completed")
                except Exception as e:
                    messagebox.showerror("Error", f"Error in template: {template_name}\n {e}")
        elif result == "Normal":
            messagebox.showinfo("Info", f"Template selected: {template_name}")

def select_output_path():
    """Prompts user to select an output directory and updates global state"""
    global output_path
    
    config = load_config()
    default_models = MODELS_DIR

    initial_dir = config.get("default_output_dir", default_models)
    if not os.path.exists(initial_dir): 
        initial_dir = default_models

    selected_path = filedialog.askdirectory(
        title="Select the output directory",
        initialdir=initial_dir
    )
    
    if selected_path:
        output_path = selected_path
        messagebox.showinfo("Output Selected", f"Output directory set to:\n{output_path}")


# ==== DATA PROCESSING ====

def process_files():
    """Iterates through global input files and passes them to the template processor"""
    if not input_files:
        messagebox.showerror("Error", "No input files selected.")
        return
    if not template_path:
        messagebox.showerror("Error", "No template file selected.")
        return
        
    global output_path
    if not output_path:
        messagebox.showwarning("Action Required", "No output directory selected.\n\nPlease click the '(O) Select Output Directory' button")
        return

    success_count = 0
    errors = []

    for input_file in input_files:
        try:
            process_file(input_file, template_path, output_path)
            success_count += 1
        except Exception as e:
            errors.append(f"{os.path.basename(input_file)}: {str(e)}")
    
    if errors:
        error_msg = "\n".join(errors[:5])
        if len(errors) > 5: error_msg += "\n..."
        messagebox.showwarning("Completed with Errors", f"Processed: {success_count}\nErrors: {len(errors)}\n\nDetails:\n{error_msg}")
    else:
        messagebox.showinfo("Success", f"All {success_count} files processed successfully.\nSaved in: {output_path}")

def process_file(input_file, template_path, output_path):
    """Opens an input file, extracts its data, and hands it off to the renderer"""
    data = {}
    L, V, R = [], [], []
    
    try:
        with open(input_file, 'r', encoding='utf-8-sig', errors='replace') as file:
            for line in file:
                line = line.strip()
                if not line: continue 

                # Check if there is an active model 
                active_model = get_active_model_name()
                
                if not active_model:
                    parts = line.split(';')

                    if len(parts) == 2:
                        parameter, value = parts
                        data[parameter] = value
                    elif len(parts) == 4:
                        param1, valor1, valor2, param2 = parts
                        data[param1] = valor1
                        data[param2] = valor2
                    elif len(parts) == 5:
                        param1, valor1, valor2, valor3, param3 = parts
                        L.append(valor1)
                        V.append(valor2)
                        R.append(valor3)
                        data[param1] = valor1 
                        data[param3] = valor3

                # Active syntax config parsing
                else:
                    _process_file_with_active_syntax(line, data)
                    
    except Exception as e:
        raise RuntimeError(f"Error reading file content: {str(e)}")
    
    data['L'] = L
    data['V'] = V
    data['R'] = R
    data['date'] = datetime.now().strftime("%d %B %Y")
    
    output_filename = os.path.basename(input_file)
    full_output_path = os.path.join(output_path, output_filename)

    data["FILENAME"] = output_filename.split(".")[0]
    print(f"FILENAME: {data["FILENAME"]}")

    save_data(full_output_path, data, template_path)

def _process_file_with_active_syntax(line, data):
    '''Extract the data of the parameter file with the active syntax model'''
    syntax = get_syntax_config()
    parts = line.split(syntax["separator"])
    
    if len(parts) == 2:
        parameter, values = parts
        # Split by list_separator, trimming outer brackets
        values = [v.strip() for v in values[1:-1].split(syntax["list_separator"])] 
    
        if len(values) == 1:
            states = [v.strip() for v in values[0].split(syntax["state_separator"])]
            if len(states) == 1:
                values = values[0]
            else:
                values = states
        else:
            for i, value in enumerate(values):
                # Split by state_separator
                states = [v.strip() for v in value.split(syntax["state_separator"])]
                if len(states) > 1:
                    values[i] = states
                else:
                    values[i] = value

        data[parameter] = values

def save_data(output_file_path, data, template_path):
    """Feeds extracted data into the Jinja2 template and writes the final output"""
    specific_template_dir = os.path.dirname(template_path)
    template_name = os.path.basename(template_path)
    models_root_dir = MODELS_DIR
    
    try:
        # Set up the environment
        env = Environment(loader=FileSystemLoader([specific_template_dir, models_root_dir]), undefined=StrictUndefined)
        template = env.get_template(template_name)
        # Template render
        content = template.render(data)
        content = remove_indentation(content)
        content = remove_extra_blank_lines(content)
        if project_name == "HumanizedSyntax":
            humanized_syntax_process_features_class = HumanizedSyntaxProcessFeatures(input_files[0], template_path)
            content, _ = humanized_syntax_process_features_class.process_humanized_syntax_template(data_return=True, jinja_rendered_template_data=content) # process the rendered template with textX grammar
            content = "\n".join(content)

        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(content)
            if not content.endswith('\n'):
                file.write("\n")
            
    except Exception as e:
        msg = f"Error rendering template '{template_name}': {str(e)}"
        if hasattr(e, 'lineno'):
            msg = f"Template Error in {e.filename} line {e.lineno}: {e.message if hasattr(e,'message') else str(e)}"
        print(msg)
        raise RuntimeError(msg)

def remove_indentation(content):
    """Strips leading whitespace from every line in the rendered string"""
    lines = content.split('\n')
    stripped_lines = [line.lstrip() for line in lines]
    return '\n'.join(stripped_lines)

def remove_extra_blank_lines(content):
    """Removes entirely empty lines from the rendered string"""
    lines = content.split('\n')
    cleaned_lines = [line for line in lines if line.strip() != ""]
    return '\n'.join(cleaned_lines)