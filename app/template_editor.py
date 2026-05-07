import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from pygments import lex, lexers
from pygments.style import Style
from pygments.token import Comment, Keyword, Name, Number, Operator, Punctuation, String, Token

import main_window_operations as mwo

# ==== SYNTAX HIGHLIGHTING CONFIGURATION ====

class VSCodeStyle(Style):
    """Custom Pygments style to simulate the VS Code dark theme syntax highlighting"""
    background_color = "#1e1e1e"
    styles = {
        Comment:                '#006400',  # Dark Green
        Comment.Preproc:        '#DAA520',  # Gold
        Keyword:                '#9932CC',  # Pink
        Name.Variable:          '#00FFFF',  # Cyan
        Name.Tag:               '#569CD6',  # Dark Blue
        String:                 '#E9967A',  # Dark Salmon
        Number:                 '#FFFFFF',  # White
        Operator:               '#FFFFFF',  # White
        Punctuation:            '#FFFFFF',  # White
        Token.Text:             '#D4D4D4',  # Light Grey
        Name.Function:          '#DCDCAA',  # Yellow
        Name.Attribute:         '#9CDCFE',  # Dark Blue
    }

# Associate token colors for easy mapping in Tkinter (dict of tok: color)
TOKEN_COLORS = {str(tok): spec['color'] for tok, spec in VSCodeStyle if spec['color']} # spec['color'] gets the hexadecimal code (e.g. #FFFFFF)


# ==== MAIN APPLICATION CLASS ====

