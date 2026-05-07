import os
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import main_window_operations as mwo

# ==== MAIN APPLICATION CLASS ====

class ProcessedFileViewer(ctk.CTkFrame):
    """A text viewer to open processed files"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, **kwargs)
        
        # Application State 
        self.filepath = None

        self.show_line_numbers = tk.BooleanVar(value=False)

        ctk.set_appearance_mode("light")

        # Initialize UI Components
        self._setup_menu_bar()
        self._setup_editor_area()
        self._setup_toolbar()

        self._bind_events()

        self.after(100, self.editor.focus_set)

    # ==== UI SETUP METHODS ====

    def _setup_menu_bar(self):
        """Sets up the top menu bar and its options"""
        self.title_lbl = ctk.CTkLabel(self, text="Press: Open Processed File")
        self.title_lbl.pack(pady=(20, 0)) 

    def _setup_editor_area(self):
        """Sets up the main text editing area"""
        self.editor_container = ctk.CTkFrame(self, fg_color="transparent")
        self.editor_container.pack(side="top", fill="both", expand=True, padx=20, pady=(20, 20))

        self.line_numbers = tk.Canvas(self.editor_container, width=40, bg="#1e1e1e", bd=0, highlightthickness=0) # bd (borderwidth=0), highlightthickness=0 to hide the line between the number of the line and the text

        self.editor = ctk.CTkTextbox(
            self.editor_container, font=("Consolas", 15), wrap="none", undo=True,
            fg_color="#1e1e1e", text_color="#D4D4D4", corner_radius=0, state="disabled"
        ) # wrap="none" disable line wrapping (prevent the automatic break line)
        self.editor.pack(side="left", fill="both", expand=True)

    def _setup_toolbar(self):
        """Sets up the bottom toolbar containing shortcut buttons"""
        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        btn_font = ("Arial", 12)
        btn_width = 120
        btn_height = 28

        self.chk_line_numbers = ctk.CTkCheckBox(
            self.toolbar, text="Line Numbers", variable=self.show_line_numbers, 
            command=self.toggle_line_numbers, font=("Arial", 12, "bold"),
            width=130 
        )
        self.chk_line_numbers.pack(side="left", padx=(5, 5))

        self.btn_close = ctk.CTkButton(self.toolbar, text="Close", fg_color="#555555", hover_color="#333333", command=self.winfo_toplevel().destroy)
        self.btn_close.pack(side="right")

        self.btn_open_out_file = ctk.CTkButton(self.toolbar, text="Open Processed File", width=btn_width, height=btn_height, font=btn_font, fg_color="#2E7D32", hover_color="#1B5E20", command=self.open_output_file)
        self.btn_open_out_file.pack(side="right", padx=(0, 5))

        self.btn_refresh_out_file = ctk.CTkButton(self.toolbar, text="Refresh Processed File", width=btn_width, height=btn_height, font=btn_font, fg_color="#2E7D32", hover_color="#1B5E20", command=lambda: self._open_output_file(manual_refresh=True))
        self.btn_refresh_out_file.pack(side="right", padx=(5, 5))

    def _bind_events(self):
        """Binds all mouse and keyboard events to the text editor"""
        self.editor._textbox.bind("<Control-r>", lambda e: self._open_output_file(manual_refresh=True))
        self.editor._textbox.bind("<Control-R>", lambda e: self._open_output_file(manual_refresh=True))
        
        self.editor._textbox.bind("<MouseWheel>", lambda e: self.after(10, self.redraw_line_numbers), add="+")
        self.editor._textbox.bind("<B1-Motion>", lambda e: self.after(10, self.redraw_line_numbers), add="+")
        self.editor._textbox.bind("<Configure>", lambda e: self.redraw_line_numbers(), add="+")
        
        self.editor._textbox.bind("<KeyRelease>", lambda e: self.after(10, self.redraw_line_numbers), add="+")

        original_command = self.editor._textbox.cget("yscrollcommand")
        
        def intercepted_scroll(*args):
            if original_command:
                self.editor._textbox.tk.call(original_command, *args)
            
            self.redraw_line_numbers()

        self.editor._textbox.configure(yscrollcommand=intercepted_scroll)
    
    # ==== FILE OPERATIONS ====
   
    def _open_output_file(self, event=None, manual_refresh=False):
        if (manual_refresh and not self.filepath):
            messagebox.showerror("Error", f"Open a processed file first\n", parent=self)
            return
        elif not self.filepath:
            return

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            self.editor.configure(state="normal")
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", content)
            self.editor.configure(state="disabled")

            self.title_lbl.configure(text=os.path.splitext(os.path.basename(self.filepath))[0], font=("Segoe UI", 18, "bold"))
            self.master.title(os.path.splitext(os.path.basename(self.filepath))[0])

            if manual_refresh:
                messagebox.showinfo("Refreshed", "Refreshed successfully!", parent=self)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open the processed file:\n{e}", parent=self)

    def open_output_file(self):
        try:
            config = mwo.load_config()
            output_dir = config.get("default_output_dir", os.getcwd())
        except Exception:
            output_dir = os.getcwd()

        self.filepath = filedialog.askopenfilename(
            parent=self,
            title="Open rendered file",
            initialdir=output_dir,
            filetypes=(("All files", "*.*"),)
        )
        self._open_output_file()

    # ==== MANAGE LINE NUMBER DISPLAY ====

    def redraw_line_numbers(self, event=None):
        """Calculates visible lines and draws the numbers on the margin canvas"""
        if not self.show_line_numbers.get():
            return
            
        self.line_numbers.delete("all")
        
        i = self.editor._textbox.index("@0,0")
        while True:
            dline = self.editor._textbox.dlineinfo(i)
            if dline is None:
                break 
            
            y = dline[1]
            actual_y = y + 2 
            linenum = str(i).split(".")[0]
            
            self.line_numbers.create_text(35, actual_y, anchor="ne", text=linenum, font=("Consolas", 12), fill="#858585")
            
            i = self.editor._textbox.index(f"{i}+1line")

    def toggle_line_numbers(self):
        """Shows or hides the line numbers canvas based on the checkbox"""
        if self.show_line_numbers.get():
            self.line_numbers.pack(side="left", fill="y", before=self.editor)
            self.redraw_line_numbers()
        else:
            self.line_numbers.pack_forget()