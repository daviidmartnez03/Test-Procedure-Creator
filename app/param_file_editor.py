import os
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tksheet import Sheet

import main_window_operations as mwo

# Ensures consistent scaling across different monitor resolutions
ctk.deactivate_automatic_dpi_awareness()

# ==== HELPER DIALOG CLASSES ====

class PreviewDialog(ctk.CTkToplevel):
    """Dialog to preview file content before saving. Requires the user to explicitly confirm or cancel the save action"""
    def __init__(self, parent, text_content, title="File Preview"):
        super().__init__(parent)
        self.title(title)
        self.geometry("700x500")
        
        self.transient(parent)
        self.grab_set()
        
        self.user_choice = False 

        # UI Elements
        lbl = ctk.CTkLabel(self, text="Please review the file content before saving:", font=("Roboto", 14, "bold"))
        lbl.pack(pady=(10, 5), padx=10, anchor="w")

        self.textbox = ctk.CTkTextbox(self, font=("Courier New", 12), wrap="none")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.textbox.insert("0.0", text_content)
        self.textbox.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_save = ctk.CTkButton(
            btn_frame, text="Confirm & Save", fg_color="#2E7D32", hover_color="#1B5E20", 
            command=self.on_save
        )
        self.btn_save.pack(side="right", padx=5)
        
        self.btn_cancel = ctk.CTkButton(
            btn_frame, text="Cancel", fg_color="#C62828", hover_color="#B71C1C", 
            command=self.on_cancel
        )
        self.btn_cancel.pack(side="right", padx=5)

    def on_save(self):
        """Sets the user choice flag to True and closes the dialog."""
        self.user_choice = True
        self.destroy()

    def on_cancel(self):
        """Sets the user choice flag to False and closes the dialog."""
        self.user_choice = False
        self.destroy()


class StateEditorDialog(ctk.CTkToplevel):
    """Dialog to edit a list of states (e.g., A | B | C) for a single table cell. Uses a horizontal tksheet to allow easy manipulation of individual states"""
    def __init__(self, parent, initial_value=""):
        super().__init__(parent)
        self.title("Edit States (List Mode)")
        self.geometry("600x250")
        self.transient(parent)
        self.grab_set()
        
        self.result = None

        syntax = mwo.get_syntax_config()
        self.state_sep = syntax.get("state_separator", "|")

        # Determine initial data structure for the sheet
        if self.state_sep in initial_value:
            data = [initial_value.split(self.state_sep)]
            data[0] = [x.strip() for x in data[0]] # Trim spaces
        elif initial_value.strip():
            data = [[initial_value]]
        else:
            data = [["", ""]] # Start with two empty columns

        # UI Elements
        lbl = ctk.CTkLabel(self, text="Define multiple states for this parameter:", font=("Roboto", 12))
        lbl.pack(pady=(10, 5))

        # Horizontal Sheet for States
        self.sheet_frame = ctk.CTkFrame(self)
        self.sheet_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.sheet = Sheet(
            self.sheet_frame,
            data=data,
            headers=[f"State {i+1}" for i in range(len(data[0]))],
            height=80
        )

        self.sheet.enable_bindings((
            "single_select", "row_select", "column_width_resize", 
            "arrowkeys", "edit_cell", "rc_insert_column", "rc_delete_column"
        ))
        self.sheet.pack(fill="both", expand=True)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.btn_add = ctk.CTkButton(btn_frame, text="+ Add State", width=100, command=self.add_column)
        self.btn_add.pack(side="left", padx=5)
        
        self.btn_ok = ctk.CTkButton(btn_frame, text="Confirm", fg_color="#2E7D32", width=100, command=self.on_ok)
        self.btn_ok.pack(side="right", padx=5)
        
        self.btn_cancel = ctk.CTkButton(btn_frame, text="Cancel", fg_color="#555555", width=80, command=self.destroy)
        self.btn_cancel.pack(side="right")

    def add_column(self):
        """Adds a new state column to the horizontal sheet."""
        # Force save of the current cell being edited
        if self.sheet.get_currently_selected():
             self.sheet.event_generate("<Return>")
             self.sheet.update()

        # Now it's safe to add the column
        self.sheet.insert_column()
        
        # Update headers
        cols = self.sheet.get_total_columns()
        self.sheet.headers([f"State {i+1}" for i in range(cols)])
        self.sheet.redraw()

    def on_ok(self):
        """Parses the sheet data, joins it using the separator, and closes."""
        # Simulate pressing "Enter" on the sheet to close active editor
        self.sheet.event_generate("<Return>")
        
        # Force the window to process that event immediately
        self.sheet.update()

        # Now it is safe to read the data
        row_data = self.sheet.get_row_data(0)
        clean_values = [str(x).strip() for x in row_data if str(x).strip()]
        self.result = f" {self.state_sep} ".join(clean_values)
        self.destroy()


