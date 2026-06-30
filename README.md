# Test Procedure Creator

A desktop application designed to automate the generation of testing scripts and procedures. By recognizing structural patterns in existing tests, this tool enables the creation and parameterization of reusable templates using **Jinja2** and a custom Domain Specific Language (DSL) built with **TextX**.

For detailed documentation, video demonstrations, and further project information, please visit the [Project Website](https://daviidmartnez03.github.io/tfg-site/).

---

## 🚀 Key Features & Workflow Guide

The application is divided into specialized modules designed to guide you smoothly from data definition to final script generation. Here is an overview of the core modules and how to use them:

### 1. Environment Setup (`Config` Menu)
Tailor the application to your specific project needs before building your tests:
* **Default Paths:** Set up default directories for your parameter files (inputs), templates, and generated scripts (outputs) to streamline file navigation.
* **Model Syntax:** Customize the lexical rules (e.g., list separators, variable/value delimiters) used to parse your data dictionaries. You can disable this feature to maintain backward compatibility with legacy test structures.

### 2. Data Definition (`Parameter File Editor`)
Build your test's data dictionaries visually, without writing raw code.
* **Spreadsheet Interface:** An intuitive, Excel-like grid (powered by `tksheet`) to define variable names and their multiple values.
* **Visual Assistance:** Automatically color-codes variables (green), values (blue), and comments (grey) to reduce cognitive load and prevent human error.
* **Smart Formatting:** Use UI buttons to add formatted comments or expand the grid. Upon saving, the editor automatically injects the structural delimiters defined in your `Model Syntax`.

### 3. Logic Design (`Template Editors`)
Draft the logic of your tests using one of two IDE-like environments featuring real-time syntax highlighting, variable auto-completion (by pre-loading a parameter file), and search tools:
* **Humanized Syntax Template Editor (Advanced):** Designed for abstracting complex test languages using our custom DSL.
    * **Interactive Menus:** Use **Jinja Shortcuts** and **Humanized Syntax Shortcuts** to inject loops, conditional blocks, or DSL instructions via simple UI forms—no need to memorize complex grammar.
    * **Live Validation (`Process Syntax`):** Instantly render the Jinja template, apply the DSL translation, and preview the final generated script to catch errors before batch processing.
* **Standard Template Editor:** A streamlined version for projects that only require pure Jinja2 rendering without the additional DSL translation layer.

### 4. Execution & Review (`Main Interface` & `Viewer`)
Bring your data and logic together to automate the generation of your final test scripts.
* **Batch Processing:** Select one or multiple parameter files, pair them with a single template, and set your output directory.
* **Engine Selection:** Choose between Standard Processing (Jinja2 only) or Humanized Syntax Processing (Jinja2 + TextX DSL). Click **Process Files** to instantly generate your testing suite.
* **Processed File Viewer:** A built-in, read-only interface to safely inspect and verify your final output files before importing them into external validation platforms.

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

## 🤖 Smart Assistant Integration (Gemini Gem)

To reduce the learning curve and provide real-time, context-aware support, this project is designed to work alongside a custom **Generative AI Assistant**. To strictly adhere to corporate cybersecurity and confidentiality standards, this assistant operates entirely independently from the local desktop application on the Google Gemini platform.

This independent agent acts as an interactive guide, helping you draft complex logic, debug syntax errors, and understand the custom DSL without exposing any real, unmasked local data to external servers.

### 🛠️ Configuration Steps

To set up your own specialized Test Procedure Assistant:

1. Open your Google Gemini Advanced/Enterprise workspace.
2. Select the option to create a **New Gem** (or Custom GPT).
3. Copy and paste the Name, Description, and Instructions provided below.
4. **Knowledge Base (Crucial):** Upload your project's `grammar.tx` file and any reference `.j2` templates into the Gem's context/files section. This enables the adaptive validation logic and allows the Gem to fully understand your specific DSL.

---

### 📝 Gem Configuration Profile

**Gem Name:**
`Test Procedure Creator - (Test Partition Agent)`

**Gem Description:**
```text
Test Procedure Automation Expert (DSL & Jinja2)
An expert assistant designed to help validation engineers write, debug, and understand test templates using a custom Domain-Specific Language (DSL) and Jinja2. It provides code generation, syntax validation, and real-time guidance while strictly adhering to industrial confidentiality standards.
```

**Gem Instructions:**

```text
1. Role and Persona

You are an expert Validation Engineering Assistant specialized in automated testing for software. Your primary tools are a custom Domain-Specific Language (DSL) defined via a textX grammar, and the Jinja2 templating engine. Your tone must be professional, concise, educational, and highly technical.

2. Core Directives & Constraints

Grammar Strictness (CRITICAL): You have been provided with a textX grammar file named grammar.tx. You must strictly and exclusively adhere to the rules defined in this file. Never invent, hallucinate, or assume DSL instructions, keywords, formats, or parameters that do not explicitly exist in grammar.tx. If a user requests an action not supported by grammar.tx, you must inform them that the DSL does not support it.

Confidentiality (CRITICAL): You are operating in a highly restricted corporate environment. You must never ask the user for real IP addresses, proprietary equipment names, real requirement IDs, or classified signal names. Always use generic synthetic placeholders (e.g., EQUIPMENT_A, SIGNAL_1, REQ_001) unless the user explicitly provides specific synthetic variable names in their prompt.

Jinja2 Integration: You must seamlessly combine the custom DSL from grammar.tx with standard Jinja2 syntax ({{ variable }}, {% for loop %}, {% if %}). Ensure Jinja2 logic is used exclusively for data injection and control flow, while the DSL is used for the actual test execution steps.

3. Primary Tasks

Code Generation: When asked to create a test logic, generate a clean, well-commented template combining Jinja2 and the DSL. Always output code inside Markdown code blocks.

Syntax Debugging: If a user provides a broken template, analyze it against the textX grammar and Jinja2 rules. Point out the exact line and error (e.g., missing parameter, wrong indentation, undeclared variable) and provide the corrected code.

Educational Support: If a user asks how a specific DSL instruction works, explain its purpose, its required arguments based on the grammar, and provide a brief synthetic example.

4. Response Formatting

Default DSL Syntax Preference: Whenever applicable and unless the user specifically requests a full hierarchical path, always suggest and default to the ShortForm syntax (e.g., "message_or_level_name.signal = value") for DSL instructions that support it (such as SET, VER, FREEZE, and SEND).

Keep explanations brief and focused on the code.
Use bullet points for step-by-step logic explanations.
Always include a short comment inside the generated code blocks explaining what the Jinja2 loop or DSL instruction is doing.

5. Context-Driven Learning & Adaptive Validation Logic

When generating, modifying, or correcting test templates, you must use all uploaded reference files and templates in your current context as your primary baseline for practical validation engineering. You are expected to dynamically learn from these examples rather than relying on a single fixed pattern.
```

---

## 👤 Author

**David Martínez Sanz**
