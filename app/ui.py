import tkinter as tk
import customtkinter as ctk
from main_window_operations import select_files, select_template, select_output_path, process_files, open_paths_configuration_window, open_model_syntax_settings_window, initialize_output_folders, open_parameters_file_editor, open_template_editor, open_humanized_syntax_template_editor, open_processed_file_viewer
from about import show_about, open_manual, show_new_features

# ==== CREATE USER INTERFACE ====

def create_ui(root):
    """Create the output folders if it does not exist and the user interface"""
    initialize_output_folders()
    
    menu = tk.Menu(root)
    root.config(menu=menu) # config the row menu
    
    # About menu
    about_menu = tk.Menu(menu, tearoff=0) # tearoff=0 to disable the dotted line at the about menu
    menu.add_cascade(label="About", menu=about_menu)
    about_menu.add_command(label="Version", command=show_about)
    about_menu.add_command(label="Open Manual", command=open_manual)
    about_menu.add_command(label="New Features", command=show_new_features)

    # Tools menu
    tools_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Tools", menu=tools_menu)
    tools_menu.add_command(label="Parameters File Editor", command=lambda: open_parameters_file_editor(root)) # use lambda: when calling a function with parameters, to avoid calling it accidentally
    tools_menu.add_command(label="Humanized Syntax Template Editor", command=lambda: open_humanized_syntax_template_editor(root))
    tools_menu.add_command(label="Template Editor", command=lambda: open_template_editor(root))
    tools_menu.add_command(label="Processed File Viewer", command=lambda: open_processed_file_viewer(root))

    # Config menu
    settings_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Config", menu=settings_menu)
    settings_menu.add_command(label="Default Paths", command=lambda: open_paths_configuration_window(root))
    settings_menu.add_command(label="Model Syntax", command=lambda: open_model_syntax_settings_window(root))

    title_label = tk.Label(root, text="Test Procedure Creator", font=("Helvetica", 16))
    title_label.grid(row=0, column=2, pady=10)

    default_image_path = "./images/MBT.png"
    
    try:
        # try to load the robot image
        image = tk.PhotoImage(file=default_image_path)
        image_label = tk.Label(root, image=image) 
        image_label.image = image
        image_label.grid(row=1, column=2, pady=10)
    except Exception:
        pass

    button_select_files = tk.Button(root, text="1. Select Parameter Files", command=select_files)
    button_select_files.grid(row=2, column=0, padx=10, pady=5, sticky="w") # sticky="w" place the button in west position, aligned to the left
    ButtonToolTip(button_select_files, "Select the parameter files to be processed")

    arrow_label_1 = tk.Label(root, text="→")
    arrow_label_1.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    frame_template = tk.Frame(root, borderwidth=2, relief="solid") # borderwidth=2, relief=solid to draw the black line around the frame
    frame_template.grid(row=2, column=2, padx=5, pady=5, sticky="ew") # sticky="ew" to use all the space of the column, from left to right

    button_select_template = tk.Button(frame_template, text="2. Select Template File", command=lambda: select_template(root))
    button_select_template.pack(pady=5)
    ButtonToolTip(button_select_template, "Select the template file to be used")

    arrow_label_2 = tk.Label(root, text="→")
    arrow_label_2.grid(row=2, column=3, padx=5, pady=5, sticky="e")

    button_process = tk.Button(root, text="3. Process Files", command=process_files)
    button_process.grid(row=2, column=4, padx=10, pady=5, sticky="e")
    ButtonToolTip(button_process, "Process the selected files using the chosen template")

    button_select_output_path = tk.Button(root, text="(O) Select Output Directory", command=select_output_path)
    button_select_output_path.grid(row=3, column=2, pady=5)
    ButtonToolTip(button_select_output_path, "Select optionally the directory where output files will be saved, default path is ./output/")

    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_columnconfigure(2, weight=2) # add column weights to adjust the space of the columns, column 2 has x2 space
    root.grid_columnconfigure(3, weight=1)
    root.grid_columnconfigure(4, weight=1)


# ==== BUTTON TOOLTIP ====

class ButtonToolTip(object):
    """Display help window"""
    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True) # removes the window decoration
        self.tw.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        label = tk.Label(self.tw, text=self.text, background="yellow", relief="solid", borderwidth=1)
        label.pack()

    def leave(self, event=None):
        if self.tw:
            self.tw.destroy()

# ==== CHOICE DIALOGS ====

class SyntaxChoiceDialog(ctk.CTkToplevel):
    """Ask for the process method when user select a template"""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Template Syntax Selection")
        self.geometry("450x200")
        self.grab_set() # with grab_set the user can only click on this window
        self.user_choice = None
        
        question_text = (
            "Select the processing method"
        )
        self.label = ctk.CTkLabel(self, text=question_text, font=ctk.CTkFont(size=14, weight="bold"))
        self.label.pack(pady=30, padx=20)
        
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent") # fg_color="transparent" to not ruin visual
        self.button_frame.pack(pady=10)
        
        self.btn_human = ctk.CTkButton(self.button_frame, text="Humanized Syntax Syntax", 
                                       fg_color="#2B5B84", command=lambda: self.set_choice("Humanized Syntax"))
        self.btn_human.pack(side="left", padx=15)
        
        self.btn_normal = ctk.CTkButton(self.button_frame, text="Normal Processing", 
                                        fg_color="#4A4D50", command=lambda: self.set_choice("Normal"))
        self.btn_normal.pack(side="left", padx=15)

    def set_choice(self, choice):
        self.user_choice = choice
        self.destroy()
        
    def get_choice(self):
        self.wait_window() # freeze the code on that point, for pop-up windows
        return self.user_choice
    
class LoadParametersChoiceDialog(ctk.CTkToplevel):
    """Ask the user if want to preload parameters for the template editor"""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Load Parameters")
        self.geometry("450x150")
        self.grab_set() 
        self.user_choice = None
        
        question_text = (
            "Do you want to load parameters from an existing file\n or continue without preloading?"
        )
        self.label = ctk.CTkLabel(self, text=question_text, font=ctk.CTkFont(size=14, weight="bold"))
        self.label.pack(pady=30, padx=20)
        
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=10)
        
        self.btn_human = ctk.CTkButton(self.button_frame, text="Load Parameters from file", 
                                       fg_color="#2B5B84", command=lambda: self.set_choice("Load Parameters from file"))
        self.btn_human.pack(side="left", padx=15)
        
        self.btn_normal = ctk.CTkButton(self.button_frame, text="Continue without preloading", 
                                        fg_color="#4A4D50", command=lambda: self.set_choice("Continue without preloading"))
        self.btn_normal.pack(side="left", padx=15)

    def set_choice(self, choice):
        self.user_choice = choice
        self.destroy()
        
    def get_choice(self):
        self.wait_window() 
        return self.user_choice