class CommentDialog(ctk.CTkToplevel):
    """Dialog to enter multi-line comments that will be inserted as rows"""
    def __init__(self, parent, title="Add Comment"):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x300") 
        self.minsize(300, 200)
        
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        
        # Shortcuts
        self.bind("<Control-k>", lambda e: self.on_ok())
        
        # UI Elements
        label = ctk.CTkLabel(self, text="Enter your comment (Multiple lines allowed):")
        label.pack(pady=(10, 5), padx=10, anchor="w")

        self.text_box = ctk.CTkTextbox(self, wrap="word", font=("Roboto", 12))
        self.text_box.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.after(100, lambda: self.text_box.focus_force())
            
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.ok_btn = ctk.CTkButton(btn_frame, text="OK", command=self.on_ok)
        self.ok_btn.pack(side="right", padx=5)
        self.ok_btn.bind("<Enter>", lambda e: self.ok_btn.configure(text="OK (Ctrl+k)"))
        self.ok_btn.bind("<Leave>", lambda e: self.ok_btn.configure(text="OK"))
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", fg_color="#555555", command=self.destroy)
        cancel_btn.pack(side="right")
        
    def on_ok(self, event=None):
        """Saves the typed text to the result variable and closes."""
        self.result = self.text_box.get("1.0", "end-1c").strip()
        self.destroy()


# ==== MAIN WINDOW CLASS ====

