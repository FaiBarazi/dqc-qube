from shiny import App, ui, render, reactive
import io
import traceback
import pennylane as pq
import os
from pathlib import Path
import markdown


def get_problems():
    """Discover available problems from the problems directory."""
    problems_dir = Path(__file__).parent / "problems"
    if not problems_dir.exists():
        return []
    
    problems = []
    for problem_dir in sorted(problems_dir.iterdir()):
        if problem_dir.is_dir() and (problem_dir / "problem.md").exists():
            problems.append(problem_dir.name)
    return problems


def get_problem_description(problem_name: str) -> str:
    """Load the problem description from problem.md."""
    problem_path = Path(__file__).parent / "problems" / problem_name / "problem.md"
    if problem_path.exists():
        return problem_path.read_text()
    return "Problem description not found."


def get_starter_code(problem_name: str) -> str:
    """Load the starter code from starter.py."""
    starter_path = Path(__file__).parent / "problems" / problem_name / "starter.py"
    if starter_path.exists():
        return starter_path.read_text()
    return "# Starter code not found"

app_ui = ui.page_fluid(
    ui.head_content(
        # CodeMirror CSS
        ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css"),
        ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/eclipse.min.css"),
        # CodeMirror JS
        ui.tags.script(src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"),
        ui.tags.script(src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/python/python.min.js"),
    ),
    ui.div(
        ui.h2(
            "Qube - Quantum Leetcode",
            style="color: white; margin: 0; font-weight: 400;",
        ),
        style="background-color: #363636; padding: 15px 20px; margin-bottom: 20px; border-bottom: 2px solid #444;",
    ),
    ui.row(
        ui.column(
            12,
            ui.div(
                ui.h3("Select Problem"),
                ui.input_select(
                    "problem_selector",
                    "Choose a problem:",
                    {p: p for p in get_problems()},
                    selected=get_problems()[0] if get_problems() else None,
                ),
                style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #f9f9f9; margin-bottom: 20px;",
            ),
        ),
    ),
    ui.row(
        ui.column(
            6,
            ui.div(
                ui.h3("Problem Description"),
                ui.output_ui("problem_description"),
                style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: white; min-height: 300px; max-height: 400px; overflow-y: auto;",
            ),
        ),
        ui.column(
            6,
            ui.div(
                ui.h3("Execution result"),
                ui.output_text_verbatim("code_output"),
                style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #f3f6ff; min-height: 300px; max-height: 400px; overflow-y: auto; white-space: pre-wrap;",
            ),
        ),
    ),
    ui.row(
        ui.column(
            12,
            ui.div(
                ui.h3("Code editor"),
                ui.p(
                    "Paste your Python code below and click Run to execute it on the backend."
                ),
                ui.HTML(
                    '<textarea id="user_code" style="display: none;"></textarea>'
                ),
                ui.div(
                    id="code_editor_container",
                    style="border: 1px solid #ccc; border-radius: 4px; height: 400px; margin-bottom: 15px; background: white;"
                ),
                ui.output_ui("_init_editor"),
                ui.input_action_button("run_code", "Run code", class_="btn-primary"),
                style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #f9f9f9;",
            ),
        ),
    ),
)

def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    allowed = {"pennylane", "pq", "math", "numpy", "random"}
    root = name.split(".")[0]
    if root in allowed:
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Import of module '{name}' is not allowed in the sandbox")

def safe_execute(code: str) -> str:
    """Run user code in a restricted environment and return captured output."""
    output_buffer = io.StringIO()
    def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        allowed = {"pennylane", "pq", "math", "numpy", "random"}
        root = name.split(".")[0]
        if root in allowed:
            return __import__(name, globals, locals, fromlist, level)
        raise ImportError(f"Import of module '{name}' is not allowed in the sandbox")

    safe_builtins = {
        "abs": abs,
        "all": all,
        "any": any,
        "bin": bin,
        "bool": bool,
        "chr": chr,
        "divmod": divmod,
        "float": float,
        "format": format,
        "int": int,
        "len": len,
        "max": max,
        "min": min,
        "pow": pow,
        "range": range,
        "round": round,
        "str": str,
        "sum": sum,
        "print": lambda *args, **kwargs: print(*args, **kwargs, file=output_buffer),
        "__import__": _safe_import,
    }
    namespace = {"__builtins__": safe_builtins, "pq": pq, "pennylane": pq}

    try:
        exec(code, namespace)
    except Exception:
        traceback.print_exc(file=output_buffer)

    return output_buffer.getvalue()


def server(input, output, session):
    # Get the current problem
    @reactive.calc
    def current_problem():
        return input.problem_selector()
    
    # Display the problem description (rendered as markdown HTML)
    @output
    @render.ui
    def problem_description():
        md_text = get_problem_description(current_problem())
        html_content = markdown.markdown(md_text, extensions=['extra', 'codehilite'])
        # Wrap in styled div with markdown styling
        styled_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; line-height: 1.6; color: #333;">
            {html_content}
        </div>
        """
        return ui.HTML(styled_html)
    
    # Get starter code for the current problem
    @reactive.calc
    def starter_code():
        return get_starter_code(current_problem())
    
    # Initialize the CodeMirror editor
    @output
    @render.ui
    def _init_editor():
        code = starter_code()
        # Escape the code properly for JavaScript
        escaped_code = code.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return ui.HTML(
            f"""
            <script>
            (function() {{
                const textarea = document.getElementById('user_code');
                // Check if editor already exists
                if (window.codeEditor) {{
                    // Update existing editor
                    window.codeEditor.setValue({repr(code)});
                }} else {{
                    // Create new editor
                    const editor = CodeMirror(document.getElementById('code_editor_container'), {{
                        value: {repr(code)},
                        mode: 'python',
                        theme: 'eclipse',
                        lineNumbers: true,
                        lineWrapping: true,
                        indentUnit: 4,
                        indentWithTabs: false,
                        tabSize: 4,
                        autoIndent: true,
                        matchBrackets: true,
                        highlightSelectionMatches: {{ showToken: /\\w/, annotateScrollbar: true }},
                        styleActiveLine: true,
                        styleActiveSelected: true,
                        extraKeys: {{
                            'Tab': function(cm) {{
                                if (cm.somethingSelected()) {{
                                    cm.indentSelection('add');
                                }} else {{
                                    cm.replaceSelection('    ', 'end');
                                }}
                            }},
                            'Shift-Tab': function(cm) {{
                                cm.indentSelection('subtract');
                            }}
                        }}
                    }});
                    
                    // Sync editor content to hidden textarea
                    editor.on('change', function() {{
                        textarea.value = editor.getValue();
                        Shiny.setInputValue('user_code', editor.getValue());
                    }});
                    
                    // Store editor globally for server access
                    window.codeEditor = editor;
                }}
            }})();
            </script>
            """
        )

    @reactive.event(input.run_code)
    def submitted_code():
        return input.user_code() if input.user_code() else ""

    @output
    @render.text
    def code_output():
        code = submitted_code()
        if not code or not code.strip():
            return "Enter Python code in the editor and click Run code."

        result = safe_execute(code)
        if result.strip() == "":
            return "Code executed successfully with no output."
        return result


app = App(app_ui, server)