class TemplateEditor(ctk.CTkFrame):
    """A customized text editor frame for Jinja2 templates with syntax highlighting, 
    auto-completion, and custom insertion shortcuts"""
    
    def __init__(self, master, parameters_filepath, **kwargs): # kwargs to inherit ctk features
        super().__init__(master, corner_radius=0, **kwargs) # corner_radius=0 to have square corners
        
        self.parameters_filepath = parameters_filepath
        # if user has selected a parameter file to load variables, extract the variables names for the autocomplete feature
        if parameters_filepath:
            self.variables_name_list = extract_variables_from_file(self.parameters_filepath)
        else: 
            self.variables_name_list = []
        self.current_template_path = None

        # auxiliar variable use to perform pygments highlight
        self._highlight_job = None

        # toogle to show the number of the line like VS Code
        self.show_line_numbers = tk.BooleanVar(value=True)
        
        # Autocomplete auxiliar variables
        self.suggestion_win = None
        self.suggestion_frame = None
        self.current_suggestions = []
        self.suggestion_buttons = []
        self.selected_index = -1

        ctk.set_appearance_mode("light") # light appearance

        # Initialize UI Components 
        self._setup_menu_bar()
        self._setup_editor_area()
        self._setup_toolbar()
        self._setup_context_menu()
        
        # Initialize Bindings and Editor Configuration
        self._configure_editor_tags()
        self._bind_events()
        
        # Focus the editor 100ms after created and trigger initial highlight
        self.after(100, self.editor.focus_set)
        self.schedule_highlight()


    # ==== UI SETUP METHODS ====

    def _setup_menu_bar(self):
        """Sets up the top menu bar and its options"""
        self.menu_bar = ctk.CTkFrame(self, corner_radius=0, height=30, fg_color=("gray85", "gray15"))
        self.menu_bar.pack(side="top", fill="x")

        def file_menu_callback(choice):
            self.file_menu.set("File Options")
            if choice == "Load Parameters":
                self.open_parameter_file()
            elif choice == "Open Template":
                self.open_template()
            elif choice == "Save (Ctrl+S)":
                self.save_template()
            elif choice == "Save as...":
                self.save_as_template()

        self.file_menu = ctk.CTkOptionMenu(
            self.menu_bar, 
            values=["Load Parameters", "Open Template", "Save (Ctrl+S)", "Save as..."],
            command=file_menu_callback,
            width=60,
            fg_color=("gray85", "gray15"),       
            button_color=("gray85", "gray15"),   
            text_color=("black", "white"),
            button_hover_color=("gray70", "gray30"),
            font=("Roboto", 14)
        )
        self.file_menu.set("File Options")
        self.file_menu.pack(side="left", padx=5, pady=2)
        
        self.title_lbl = ctk.CTkLabel(self, text="New Template", font=("Arial", 16, "bold"))
        self.title_lbl.pack(pady=(10, 0))  # 10px top padding, 0px bottom padding

        if self.parameters_filepath:
            self.params_lbl = ctk.CTkLabel(self, text=f"Parameters loaded from: {os.path.splitext(os.path.basename(self.parameters_filepath))[0]}", 
                                        font=("Arial", 12), text_color="#2B2827")
        else:
            self.params_lbl = ctk.CTkLabel(self, text=f"Parameters not loaded", 
                                        font=("Arial", 12), text_color="#2B2827")
        self.params_lbl.pack(pady=(0, 10)) # 0px top padding, 10px bottom padding

    def _setup_editor_area(self):
        """Sets up the main text editing area"""
        # Create a horizontal container to hold both elements side-by-side
        self.editor_container = ctk.CTkFrame(self, fg_color="transparent")
        self.editor_container.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 10))

        # Add the Canvas to the container
        self.line_numbers = tk.Canvas(self.editor_container, width=40, bg="#1e1e1e", bd=0, highlightthickness=0)
        self.line_numbers.pack(side="left", fill="y")

        # Add the Editor to the container
        self.editor = ctk.CTkTextbox(
            self.editor_container, font=("Consolas", 15), wrap="none", undo=True,
            fg_color="#1e1e1e", text_color="#D4D4D4", corner_radius=0
        )
        self.editor.pack(side="left", fill="both", expand=True)

    def _setup_toolbar(self):
        """Sets up the bottom toolbar containing shortcut buttons"""
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        def run_jinja_shortcut(selected_option):
            if selected_option == jinja_shortcuts[0]:
                self.insert_variable_brackets()
            elif selected_option == jinja_shortcuts[1]:
                self.insert_code_brackets()
            elif selected_option == jinja_shortcuts[2]:
                self.insert_for_loop()
            elif selected_option == jinja_shortcuts[3]:
                self.insert_comment()
                
            self.jinja_menu.set("Jinja Shortcuts")

        jinja_shortcuts = ["Add Variable", "Add Code", "Add For", "Add Comment"]
        self.jinja_menu = ctk.CTkOptionMenu(
            self.toolbar,
            values=jinja_shortcuts,
            command=run_jinja_shortcut
        )
        self.jinja_menu.set("Jinja Shortcuts")
        self.jinja_menu.pack(side="left", padx=10)

        self.chk_line_numbers = ctk.CTkCheckBox(
            self.toolbar, text="Line Numbers", variable=self.show_line_numbers, 
            command=self.toggle_line_numbers, font=("Arial", 12, "bold"),
            width=130)
        self.chk_line_numbers.pack(side="left", padx=(5, 5))

        # Button configurations
        btn_font = ("Arial", 12, "bold")
        btn_height = 28

        self.btn_close = ctk.CTkButton(self.toolbar, text="Close", fg_color="#555555", hover_color="#333333", command=self.winfo_toplevel().destroy)
        self.btn_close.pack(side="right")

        self.btn_refresh = ctk.CTkButton(self.toolbar, text="Refresh Parameters", width=130, height=btn_height, font=btn_font, fg_color="#2E7D32", hover_color="#1B5E20", command=self.refresh_variables)
        self.btn_refresh.pack(side="right", padx=(5, 5))
        self.btn_refresh.bind("<Enter>", lambda e: self.btn_refresh.configure(text="Ctrl + R"))
        self.btn_refresh.bind("<Leave>", lambda e: self.btn_refresh.configure(text="Refresh Parameters"))

    def _setup_context_menu(self):
        # Create the Menu object (tearoff=0 to hide the line before the options)
        self.context_menu = tk.Menu(self.editor._textbox, tearoff=0)
        
        # Add standard options
        self.context_menu.add_command(label="Add Variable (Ctrl+D)", command=self.insert_variable_brackets)
        self.context_menu.add_command(label="Add Code (Ctrl+T)", command=self.insert_code_brackets)
        self.context_menu.add_command(label="Add For (Ctrl+L)", command=self.insert_for_loop)
        self.context_menu.add_command(label="Add Comment (Ctrl+M)", command=self.insert_comment)
        self.context_menu.add_command(label="Refresh Parameters (Ctrl+R)", command=self.refresh_variables)

        self.context_menu.add_separator()

        self.context_menu.add_command(label="Load Parameters", command=self.open_parameter_file)
        self.context_menu.add_command(label="Open Template", command=self.open_template)
        self.context_menu.add_command(label="Save (Ctrl+S)", command=self.save_template)
        self.context_menu.add_command(label="Save as...", command=self.save_as_template)

        # Bind the Right Click event
        self.editor._textbox.bind("<Button-3>", self._show_menu)

    def _show_menu(self, event):
        """Displays the context menu at the mouse cursor position"""
        # event.x_root and event.y_root give the global screen coordinates
        self.context_menu.post(event.x_root, event.y_root)

    def _configure_editor_tags(self):
        """Applies color configuration to text tags based on Pygments token mapping"""
        for token, color in TOKEN_COLORS.items():
            color_hex = f"#{color}" if color else "black"
            self.editor.tag_config(token, foreground=color_hex)

    def _bind_events(self):
        """Binds all mouse and keyboard events to the text editor"""
        # Custom intercepted actions
        self.editor._textbox.bind("<Double-Button-1>", self.on_double_click)
        self.editor._textbox.bind("<Up>", self.on_up)
        self.editor._textbox.bind("<Down>", self.on_down)
        self.editor._textbox.bind("<Return>", self.on_enter)
        self.editor._textbox.bind("<Tab>", self.on_tab)
        self.editor._textbox.bind("<Shift-Tab>", self.on_shift_tab)
        self.editor._textbox.bind("<KeyRelease>", self.on_key_release)
        self.editor._textbox.bind("<KeyPress>", self.on_key_press)
        self.editor._textbox.bind("<BackSpace>", self.on_backspace)
        self.editor._textbox.bind("<Button-1>", self.close_autocomplete, add="+")
        
        # Keyboard Shortcuts
        self.editor._textbox.bind("<Control-d>", self.insert_variable_brackets)
        self.editor._textbox.bind("<Control-D>", self.insert_variable_brackets)
        self.editor._textbox.bind("<Control-r>", self.refresh_variables)
        self.editor._textbox.bind("<Control-R>", self.refresh_variables)
        self.editor._textbox.bind("<Control-t>", self.insert_code_brackets) 
        self.editor._textbox.bind("<Control-T>", self.insert_code_brackets) 
        self.editor._textbox.bind("<Control-l>", self.insert_for_loop)
        self.editor._textbox.bind("<Control-L>", self.insert_for_loop)
        self.editor._textbox.bind("<Control-m>", self.insert_comment)
        self.editor._textbox.bind("<Control-M>", self.insert_comment)
        self.editor._textbox.bind("<Control-s>", self.save_template)
        self.editor._textbox.bind("<Control-S>", self.save_template)
        self.editor._textbox.bind("<MouseWheel>", lambda e: self.after(10, self.redraw_line_numbers), add="+")
        self.editor._textbox.bind("<B1-Motion>", lambda e: self.after(10, self.redraw_line_numbers), add="+")
        self.editor._textbox.bind("<Configure>", lambda e: self.redraw_line_numbers(), add="+")

        original_command = self.editor._textbox.cget("yscrollcommand") # save textbox yscrollcomand
        
        def intercepted_scroll(*args):
            if original_command:
                self.editor._textbox.tk.call(original_command, *args) # maintain textbox yscrollcomand feature
            
            self.redraw_line_numbers() # add redraw_line_numbers to the main yscrollcomand feature

        self.editor._textbox.configure(yscrollcommand=intercepted_scroll)

        self.setup_win_F_search()


    # ==== FILE OPERATIONS ====

    def open_parameter_file(self, humanized_syntax=False):
        """Allows the user to select a new input file to update the template variables"""
        try:
            config = mwo.load_config()
            initial_dir = config.get("default_input_dir", os.getcwd())
        except Exception:
            initial_dir = os.getcwd()

        parameters_filepath = filedialog.askopenfilename(
            parent=self,
            title="Load Parameters (Update Variables)",
            initialdir=initial_dir,
            filetypes=(("All Files", "*.*"), ("CSV Files", "*.csv"), ("Text Files", "*.txt")))
        
        if not parameters_filepath:
            return  # The user clicked cancel

        # Update the stored filepath for the editor
        self.parameters_filepath = parameters_filepath
        if humanized_syntax:
            self.humanized_syntax_process_features_class.parameters_filepath = parameters_filepath # update parameters_filepath of the process_class if humanized_syntax
        self.params_lbl.configure(text=f"Parameters loaded from: {os.path.splitext(os.path.basename(self.parameters_filepath))[0]}") # update title
        
        # Reuse refresh function to update state
        if humanized_syntax:
            self.refresh_variables(return_dict_variable_value=True)
        else:
            self.refresh_variables()
        
        # Notify user
        messagebox.showinfo("Variables Updated", f"Loaded variables from:\n{os.path.basename(parameters_filepath)}", parent=self)

    def open_template(self):
        """Opens an existing Jinja2 template file into the editor"""
        try:
            config = mwo.load_config()
            initial_dir = config.get("default_template_dir", os.getcwd())
        except Exception:
            initial_dir = os.getcwd()

        template_filepath = filedialog.askopenfilename(
            parent=self,
            title="Open Template",
            initialdir=initial_dir,
            filetypes=(("Jinja2 files", "*.j2"), ("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        
        if not template_filepath:
            return

        try:
            with open(template_filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # start in 1.0 -> line 1, char 0, delete until the end    
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", content)
            
            self.current_template_path = template_filepath
            self.schedule_highlight()
            self.title_lbl.configure(text=f"Template: {os.path.splitext(os.path.basename(self.current_template_path))[0]}")
            self.master.title(os.path.splitext(os.path.basename(self.current_template_path))[0])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open template:\n{e}", parent=self)

    def save_template(self, event=None):
        """Saves the current template. Triggers 'Save as' if no file path exists yet"""
        # If we already have a path, just overwrite it silently
        if self.current_template_path:
            self._write_file(self.current_template_path)
            messagebox.showinfo("Saved", f"Template saved successfully:\n{os.path.basename(self.current_template_path)}", parent=self)
        else:
            # If it's a new template, trigger Save as
            self.save_as_template()
            
        return "break"  # Prevents default tkinter text events

    def save_as_template(self):
        """Prompts the user to save the current text as a new template file"""
        try:
            config = mwo.load_config()
            initial_dir = config.get("default_template_dir", os.getcwd())
        except Exception:
            initial_dir = os.getcwd()

        template_filepath = filedialog.asksaveasfilename(
            parent=self,
            title="Save Template As",
            initialdir=initial_dir,
            defaultextension=".j2",
            filetypes=(("Jinja2 files", "*.j2"), ("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        
        if not template_filepath:
            return

        self.current_template_path = template_filepath
        if self._write_file(template_filepath):
            self.title_lbl.configure(text=f"Template: {os.path.splitext(os.path.basename(self.current_template_path))[0]}")
            self.master.title(os.path.splitext(os.path.basename(self.current_template_path))[0])
            messagebox.showinfo("Success", "Template saved successfully!", parent=self)

    def _write_file(self, path):
        """Helper method to write editor contents to the filesystem"""
        content = self.editor.get("1.0", "end-1c")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}", parent=self)
            return False


    # ==== TEXT MANIPULATION / TEMPLATE INSERTIONS ====

    def insert_variable_brackets(self, event=None):
        """Wraps selected text in Jinja variable tags {{ }} or inserts empty ones"""
        if self.editor.tag_ranges("sel"):
            sel_start = self.editor.index("sel.first")
            sel_end = self.editor.index("sel.last")
            selected_text = self.editor.get(sel_start, sel_end)
            self.editor.delete(sel_start, sel_end)
            self.editor.insert("insert", f"{{{{{selected_text}}}}}") # need {{}} to write {} in f" "
        else:
            self.editor.insert("insert", "{{}}")
            self.editor.mark_set("insert", "insert-2c")
            
        self.schedule_highlight()
        self.editor.focus_set()
        return "break"

    def insert_code_brackets(self, event=None):
        """Wraps selected text in Jinja code block tags {% %} or inserts empty ones"""
        if self.editor.tag_ranges("sel"):
            sel_start = self.editor.index("sel.first")
            sel_end = self.editor.index("sel.last")
            selected_text = self.editor.get(sel_start, sel_end)
            self.editor.delete(sel_start, sel_end)
            self.editor.insert("insert", f"{{% {selected_text} %}}")
        else:
            self.editor.insert("insert", "{%  %}")
            self.editor.mark_set("insert", "insert-3c")
            
        self.schedule_highlight()
        self.editor.focus_set()
        return "break"

    def insert_for_loop(self, event=None):
        """Insert a Jinja for-loop with auto-indentation"""
        if self.editor.tag_ranges("sel"):
            sel_start = self.editor.index("sel.first") # idx of the sel_start
            sel_end = self.editor.index("sel.last") # idx of the sel_end
            
            line_start = self.editor.index(f"{sel_start} linestart") 
            line_text = self.editor.get(line_start, f"{line_start} lineend")
            base_indent = re.match(r"^[ \t]*", line_text).group(0) # read from left to right and save all the tabs

            selected_text = self.editor.get(sel_start, sel_end)
            self.editor.delete(sel_start, sel_end)
            
            indented_text = selected_text.replace('\n', '\n\t')
            
            block = f"{{% for  %}}\n{base_indent}\t{indented_text}\n{base_indent}{{% endfor %}}"
            self.editor.insert("insert", block)
            
            offset = len(f"\n{base_indent}\t{indented_text}\n{base_indent}{{% endfor %}}") + 3
            self.editor.mark_set("insert", f"insert-{offset}c")
        else:
            line_start = self.editor.index("insert linestart")
            line_text = self.editor.get(line_start, f"{line_start} lineend")
            base_indent = re.match(r"^[ \t]*", line_text).group(0) # group(0) to take everything

            block = f"{{% for  %}}\n{base_indent}\t\n{base_indent}{{% endfor %}}"
            self.editor.insert("insert", block)
            
            offset = len(f"\n{base_indent}\t\n{base_indent}{{% endfor %}}") + 3
            self.editor.mark_set("insert", f"insert-{offset}c") # to put the cursor right after the for
            
        self.schedule_highlight()
        self.editor.focus_set()
        return "break"

    def insert_comment(self, event=None):
        """Wraps selected text in Jinja comment tags {# #} or inserts empty ones."""
        if self.editor.tag_ranges("sel"):
            sel_start = self.editor.index("sel.first")
            sel_end = self.editor.index("sel.last")
            selected_text = self.editor.get(sel_start, sel_end)
            self.editor.delete(sel_start, sel_end)
            self.editor.insert("insert", f"{{# {selected_text} #}}")
        else:
            self.editor.insert("insert", "{#  #}")
            self.editor.mark_set("insert", "insert-3c")
            
        self.schedule_highlight()
        self.editor.focus_set()
        return "break"


    # ==== VARIABLE MANAGEMENT ====

    def refresh_variables(self, event=None, return_dict_variable_value=False):
        """Reloads variables from the selected filepath to update autocomplete pool"""
        if not self.parameters_filepath:
            return
        try:
            if not return_dict_variable_value:
                self.variables_name_list = extract_variables_from_file(self.parameters_filepath)
            else:
                self.humanized_syntax_process_features_class.parameters_file_dict = extract_variables_from_file(self.parameters_filepath, return_dict_variable_value=True)
                self.variables_name_list = extract_variables_from_file(self.parameters_filepath)
            self.btn_refresh.configure(text="✓ Refreshed!", fg_color="#2E7D32")
            self.after(2000, lambda: self.btn_refresh.configure(text="Refresh Parameters", fg_color="#2E7D32"))
        except Exception as e:
            messagebox.showerror("Refresh Error", f"Could not refresh variables:\n{e}", parent=self)


    # ==== AUTOCOMPLETE SYSTEM ====

    def close_autocomplete(self, event=None):
        """Destroys the autocomplete popup and resets suggestions state"""
        if self.suggestion_win:
            self.suggestion_win.destroy()
            self.suggestion_win = None
            self.current_suggestions = []
            self.suggestion_buttons = []
            self.selected_index = -1

    def update_autocomplete(self, prefix):
        """Filters variables by prefix and displays the autocomplete popup window"""
        filtered_vars = [var for var in self.variables_name_list if var.lower().startswith(prefix.lower())]
        
        if not filtered_vars or (prefix in self.variables_name_list):
            self.close_autocomplete()
            return

        self.current_suggestions = filtered_vars

        if not self.suggestion_win:
            cursor_pos = self.editor.bbox("insert") # get the cursor coordinates
            if not cursor_pos: return
            # calculate suggestion_win coordinates
            x = self.editor.winfo_rootx() + cursor_pos[0] + 20
            y = self.editor.winfo_rooty() + cursor_pos[1] + 25

            self.suggestion_win = tk.Toplevel(self)
            self.suggestion_win.overrideredirect(True) # removes the window decoration
            self.suggestion_win.geometry(f"+{x}+{y}") # place the suggestion_win in the coordinates
            self.suggestion_frame = ctk.CTkFrame(
                self.suggestion_win, border_width=1, border_color="#555", fg_color="#2b2b2b"
            )
            self.suggestion_frame.pack()

        for btn in self.suggestion_buttons: 
            btn.destroy()
        self.suggestion_buttons = []

        for i, var in enumerate(self.current_suggestions):
            bg_color = "#007acc" if i == 0 else "transparent" # highlight the first option in blue
            btn = ctk.CTkButton(
                self.suggestion_frame, text=var, height=25, corner_radius=0,
                fg_color=bg_color, text_color="white", hover_color="#555555",
                anchor="w", command=lambda v=var: self.insert_var(v) # v=var freeze the value for each button
            )
            btn.pack(fill="x")
            self.suggestion_buttons.append(btn)
        
        self.selected_index = 0

    def insert_var(self, var_name):
        """Inserts the selected autocomplete result with a compact closure '}}' if applicable"""
        line_start = self.editor.index("insert linestart")
        cursor_pos = self.editor.index("insert")
        text_before = self.editor.get(line_start, cursor_pos)
        text_after = self.editor.get("insert", f"{line_start} lineend")

        match = re.search(r"([a-zA-Z0-9_]*)$", text_before) # & jump to the final of the string, this permits to read from right to left
        prefix_len = len(match.group(1)) if match else 0

        idx_var_open = text_before.rfind("{{")
        idx_block_open = text_before.rfind("{%")

        start_replace = self.editor.index(f"insert-{prefix_len}c")
        self.editor.delete(start_replace, "insert")
        
        # Determine if we are inside {{ or {% to close compactly
        if idx_var_open > idx_block_open:
            if "}}" not in text_after[0:5]: # check if the variable has }}
                self.editor.insert("insert", var_name + "}}")
            else:
                self.editor.insert("insert", var_name)
        else:
            self.editor.insert("insert", var_name)
        
        self.close_autocomplete()
        self.schedule_highlight()
        return "break"

    def set_selected_index(self, index):
        """Updates the visual selection state within the autocomplete list"""
        if 0 <= self.selected_index < len(self.suggestion_buttons):
            self.suggestion_buttons[self.selected_index].configure(fg_color="transparent") 
        self.selected_index = index
        self.suggestion_buttons[self.selected_index].configure(fg_color="#007acc")


    # ==== SYNTAX HIGHLIGHTING PROCESSING ====

    def schedule_highlight(self):
        """Prevent lag while typing fast, permits to avoid running the same function over and over again"""
        if self._highlight_job is not None: # if we have a highlight job scheduled
            self.after_cancel(self._highlight_job) # cancel the function call
        self._highlight_job = self.after(50, self._perform_highlight) # schedule a new highlight job 

        self.redraw_line_numbers()

    def redraw_line_numbers(self, event=None):
        """Calculates visible lines and draws the numbers on the margin canvas"""
        if not self.show_line_numbers.get():
            return
            
        self.line_numbers.delete("all")
        
        # Get the index of the first currently visible line on screen
        i = self.editor._textbox.index("@0,0")
        while True:
            dline = self.editor._textbox.dlineinfo(i) # display line info
            if dline is None:
                break # Reached the bottom of the visible screen
            
            y = dline[1] # Vertical position of the line
            actual_y = y + 2 # Offset to match CTkTextbox internal padding
            linenum = str(i).split(".")[0] # Get the row number
            
            # Draw the number dynamically
            self.line_numbers.create_text(35, actual_y, anchor="ne", text=linenum, font=("Consolas", 12), fill="#858585") # 35 horizontal position, north-east aligned
            
            # Move index to the next visual line
            i = self.editor._textbox.index(f"{i}+1line")

    def toggle_line_numbers(self):
        """Shows or hides the line numbers canvas based on the checkbox"""
        if self.show_line_numbers.get():
            self.line_numbers.pack(side="left", fill="y", before=self.editor) # place it before the template textbox
            self.redraw_line_numbers()
        else:
            self.line_numbers.pack_forget()

    def _perform_highlight(self):
        """Parses the text and applies Pygments syntax highlighting tags"""
        content = self.editor.get("1.0", "end-1c")
        lexer = lexers.get_lexer_by_name("jinja", stripnl=False) # stripnl=False (do not strip newlines) avoid coloring issues
        
        # Remove old tags before re-applying
        for tag in self.editor.tag_names():
            if tag != "sel": # skip selected text by the user
                self.editor.tag_remove(tag, "1.0", "end")

        index = "1.0"
        for token_type, value in lex(content, lexer): # Parse the content with jinja syntax
            end_index = self.editor.index(f"{index} + {len(value)}c")
            tag_name = str(token_type)
            if tag_name in TOKEN_COLORS and TOKEN_COLORS[tag_name]:
                self.editor.tag_add(tag_name, index, end_index)
            index = end_index


    # ==== EVENT HANDLERS (MOUSE & KEYBOARD) ====

    def on_backspace(self, event):
        """Handles smart deletion of paired brackets/characters"""
        char_before = self.editor.get("insert-1c", "insert")
        char_after = self.editor.get("insert", "insert+1c")

        pairs = {'{': '}', '[': ']', '(': ')', '"': '"', "'": "'", '%': '%', '#': '#'}
        if char_before in pairs and pairs[char_before] == char_after:
            self.editor.delete("insert", "insert+1c")
            self.editor.delete("insert-1c", "insert")
            self.schedule_highlight()
            return "break" # to skip normal delete behaviour

        if char_before == " " and char_after == " ":
            prev_2 = self.editor.get("insert-2c", "insert-1c")
            next_2 = self.editor.get("insert+1c", "insert+2c")
            if (prev_2 == "{" and next_2 == "}") or (prev_2 == "%" and next_2 == "%") or (prev_2 == "#" and next_2 == "#"):
                self.editor.delete("insert", "insert+1c")
                self.editor.delete("insert-1c", "insert")
                self.schedule_highlight()
                return "break" # to skip normal delete behaviour

    def on_key_press(self, event):
        """Handles smart auto-pairing and spacing logic during typing"""        
        closings = {"}": "{", "]": "[", ")": "(", '"': '"', "'": "'"}
        if event.char in closings:
            if self.editor.get("insert", "insert+1c") == event.char:
                self.editor.mark_set("insert", "insert+1c") # prevents the user of typing another closing sign
                return "break"

        auto_pairs = {'{': '}', '[': ']', '(': ')', '"': '"', "'": "'"}
        if event.char in auto_pairs:
            self.editor.insert("insert", event.char + auto_pairs[event.char])
            self.editor.mark_set("insert", "insert-1c")
            self.schedule_highlight()
            return "break"

        if event.char in ['%', '#']:
            if self.editor.get("insert-1c", "insert") == '{':
                if self.editor.get("insert", "insert+1c") == '}':
                    self.editor.delete("insert", "insert+1c")
                
                self.editor.insert("insert", f"{event.char}  {event.char}}}")
                self.editor.mark_set("insert", "insert-3c")
                self.schedule_highlight()
                return "break"

        if event.char == ' ':
            prev_2 = self.editor.get("insert-2c", "insert")
            next_2 = self.editor.get("insert", "insert+2c")
            # Only expand spaces for code or comment blocks
            if (prev_2 == "{%" and next_2 == "%}") or (prev_2 == "{#" and next_2 == "#}"):
                self.editor.insert("insert", "  ")
                self.editor.mark_set("insert", "insert-1c")
                self.schedule_highlight()
                return "break"
        
        is_shortcut = not event.char.isprintable()
        if (not self.editor.tag_ranges("sel") or not event.char or is_shortcut):
            return
    
        if self.editor.tag_ranges("sel"): # define this to prevent issues
            self.editor.delete("sel.first", "sel.last")
            self.editor.insert("insert", event.char)
            return "break"

    def on_key_release(self, event):
        """Analyzes typed text to trigger autocomplete suggestions"""
        self.redraw_line_numbers()

        if event.keysym in ["Up", "Down","Return", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"]: # Normal behaviour
            return
        elif event.keysym in ["Left", "Right", "Escape"]:
            self.close_autocomplete()
            return
            
        # Check if press Ctrl + letter (e.g. Ctrl+L)
        if event.keysym.lower() in ['d', 't', 'l', 'm'] and (event.state & 0x0004): 
            return

        self.schedule_highlight()

        line_start = self.editor.index("insert linestart")
        cursor_pos = self.editor.index("insert")
        text_before = self.editor.get(line_start, cursor_pos)

        idx_var_open = text_before.rfind("{{")
        idx_block_open = text_before.rfind("{%")
        last_open_idx = max(idx_var_open, idx_block_open)

        idx_var_close = text_before.rfind("}}")
        idx_block_close = text_before.rfind("%}")
        last_close_idx = max(idx_var_close, idx_block_close)

        if last_open_idx > last_close_idx:
            content_inside = text_before[last_open_idx+2:]
            
            match = re.search(r"([a-zA-Z0-9_]+)$", content_inside)
            prefix = match.group(1) if match else ""
            
            jinja_keywords = ["if", "else", "elif", "endif", "for", "in", "endfor", "block", "endblock"] # to avoid showing the autocomplete for jinja keywords
            
            if prefix and prefix not in jinja_keywords:
                self.update_autocomplete(prefix)
            else:
                self.close_autocomplete()
        else:
            self.close_autocomplete()

    def on_double_click(self, event):
        """Selects the word"""
        # Get the exact line and column where the mouse clicked
        click_idx = self.editor._textbox.index(f"@{event.x},{event.y}")
        line_num, col_num = map(int, click_idx.split('.'))
        
        # Get the full text of that specific line
        line_text = self.editor.get(f"{line_num}.0", f"{line_num}.end")
        
        if col_num >= len(line_text):
            return "break"
            
        # Search backwards to find where the word starts
        start_col = col_num
        while start_col > 0 and re.match(r"\w", line_text[start_col - 1]):
            start_col -= 1
            
        # Search forwards to find where the word ends
        end_col = col_num
        while end_col < len(line_text) and re.match(r"\w", line_text[end_col]):
            end_col += 1
            
        # Clear any existing selection
        self.editor.tag_remove("sel", "1.0", "end")
        
        # If we successfully found a word, select it
        if start_col != end_col:
            self.editor.tag_add("sel", f"{line_num}.{start_col}", f"{line_num}.{end_col}")
            self.editor.mark_set("insert", f"{line_num}.{end_col}") # Move cursor to the end of the word
            
        return "break" # Skip tkinter double-click function

    def on_up(self, event):
        """Navigates up within the autocomplete suggestion list"""
        if self.suggestion_win:
            # Loop back to the bottom if we are at the top
            new_index = (self.selected_index - 1) % len(self.current_suggestions)
            self.set_selected_index(new_index)
            return "break" # Always break so the text cursor does not move
            
    def on_down(self, event):
        """Navigates down within the autocomplete suggestion list"""
        if self.suggestion_win:
            # Loop back to the top if we are at the bottom
            new_index = (self.selected_index + 1) % len(self.current_suggestions)
            self.set_selected_index(new_index)
            return "break" # Always break so the text cursor does not move
            
    def on_tab(self, event):
        """Inserts selected autocomplete item or applies a hard tab"""
        if self.suggestion_win and self.current_suggestions:
            self.insert_var(self.current_suggestions[self.selected_index])
            return "break"

        if self.editor.tag_ranges("sel"):
            start, end = self.editor.tag_ranges("sel") 

            first_line = int(self.editor.index(start).split('.')[0])
            last_line = int(self.editor.index(end).split('.')[0])

            for line_num in range(first_line, last_line + 1):
                self.editor.insert(f"{line_num}.0", "\t")

            self.schedule_highlight()
            return "break"

        self.editor.insert("insert", "\t")
        self.schedule_highlight()
        return "break"

    def on_shift_tab(self, event):
        """Delete a tab for each line selected"""
        try:
            if self.editor.tag_ranges("sel"):
                start_idx = self.editor.index("sel.first")
                end_idx = self.editor.index("sel.last")
                
                first_line = int(start_idx.split('.')[0])
                last_line = int(end_idx.split('.')[0])
            else:
                first_line = last_line = int(self.editor.index("insert").split('.')[0])

            for line_num in range(first_line, last_line + 1):
                line_start = self.editor.get(f"{line_num}.0", f"{line_num}.4")
                
                if line_start.startswith("\t"):
                    self.editor.delete(f"{line_num}.0", f"{line_num}.1")
                else:
                    spaces_to_delete = 0
                    for char in line_start:
                        if char == " ":
                            spaces_to_delete += 1
                        else:
                            break
                    
                    if spaces_to_delete > 0:
                        self.editor.delete(f"{line_num}.0", f"{line_num}.{spaces_to_delete}")
            
            # Implement visual selection movement
            if self.editor.tag_ranges("sel"):
                self.editor.tag_remove("sel", "1.0", "end") 
                self.editor.tag_add("sel", f"{first_line}.0", f"{last_line}.end") 

            self.schedule_highlight()

        except Exception as e:
            print(f"Error in on_shift_tab: {e}")

        return "break"
            
    def on_enter(self, event):
        """Inserts selected autocomplete item or handles smart auto-indentation on new line"""
        if self.suggestion_win and self.current_suggestions:
            self.insert_var(self.current_suggestions[self.selected_index])
            return "break"
            
        # Auto-indentation on enter
        line_start = self.editor.index("insert linestart")
        line_text = self.editor.get(line_start, "insert lineend")
        
        # Extracts the base indentation
        base_indent = re.match(r"^[ \t]*", line_text).group(0)
        
        self.editor.insert("insert", "\n" + base_indent)
        self.editor.see("insert") # Force auto-scroll
        
        self.schedule_highlight()
        return "break"
    

    # ==== F SEARCH FEATURE ====

    def setup_win_F_search(self):
        """Binds the Ctrl+F shortcut and configures highlight colors"""
        # Yellow for all matches
        self.editor._textbox.tag_configure("search_highlight", background="#ffd700", foreground="black")
        # Orange for the currently selected match
        self.editor._textbox.tag_configure("current_match", background="#ff8c00", foreground="white")
        
        self.editor._textbox.bind("<Control-f>", self.show_integrated_search)
        self.editor._textbox.bind("<Control-F>", self.show_integrated_search)

    def show_integrated_search(self, event=None):
        """Displays the search bar with match counter, navigation, and a close button"""
        if hasattr(self, 'search_frame') and self.search_frame.winfo_exists(): # check if variable searchframe and search window exists
            self.search_entry.focus() # if exist focus on the window
            return

        # Create the main search container
        self.search_frame = ctk.CTkFrame(self.editor, corner_radius=5, border_width=1)
        self.search_frame.place(relx=0.98, rely=0.02, anchor="ne") # relx=0.98 place the search_frame at the 98% of the window width, anchor=north-east (correspond with the position of the search_frame)

        self.close_btn = ctk.CTkButton(self.search_frame, text="✕", width=28, height=28, corner_radius=4, fg_color="transparent", text_color=("black", "white"), hover_color=("#e5e5e5", "#333333"), command=self.close_search_bar)
        self.close_btn.pack(side="right", padx=(5, 5), pady=5)

        self.close_btn = ctk.CTkButton(self.search_frame, text="↓", width=28, height=28, corner_radius=4, fg_color="transparent", text_color=("black", "white"), hover_color=("#e5e5e5", "#333333"), command=self.go_to_next_match)
        self.close_btn.pack(side="right", padx=(5, 5), pady=5)

        self.close_btn = ctk.CTkButton(self.search_frame, text="↑", width=28, height=28, corner_radius=4, fg_color="transparent", text_color=("black", "white"), hover_color=("#e5e5e5", "#333333"), command=self.go_to_previous_match)
        self.close_btn.pack(side="right", padx=(5, 0), pady=5)

        self.close_btn = ctk.CTkButton(self.search_frame, text=">", width=28, height=28, corner_radius=4, fg_color="transparent", text_color=("black", "white"), hover_color=("#e5e5e5", "#333333"), command=self.toogle_replace_bar)
        self.close_btn.pack(side="left", padx=(5, 0), pady=5)

        # Add the Entry (Search Box)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.perform_live_search) # monitor the entry to update the matches

        self.search_entry = ctk.CTkEntry(self.search_frame, textvariable=self.search_var, width=200, border_width=0, fg_color="transparent")
        self.search_entry.pack(side="left", padx=(10, 5), pady=5)
        self.search_entry.focus()

        self.match_count_label = ctk.CTkLabel(self.search_frame, text="0 / 0", text_color="gray")
        self.match_count_label.pack(side="left", padx=(0, 10))

        # Key Bindings
        self.search_entry.bind("<Return>", self.go_to_next_match)
        self.search_entry.bind("<Tab>", self.go_to_next_match)
        self.search_entry.bind("<Shift-Return>", self.go_to_previous_match)
        self.search_entry.bind("<Escape>", lambda e: self.close_search_bar())
        # Listen to typing inside the text editor while search is open
        self.editor_bind_id = self.editor._textbox.bind("<KeyRelease>", self.refresh_highlights, add="+")

        self.match_positions = [] #[("1.5", "1.10"), ("4.2", "4.7")] save in each tuple start and end of the match
        self.current_match_index = -1

    def perform_live_search(self, *args, auto_scroll=True):
        """Finds all matches, saves their positions, and highlights them"""
        
        # If the function is called automatically by typing in the search box, args will contain 3 items. We want to auto_scroll in that case
        if len(args) == 3:
            auto_scroll = True

        self.editor._textbox.tag_remove("search_highlight", "1.0", tk.END)
        self.editor._textbox.tag_remove("current_match", "1.0", tk.END)
        
        self.match_positions.clear()
        
        search_query = self.search_var.get()
        if not search_query:
            self.match_count_label.configure(text="0 / 0")
            return

        start_pos = "1.0" 
        while True:
            # Save the idx of the start_position
            start_pos = self.editor._textbox.search(search_query, start_pos, stopindex=tk.END, nocase=True) # no case sensitive
            
            if not start_pos:
                break 
                
            end_pos = f"{start_pos}+{len(search_query)}c"
            self.editor._textbox.tag_add("search_highlight", start_pos, end_pos)
            self.match_positions.append((start_pos, end_pos))
            start_pos = end_pos

        if self.match_positions:
            # Try to keep the current match index valid if text was deleted
            if self.current_match_index >= len(self.match_positions) or self.current_match_index < 0:
                self.current_match_index = 0
                
            # Update the counter
            total_matches = len(self.match_positions)
            self.match_count_label.configure(text=f"{self.current_match_index + 1} / {total_matches}")

            # Highlight the current match in orange
            c_start, c_end = self.match_positions[self.current_match_index]
            self.editor._textbox.tag_add("current_match", c_start, c_end)

            # Move the camera if we are searching, not if we are just typing in the editor
            if auto_scroll:
                self.editor._textbox.see(c_start)
        else:
            self.match_count_label.configure(text="0 / 0")

    def go_to_next_match(self, event=None):
        """Jump to the next match when Enter or Tab is pressed"""
        if not self.match_positions:
            return "break"

        self.current_match_index += 1
        
        if self.current_match_index >= len(self.match_positions):
            self.current_match_index = 0
            
        self.update_current_match_display()
        return "break"

    def go_to_previous_match(self, event=None):
        """Jump to the previous match when Shift+Enter is pressed"""
        if not self.match_positions:
            return "break"

        self.current_match_index -= 1
        
        if self.current_match_index < 0:
            self.current_match_index = len(self.match_positions) - 1
            
        self.update_current_match_display()
        return "break"

    def update_current_match_display(self):
        """Highlights the active match in orange and scrolls to it"""
        # Remove the orange tag from anywhere it was before
        self.editor._textbox.tag_remove("current_match", "1.0", tk.END)
        
        # Get the coordinates of the current match
        start_pos, end_pos = self.match_positions[self.current_match_index]
        
        # Apply the orange tag
        self.editor._textbox.tag_add("current_match", start_pos, end_pos)
        
        # Update the counter label
        total_matches = len(self.match_positions)
        self.match_count_label.configure(text=f"{self.current_match_index + 1} / {total_matches}")
        
        # Force the textbox to scroll to the active match
        self.editor._textbox.see(start_pos)
    
    def replace_occurrences(self, new_word, replace_all=False):
        """Replace occurrences with the new word"""
        if not self.match_positions or (new_word == ""):
            return

        # Implement manual separator to fix Ctrl+Z behaviour
        self.editor._textbox.configure(autoseparators=False)
        self.editor.edit_separator()

        if replace_all:
            for location in reversed(self.match_positions):
                start_pos, end_pos = location
                self.editor.delete(start_pos, end_pos)
                self.editor.insert(start_pos, new_word, "neutral_tag") # Replace the word with "neutral_tag" to avoid inheriting old tags ("search_highlight" or "current_match")
        else:
            start_pos, end_pos = self.match_positions[self.current_match_index]
            self.editor.delete(start_pos, end_pos)
            self.editor.insert(start_pos, new_word, "neutral_tag")
            
        self._perform_highlight() 
        self.perform_live_search() 
        
        self.editor.edit_separator()
        self.editor._textbox.configure(autoseparators=True)

    def close_search_bar(self):
        """Closes the search bar and clears all data"""
        if hasattr(self, 'search_frame') and self.search_frame.winfo_exists():
            self.search_frame.destroy()
        
        if hasattr(self, 'refactor_frame') and self.refactor_frame.winfo_exists():
            self.refactor_frame.destroy()
            
        if hasattr(self, 'editor_bind_id'):
            self.editor._textbox.unbind("<KeyRelease>", self.editor_bind_id)
            
        self.editor._textbox.tag_remove("search_highlight", "1.0", tk.END)
        self.editor._textbox.tag_remove("current_match", "1.0", tk.END)
        self.match_positions.clear()
        self.after(100, self.editor.focus_set)

    def toogle_replace_bar(self):
        """Manage the display of the replace_bar"""
        if hasattr(self, 'refactor_frame') and self.refactor_frame.winfo_exists():
            self.refactor_frame.destroy()
            return

        self.refactor_frame = ctk.CTkFrame(self.editor, corner_radius=5, border_width=1)
        self.refactor_frame.place(in_=self.search_frame, relx=1.0, rely=1.0, y=2, anchor="ne")

        self.refactor_var = tk.StringVar()
        self.refactor_entry = ctk.CTkEntry(self.refactor_frame, textvariable=self.refactor_var, width=200, border_width=0, fg_color="transparent")
        self.refactor_entry.pack(side="left", padx=(10, 5), pady=5)
        self.refactor_entry.focus()

        self.btn_replace = ctk.CTkButton(self.refactor_frame, text="Replace", width=28, height=28, corner_radius=4, fg_color="transparent", text_color=("black", "white"), hover_color=("#e5e5e5", "#333333"), command=lambda: self.replace_occurrences(new_word=self.refactor_var.get()))
        self.btn_replace.pack(side="left", padx=(5, 0), pady=5)

        self.btn_replace_all = ctk.CTkButton(self.refactor_frame, text="Replace all", width=28, height=28, corner_radius=4, fg_color="transparent", text_color=("black", "white"), hover_color=("#e5e5e5", "#333333"), command=lambda: self.replace_occurrences(new_word=self.refactor_var.get(), replace_all=True))
        self.btn_replace_all.pack(side="left", padx=(5, 0), pady=5)

        self.close_refactor_btn = ctk.CTkButton(self.refactor_frame, text="✕", width=28, height=28, corner_radius=4, fg_color="transparent", text_color=("black", "white"), hover_color=("#e5e5e5", "#333333"), command=lambda: self.refactor_frame.destroy())
        self.close_refactor_btn.pack(side="right", padx=(5, 5), pady=5)

        self.refactor_entry.bind("<Escape>", lambda e: self.refactor_frame.destroy())
    
    def refresh_highlights(self, event=None):
        """Triggered when the user types inside the text editor to update current_matches and tags"""
        if hasattr(self, 'search_frame') and self.search_frame.winfo_exists():
            
            # If there is already a timer waiting to execute, cancel it
            if hasattr(self, '_search_timer') and self._search_timer is not None:
                self.editor.after_cancel(self._search_timer)
                
            # Schedule a new search to run 50 milliseconds from now (this gives time to the editor to insert the text before coloring it)
            self._search_timer = self.editor.after(50, lambda: self.perform_live_search(auto_scroll=False))

# ==== FUNCTION SHARED BETWEEN TEMPLATE EDITOR AND HUMANIZED_SYNTAX_TEMPLATE_EDITOR (HumanizedSyntaxProcessFeatures Class) ====
# ==== VARIABLE MANAGEMENT ====          

def extract_variables_from_file(parameters_filepath, return_dict_variable_value=False):
        """Reads an input file and extracts parameter keys based on active syntax"""
        data={} 
        try:
            with open(parameters_filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    mwo._process_file_with_active_syntax(line, data)

            data["FILENAME"] = os.path.basename(parameters_filepath).split(".")[0]

            for key_name, item in data.items():
                print(f"{key_name}: {item}")
            
            print("-------------------------------------------------------------------------------------------------------")

            if return_dict_variable_value:
                return data

            keys = []

            # loop to add [] to keys for the autocomplete feature
            for key, values in data.items():
                if isinstance(values, list):
                    if len(values) > 0 and isinstance(values[0], list):
                        keys.append(f"{key}[][]")
                    else:
                        keys.append(f"{key}[]")
                else:
                    keys.append(key)

        except Exception as e:
            raise RuntimeError(f"Error reading file:\n{e}")
            
        return keys