class ParamFileEditorWindow(tk.Toplevel):
    """Main editor window for parameter files. Provides a spreadsheet-like interface with dynamic syntax validation, styling, and robust data manipulation"""
    def __init__(self, master):
        super().__init__(master)

        # Application State 
        self.current_file_path = None
        
        # Ensure Syntax Folder/Config Exists on Startup
        mwo.ensure_syntax_config_exists()

        # Window Configuration 
        self.title("New File")
        self.geometry("1100x600")
        self.minsize(600, 400)
        self.lift()
        self.focus_force()

        # Global Shortcuts
        self.bind_all("<Control-m>", lambda e: self.add_comment_row())
        self.bind_all("<Control-r>", lambda e: self.reset_cell_style())
        self.bind_all("<Control-s>", lambda e: self.save_file())

        # Base Layout Container
        self.container = ctk.CTkFrame(self, corner_radius=0)
        self.container.pack(fill="both", expand=True)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(2, weight=1) # Table expands in row 2 (tksheet)

        # Initialize UI Components
        self._setup_menu_bar()
        self._setup_header()
        self._setup_table()
        self._setup_footer()

    # ==== UI SETUP METHODS ====

    def _setup_menu_bar(self):
        """Sets up the top menu bar"""
        self.menu_bar = ctk.CTkFrame(self.container, corner_radius=0, height=30, fg_color=("gray85", "gray15"))
        self.menu_bar.grid(row=0, column=0, sticky="ew")

        def file_menu_callback(choice):
            # Reset text immediately so it acts like a menu button
            self.file_menu.set("File Options")
            # Trigger the correct function based on the choice
            if choice == "Open File":
                self.import_file()
            elif choice == "Save (Ctrl+s)":
                self.save_file()
            elif choice == "Save As...":
                self.save_as_file()

        # OptionMenu styled as a flat menu button
        self.file_menu = ctk.CTkOptionMenu(
            self.menu_bar, 
            values=["Open File", "Save (Ctrl+s)", "Save As..."],
            command=file_menu_callback,
            width=60,
            fg_color=("gray85", "gray15"),       
            button_color=("gray85", "gray15"),   
            text_color=("black", "white"),
            button_hover_color=("gray70", "gray30"),
            font=("Roboto", 14)
        )
        self.file_menu.set("File Options") # Default label
        self.file_menu.pack(side="left", padx=5, pady=2)

    def _setup_header(self):
        """Sets up the header area with title and hints"""
        self.header_frame = ctk.CTkFrame(self.container, corner_radius=0, fg_color=("gray85", "gray15"))
        self.header_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        
        self.active_model = mwo.get_active_model_name()
        
        self.title_lbl = ctk.CTkLabel(
            self.header_frame, text="New File", font=("Roboto", 20, "bold"), fg_color=("gray85", "gray15")
        )
        self.title_lbl.pack(pady=10)
        
        self.hint_lbl = ctk.CTkLabel(
            self.header_frame, text="Tip: Right-click to view shortcuts", font=("Roboto", 10), text_color="gray"
        )
        self.hint_lbl.pack(pady=(0, 5))

    def _setup_table(self):
        """Sets up the primary tksheet data table"""
        self.table_frame = ctk.CTkFrame(self.container)
        self.table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        
        self.headers_list = ["Parameter Name"] + [f"Value {i}" for i in range(1, 5)]
        
        self.sheet = Sheet(
            self.table_frame,
            data=[["" for _ in range(5)] for _ in range(30)], 
            headers=self.headers_list,
            horizontal_grid_color="#505050", 
            vertical_grid_color="#505050",
            edit_cell_bg="#FFFFFF",
            edit_cell_fg="#333333"
        ) 
        
        self.sheet.enable_bindings((
            "single_select", "drag_select", "row_select", "column_select", "column_width_resize", "row_height_resize",
            "arrowkeys", "right_click_popup_menu", "rc_select",
            "rc_insert_row", "rc_delete_row", "rc_insert_column", 
            "rc_delete_column", "copy", "cut", "paste", 
            "delete", "undo", "edit_cell"
        ))
        
        # Context Menu
        self.sheet.popup_menu_add_command("Add Comment (Ctrl+m)", self.add_comment_row)
        self.sheet.popup_menu_add_command("Edit States (List Mode)", self.open_state_editor)
        self.sheet.popup_menu_add_command("Reset Style (Ctrl+r)", self.reset_cell_style)

        # Extra bindings
        self.sheet.extra_bindings([
            ("end_edit_cell", self.on_cell_edit_event)
        ])

        self.sheet.pack(fill="both", expand=True)
        self.apply_colors()

    def _setup_footer(self):
        """Sets up the bottom toolbar with actions"""
        self.footer_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.footer_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)

        self.btn_close = ctk.CTkButton(self.footer_frame, text="Close", fg_color="#555555", command=self.destroy)
        self.btn_close.pack(side="right")

        # Buttons
        self.btn_comment = ctk.CTkButton(
            self.footer_frame, text="+ Add Comment", width=110, 
            fg_color="#2E7D32", hover_color="#1B5E20", command=self.add_comment_row
        )
        self.btn_comment.pack(side="left", padx=5)
        self.btn_comment.bind("<Enter>", lambda e: self.btn_comment.configure(text="Ctrl+M"))
        self.btn_comment.bind("<Leave>", lambda e: self.btn_comment.configure(text="+ Add Comment"))

        self.btn_reset = ctk.CTkButton(
            self.footer_frame, text="Reset Style", width=100, 
            fg_color="#2E7D32", hover_color="#1B5E20", command=self.reset_cell_style
        )
        self.btn_reset.pack(side="left", padx=5)
        self.btn_reset.bind("<Enter>", lambda e: self.btn_reset.configure(text="Ctrl+R"))
        self.btn_reset.bind("<Leave>", lambda e: self.btn_reset.configure(text="Reset Style"))

        self.btn_add_row = ctk.CTkButton(
            self.footer_frame, text="+ 10 Rows", width=80, 
            fg_color="#2E7D32", hover_color="#1B5E20", command=self.add_10_rows
        )
        self.btn_add_row.pack(side="left", padx=5)

        self.btn_add_col = ctk.CTkButton(
            self.footer_frame, text="+ 5 Cols", width=80, 
            fg_color="#2E7D32", hover_color="#1B5E20", command=self.add_5_columns
        )
        self.btn_add_col.pack(side="left", padx=5)

    # ==== UI HELPERS & VALIDATION ====
    
    def apply_colors(self):
        """Applies the default green/blue column coloring"""
        try:
            total_cols = self.sheet.get_total_columns()
            self.sheet.highlight_columns(columns=[0], bg=None, fg="#2E7D32")
            if total_cols > 1:
                blue_cols = list(range(1, total_cols))
                self.sheet.highlight_columns(columns=blue_cols, bg=None, fg="#1565C0")
            self.sheet.redraw()
        except Exception: 
            pass

    def on_cell_edit_event(self, event=None):
        """Triggered when a cell edit finishes. Delegates to validation"""
        try:
            r, c = event[0], event[1] # row, column
            # Delay check to ensure value is fully committed to the cell
            self.after(50, lambda: self.validate_and_color_cell(r, c))
        except Exception: 
            pass

    def validate_and_color_cell(self, r, c):
        """Applies dynamic coloring logic based on cell content (List, Comment, Normal Value)"""
        try:
            value = str(self.sheet.get_cell_data(r, c)).strip()

            # Reset Highlight
            self.sheet.dehighlight_cells(row=r, column=c)
            
            # Check for Comment or Standard
            if value.startswith("#"):
                self.sheet.highlight_cells(row=r, column=c, bg="white", fg="#808080")
            else:
                default_fg = "#2E7D32" if c == 0 else "#1565C0"
                self.sheet.highlight_cells(row=r, column=c, bg="white", fg=default_fg)
            self.sheet.redraw()
        except Exception: 
            pass

    # ==== USER ACTIONS (DIALOG TRIGGERS & FORMATTING) ====

    def add_comment_row(self, event=None):
        """Opens dialog to add a full-width comment row at the current cursor"""
        try:
            dialog = CommentDialog(self, "Add Comment")
            self.wait_window(dialog) 
            raw_text = dialog.result
            
            if not raw_text: 
                return 
                
            lines = raw_text.split('\n')
            selection = self.sheet.get_currently_selected()
            
            if selection: 
                start_r = selection[0] 
            else: 
                return
                
            current_r = start_r
            for line in lines:
                stripped_line = line.strip()
                if not stripped_line:
                    formatted_text = ""
                else:
                    formatted_text = f"### {stripped_line} ###"
                self.sheet.insert_row(idx=current_r) 
                self.sheet.set_cell_data(current_r, 0, formatted_text) #current row, column 0
                self.sheet.highlight_cells(row=current_r, column=0, bg="white", fg="#808080")
                current_r += 1
            self.sheet.redraw()
        except Exception as e:
            messagebox.showerror("Error", f"Could not add comment: {e}", parent=self)

    def open_state_editor(self):
        """Opens dialog to edit list values (e.g., A | B | C) for a selected cell"""
        # Get raw selection (returns a SET)
        selection_set = self.sheet.get_selected_cells()
        
        if not selection_set:
            messagebox.showinfo("Info", "Please select a cell first.", parent=self)
            return
        
        # Convert Set to List to access the first item
        selection_list = list(selection_set)
        r, c = selection_list[0]
        
        current_val = str(self.sheet.get_cell_data(r, c))
        
        # Open Dialog
        dialog = StateEditorDialog(self, initial_value=current_val)
        self.wait_window(dialog)
        
        if dialog.result is not None:
            # Update cell and highlight Blue to indicate a list
            self.sheet.set_cell_data(r, c, dialog.result)
            self.sheet.highlight_cells(row=r, column=c, bg="white", fg="#0277BD")
            self.sheet.redraw()

    def reset_cell_style(self, event=None):
        """Resets currently selected cells to their default base colors"""
        try:
            selection = self.sheet.get_selected_cells()
            if not selection: return
            
            for r, c in selection:
                self.sheet.dehighlight_cells(row=r, column=c)
                default_fg = "#2E7D32" if c == 0 else "#1565C0"
                self.sheet.highlight_cells(row=r, column=c, bg="white", fg=default_fg)
            self.sheet.redraw()
        except Exception: 
            pass

    # ==== TABLE MODIFICATIONS (ROWS & COLUMNS) ====

    def add_10_rows(self):
        """Appends 10 blank rows to the bottom of the sheet"""
        for _ in range(10):
            self.sheet.insert_row()
        self.sheet.redraw()

    def add_5_columns(self):
        """Appends 5 new columns and recalculates headers/colors"""
        num_columns = 5
        for _ in range(num_columns):
            self.sheet.insert_column() 
            
        new_total_cols = self.sheet.get_total_columns()
        new_headers_list = ["Parameter Name"] + [f"Value {i}" for i in range(1, new_total_cols)]
        self.sheet.headers(new_headers_list)
        self.apply_colors()

    # ==== DATA OPERATIONS & EXPORT ====

    def get_clean_data(self):
        """Returns all sheet data, omitting any entirely empty rows"""
        raw_data = self.sheet.get_sheet_data()
        clean_data = []
        for row in raw_data:
            if any(cell.strip() for cell in row): # check if data
                clean_data.append(row)
        return clean_data

    def import_file(self):
        """Loads data into the sheet using the active syntax configuration"""
        try:
            config = mwo.load_config()
            default_dir = config.get("default_input_dir", os.getcwd())
        except AttributeError:
            default_dir = os.getcwd()

        file_path = filedialog.askopenfilename(
            parent=self, 
            title="Open Parameter File", 
            initialdir=default_dir,
            filetypes=(("All Files", "*.*"), ("CSV Files", "*.csv"), ("Text Files", "*.txt"))
        )
        
        if not file_path:
            return

        self.current_file_path = file_path

        # Load Active Syntax
        syntax = mwo.get_syntax_config()
        SEP = syntax.get("separator", ";")
        L_START = syntax.get("list_start", "{")
        L_END = syntax.get("list_end", "}")
        LIST_SEP = syntax.get("list_separator", ",") 

        new_data = []
        max_cols = 5 

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()

            for line in all_lines:
                line = line.strip()
                if not line: continue
                
                if line.startswith("#"):
                    new_data.append([line])
                    continue
                
                parts = line.split(SEP, 1) # only split by SEP once
                key = parts[0].strip()
                row_items = [key]
                
                if len(parts) > 1:
                    raw_values = parts[1].strip()
                    
                    if raw_values.startswith(L_START) and raw_values.endswith(L_END):
                        raw_values = raw_values[len(L_START):-len(L_END)]
                    
                    if raw_values:
                        val_list = [v.strip() for v in raw_values.split(LIST_SEP)]
                        row_items.extend(val_list)
                
                if len(row_items) > max_cols:
                    max_cols = len(row_items)
                    
                new_data.append(row_items)
            
            current_headers = ["Parameter Name"] + [f"Value {i}" for i in range(1, max_cols)]
            self.sheet.headers(current_headers)
            self.sheet.set_sheet_data(new_data)
            
            # call validate_and_color_cell function instead of apply_colors to avoid coloring comments with green
            for r, row in enumerate(new_data):
                for c, _ in enumerate(row):
                    self.validate_and_color_cell(r, c)
            
            self.title_lbl.configure(text=os.path.splitext(os.path.basename(file_path))[0])
            self.title(os.path.splitext(os.path.basename(file_path))[0])
            messagebox.showinfo("Success", "File loaded successfully.", parent=self)

        except Exception as e:
            messagebox.showerror("Import Error", f"Could not read the file:\n{e}", parent=self)

    def _save_input_file(self, filepath, data):
        """Saves table data into a custom CSV or TXT format"""
        try:
            with open(filepath, mode='w', encoding='utf-8') as file:
                file.write(data)

        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save the file:\n{e}")

    def save_as_file(self):
        """Shows a preview dialog, and prompts for Save As"""
        # Force the main table to commit the current edit
        self.sheet.event_generate("<Return>")
        self.sheet.update()
        
        data = self.get_clean_data()
        if not data:
            messagebox.showwarning("Empty Table", "There is no data to save.", parent=self)
            return
        
        # Generate Preview String
        processed_text = self.add_syntax_to_file(data)

        # Show Preview Dialog
        dialog = PreviewDialog(self, processed_text, "Preview Input File")
        self.wait_window(dialog)

        if not dialog.user_choice:
            return 

        # Save File via User Prompt
        try:
            config = mwo.load_config()
            default_dir = config.get("default_input_dir", os.getcwd())
        except AttributeError:
            default_dir = os.getcwd()
            
        file_path = filedialog.asksaveasfilename(
            parent=self, title="Save File", initialdir=default_dir, defaultextension=".csv", 
            filetypes=(("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        
        if file_path:
            self.current_file_path = file_path
            self.title_lbl.configure(text=os.path.splitext(os.path.basename(self.current_file_path))[0])
            self.title(os.path.splitext(os.path.basename(file_path))[0])

            self._save_input_file(file_path, processed_text)
            
            ext = os.path.splitext(file_path)[1].upper().replace(".", "")
            messagebox.showinfo("Success", f"{ext} file saved successfully.", parent=self)

    def save_file(self, event=None):
        """Save (Ctrl+S) behavior"""
        # Force commit of current edit in the sheet
        self.sheet.event_generate("<Return>")
        self.sheet.update()

        if self.current_file_path:
            # Path exists, save directly
            data = self.get_clean_data()
            if not data:
                messagebox.showwarning("Empty Table", "There is no data to save.", parent=self)
                return

            try:
                processed_text = self.add_syntax_to_file(data)
                self._save_input_file(self.current_file_path, processed_text)
                messagebox.showinfo(
                    "Saved", f"File saved successfully!\n{os.path.basename(self.current_file_path)}", parent=self
                )
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save file:\n{e}", parent=self)
        else:
            # No file path known -> Trigger Save As flow
            self.save_as_file()
    
    def add_syntax_to_file(self, data):
        '''Formats the data using the current syntax config'''
        # Load Active Syntax
        syntax = mwo.get_syntax_config()
        SEP = syntax.get("separator", ";")
        L_START = syntax.get("list_start", "{")
        L_END = syntax.get("list_end", "}")
        LIST_SEP = syntax.get("list_separator", ",")

        processed_lines = []
        
        for row in data:
            if not row or not any(row): continue # any(row) to avoid process ["", "", ""]
            
            key = str(row[0]).strip()
            
            if key.startswith("#"):
                processed_lines.append(key)
            else:
                # Syntax-Aware Key{SEP}{Values} formatting
                values = [str(x).strip() for x in row[1:] if str(x).strip()]
                joined_values = LIST_SEP.join(values) 
                
                # Apply Dynamic Brackets
                if not joined_values.startswith(L_START) or not joined_values.endswith(L_END):
                    final_value = f"{L_START}{joined_values}{L_END}"
                else:
                    final_value = joined_values
                
                # Apply Dynamic Separator
                processed_lines.append(f"{key}{SEP}{final_value}")
        
        return "\n".join(processed_lines)
                