# Test Procedure Creator

A desktop application designed to automate the generation of testing scripts and procedures. By recognizing structural patterns in existing tests, this tool enables the creation and parameterization of reusable templates using **Jinja2** and a custom Domain Specific Language (DSL) built with **TextX**.

For detailed documentation, video demonstrations, and further project information, please visit the [Project Website](https://daviidmartnez03.github.io/tfg-site/).

---

## 🚀 Key Features

* **Main Interface:** A centralized dashboard to select parameter files, templates, and output directories. It allows users to quickly switch between standard processing (Jinja only) and DSL processing (Jinja + TextX).
* **Parameter File Editor:** An Excel-style spreadsheet editor (powered by `tksheet`) to manage variable/value pairs. Features include dynamic row/column addition, syntax highlighting (green for variables, blue for values, grey for comments), custom list separators, and inline commenting.
* **Humanized Syntax Template Editor:** An advanced IDE-like editor built with `customtkinter` and `pygments`. It bridges the gap between complex test scripts and user-friendly design:
    * **Jinja Shortcuts:** One-click UI insertions for variables, for-loops, comments, and raw code snippets.
    * **DSL Shortcuts:** Automated UI prompts to fill out custom DSL instructions without needing to memorize the underlying grammar.
    * **Process Syntax:** A live preview feature that renders the Jinja template with loaded parameters, applies the DSL grammar, and displays the final output in a read-only viewer.
* **Standard Template Editor:** A streamlined version of the editor focused purely on Jinja syntax generation.
* **Processed File Viewer:** A dedicated interface to review and inspect generated output files.
* **Dynamic Configuration:** Customize default file paths and syntax models (list separators, variable identifiers) globally or per project via the built-in configuration menu.

---

## 📁 Project Structure

The application follows a modular structure. All project environments must be contained directly within the `models/` directory.

* `app/`: Contains the core Python application code, UI components, and logic.
* `models/`: Root directory for all projects.
    * `Proyecto 1/`: An example of an existing project environment.
    * **Creating a New Project:** To add a new project, create a new folder directly inside `models/` (e.g., `models/Proyecto 2/`) and replicate this mandatory internal structure:
        * `input/`: Default folder for parameter files.
        * `output/`: Default folder for processed generated files.
        * `template/`: Default folder for Jinja/DSL templates.
        * `textx/`: Houses the specific `grammar.tx` file containing the syntax definition for that project's DSL.
* `MTB_test_procedure.bat`: Execution script.
* `requirements.txt`: Python dependencies.

---

## ⚙️ Installation & Usage

**Prerequisites:** Ensure you have Python installed on your system.

**1. Install Dependencies:**
Navigate to the root directory of the project in your terminal and run:
```bash
pip install -r requirements.txt

```

**2. Run the Application:**
Execute the provided batch file to start the program:

```bash
.\MTB_test_procedure.bat
```

*Note: Upon the first execution, a shortcut will automatically be generated on your desktop. For all future uses, you can simply double-click the desktop shortcut to launch the application directly.*

---

## 👤 Author

**David Martínez Sanz**
