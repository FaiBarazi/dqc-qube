from shiny import App, ui, render, reactive
import io
import traceback
import pennylane as qml

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
            6,
            ui.div(
                ui.h3("Code editor"),
                ui.p(
                    "Paste your Python code below and click Run to execute it on the backend."
                ),
                ui.HTML(
                    '<textarea id="user_code" style="display: none;">print(\'Hello Qube!\')\n</textarea>'
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
        ui.column(
            6,
            ui.div(
                ui.h3("Execution result"),
                ui.output_text_verbatim("code_output"),
                style="padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #f3f6ff; min-height: 400px; white-space: pre-wrap;",
            ),
        ),
    ),
)

def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    allowed = {"pennylane", "qml", "math", "numpy", "random"}
    root = name.split(".")[0]
    if root in allowed:
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Import of module '{name}' is not allowed in the sandbox")

def safe_execute(code: str) -> str:
    """Run user code in a restricted environment and return captured output."""
    output_buffer = io.StringIO()
    def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        allowed = {"pennylane", "qml", "math", "numpy", "random"}
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
    namespace = {"__builtins__": safe_builtins, "qml": qml, "pennylane": qml}

    try:
        exec(code, namespace)
    except Exception:
        traceback.print_exc(file=output_buffer)

    return output_buffer.getvalue()


def server(input, output, session):
    # Initialize the CodeMirror editor
    @output
    @render.ui
    def _init_editor():
        return ui.HTML(
            """
            <script>
            (function() {
                const textarea = document.getElementById('user_code');
                const editor = CodeMirror(document.getElementById('code_editor_container'), {
                    value: textarea.value,
                    mode: 'python',
                    theme: 'eclipse',
                    lineNumbers: true,
                    lineWrapping: true,
                    indentUnit: 4,
                    indentWithTabs: false,
                    tabSize: 4,
                    autoIndent: true,
                    matchBrackets: true,
                    highlightSelectionMatches: { showToken: /\\w/, annotateScrollbar: true },
                    styleActiveLine: true,
                    styleActiveSelected: true,
                    extraKeys: {
                        'Tab': function(cm) {
                            if (cm.somethingSelected()) {
                                cm.indentSelection('add');
                            } else {
                                cm.replaceSelection('    ', 'end');
                            }
                        },
                        'Shift-Tab': function(cm) {
                            cm.indentSelection('subtract');
                        }
                    }
                });
                
                // Sync editor content to hidden textarea
                editor.on('change', function() {
                    textarea.value = editor.getValue();
                    Shiny.setInputValue('user_code', editor.getValue());
                });
                
                // Store editor globally for server access
                window.codeEditor = editor;
            })();
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

