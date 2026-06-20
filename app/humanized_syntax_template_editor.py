import os
import re

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pygments import lex, lexers

from jinja2 import StrictUndefined, Environment, FileSystemLoader

from textx import metamodel_from_file
import xml.etree.ElementTree as ET

import main_window_operations as mwo
from template_editor import TemplateEditor, extract_variables_from_file, TOKEN_COLORS

# ==== MAIN APPLICATION CLASS ====

class HumanizedSyntaxTemplateEditor(TemplateEditor):
    def __init__(self, master, parameters_filepath, **kwargs):
        super().__init__(master, parameters_filepath, **kwargs)
        # parameters loaded from parameters_file_name
        self.parameters_filepath = parameters_filepath
        # initialize process class (contains process methods)
        self.humanized_syntax_process_features_class = HumanizedSyntaxProcessFeatures(self.parameters_filepath, self.current_template_path)

    # ==== UI SETUP METHODS ====

    def _setup_menu_bar(self):
        """Sets up the top menu bar and its options"""
        self.menu_bar = ctk.CTkFrame(self, corner_radius=0, height=30, fg_color=("gray85", "gray15"))
        self.menu_bar.pack(side="top", fill="x")

        def file_menu_callback(choice):
            self.file_menu.set("File Options")
            if choice == "Load Parameters":
                self.open_parameter_file(humanized_syntax=True)
            elif choice == "Open Template":
                self.open_humanized_syntax_template()
            elif choice == "Save (Ctrl+S)":
                self.save_humanized_syntax_template()
            elif choice == "Save as...":
                self.save_as_humanized_syntax_template()

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
        self.title_lbl.pack(pady=(10, 0))  # 10px top padding, 0px bottom padding to group them

        if self.parameters_filepath:
            self.params_lbl = ctk.CTkLabel(self, text=f"Parameters loaded from: {os.path.splitext(os.path.basename(self.parameters_filepath))[0]}", 
                                       font=("Arial", 12), text_color="#2B2827")
        else:
            self.params_lbl = ctk.CTkLabel(self, text=f"Parameters not loaded", 
                                       font=("Arial", 12), text_color="#2B2827")
        self.params_lbl.pack(pady=(0, 10)) # 0px top padding, 10px bottom padding

    def _setup_toolbar(self):
        super()._setup_toolbar()

        def run_humanized_syntax_shortcut(selected_option):
            if selected_option in humanized_syntax_shortcuts:
                self.display_instruction_guide(selected_option, humanized_syntax_shortcuts)
            self.humanized_syntax_menu.set("Humanized Syntax Shortcuts")

        btn_font = ("Arial", 12, "bold")
        btn_height = 28

        self.btn_refresh.configure(command=lambda: self.refresh_variables(return_dict_variable_value=True))

        self.btn_process = ctk.CTkButton(self.toolbar, text="Process Syntax", width=130, height=btn_height, font=btn_font, fg_color="#2E7D32", hover_color="#1B5E20", command=self.save_and_process_humanized_syntax_template)
        self.btn_process.pack(side="right", padx=(5, 5))

        humanized_syntax_shortcuts = ["Add Comment Instruction", "Add Set Instruction", "Add Send Instruction", "Add Chk Sp Eq Instruction", "Add Chk Wt Eq Instruction", "Add End Cycle Instruction", "Add Traceability Instruction", "Add Framing 1553 Instruction", "Add Suspend Instruction"]
        self.humanized_syntax_menu = ctk.CTkOptionMenu(
            self.toolbar,
            values=humanized_syntax_shortcuts,
            command=run_humanized_syntax_shortcut
        )
        self.humanized_syntax_menu.set("Humanized Syntax Shortcuts")
        self.humanized_syntax_menu.pack(side="left", padx=10)

        self.chk_line_numbers.pack(side="left", padx=(5, 5), after=self.humanized_syntax_menu)

    def _setup_context_menu(self):
        # Create the Menu object (tearoff=0 hide the line at the top of the menu)
        self.context_menu = tk.Menu(self.editor._textbox, tearoff=0)
        
        # Add standard options
        self.context_menu.add_command(label="Add Variable (Ctrl+D)", command=self.insert_variable_brackets)
        self.context_menu.add_command(label="Add Code (Ctrl+T)", command=self.insert_code_brackets)
        self.context_menu.add_command(label="Add For (Ctrl+L)", command=self.insert_for_loop)
        self.context_menu.add_command(label="Add Comment (Ctrl+M)", command=self.insert_comment)
        self.context_menu.add_command(label="Refresh Parameters (Ctrl+R)", command=lambda: self.refresh_variables(return_dict_variable_value=True))

        self.context_menu.add_separator()

        self.context_menu.add_command(label="Load Parameters", command=lambda: self.open_parameter_file(humanized_syntax=True))
        self.context_menu.add_command(label="Open Template", command=self.open_humanized_syntax_template)
        self.context_menu.add_command(label="Save (Ctrl+S)", command=self.save_humanized_syntax_template)
        self.context_menu.add_command(label="Save as...", command=self.save_as_humanized_syntax_template)

        # Bind the Right Click event
        self.editor._textbox.bind("<Button-3>", self._show_menu)

    def _bind_events(self):
        super()._bind_events()
        self.editor._textbox.bind("<Control-s>", self.save_humanized_syntax_template)
        self.editor._textbox.bind("<Control-S>", self.save_humanized_syntax_template)
        self.editor._textbox.bind("<Control-p>", self.save_and_process_humanized_syntax_template)
        self.editor._textbox.bind("<Control-P>", self.save_and_process_humanized_syntax_template)

    def display_instruction_guide(self, selected_option, humanized_syntax_shortcuts):
        """Displays instruction shortcuts to assist users """
        # COMMENT INSTRUCTION
        if selected_option == humanized_syntax_shortcuts[0]:
            line = "// Replace_your_COMMENT_here\n"
            self.editor._textbox.insert("insert", line)
            self.redraw_line_numbers()
        # SET INSTRUCTION
        elif selected_option == humanized_syntax_shortcuts[1]:
            self._display_SET_or_CHK_window("SET")
        # SEND INSTRUCTION
        elif selected_option == humanized_syntax_shortcuts[2]:
            self._display_SEND_window()
        # CHK_SP_EQ INSTRUCTION
        elif selected_option == humanized_syntax_shortcuts[3]:
            self._display_SET_or_CHK_window("CHK_SP_EQ")
        # CHK_WT_EQ INSTRUCTION
        elif selected_option == humanized_syntax_shortcuts[4]:
            self._display_SET_or_CHK_window("CHK_WT_EQ")
        # END_CYCLE INSTRUCTION
        elif selected_option == humanized_syntax_shortcuts[5]:
            line = "END_CYCLE\n"
            self.editor._textbox.insert("insert", line)
            self.redraw_line_numbers()
        # TRACEABILITY INSTRUCTION
        elif selected_option == humanized_syntax_shortcuts[6]:
            self._display_TRAC_window()
        # FRAMING_1553 INSTRUCTION
        elif selected_option == humanized_syntax_shortcuts[7]:
            self._display_FRAMING_1553_window()
        # SUSPEND INSTRUCTION
        elif selected_option == humanized_syntax_shortcuts[8]:
            self._display_SUSPEND_window()

    def _display_SET_or_CHK_window(self, instruction):
        """Display instruction forms to assist the user with the humanized syntax"""
        help_instructions_window, help_instructions_frame = self.create_help_instruction_window_and_frame(instruction)

        # SHORT FORM
        short_form_label = ctk.CTkLabel(help_instructions_frame, text="Short Form:", font=ctk.CTkFont(size=12, weight="bold"), width=70)
        short_form_label.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=15)

        short_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        short_middle_frame.grid(row=0, column=1, sticky="w", padx=0, pady=15)

        if (instruction == "CHK_SP_EQ") or (instruction == "CHK_WT_EQ"):
            short_form_lbl0 = ctk.CTkLabel(short_middle_frame, text="VER: ")
            short_form_lbl0.pack(side="left", padx=(0, 5))

        short_form_signal_name_entry = ctk.CTkEntry(short_middle_frame, placeholder_text="Signal Name", width=350)
        short_form_signal_name_entry.pack(side="left", padx=(0, 5))

        short_form_lbl1 = ctk.CTkLabel(short_middle_frame, text=" = ")
        short_form_lbl1.pack(side="left", padx=(0, 5))

        short_form_signal_value_entry = ctk.CTkEntry(short_middle_frame, placeholder_text="Value", width=200)
        short_form_signal_value_entry.pack(side="left", padx=(0, 5))
        if (instruction == "CHK_WT_EQ"):
            short_form_lbl2 = ctk.CTkLabel(short_middle_frame, text=" (Timeout=")
            short_form_lbl2.pack(side="left", padx=(0, 5))

            short_form_timeout_value_entry = ctk.CTkEntry(short_middle_frame, placeholder_text="ms", width=100)
            short_form_timeout_value_entry.pack(side="left", padx=(0, 5))

            short_form_lbl3 = ctk.CTkLabel(short_middle_frame, text=")")
            short_form_lbl3.pack(side="left", padx=(0, 5))

            short_form_button = ctk.CTkButton(help_instructions_frame, text="Use Short Form", width=100, command=lambda: self.write_SET_or_CHK_instruction(short_form_signal_name_entry.get(), short_form_signal_value_entry.get(), help_instructions_window, instruction, "Short Form", timeout=short_form_timeout_value_entry.get()))
            short_form_button.grid(row=0, column=2, sticky="e", padx=(10, 20), pady=15)
        else:
            short_form_button = ctk.CTkButton(help_instructions_frame, text="Use Short Form", width=100, command=lambda: self.write_SET_or_CHK_instruction(short_form_signal_name_entry.get(), short_form_signal_value_entry.get(), help_instructions_window, instruction, "Short Form"))
            short_form_button.grid(row=0, column=2, sticky="e", padx=(10, 20), pady=15)

        # EXTENDED FORM
        extended_form_label = ctk.CTkLabel(help_instructions_frame, text="Extended Form:", font=ctk.CTkFont(size=12, weight="bold"), width=70)
        extended_form_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=15)

        extended_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        extended_middle_frame.grid(row=1, column=1, sticky="w", padx=0, pady=15)

        if (instruction == "CHK_SP_EQ") or (instruction == "CHK_WT_EQ"):
            extended_form_lbl0 = ctk.CTkLabel(extended_middle_frame, text="VER: ")
            extended_form_lbl0.pack(side="left", padx=(0, 5))

        extended_form_equipment_name_entry = ctk.CTkEntry(extended_middle_frame, placeholder_text="Equipment Name", width=100)
        extended_form_equipment_name_entry.pack(side="left", padx=(0, 5))

        extended_form_lbl1 = ctk.CTkLabel(extended_middle_frame, text=".")
        extended_form_lbl1.pack(side="left", padx=(0, 5))

        extended_form_module_name_entry = ctk.CTkEntry(extended_middle_frame, placeholder_text="Module Name", width=130)
        extended_form_module_name_entry.pack(side="left", padx=(0, 5))

        extended_form_lbl2 = ctk.CTkLabel(extended_middle_frame, text=".")
        extended_form_lbl2.pack(side="left", padx=(0, 5))

        extended_form_partition_name_entry = ctk.CTkEntry(extended_middle_frame, placeholder_text="Partition Name", width=150)
        extended_form_partition_name_entry.pack(side="left", padx=(0, 5))

        extended_form_lbl3 = ctk.CTkLabel(extended_middle_frame, text=".")
        extended_form_lbl3.pack(side="left", padx=(0, 5))

        extended_form_message_name_entry = ctk.CTkEntry(extended_middle_frame, placeholder_text="Message Name", width=150)
        extended_form_message_name_entry.pack(side="left", padx=(0, 5))

        extended_form_lbl4 = ctk.CTkLabel(extended_middle_frame, text=".")
        extended_form_lbl4.pack(side="left", padx=(0, 5))

        extended_form_level_name_entry = ctk.CTkEntry(extended_middle_frame, placeholder_text="(Level Name)", width=100)
        extended_form_level_name_entry.pack(side="left", padx=(0, 5))

        extended_form_lbl8 = ctk.CTkLabel(extended_middle_frame, text=".")
        extended_form_lbl8.pack(side="left", padx=(0, 5))

        extended_form_signal_name_entry = ctk.CTkEntry(extended_middle_frame, placeholder_text="Signal Name", width=250)
        extended_form_signal_name_entry.pack(side="left", padx=(0, 5))

        extended_form_lbl5 = ctk.CTkLabel(extended_middle_frame, text=" = ")
        extended_form_lbl5.pack(side="left", padx=(0, 5))

        extended_form_signal_value_entry = ctk.CTkEntry(extended_middle_frame, placeholder_text="Value", width=100)
        extended_form_signal_value_entry.pack(side="left", padx=(0, 5))

        if (instruction == "CHK_WT_EQ"):
            extended_form_lbl6 = ctk.CTkLabel(extended_middle_frame, text=" (Timeout=")
            extended_form_lbl6.pack(side="left", padx=(0, 5))

            extended_form_timeout_value_entry = ctk.CTkEntry(extended_middle_frame, placeholder_text="ms", width=60)
            extended_form_timeout_value_entry.pack(side="left", padx=(0, 5))

            extended_form_lbl7 = ctk.CTkLabel(extended_middle_frame, text=")")
            extended_form_lbl7.pack(side="left", padx=(0, 5))

            extended_form_button = ctk.CTkButton(help_instructions_frame, text="Use Extended Form", width=100, command=lambda: self.write_SET_or_CHK_instruction(extended_form_signal_name_entry.get(), extended_form_signal_value_entry.get(), help_instructions_window, instruction, "Extended Form", equipment_name=extended_form_equipment_name_entry.get(), module_name=extended_form_module_name_entry.get(), partition_name=extended_form_partition_name_entry.get(), message_name=extended_form_message_name_entry.get(), level_name=extended_form_level_name_entry.get(), timeout=extended_form_timeout_value_entry.get()))
            extended_form_button.grid(row=1, column=2, sticky="e", padx=(10, 20), pady=15)
        else:
            extended_form_button = ctk.CTkButton(help_instructions_frame, text="Use Extended Form", width=100, command=lambda: self.write_SET_or_CHK_instruction(extended_form_signal_name_entry.get(), extended_form_signal_value_entry.get(), help_instructions_window, instruction, "Extended Form", equipment_name=extended_form_equipment_name_entry.get(), module_name=extended_form_module_name_entry.get(), partition_name=extended_form_partition_name_entry.get(), message_name=extended_form_message_name_entry.get(), level_name=extended_form_level_name_entry.get()))
            extended_form_button.grid(row=1, column=2, sticky="e", padx=(10, 20), pady=15)

        # FULL FORM
        full_form_label = ctk.CTkLabel(help_instructions_frame, text="Full Form:", font=ctk.CTkFont(size=12, weight="bold"), width=70)
        full_form_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=15)

        full_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        full_middle_frame.grid(row=2, column=1, sticky="w", padx=0, pady=15)

        if (instruction == "CHK_SP_EQ") or (instruction == "CHK_WT_EQ"):
            full_form_lbl0 = ctk.CTkLabel(full_middle_frame, text="VER: ")
            full_form_lbl0.pack(side="left", padx=(0, 5))

        full_form_equipment_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Equipment Name", width=100)
        full_form_equipment_name_entry.pack(side="left", padx=(0, 5))

        full_form_lbl1 = ctk.CTkLabel(full_middle_frame, text=".")
        full_form_lbl1.pack(side="left", padx=(0, 5))

        full_form_module_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Module Name", width=120)
        full_form_module_name_entry.pack(side="left", padx=(0, 5))

        full_form_lbl2 = ctk.CTkLabel(full_middle_frame, text=".")
        full_form_lbl2.pack(side="left", padx=(0, 5))

        full_form_partition_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Partition Name", width=130)
        full_form_partition_name_entry.pack(side="left", padx=(0, 5))

        full_form_lbl3 = ctk.CTkLabel(full_middle_frame, text=".")
        full_form_lbl3.pack(side="left", padx=(0, 5))

        full_form_message_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Message Name", width=150)
        full_form_message_name_entry.pack(side="left", padx=(0, 5))

        full_form_lbl4 = ctk.CTkLabel(full_middle_frame, text=".")
        full_form_lbl4.pack(side="left", padx=(0, 5))

        full_form_level_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="(Level Name)", width=100)
        full_form_level_name_entry.pack(side="left", padx=(0, 5))

        full_form_lbl9 = ctk.CTkLabel(full_middle_frame, text=".")
        full_form_lbl9.pack(side="left", padx=(0, 5))

        full_form_signal_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Signal Name", width=180)
        full_form_signal_name_entry.pack(side="left", padx=(0, 5))

        full_form_lbl5 = ctk.CTkLabel(full_middle_frame, text=".")
        full_form_lbl5.pack(side="left", padx=(0, 5))

        full_form_signal_type_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Signal Type", width=100)
        full_form_signal_type_entry.pack(side="left", padx=(0, 5))

        full_form_lbl6 = ctk.CTkLabel(full_middle_frame, text=" = ")
        full_form_lbl6.pack(side="left", padx=(0, 5))

        full_form_signal_value_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Value", width=100)
        full_form_signal_value_entry.pack(side="left", padx=(0, 5))

        if (instruction == "CHK_WT_EQ"):
            full_form_lbl7 = ctk.CTkLabel(full_middle_frame, text=" (Timeout=")
            full_form_lbl7.pack(side="left", padx=(0, 5))

            full_form_timeout_value_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="ms", width=60)
            full_form_timeout_value_entry.pack(side="left", padx=(0, 5))

            full_form_lbl8 = ctk.CTkLabel(full_middle_frame, text=")")
            full_form_lbl8.pack(side="left", padx=(0, 5))

            full_form_button = ctk.CTkButton(help_instructions_frame, text="Use Full Form", width=100, command=lambda: self.write_SET_or_CHK_instruction(full_form_signal_name_entry.get(), full_form_signal_value_entry.get(), help_instructions_window, instruction, "Full Form", equipment_name=full_form_equipment_name_entry.get(), module_name=full_form_module_name_entry.get(), partition_name=full_form_partition_name_entry.get(), message_name=full_form_message_name_entry.get(), level_name=full_form_level_name_entry.get(), signal_type=full_form_signal_type_entry.get(), timeout=full_form_timeout_value_entry.get()))
            full_form_button.grid(row=2, column=2, sticky="e", padx=(10, 20), pady=15)
        else:
            full_form_button = ctk.CTkButton(help_instructions_frame, text="Use Full Form", width=100, command=lambda: self.write_SET_or_CHK_instruction(full_form_signal_name_entry.get(), full_form_signal_value_entry.get(), help_instructions_window, instruction, "Full Form", equipment_name=full_form_equipment_name_entry.get(), module_name=full_form_module_name_entry.get(), partition_name=full_form_partition_name_entry.get(), message_name=full_form_message_name_entry.get(), level_name=full_form_level_name_entry.get(), signal_type=full_form_signal_type_entry.get()))
            full_form_button.grid(row=2, column=2, sticky="e", padx=(10, 20), pady=15)

    def _display_SEND_window(self):
        """Display instruction forms to assist the user with the humanized syntax"""
        help_instructions_window, help_instructions_frame = self.create_help_instruction_window_and_frame("SEND")

        # SHORT FORM
        short_form_label = ctk.CTkLabel(help_instructions_frame, text="Short Form:", font=ctk.CTkFont(size=12, weight="bold"), width=70)
        short_form_label.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=15)

        short_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        short_middle_frame.grid(row=0, column=1, sticky="w", padx=0, pady=15)

        short_form_lbl0 = ctk.CTkLabel(short_middle_frame, text="SEND: ")
        short_form_lbl0.pack(side="left", padx=(0, 5))

        short_form_message_name_entry = ctk.CTkEntry(short_middle_frame, placeholder_text="Message Name", width=350)
        short_form_message_name_entry.pack(side="left", padx=(0, 5))

        short_form_button = ctk.CTkButton(help_instructions_frame, text="Use Short Form", width=100, command=lambda: self.write_SEND_or_SUSPEND_instruction(short_form_message_name_entry.get(), help_instructions_window, "Short Form"))
        short_form_button.grid(row=0, column=2, sticky="e", padx=(10, 20), pady=15)

        # FULL FORM
        full_form_label = ctk.CTkLabel(help_instructions_frame, text="Full Form:", font=ctk.CTkFont(size=12, weight="bold"), width=70)
        full_form_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=15)

        full_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        full_middle_frame.grid(row=1, column=1, sticky="w", padx=0, pady=15)

        full_form_lbl0 = ctk.CTkLabel(full_middle_frame, text="SEND: ")
        full_form_lbl0.pack(side="left", padx=(0, 5))

        full_form_equipment_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Equipment Name", width=100)
        full_form_equipment_name_entry.pack(side="left", padx=(0, 5))

        full_form_lbl1 = ctk.CTkLabel(full_middle_frame, text=".")
        full_form_lbl1.pack(side="left", padx=(0, 5))

        full_form_module_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Module Name", width=130)
        full_form_module_name_entry.pack(side="left", padx=(0, 5))

        full_form_lbl2 = ctk.CTkLabel(full_middle_frame, text=".")
        full_form_lbl2.pack(side="left", padx=(0, 5))

        full_form_partition_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Partition Name", width=150)
        full_form_partition_name_entry.pack(side="left", padx=(0, 5))

        full_form_lbl3 = ctk.CTkLabel(full_middle_frame, text=".")
        full_form_lbl3.pack(side="left", padx=(0, 5))

        full_form_message_name_entry = ctk.CTkEntry(full_middle_frame, placeholder_text="Message Name", width=150)
        full_form_message_name_entry.pack(side="left", padx=(0, 5))

        full_form_button = ctk.CTkButton(help_instructions_frame, text="Use Full Form", width=100, command=lambda: self.write_SEND_or_SUSPEND_instruction(full_form_message_name_entry.get(), help_instructions_window, "Full Form", equipment_name=full_form_equipment_name_entry.get(), module_name=full_form_module_name_entry.get(), partition_name=full_form_partition_name_entry.get()))
        full_form_button.grid(row=1, column=2, sticky="e", padx=(10, 20), pady=15)

    def _display_TRAC_window(self):
        """Display instruction forms to assist the user with the humanized syntax"""
        help_instructions_window, help_instructions_frame = self.create_help_instruction_window_and_frame("TRACEABILITY", only_two_columns=True)

        # TRACEABILITY
        frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="w", padx=0, pady=15)

        lbl0 = ctk.CTkLabel(frame, text="TRAC: ")
        lbl0.pack(side="left", padx=(20, 5))

        pss_reqs_entry = ctk.CTkEntry(frame, placeholder_text="PSS_REQS", width=130)
        pss_reqs_entry.pack(side="left", padx=(0, 5))

        instant_entry = ctk.CTkEntry(frame, placeholder_text="Instant", width=130)
        instant_entry.pack(side="left", padx=(0, 5))

        button = ctk.CTkButton(help_instructions_frame, text="Use", width=100, command=lambda: self.write_TRAC_instruction(pss_reqs_entry.get(), instant_entry.get(), help_instructions_window))
        button.grid(row=0, column=1, sticky="e", padx=(10, 20), pady=15)

    def _display_FRAMING_1553_window(self):
        """Display instruction forms to assist the user with the humanized syntax"""
        help_instructions_window, help_instructions_frame = self.create_help_instruction_window_and_frame("FRAMING 1553", only_two_columns=True)

        # FORM
        short_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        short_middle_frame.grid(row=0, column=0, sticky="w", padx=0, pady=15)

        short_form_bus_name_entry = ctk.CTkEntry(short_middle_frame, placeholder_text="Bus Name", width=350)
        short_form_bus_name_entry.pack(side="left", padx=(20, 5))

        short_form_lbl1 = ctk.CTkLabel(short_middle_frame, text=" = ")
        short_form_lbl1.pack(side="left", padx=(0, 5))

        short_form_bus_mode_entry = ctk.CTkEntry(short_middle_frame, placeholder_text="Mode", width=200)
        short_form_bus_mode_entry.pack(side="left", padx=(0, 5))

        short_form_button = ctk.CTkButton(help_instructions_frame, text="Use", width=100, command=lambda: self.write_FRAMING_1553_instruction(short_form_bus_name_entry.get(), short_form_bus_mode_entry.get(), help_instructions_window))
        short_form_button.grid(row=0, column=1, sticky="e", padx=(10, 20), pady=15)

    def _display_SUSPEND_window(self):
        """Display instruction forms to assist the user with the humanized syntax"""
        help_instructions_window, help_instructions_frame = self.create_help_instruction_window_and_frame("SUSPEND")

        # SUSPEND (true) SHORT FORM
        freeze_label = ctk.CTkLabel(help_instructions_frame, text="SUSPEND (true)", font=ctk.CTkFont(size=14, weight="bold", underline=True), width=70)
        freeze_label.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=15)

        freeze_short_form_label = ctk.CTkLabel(help_instructions_frame, text="Short Form:", font=ctk.CTkFont(size=12, weight="bold"), width=70)
        freeze_short_form_label.grid(row=1, column=0, sticky="w", padx=(20, 10), pady=15)

        freeze_short_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        freeze_short_middle_frame.grid(row=1, column=1, sticky="w", padx=0, pady=15)

        freeze_short_form_lbl0 = ctk.CTkLabel(freeze_short_middle_frame, text="FREEZE: ")
        freeze_short_form_lbl0.pack(side="left", padx=(0, 5))

        freeze_short_form_message_name_entry = ctk.CTkEntry(freeze_short_middle_frame, placeholder_text="Message Name", width=350)
        freeze_short_form_message_name_entry.pack(side="left", padx=(0, 5))

        freeze_short_form_button = ctk.CTkButton(help_instructions_frame, text="Use Short Form", width=100, command=lambda: self.write_SEND_or_SUSPEND_instruction(freeze_short_form_message_name_entry.get(), help_instructions_window, "Short Form", suspend_form="Suspend (true)"))
        freeze_short_form_button.grid(row=1, column=2, sticky="e", padx=(10, 20), pady=15)

        # SUSPEND (true) FULL FORM
        freeze_full_form_label = ctk.CTkLabel(help_instructions_frame, text="Full Form:", font=ctk.CTkFont(size=13, weight="bold"), width=70)
        freeze_full_form_label.grid(row=2, column=0, sticky="w", padx=(20, 10), pady=15)

        freeze_full_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        freeze_full_middle_frame.grid(row=2, column=1, sticky="w", padx=0, pady=15)

        freeze_full_form_lbl0 = ctk.CTkLabel(freeze_full_middle_frame, text="FREEZE: ")
        freeze_full_form_lbl0.pack(side="left", padx=(0, 5))

        freeze_full_form_equipment_name_entry = ctk.CTkEntry(freeze_full_middle_frame, placeholder_text="Equipment Name", width=100)
        freeze_full_form_equipment_name_entry.pack(side="left", padx=(0, 5))

        freeze_full_form_lbl1 = ctk.CTkLabel(freeze_full_middle_frame, text=".")
        freeze_full_form_lbl1.pack(side="left", padx=(0, 5))

        freeze_full_form_module_name_entry = ctk.CTkEntry(freeze_full_middle_frame, placeholder_text="Module Name", width=130)
        freeze_full_form_module_name_entry.pack(side="left", padx=(0, 5))

        freeze_full_form_lbl2 = ctk.CTkLabel(freeze_full_middle_frame, text=".")
        freeze_full_form_lbl2.pack(side="left", padx=(0, 5))

        freeze_full_form_partition_name_entry = ctk.CTkEntry(freeze_full_middle_frame, placeholder_text="Partition Name", width=150)
        freeze_full_form_partition_name_entry.pack(side="left", padx=(0, 5))

        freeze_full_form_lbl3 = ctk.CTkLabel(freeze_full_middle_frame, text=".")
        freeze_full_form_lbl3.pack(side="left", padx=(0, 5))

        freeze_full_form_message_name_entry = ctk.CTkEntry(freeze_full_middle_frame, placeholder_text="Message Name", width=150)
        freeze_full_form_message_name_entry.pack(side="left", padx=(0, 5))

        freeze_full_form_button = ctk.CTkButton(help_instructions_frame, text="Use Full Form", width=100, command=lambda: self.write_SEND_or_SUSPEND_instruction(freeze_full_form_message_name_entry.get(), help_instructions_window, "Full Form", equipment_name=freeze_full_form_equipment_name_entry.get(), module_name=freeze_full_form_module_name_entry.get(), partition_name=freeze_full_form_partition_name_entry.get(), suspend_form="Suspend (true)"))
        freeze_full_form_button.grid(row=2, column=2, sticky="e", padx=(10, 20), pady=15)

        # SUSPEND (false) SHORT FORM
        unfreeze_label = ctk.CTkLabel(help_instructions_frame, text="SUSPEND (false)", font=ctk.CTkFont(size=13, weight="bold", underline=True), width=70)
        unfreeze_label.grid(row=3, column=0, sticky="w", padx=(20, 10), pady=15)

        unfreeze_short_form_label = ctk.CTkLabel(help_instructions_frame, text="Short Form:", font=ctk.CTkFont(size=12, weight="bold"), width=70)
        unfreeze_short_form_label.grid(row=4, column=0, sticky="w", padx=(20, 10), pady=15)

        unfreeze_short_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        unfreeze_short_middle_frame.grid(row=4, column=1, sticky="w", padx=0, pady=15)

        unfreeze_short_form_lbl0 = ctk.CTkLabel(unfreeze_short_middle_frame, text="UNFREEZE: ")
        unfreeze_short_form_lbl0.pack(side="left", padx=(0, 5))

        unfreeze_short_form_message_name_entry = ctk.CTkEntry(unfreeze_short_middle_frame, placeholder_text="Message Name", width=350)
        unfreeze_short_form_message_name_entry.pack(side="left", padx=(0, 5))

        unfreeze_short_form_button = ctk.CTkButton(help_instructions_frame, text="Use Short Form", width=100, command=lambda: self.write_SEND_or_SUSPEND_instruction(unfreeze_short_form_message_name_entry.get(), help_instructions_window, "Short Form", suspend_form="Suspend (false)"))
        unfreeze_short_form_button.grid(row=4, column=2, sticky="e", padx=(10, 20), pady=15)

        # SUSPEND (false) FULL FORM
        unfreeze_full_form_label = ctk.CTkLabel(help_instructions_frame, text="Full Form:", font=ctk.CTkFont(size=12, weight="bold"), width=70)
        unfreeze_full_form_label.grid(row=5, column=0, sticky="w", padx=(20, 10), pady=15)

        unfreeze_full_middle_frame = ctk.CTkFrame(help_instructions_frame, fg_color="transparent")
        unfreeze_full_middle_frame.grid(row=5, column=1, sticky="w", padx=0, pady=15)

        unfreeze_full_form_lbl0 = ctk.CTkLabel(unfreeze_full_middle_frame, text="UNFREEZE: ")
        unfreeze_full_form_lbl0.pack(side="left", padx=(0, 5))

        unfreeze_full_form_equipment_name_entry = ctk.CTkEntry(unfreeze_full_middle_frame, placeholder_text="Equipment Name", width=100)
        unfreeze_full_form_equipment_name_entry.pack(side="left", padx=(0, 5))

        unfreeze_full_form_lbl1 = ctk.CTkLabel(unfreeze_full_middle_frame, text=".")
        unfreeze_full_form_lbl1.pack(side="left", padx=(0, 5))

        unfreeze_full_form_module_name_entry = ctk.CTkEntry(unfreeze_full_middle_frame, placeholder_text="Module Name", width=130)
        unfreeze_full_form_module_name_entry.pack(side="left", padx=(0, 5))

        unfreeze_full_form_lbl2 = ctk.CTkLabel(unfreeze_full_middle_frame, text=".")
        unfreeze_full_form_lbl2.pack(side="left", padx=(0, 5))

        unfreeze_full_form_partition_name_entry = ctk.CTkEntry(unfreeze_full_middle_frame, placeholder_text="Partition Name", width=150)
        unfreeze_full_form_partition_name_entry.pack(side="left", padx=(0, 5))

        unfreeze_full_form_lbl3 = ctk.CTkLabel(unfreeze_full_middle_frame, text=".")
        unfreeze_full_form_lbl3.pack(side="left", padx=(0, 5))

        unfreeze_full_form_message_name_entry = ctk.CTkEntry(unfreeze_full_middle_frame, placeholder_text="Message Name", width=150)
        unfreeze_full_form_message_name_entry.pack(side="left", padx=(0, 5))

        unfreeze_full_form_button = ctk.CTkButton(help_instructions_frame, text="Use Full Form", width=100, command=lambda: self.write_SEND_or_SUSPEND_instruction(unfreeze_full_form_message_name_entry.get(), help_instructions_window, "Full Form", equipment_name=unfreeze_full_form_equipment_name_entry.get(), module_name=unfreeze_full_form_module_name_entry.get(), partition_name=unfreeze_full_form_partition_name_entry.get(), suspend_form="Suspend (false)"))
        unfreeze_full_form_button.grid(row=5, column=2, sticky="e", padx=(10, 20), pady=15)

    def create_help_instruction_window_and_frame(self, instruction, only_two_columns=False):
        """Create the structure of the shortcut frame"""
        help_instructions_window = tk.Toplevel(self)
        help_instructions_window.title(f"{instruction} Grammar Window")
        if instruction == "SET":
            help_instructions_window.geometry("1400x225")
        elif instruction == "CHK_SP_EQ":  
            help_instructions_window.geometry("1500x225")
        elif instruction == "CHK_WT_EQ":
            help_instructions_window.geometry("1580x225")
        elif instruction == "SEND":
            help_instructions_window.geometry("900x175")
        elif instruction == "TRACEABILITY":
            help_instructions_window.geometry("550x100")
        elif instruction == "FRAMING 1553":
            help_instructions_window.geometry("900x100")
        elif instruction == "SUSPEND":
            help_instructions_window.geometry("1000x430")
            
        help_instructions_window.transient(self)
        help_instructions_window.grab_set()
        help_instructions_window.focus_force()

        help_instructions_frame = ctk.CTkFrame(help_instructions_window, corner_radius=10)
        help_instructions_frame.pack(fill="both", expand=True, padx=20, pady=20)

        if only_two_columns:
            help_instructions_frame.grid_columnconfigure(0, weight=0)
            help_instructions_frame.grid_columnconfigure(1, weight=1)
            help_instructions_frame.grid_columnconfigure(2, weight=0)
        else:
            help_instructions_frame.grid_columnconfigure(0, weight=1)
            help_instructions_frame.grid_columnconfigure(1, weight=0)

        return help_instructions_window, help_instructions_frame

    def write_SET_or_CHK_instruction(self, signal_name, signal_value, help_instructions_window, instruction, form, equipment_name=None, module_name=None, partition_name=None, message_name=None, level_name="", signal_type=None, timeout=None):
        """Insert the instruction line in the textbox"""
        line=""
        if (equipment_name and module_name and partition_name and message_name and signal_name and signal_value and signal_type and (form=="Full Form")):
            line = f"{"VER: " if (instruction == "CHK_SP_EQ" or instruction == "CHK_WT_EQ") else ""}{equipment_name}.{module_name}.{partition_name}.{message_name}.{f'{level_name}.' if level_name else ""}{signal_name}.{signal_type} = {signal_value} {f'(Timeout={timeout})'if instruction == "CHK_WT_EQ" else ""}\n"
        elif (equipment_name and module_name and partition_name and message_name and signal_name and signal_value and (form=="Extended Form")):
            line = f"{"VER: " if (instruction == "CHK_SP_EQ" or instruction == "CHK_WT_EQ") else ""}{equipment_name}.{module_name}.{partition_name}.{message_name}.{f'{level_name}.' if level_name else ""}{signal_name} = {signal_value} {f'(Timeout={timeout})'if instruction == "CHK_WT_EQ" else ""}\n"
        elif (signal_name and signal_value and (form=="Short Form")):
            line = f"{"VER: " if (instruction == "CHK_SP_EQ" or instruction == "CHK_WT_EQ") else ""}{signal_name} = {signal_value} {f'(Timeout={timeout})'if instruction == "CHK_WT_EQ" else ""}\n"
        else:
            messagebox.showerror("Error", f"Missing arguments", parent=help_instructions_window)
            return
        
        help_instructions_window.destroy()
        self.editor._textbox.insert("insert", line)
        self.schedule_highlight()

    def write_SEND_or_SUSPEND_instruction(self, message_name, help_instructions_window, form, equipment_name=None, module_name=None, partition_name=None, suspend_form=None):
        """Insert the instruction line in the textbox"""
        line=""
        if (equipment_name and module_name and partition_name and message_name and (form=="Full Form")):
            line = f"{"FREEZE: " if suspend_form == "Suspend (true)" else "UNFREEZE: " if suspend_form == "Suspend (false)" else "SEND: "}{equipment_name}.{module_name}.{partition_name}.{message_name}\n"
        elif (message_name and (form=="Short Form")):
            line = f"{"FREEZE: " if suspend_form == "Suspend (true)" else "UNFREEZE: " if suspend_form == "Suspend (false)" else "SEND: "}{message_name}\n"
        else:
            messagebox.showerror("Error", f"Missing arguments", parent=help_instructions_window)
            return
        
        help_instructions_window.destroy()
        self.editor._textbox.insert("insert", line)
        self.schedule_highlight()

    def write_TRAC_instruction(self, pss_reqs, instant, help_instructions_window):
        """Insert the instruction line in the textbox"""
        line=""
        if (pss_reqs and instant):
            line = f"TRAC: {pss_reqs} {instant}\n"
        else:
            messagebox.showerror("Error", f"Missing arguments", parent=help_instructions_window)
            return
        
        help_instructions_window.destroy()
        self.editor._textbox.insert("insert", line)
        self.schedule_highlight()

    def write_FRAMING_1553_instruction(self, bus_name, bus_mode, help_instructions_window):
        """Insert the instruction line in the textbox"""
        line=""
        if (bus_name and bus_mode):
            line = f"{bus_name} = {bus_mode}\n"
        else:
            messagebox.showerror("Error", f"Missing arguments", parent=help_instructions_window)
            return
        
        help_instructions_window.destroy()
        self.editor._textbox.insert("insert", line)
        self.schedule_highlight()


    # ==== TEMPLATE MANAGEMENT ====

    def open_humanized_syntax_template(self):
        """Opens an existing Jinja2 template file into the editor."""
        try:
            config = mwo.load_config()
            initial_dir = config.get("default_template_dir", os.getcwd())
        except Exception:
            initial_dir = os.getcwd()

        file_path = filedialog.askopenfilename(
            parent=self,
            title="Open Processed Template",
            initialdir=initial_dir,
            filetypes=(("j2 files", "*.j2"), ("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # start in 1.0 -> line 1, char 0, delete until the end    
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", content)

            # update the template_path of this class and process class selected by the user 
            self.current_template_path = file_path
            self.humanized_syntax_process_features_class.current_template_path = file_path  # update process template class
            # restart processed_template_path so the user can save the processed_template with another name
            self.processed_template_path = None
            self.schedule_highlight()
            # update the title with the template name
            self.title_lbl.configure(text=f"Template: {os.path.splitext(os.path.basename(self.current_template_path))[0]}")
            self.master.title(os.path.splitext(os.path.basename(self.current_template_path))[0])
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open template:\n{e}", parent=self)

    def save_humanized_syntax_template(self, event=None, is_manual_refresh=False):
        """Prompts the user to save the current text as a new template file."""
        if self.current_template_path:
            self._write_file(self.current_template_path)
            if not is_manual_refresh:
                messagebox.showinfo("Saved", f"Template saved successfully:\n{os.path.basename(self.current_template_path)}", parent=self)
        else:
            self.save_as_humanized_syntax_template(is_manual_refresh)

    def save_as_humanized_syntax_template(self, event=None, is_manual_refresh=False):
        try:
            config = mwo.load_config()
            initial_dir = config.get("default_template_dir", os.getcwd())
        except Exception:
            initial_dir = os.getcwd()

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Template As",
            initialdir=initial_dir,
            defaultextension=".j2",
            filetypes=(("Jinja files", "*.j2"), ("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        
        if not file_path:
            return

        self.current_template_path = file_path
        self.humanized_syntax_process_features_class.current_template_path = file_path

        if self._write_file(file_path):
            self.title_lbl.configure(text=f"Template: {os.path.splitext(os.path.basename(self.current_template_path))[0]}")
            self.master.title(os.path.splitext(os.path.basename(self.current_template_path))[0])
            if not is_manual_refresh:
                messagebox.showinfo("Success", "Template saved successfully!", parent=self)

    def save_and_process_humanized_syntax_template(self, event=None):
        """Save humanized_syntax_template, process the template and show the result in a Preview Viewer"""
        try:
            self.save_humanized_syntax_template(is_manual_refresh=True)

            data, show_warning = self.humanized_syntax_process_features_class.process_humanized_syntax_template(data_return=True)

            if show_warning:
                print("-------------------------------------------------------------------------------------------------------")
                messagebox.showwarning("Warning!", "Warnings detected. Please review the terminal for details.", parent=self)
        
            dialog = HumanizedSyntaxTemplatePreviewDialog(self, "\n".join(data), "Preview Processed Template")
            self.wait_window(dialog)

            if not dialog.user_choice:
                return
            
            if self.humanized_syntax_process_features_class.processed_template_path and (dialog.user_choice != "Save as..."): # Save option
                if self.humanized_syntax_process_features_class._write_humanized_syntax_processed_template(self.humanized_syntax_process_features_class.processed_template_path, data):
                    messagebox.showinfo("Success", "Template saved successfully!", parent=self)
            else:
                try:
                    config = mwo.load_config()
                    initial_dir = config.get("default_template_dir", os.getcwd())
                except Exception:
                    initial_dir = os.getcwd()

                file_path = filedialog.asksaveasfilename(
                    parent=self,
                    title="Save Template As",
                    initialdir=initial_dir,
                    defaultextension=".j2",
                    filetypes=(("Jinja2 files", "*.j2"), ("Text Files", "*.txt"), ("All Files", "*.*"))
                )
                
                if not file_path:
                    return
                
                save_success = self.humanized_syntax_process_features_class.save_as_humanized_syntax_processed_template(data, file_path)

                if save_success:
                    messagebox.showinfo("Success", "Template saved successfully!", parent=self)

        except Exception as e:
            messagebox.showerror("Error", f"Error processing the file: {e}", parent=self)


# ==== PROCESS FEATURES CLASS ====

class HumanizedSyntaxProcessFeatures:
    def __init__(self, parameters_filepath, current_template_path):
        self.parameters_filepath = parameters_filepath
        self.processed_template_path = None # store the path when user save a processed_template (Jinja Rendered -> TextX -> Processed_template ) 
        self.current_template_path = current_template_path

        CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT_DIR = os.path.dirname(CURRENT_SCRIPT_DIR)
        MODEL_DIR = os.path.join(PROJECT_ROOT_DIR, "models/Proyecto 1")

        xml_path = os.path.join(MODEL_DIR, "textx/Synthetic.xml")
        grammar_path = os.path.join(MODEL_DIR, "textx/grammar.tx")
        
        self.meta_model = metamodel_from_file(grammar_path)

        # store paths for each message
        self.xml_messages_dict = {}
        # store paths for each signal
        self.xml_signals_dict = {}
        # store bus_name and modes for each bus
        self.xml_buses_dict = {}

        self.load_xml_dict(xml_path) # preload the dictionaries by reading the xml file
        self.show_warning_window = False # store if warning has been seen when processing a template with TextX (e.g. Multiple paths found for ...) 

        if self.parameters_filepath:
            self.parameters_file_dict = extract_variables_from_file(self.parameters_filepath, return_dict_variable_value=True)
        else:
            self.parameters_file_dict = {}

    # ==== XML PARSER ====

    def load_xml_dict(self, xml_path):
        """Load the dictionaries by reading the xml file. Stores messages, signals and buses paths and modes"""
        tree = ET.parse(xml_path)
        root = tree.getroot()    

        for equipment in root.iter("Equipment"):
                for module in equipment.iter("Module"):
                    for partition in module.iter("Partition"):
                        for message in partition.iter("Message"):
                            equipment_name = equipment.get("EquipmentName")
                            module_name = module.get("ModuleName")
                            partition_name = partition.get("PartitionName")
                            message_name = message.get("MessageName")
                            message_path = ".".join([equipment_name, module_name, partition_name, message_name])
                            if message_name in self.xml_messages_dict:
                                if message_path not in self.xml_messages_dict[message_name]["paths"]:
                                    self.xml_messages_dict[message_name]["paths"].append(message_path)
                            else:
                                self.xml_messages_dict[message_name] = {}
                                self.xml_messages_dict[message_name]["paths"] = [message_path]
                            for level in message.iter("Level"):
                                level_name = level.get("LevelName")
                                for info in level.iter("Information"):
                                    signal_name = info.get("InformationName")
                                    signal_type = info.get("Type")

                                    if level_name:
                                        signal_path = ".".join([equipment_name, module_name, partition_name, message_name, level_name, signal_name, signal_type])
                                    else:
                                        signal_path = ".".join([equipment_name, module_name, partition_name, message_name, signal_name, signal_type])

                                    if signal_name in self.xml_signals_dict:
                                        if signal_path not in self.xml_signals_dict[signal_name]["paths"]:
                                            self.xml_signals_dict[signal_name]["paths"].append(signal_path)
                                            if level_name:
                                                self.xml_signals_dict[signal_name]["level"].append(signal_path)
                                    else:
                                        self.xml_signals_dict[signal_name] = {}
                                        self.xml_signals_dict[signal_name]["paths"] = [signal_path]
                                        if level_name:
                                            self.xml_signals_dict[signal_name]["level"] = [signal_path]
                                        else:
                                            self.xml_signals_dict[signal_name]["level"] = []

                                    check_enum_value = info.find("Values")
                                    if check_enum_value is not None:
                                        for value in info.iter("Values"):
                                            enum_first_value = value.get("EnumValue")
                                            enum_second_value = value.get("Value")

                                            if "enum" not in self.xml_signals_dict[signal_name]:
                                                self.xml_signals_dict[signal_name]["enum"] = {}
                                                self.xml_signals_dict[signal_name]["enum"][enum_first_value] = enum_second_value
                                            else:
                                                self.xml_signals_dict[signal_name]["enum"][enum_first_value] = enum_second_value
        
        for milbus_network in root.iter("MilbusNetwork"):
            bus_name = milbus_network.get("Name")
            self.xml_buses_dict[bus_name] = {}
            for milbus_framing in milbus_network.iter("MilbusFraming"):
                bus_mode = milbus_framing.get("Name")
                bus_value = milbus_framing.get("Value")
                self.xml_buses_dict[bus_name][bus_mode] = bus_value

    # ==== TEXTX MANAGEMENT ====

    def process_humanized_syntax_template(self, data_return=False):
        """Main processing function with textX"""
        self.show_warning_window = False
        data = []

        specific_template_dir = os.path.dirname(self.current_template_path)
        template_name = os.path.basename(self.current_template_path)

        env = Environment(loader=FileSystemLoader(specific_template_dir), undefined=StrictUndefined)
        template = env.get_template(template_name)
        content = template.render(self.parameters_file_dict)
        content = mwo.remove_indentation(content)
        content = mwo.remove_extra_blank_lines(content)

        humanized_template = self.meta_model.model_from_str(content)
            
        self.sub_cycle_count = 1
        self.cycle_count = 1
        self.instruction = None

        for self.instruction in humanized_template.instructions:
            line = self.process_instruction()
            data.append(line)
        
        # when the user select a template in the main interface, we only process the template to see if there are errors (this happens when data_return=False)
        # when data_return = True, return data and self.show_warning_window
        if data_return:
            return data, self.show_warning_window

    def process_instruction(self):
        """Process every instruction using the textX grammar defined in grammar.tx"""
        try:
            match self.instruction.__class__.__name__:
                # COMMENT Instruction
                case "Note":
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};COMMENT;{self.instruction.comment_text.strip()};;;;;;;;;;;;")
                    self.sub_cycle_count += 1
                    return line
                # SET Instruction
                case "Set_ShortForm_or_Framing_1553":
                    # Check if FRAMING_1553 instruction ↓
                    bus_mode_found, bus_mode_value = self.search_in_xml_buses_dict()
                    if bus_mode_found:
                        if bus_mode_found == "Mode not found":
                            bus_mode_found = ""
                            print(f"Mode not found for: {self.instruction.signal_or_bus_name}\nValid modes: {self.xml_buses_dict[self.instruction.signal_or_bus_name]}")
                        line = (f"{self.cycle_count}.{self.sub_cycle_count};FRAMING_1553;;;;;;;{self.instruction.signal_or_bus_name};enum;{bus_mode_found};;{bus_mode_value or bus_mode_found};;")
                        self.sub_cycle_count += 1
                        return line
                    # If not FRAMING_1553 is SET instruction ↓
                    searched_signal_type, searched_level_name, searched_message_name, searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.signal_or_bus_name)
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal_or_bus_name, self.instruction.value)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SET;;{searched_equipment_name};{searched_module_name};{searched_partition_name};{searched_message_name};{searched_level_name};{self.instruction.signal_or_bus_name};{searched_signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Set_ExtendedForm":
                    searched_signal_type, searched_level_name = self.extract_and_search_instruction_parameters(self.instruction.signal, extended_form=True)
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SET;;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};{searched_level_name};{self.instruction.signal};{searched_signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Set_FullForm_or_Set_with_Level_Extended_Form":
                    is_Set_with_Level = self.extract_and_search_instruction_parameters(self.instruction.signal_type_or_signal, check_if_extended_level_structure=True)
                    ## Set_with_Level_Extended_Form instruction
                    if is_Set_with_Level:
                        enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal_type_or_signal, self.instruction.value)
                        line = (f"{self.cycle_count}.{self.sub_cycle_count};SET;;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};{self.instruction.signal_or_level};{self.instruction.signal_type_or_signal};{is_Set_with_Level};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    ## Set_FullForm instruction
                    else:
                        enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal_or_level, self.instruction.value)
                        line = (f"{self.cycle_count}.{self.sub_cycle_count};SET;;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};;{self.instruction.signal_or_level};{self.instruction.signal_type_or_signal};;{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Set_with_Level_FullForm":
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SET;;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};{self.instruction.level};{self.instruction.signal};{self.instruction.signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Set_with_Level_ShortForm":
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    searched_signal_type, searched_level_name, searched_message_name, searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.signal, message_or_level_info=True)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SET;;{searched_equipment_name};{searched_module_name};{searched_partition_name};{searched_message_name};{searched_level_name};{self.instruction.signal};{searched_signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                # SEND Instruction
                case "Send_ShortForm":
                    searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.message_name, return_message_or_suspend_path=True)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SEND;;{searched_equipment_name};{searched_module_name};{searched_partition_name};{self.instruction.message_name};;;;;;;;")
                    self.sub_cycle_count += 1
                    return line
                case "Send_FullForm":
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SEND;;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};;;;;;;;")
                    self.sub_cycle_count += 1
                    return line
                # CHK_SP_EQ Instruction
                case "Chk_Sp_Eq_ShortForm":
                    searched_signal_type, searched_level_name, searched_message_name, searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.signal)
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_SP_EQ;;{searched_equipment_name};{searched_module_name};{searched_partition_name};{searched_message_name};{searched_level_name};{self.instruction.signal};{searched_signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Chk_Sp_Eq_ExtendedForm":
                    searched_signal_type, searched_level_name = self.extract_and_search_instruction_parameters(self.instruction.signal, extended_form=True)
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_SP_EQ;;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};{searched_level_name};{self.instruction.signal};{searched_signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Chk_Sp_Eq_FullForm_or_Chk_Sp_Eq_with_Level_Extended_Form":
                    is_Chk_Sp_Eq_with_Level = self.extract_and_search_instruction_parameters(self.instruction.signal_type_or_signal, check_if_extended_level_structure=True)
                    ## Chk_Sp_Eq_with_Level_Extended_Form instruction
                    if is_Chk_Sp_Eq_with_Level:
                        enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal_type_or_signal, self.instruction.value)
                        line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_SP_EQ;;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};{self.instruction.signal_or_level};{self.instruction.signal_type_or_signal};{is_Chk_Sp_Eq_with_Level};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    ## Chk_Sp_Eq_FullForm instruction
                    else:
                        enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal_or_level, self.instruction.value)
                        line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_SP_EQ;;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};;{self.instruction.signal_or_level};{self.instruction.signal_type_or_signal};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Chk_Sp_Eq_with_Level_FullForm":
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_SP_EQ;;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};{self.instruction.level};{self.instruction.signal};{self.instruction.signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Chk_Sp_Eq_with_Level_ShortForm":
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    searched_signal_type, searched_level_name, searched_message_name, searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.signal, message_or_level_info=True)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_SP_EQ;;{searched_equipment_name};{searched_module_name};{searched_partition_name};{searched_message_name};{searched_level_name};{self.instruction.signal};{searched_signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                # CHK_WT_EQ Instruction
                case "Chk_Wt_Eq_ShortForm":
                    searched_signal_type, searched_level_name, searched_message_name, searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.signal)
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_WT_EQ;{self.instruction.time_interval};{searched_equipment_name};{searched_module_name};{searched_partition_name};{searched_message_name};{searched_level_name};{self.instruction.signal};{searched_signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Chk_Wt_Eq_ExtendedForm":
                    searched_signal_type, searched_level_name = self.extract_and_search_instruction_parameters(self.instruction.signal, extended_form=True)
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_WT_EQ;{self.instruction.time_interval};{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};{searched_level_name};{self.instruction.signal};{searched_signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Chk_Wt_Eq_FullForm_or_Chk_Wt_Eq_with_Level_Extended_Form":
                    is_Chk_Wt_Eq_with_Level = self.extract_and_search_instruction_parameters(self.instruction.signal_type_or_signal, check_if_extended_level_structure=True)
                    ## Chk_Wt_Eq_with_Level_Extended_Form instruction
                    if is_Chk_Wt_Eq_with_Level:
                        enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal_type_or_signal, self.instruction.value)
                        line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_WT_EQ;{self.instruction.time_interval};{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};{self.instruction.signal_or_level};{self.instruction.signal_type_or_signal};{is_Chk_Wt_Eq_with_Level};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    ## Chk_Wt_Eq_FullForm instruction
                    else:
                        enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal_or_level, self.instruction.value)
                        line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_WT_EQ;{self.instruction.time_interval};{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};;{self.instruction.signal_or_level};{self.instruction.signal_type_or_signal};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Chk_Wt_Eq_with_Level_FullForm":
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_WT_EQ;{self.instruction.time_interval};{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};{self.instruction.level};{self.instruction.signal};{self.instruction.signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                case "Chk_Wt_Eq_with_Level_ShortForm":
                    enum_value = self.search_instruction_value_in_xml_signals_dict(self.instruction.signal, self.instruction.value)
                    searched_signal_type, searched_level_name, searched_message_name, searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.signal, message_or_level_info=True)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};CHK_WT_EQ;{self.instruction.time_interval};{searched_equipment_name};{searched_module_name};{searched_partition_name};{searched_message_name};{searched_level_name};{self.instruction.signal};{searched_signal_type};{self.instruction.value};;{enum_value or self.instruction.value};;")
                    self.sub_cycle_count += 1
                    return line
                # END_CYCLE Instruction
                case "End_Cycle":
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};END_CYCLE;;;;;;;;;;;;;")
                    self.cycle_count += 1
                    self.sub_cycle_count = 1
                    return line
                # TRACEABILITY Instruction
                case "Traceability":
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};TRACEABILITY;{self.instruction.pss_reqs};;;;;;;;{self.instruction.instant};;;;")
                    self.sub_cycle_count += 1
                    return line
                # SUSPEND Instruction
                ## SUSPEND_TRUE Instruction
                case "Suspend_True_FullForm":
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SUSPEND;True;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};;;;;;;;")
                    self.sub_cycle_count += 1
                    return line
                case "Suspend_True_ShortForm":
                    searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.message_name, return_message_or_suspend_path=True)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SUSPEND;True;{searched_equipment_name};{searched_module_name};{searched_partition_name};{self.instruction.message_name};;;;;;;;")
                    self.sub_cycle_count += 1
                    return line
                ## SUSPEND_FALSE Instruction
                case "Suspend_False_FullForm":
                    searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.message_name, return_message_or_suspend_path=True)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SUSPEND;False;{self.instruction.equipment_name};{self.instruction.module_name};{self.instruction.partition_name};{self.instruction.message_name};;;;;;;;")
                    self.sub_cycle_count += 1
                    return line
                case "Suspend_False_ShortForm":
                    searched_partition_name, searched_module_name, searched_equipment_name = self.extract_and_search_instruction_parameters(self.instruction.message_name, return_message_or_suspend_path=True)
                    line = (f"{self.cycle_count}.{self.sub_cycle_count};SUSPEND;False;{searched_equipment_name};{searched_module_name};{searched_partition_name};{self.instruction.message_name};;;;;;;;")
                    self.sub_cycle_count += 1
                    return line
                # CODE Instruction
                case "Jinja_Code":
                    line = self.instruction.jinja_code
                    return line
                # COMMENT CODE Instruction
                case "Jinja_Comment":
                    line = self.instruction.jinja_comment
                    return line
                case _:
                    print("Error: Unrecognized instruction")

        except Exception as e:
            print(f"Error: {e}")

    # ==== PROCESSED TEMPLATE MANAGEMENT ====

    def save_as_humanized_syntax_processed_template(self, data, file_path):
        if self._write_humanized_syntax_processed_template(file_path, data):
            self.processed_template_path = file_path
            return True

    def _write_humanized_syntax_processed_template(self, path, data):
        """Helper method to write editor contents to the filesystem."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(data))
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save:\n{e}", parent=self)
            return False
        
    # ==== HELP METHODS ====

    def extract_and_search_instruction_parameters(self, parameter, return_message_or_suspend_path=False, extended_form=False, message_or_level_info=False, check_if_extended_level_structure=False):
        """Search the other parameters of the path depending on the user_input_path"""
        parameter = self.search_parameter_in_parameter_file(parameter) or parameter
        # search and return path parameters if not message or suspend instruction
        if not return_message_or_suspend_path:
            if check_if_extended_level_structure:
                return self.search_parameter_in_xml_file(parameter, search_type_only=extended_form, search_with_message_or_level_info=message_or_level_info, check_if_extended_level_structure=check_if_extended_level_structure)
            else:
                searched_signal_type, searched_level_name, searched_message_name, searched_partition_name, searched_module_name, searched_equipment_name = self.search_parameter_in_xml_file(parameter, search_type_only=extended_form, search_with_message_or_level_info=message_or_level_info)
            if not extended_form:
                return searched_signal_type, searched_level_name, searched_message_name, searched_partition_name, searched_module_name, searched_equipment_name
            else:
                return searched_signal_type, searched_level_name
        # if message or suspend instruction search and return message or suspend path
        else:
            searched_partition_name, searched_module_name, searched_equipment_name = self.search_parameter_in_xml_file(parameter, return_message_or_suspend_path=True)
            return searched_partition_name, searched_module_name, searched_equipment_name
        
    def search_parameter_in_parameter_file(self, parameter):
        """Check if the parameter is in the parameter file selected by the user"""
        if isinstance(parameter, str):
            if (parameter.startswith("{{") and parameter.endswith("}}")):
                tail_match = re.search(r'(\[\d+\])+$', parameter[2:-2])
                if tail_match:
                    bracket_tail = tail_match.group(0)
            
                    string_indexes = re.findall(r'\d+', bracket_tail)
                    
                    indexes = [int(num) for num in string_indexes]
                    
                    variable_name = parameter[2:-2][:tail_match.start()]
                    
                    if len(indexes) == 1:
                        if variable_name in self.parameters_file_dict:
                            return self.parameters_file_dict[variable_name][indexes[0]]
                        else:
                            return False
                    elif len(indexes) == 2:
                        if variable_name in self.parameters_file_dict:
                            return self.parameters_file_dict[variable_name][indexes[0]][indexes[1]]
                        else:
                            return False
                elif parameter[2:-2] in self.parameters_file_dict: 
                    return self.parameters_file_dict[parameter[2:-2]]
                else:
                    return False
        else:
            return False
        
    def search_parameter_in_xml_file(self, parameter, return_message_or_suspend_path=False, search_type_only=False, search_with_message_or_level_info=False, check_if_extended_level_structure=False):
        """Search in the xml file the path associated with the user_input_path"""
        # check if not (SEND/SUSPEND) Short Form
        if not return_message_or_suspend_path:
            # initialize variables to return empty strings if path not found
            searched_signal_type = searched_level_name = searched_message_name = searched_partition_name = searched_module_name = searched_equipment_name = ""
            # check if signal not in xml_signals_dict and has Level_Extended_Form Structure (Equip.Mod.Parti.Mess.Level.Sign) to return type_found = False
            if not parameter in self.xml_signals_dict and check_if_extended_level_structure:
                signal = self.search_parameter_in_parameter_file(self.instruction.signal_or_level) or self.instruction.signal_or_level
                if signal in self.xml_signals_dict:
                    # Full Form Found return False to write the complete path specified by the user
                    return False
                else:
                    print(f"Path not found for signal: {self.instruction.equipment_name}.{self.instruction.module_name}.{self.instruction.partition_name}.{self.instruction.message_name}.{self.instruction.signal_or_level}.{parameter}, check the name or specify the complete path")
                    self.show_warning_window = True
                    type_found = False
                    return type_found
            # check if signal in xml_dict
            elif parameter in self.xml_signals_dict:
                # search_type_only = extended_form_structure -> (Equip.Mod.Parti.Mess.Sign) 
                if search_type_only or check_if_extended_level_structure:
                    ## Check if any variable is parameter
                    equipment = self.search_parameter_in_parameter_file(self.instruction.equipment_name) or self.instruction.equipment_name
                    module = self.search_parameter_in_parameter_file(self.instruction.module_name) or self.instruction.module_name
                    partition = self.search_parameter_in_parameter_file(self.instruction.partition_name) or self.instruction.partition_name
                    message = self.search_parameter_in_parameter_file(self.instruction.message_name) or self.instruction.message_name
                
                ## Check if level is parameter if Level_Extended_Form Structure
                if check_if_extended_level_structure:
                    level = self.search_parameter_in_parameter_file(self.instruction.signal_or_level) or self.instruction.signal_or_level

                # Enter if multiple paths found in xml dict       
                if len(self.xml_signals_dict[parameter]["paths"]) > 1:
                    if search_type_only or check_if_extended_level_structure:
                        # Create the user input path
                        if check_if_extended_level_structure:
                            user_input_path = (".").join([equipment, module, partition, message, level, parameter])
                        else:
                            user_input_path = (".").join([equipment, module, partition, message, parameter])
                        # Check if we find the user input path in xml_dict[signal_name]["paths"] 
                        path_found = next((path for path in self.xml_signals_dict[parameter]["paths"] if all(component in path.split(".") for component in user_input_path.split("."))), None)
                        if path_found:
                            # Check if the xml_dict[signal_name] contains a level structure and the user_input_path is in
                            if self.xml_signals_dict[parameter]["level"] and (path_found in self.xml_signals_dict[parameter]["level"]):
                                searched_signal_type = path_found.split(".")[6]
                                if check_if_extended_level_structure:
                                    return searched_signal_type
                                searched_level_name = path_found.split(".")[4]
                            else:
                                searched_signal_type = path_found.split(".")[5]
                        else:
                            self.show_warning_window = True
                            print(f"Type not found for path: {user_input_path}\nValid paths for signal {parameter}: {self.xml_signals_dict[parameter]["paths"]}")
                            if check_if_extended_level_structure:
                                return False
                    # check if the user input path has the structure (message_name.signal_name or level_name.signal_name)
                    elif search_with_message_or_level_info:
                        ## Check if the message or the level introduced by the user is parameter
                        message_or_level_name = self.search_parameter_in_parameter_file(self.instruction.message_or_level_name) or self.instruction.message_or_level_name
                        # create the user input path
                        user_input_path = (".").join([message_or_level_name, parameter])
                        # check if the user input path is in xml_dict[signal_name]["paths"]
                        path_found = next((path for path in self.xml_signals_dict[parameter]["paths"] if all(component in path.split(".") for component in user_input_path.split("."))), None)
                        if path_found:
                            searched_equipment_name = path_found.split(".")[0]
                            searched_module_name = path_found.split(".")[1]
                            searched_partition_name = path_found.split(".")[2]

                            if self.xml_signals_dict[parameter]["level"] and (path_found in self.xml_signals_dict[parameter]["level"]):
                                # check if the user has type the level name in the path (level_name.signal_name)
                                if not (path_found.split(".")[3] in user_input_path.split(".")):
                                    searched_message_name = path_found.split(".")[3]
                                else:
                                    searched_message_name = self.instruction.message_or_level_name
                                # check if the user has type the message name in the path (message_name.signal_name)
                                if not (path_found.split(".")[4] in user_input_path.split(".")):
                                    searched_level_name = path_found.split(".")[4]
                                else:
                                    searched_level_name = self.instruction.message_or_level_name
                                searched_signal_type = path_found.split(".")[6]
                            else:
                                searched_message_name = self.instruction.message_or_level_name
                                searched_signal_type = path_found.split(".")[5]
                        else:
                            self.show_warning_window = True
                            print(f"Path not found for path: {user_input_path}\nValid paths for signal {parameter}: {self.xml_signals_dict[parameter]["paths"]}")
                    else:
                        self.show_warning_window = True
                        print(f"Different paths found for signal {parameter}: {self.xml_signals_dict[parameter]["paths"]}")
                # enter here if the user_input_path only has one path
                else:
                    path_list = self.xml_signals_dict[parameter]["paths"][0].split(".")
                    # check if Extended_Level_Structure
                    if check_if_extended_level_structure:
                        user_input_path = (".").join([equipment, module, partition, message, level, parameter])
                        path_found = next((path for path in self.xml_signals_dict[parameter]["paths"] if all(component in path.split(".") for component in user_input_path.split("."))), None)
                        if path_found:
                                # return the type
                                return path_list[6]
                        else:
                            print(f"Path: {user_input_path} is incorrect")
                    # check if extended form
                    elif search_type_only:
                        user_input_path = (".").join([equipment, module, partition, message, parameter])
                        path_found = next((path for path in self.xml_signals_dict[parameter]["paths"] if all(component in path.split(".") for component in user_input_path.split("."))), None)
                        if path_found:
                            searched_equipment_name = path_list[0]
                            searched_module_name = path_list[1]
                            searched_partition_name = path_list[2]
                            searched_message_name = path_list[3]
                            searched_signal_type = path_list[5]
                        else:
                            print(f"Path: {user_input_path} is incorrect")
                    # short form
                    else:
                        searched_equipment_name = path_list[0]
                        searched_module_name = path_list[1]
                        searched_partition_name = path_list[2]
                        searched_message_name = path_list[3]

                        if self.xml_signals_dict[parameter]["level"]:
                            searched_level_name = path_list[4]
                            searched_signal_type = path_list[6]
                        else:
                            searched_signal_type = path_list[5]
            else:
                self.show_warning_window = True
                if search_type_only:
                    print(f"Type not found for signal: {parameter}, check the name or specify the type in the path")
                else:
                    print(f"Path not found for signal: {parameter}, check the name or specify the complete path")
            return searched_signal_type, searched_level_name, searched_message_name, searched_partition_name, searched_module_name, searched_equipment_name
        # (SEND/SUSPEND) short form, try to search the equipment, module and partition for the user_input_message 
        else:
            searched_partition_name = searched_module_name = searched_equipment_name = ""
            # if path found for the message in messages_dict
            if parameter in self.xml_messages_dict:
                # check if more than one path found for the message
                if len(self.xml_messages_dict[parameter]["paths"]) > 1:
                    self.show_warning_window = True
                    print(f"Different paths found for message {parameter}: {self.xml_messages_dict[parameter]["paths"]}, please specify the complete path")
                else:
                    # if only one path, access the first element to get the path and split by (".") to get the equipment, module and partition
                    path_list = self.xml_messages_dict[parameter]["paths"][0].split(".")
                    searched_equipment_name = path_list[0]
                    searched_module_name = path_list[1]
                    searched_partition_name = path_list[2]
            else:
                self.show_warning_window = True
                print(f"Path not found for message: {parameter}, check the name or specify the complete path")

            return searched_partition_name, searched_module_name, searched_equipment_name
    
    def search_instruction_value_in_xml_signals_dict(self, signal, value):
        """Check if signal has enum structure"""
        signal_in_parameter_file = self.search_parameter_in_parameter_file(signal)
        if signal_in_parameter_file:
            signal = signal_in_parameter_file
        if signal in self.xml_signals_dict:
            value_in_parameter_file = self.search_parameter_in_parameter_file(value)
            if value_in_parameter_file:
                value = value_in_parameter_file
            if "enum" in self.xml_signals_dict[signal]:
                if value in self.xml_signals_dict[signal]["enum"]:
                    return self.xml_signals_dict[signal]["enum"][value]
        else:
            return None
    
    def search_in_xml_buses_dict(self):
        """Check if the parameter is in the xml_buses_dict or not"""
        bus_name = self.instruction.signal_or_bus_name
        bus_name_in_parameter_file = self.search_parameter_in_parameter_file(bus_name)
        if bus_name_in_parameter_file:
            bus_name = bus_name_in_parameter_file
        value = self.instruction.value
        value_in_parameter_file = self.search_parameter_in_parameter_file(value)
        if value_in_parameter_file:
            value = value_in_parameter_file
        if bus_name in self.xml_buses_dict:
            mode_found = next((mode for mode in self.xml_buses_dict[bus_name] if value in mode), None)
            if mode_found:
                mode_value = self.xml_buses_dict[bus_name][mode_found]
                return mode_found, mode_value
            else:
                self.show_warning_window = True
                return "Mode not found", None
        else:
            return None, None
        
# ==== PROCESSED TEMPLATE PREVIEW CLASS ====

class HumanizedSyntaxTemplatePreviewDialog(ctk.CTkToplevel):
    """Dialog to preview file content before saving. Requires the user to explicitly confirm or cancel the save action"""
    def __init__(self, parent, text_content, title="Processed Template Preview"):
        super().__init__(parent)
        self.title(title)
        self.geometry("1100x700")
        
        self.after(100, lambda: (self.lift(), self.focus())) # self.lift bring the window to the front
        
        self.user_choice = False 

        # UI Elements
        lbl = ctk.CTkLabel(self, text="Please review the file content before saving:", font=("Roboto", 14, "bold"))
        lbl.pack(pady=(10, 5), padx=10, anchor="w")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 10))

        self.line_num = tk.Canvas(self.container, width=40, bg="#1e1e1e", bd=0, highlightthickness=0)
        self.line_num.pack(side="left", fill="y")

        self.textbox = ctk.CTkTextbox(self.container, font=("Consolas", 15), wrap="none", fg_color="#1e1e1e", text_color="#D4D4D4", corner_radius=0)
        self.textbox.pack(side="left", fill="both", expand=True)
        
        self.textbox.insert("0.0", text_content)
        self.textbox.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.btn_save = ctk.CTkButton(
            btn_frame, text="Save as...", fg_color="#2E7D32", hover_color="#1B5E20", 
            command=self.on_save_as
        )
        self.btn_save.pack(side="right", padx=5)
        
        self.btn_save = ctk.CTkButton(
            btn_frame, text="Save", fg_color="#2E7D32", hover_color="#1B5E20", 
            command=self.on_save
        )
        self.btn_save.pack(side="right", padx=5)
        
        self.btn_cancel = ctk.CTkButton(
            btn_frame, text="Cancel", fg_color="#C62828", hover_color="#B71C1C", 
            command=self.on_cancel
        )
        self.btn_cancel.pack(side="right", padx=5)

        self.textbox._textbox.bind("<MouseWheel>", lambda e: self.after(10, self.draw_line_numbers), add="+")
        self.textbox._textbox.bind("<B1-Motion>", lambda e: self.after(10, self.draw_line_numbers), add="+")
        self.textbox._textbox.bind("<Configure>", lambda e: self.draw_line_numbers(), add="+")

        original_command = self.textbox._textbox.cget("yscrollcommand")
        
        def intercepted_scroll(*args):
            if original_command:
                self.textbox._textbox.tk.call(original_command, *args)
            
            self.draw_line_numbers()

        self.textbox._textbox.configure(yscrollcommand=intercepted_scroll)

        self._configure_editor_tags()
        self._perform_highlight()
        self.draw_line_numbers()

    def on_save(self):
        """Sets the user choice flag to True and closes the dialog."""
        self.user_choice = "Save"
        self.destroy()

    def on_save_as(self):
        """Sets the user choice flag to True and closes the dialog."""
        self.user_choice = "Save as..."
        self.destroy()

    def on_cancel(self):
        """Sets the user choice flag to False and closes the dialog."""
        self.user_choice = False
        self.destroy()

    def _configure_editor_tags(self):
        """Applies color configuration to text tags based on Pygments token mapping."""
        for token, color in TOKEN_COLORS.items():
            color_hex = f"#{color}" if color else "black"
            self.textbox.tag_config(token, foreground=color_hex)
    
    def _perform_highlight(self):
        """Parses the text and applies Pygments syntax highlighting tags."""
        content = self.textbox.get("1.0", "end-1c")
        lexer = lexers.get_lexer_by_name("jinja", stripnl=False)
        
        # Remove old tags before re-applying
        for tag in self.textbox.tag_names():
            if tag != "sel": 
                self.textbox.tag_remove(tag, "1.0", "end")

        index = "1.0"
        for token_type, value in lex(content, lexer):
            end_index = self.textbox.index(f"{index} + {len(value)}c")
            tag_name = str(token_type)
            if tag_name in TOKEN_COLORS and TOKEN_COLORS[tag_name]:
                self.textbox.tag_add(tag_name, index, end_index)
            index = end_index

    def draw_line_numbers(self):
        """Calculates visible lines and draws the numbers on the margin canvas."""   
        self.line_num.delete("all")

        # Get the index of the first currently visible line on screen
        i = self.textbox._textbox.index("@0,0")
        while True:
            dline = self.textbox._textbox.dlineinfo(i)
            if dline is None:
                break # Reached the bottom of the visible screen
            
            y = dline[1]
            actual_y = y + 2 # Offset to match CTkTextbox internal padding
            linenum = str(i).split(".")[0]
            
            # Draw the number dynamically
            self.line_num.create_text(35, actual_y, anchor="ne", text=linenum, font=("Consolas", 12), fill="#858585")
            
            # Move index to the next visual line
            i = self.textbox._textbox.index(f"{i}+1line")