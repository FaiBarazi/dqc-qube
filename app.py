from shiny import App, ui, render, reactive
from shinywidgets import output_widget, render_widget
import io
import importlib
import json
import sys
import traceback
import pennylane as pq
import os
from pathlib import Path
import markdown
import plotly.graph_objects as go
import qiskit
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import Parameter, ParameterVector
from qiskit.quantum_info import SparsePauliOp, Statevector

from pipeline.converters.qiskit_converter import ConversionError, source_to_circuit
from pipeline.converters.sandbox import (
    ALLOWED_IMPORT_ROOTS_QISKIT,
    EntryPointConfig,
    build_execution_namespace,
)
from pipeline.evaluation_pipeline import get_reference_circuit
from pipeline.benchmark_pipeline import benchmark_metrics


MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js"
MATHJAX_CONFIG = r"""
window.MathJax = {
    tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']],
        processEscapes: true
    },
    options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
    },
    startup: {
        typeset: false
    }
};
"""
MATHJAX_SHINY_HANDLER = r"""
(function () {
    const outputId = 'problem_description';

    function mathJaxIsReady() {
        return window.MathJax &&
            window.MathJax.startup &&
            window.MathJax.startup.promise &&
            typeof window.MathJax.typesetPromise === 'function';
    }

    function typesetProblemDescription() {
        const container = document.getElementById(outputId);
        if (!container || !mathJaxIsReady()) {
            return;
        }

        window.MathJax.startup.promise
            .then(function () {
                return window.MathJax.typesetPromise([container]);
            })
            .catch(function (error) {
                console.error('MathJax could not render the problem description.', error);
            });
    }

    document.addEventListener('DOMContentLoaded', function () {
        window.jQuery(document).on('shiny:value', function (event) {
            if (event.name !== outputId) {
                return;
            }

            const container = document.getElementById(outputId);
            if (
                container &&
                window.MathJax &&
                typeof window.MathJax.typesetClear === 'function'
            ) {
                window.MathJax.typesetClear([container]);
            }

            window.setTimeout(typesetProblemDescription, 0);
        });
    });
})();
"""


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


def render_problem_markdown(md_text: str) -> str:
    """Convert problem Markdown to HTML while preserving MathJax delimiters."""
    return markdown.markdown(md_text, extensions=["extra", "codehilite"])


def get_starter_code(problem_name: str) -> str:
    """Load the starter code from starter.py."""
    starter_path = Path(__file__).parent / "problems" / problem_name / "starter.py"
    if starter_path.exists():
        return starter_path.read_text()
    return "# Starter code not found"


def get_problem_metadata(problem_name: str) -> dict:
    """Load metadata.json for a problem. Returns empty dict on failure."""
    meta_path = Path(__file__).parent / "problems" / problem_name / "metadata.json"
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text())
        except Exception:
            return {}
    return {}


def load_problem_tests(problem_name: str):
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    module_name = f"problems.{problem_name}.tests"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None
    except Exception:
        return None


def get_entry_point_config(metadata: dict) -> EntryPointConfig:
    """Extract entry point configuration from problem metadata.
    
    If no entry_point field exists, returns default config (function mode, name="solve").
    """
    entry_point_data = metadata.get("entry_point")
    if entry_point_data is None:
        return EntryPointConfig(mode="function", name="solve")
    
    # Parse the entry_point config from metadata
    mode = entry_point_data["mode"]
    name = entry_point_data["name"]
    method_name = entry_point_data.get("method_name","")
    args = entry_point_data.get("args", [])
    kwargs = entry_point_data.get("kwargs", {})
    
    return EntryPointConfig(
        mode=mode,
        name=name,
        method_name=method_name,
        args=args,
        kwargs=kwargs,
    )


def source_to_entry_point(source: str, entry_point_config: EntryPointConfig):
    """Execute Qiskit source and return the configured entry point object."""
    namespace = build_execution_namespace(
        allowed_import_roots=ALLOWED_IMPORT_ROOTS_QISKIT,
        extra_symbols={
            "ClassicalRegister": ClassicalRegister,
            "Parameter": Parameter,
            "ParameterVector": ParameterVector,
            "QuantumCircuit": QuantumCircuit,
            "QuantumRegister": QuantumRegister,
            "SparsePauliOp": SparsePauliOp,
            "Statevector": Statevector,
            "qiskit": qiskit,
        },
    )

    try:
        exec(compile(source, "<submission>", "exec"), namespace)
    except Exception as exc:
        raise ConversionError(f"Could not execute submission source: {exc}") from exc

    entry_point = namespace.get(entry_point_config.name)
    if entry_point is None:
        raise ConversionError(
            f"Submission must define a callable '{entry_point_config.name}'"
        )
    if not callable(entry_point):
        raise ConversionError(
            f"Submission entry point '{entry_point_config.name}' is not callable"
        )

    return entry_point


def get_validation_target(problem_tests) -> str:
    return getattr(problem_tests, "VALIDATION_TARGET", "circuit")


def format_validation_key(key: str) -> str:
    return key.replace("_", " ").capitalize()


def format_validation_scalar(key: str, value) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if "fidelity" in key:
            return f"{value:.6f}"
        if "delta" in key or "threshold" in key:
            return f"{value:.3e}"
        return f"{value:.12f}"
    return str(value)


def format_validation_field(key: str, value, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    label = format_validation_key(key)

    if isinstance(value, dict):
        lines = [f"{prefix}{label}:"]
        for nested_key, nested_value in value.items():
            lines.extend(
                format_validation_field(nested_key, nested_value, indent + 1)
            )
        return lines

    if isinstance(value, (list, tuple)):
        display_value = ", ".join(str(item) for item in value) if value else "None"
        return [f"{prefix}{label}: {display_value}"]

    return [f"{prefix}{label}: {format_validation_scalar(key, value)}"]


def format_validation_result(validation: dict) -> str:
    if not isinstance(validation, dict):
        return f"Validation returned unexpected result: {validation}"

    lines = [
        f"Validation: {validation.get('message', 'n/a')}",
        f"Passed: {validation.get('passed', False)}",
    ]

    for key, value in validation.items():
        if key in {"message", "passed"}:
            continue
        lines.extend(format_validation_field(key, value))

    return "\n".join(lines)


app_ui = ui.page_fluid(
    ui.head_content(
        # MathJax configuration must be defined before the deferred library loads.
        ui.tags.script(MATHJAX_CONFIG),
        ui.tags.script(src=MATHJAX_URL, defer_=""),
        # Problem descriptions are reactive, so typeset after every Shiny update.
        ui.tags.script(MATHJAX_SHINY_HANDLER),
        # CodeMirror CSS
        ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css"),
        ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/eclipse.min.css"),
        # CodeMirror JS
        ui.tags.script(src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"),
        ui.tags.script(src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/python/python.min.js"),
        # Plotly JS
        ui.tags.script(src="https://cdn.plot.ly/plotly-latest.min.js"),
        # Custom styles
        ui.tags.style("""
            .red-button { background-color: #e74c3c !important; border-color: #c0392b !important; }
            .red-button:hover { background-color: #c0392b !important; }
            .problem-section { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .code-section { background: white; padding: 20px; border-radius: 8px; display: flex; flex-direction: column; border: 1px solid #ddd; }
            .code-editor-label { color: #888; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
            #code_editor_container { border-radius: 4px; background: white; border: 1px solid #ccc; }
            .CodeMirror { background: white !important; color: #333 !important; height: 450px !important; }
            .CodeMirror-cursor { border-left: 2px solid #e74c3c !important; }
            .benchmark-section { background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 100%; box-sizing: border-box; }
            .benchmark-title { font-size: 20px; font-weight: 600; color: #222; margin-bottom: 4px; }
            .benchmark-subtitle { font-size: 13px; color: #888; margin-bottom: 16px; }
            .result-card { background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 100%; box-sizing: border-box; }
            .result-card pre.shiny-text-output { background: #f5f5f5; padding: 15px; border-radius: 4px; border: 1px solid #ddd; font-size: 13px; margin: 0; }
        """)
    ),
    ui.div(
        ui.h1(
            "Quantum Code Challenge",
            style="color: black; margin: 0; font-weight: 700; font-size: 48px;",
        ),
        style="background-color: white; padding: 30px; margin-bottom: 30px;",
    ),
    ui.row(
        ui.column(
            12,
            ui.div(
                ui.input_select(
                    "problem_selector",
                    "Select Problem:",
                    {p: p for p in get_problems()},
                    selected=get_problems()[0] if get_problems() else None,
                ),
                style="margin-bottom: 30px;",
            ),
        ),
    ),
    ui.row(
        ui.column(
            6,
            ui.div(
                ui.p("Description", style="font-size: 13px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 12px 0;"),
                ui.output_ui("problem_description"),
                class_="problem-section",
                style="height: 600px; overflow-y: auto;",
            ),
        ),
        ui.column(
            6,
            ui.div(
                ui.div(
                    ui.tags.span("PYTHON - QISKIT", class_="code-editor-label"),
                    style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;",
                ),
                ui.HTML(
                    '<textarea id="user_code" style="display: none;"></textarea>'
                ),
                ui.div(
                    id="code_editor_container",
                    style="margin-bottom: 15px;"
                ),
                ui.output_ui("_init_editor"),
                ui.input_action_button("run_code", "Submit solution", class_="btn-danger red-button", style="width: 100%; padding: 12px; font-weight: bold; font-size: 16px; border: none;"),
                class_="code-section",
                style="height: 600px; display: flex; flex-direction: column; overflow: hidden;",
            ),
        ),
    ),
    # ── Results + Benchmark ────────────────────────────────────────────────────
    ui.row(
        ui.column(
            6,
            ui.div(
                ui.p("Output", style="font-size: 13px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 12px 0;"),
                ui.output_text_verbatim("code_output"),
                class_="result-card",
            ),
        ),
        ui.column(
            6,
            ui.div(
                ui.p("Benchmark", style="font-size: 13px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 12px 0;"),
                ui.output_ui("benchmark_comparison"),
                class_="benchmark-section",
            ),
        ),
        style="margin-top: 24px; display: flex; align-items: stretch;",
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
        html_content = render_problem_markdown(md_text)
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
        code.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
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

    @reactive.calc
    def current_metadata():
        return get_problem_metadata(current_problem())

    @reactive.event(input.run_code)
    def submitted_code():
        return input.user_code() if input.user_code() else ""

    # Reactive that holds the benchmark comparison result (or an error string)
    # after a successful submission.  None = not yet submitted.
    _benchmark_result: reactive.Value = reactive.value(None)

    @reactive.effect
    @reactive.event(input.run_code)
    def _compute_benchmark():
        code = input.user_code() if input.user_code() else ""
        if not code.strip():
            _benchmark_result.set(None)
            return

        meta = current_metadata()
        entry_point_config = get_entry_point_config(meta)

        try:
            circuit = source_to_circuit(code, entry_point_config=entry_point_config)
            ref_circuit = get_reference_circuit(current_problem(), meta, circuit.num_qubits)
            result = benchmark_metrics(ref_circuit, circuit)
            _benchmark_result.set(result)
        except Exception as exc:
            _benchmark_result.set({"error": str(exc)})

    @output
    @render.text
    def code_output():
        code = submitted_code()
        if not code or not code.strip():
            return "Enter Python code in the editor and click Run code."

        meta = current_metadata()
        entry_point_config = get_entry_point_config(meta)
        problem_tests = load_problem_tests(current_problem())
        if problem_tests is None:
            return "Could not load validation tests for this problem."

        validation_target = get_validation_target(problem_tests)
        if validation_target == "entry_point":
            try:
                entry_point = source_to_entry_point(code, entry_point_config)
            except ConversionError as exc:
                return f"ConversionError: {exc}"
            except Exception:
                return traceback.format_exc()

            try:
                validation = problem_tests.validate(entry_point)
            except Exception as exc:
                return f"Could not validate solution: {exc}"

            return "\n".join(
                [
                    "Entry point loaded successfully.",
                    f"Entry point: {entry_point_config.name}",
                    format_validation_result(validation),
                ]
            )

        try:
            circuit = source_to_circuit(code, entry_point_config=entry_point_config)
        except ConversionError as exc:
            return f"ConversionError: {exc}"
        except Exception:
            return traceback.format_exc()

        try:
            validation = problem_tests.validate(circuit)
        except Exception as exc:
            return f"Could not validate solution: {exc}"

        result_lines = [
            "Circuit built successfully.",
            f"Qubits: {circuit.num_qubits}",
            format_validation_result(validation),
        ]

        return "\n".join(result_lines)

    # ── MQT Bench comparison visual ────────────────────────────────────────
    @output
    @render.ui
    def benchmark_comparison():
        result = _benchmark_result.get()

        # Nothing submitted yet
        if result is None:
            return ui.div(
                ui.p(
                    "Submit a solution to see how your circuit compares against the reference.",
                    style="color: #aaa; font-style: italic; text-align: center; padding: 20px 0;",
                )
            )

        # Benchmark computation hit an error
        if "error" in result:
            return ui.div(
                ui.p(
                    f"Could not compute benchmark comparison: {result['error']}",
                    style="color: #c0392b;",
                )
            )

        # Build grouped bar chart
        metrics_labels = [
            ("depth",             "Depth"),
            ("num_single_gates",  "Single-Qubit Gates"),
            ("controlled_gates",  "Controlled Gates"),
            ("total_num_gates",   "Total Gates"),
        ]

        submitted_vals = [result["submitted"][k] for k, _ in metrics_labels]
        reference_vals = [result["reference"][k]  for k, _ in metrics_labels]
        y_labels       = [label for _, label in metrics_labels]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Your Circuit",
            y=y_labels,
            x=submitted_vals,
            orientation="h",
            marker_color="#e74c3c",
            text=submitted_vals,
            textposition="outside",
        ))
        fig.add_trace(go.Bar(
            name="Reference Circuit",
            y=y_labels,
            x=reference_vals,
            orientation="h",
            marker_color="#3d3d3d",
            text=reference_vals,
            textposition="outside",
        ))

        meta = current_metadata()
        problem_title = meta.get("title", current_problem())

        fig.update_layout(
            barmode="group",
            title=dict(
                text=f"{problem_title}: Your Solution vs Reference",
                font=dict(size=14, color="#222"),
                x=0,
                xref="paper",
                xanchor="left",
            ),
            xaxis=dict(title="Count", tickfont=dict(size=12), showgrid=True, gridcolor="#eee", showticklabels=False),
            yaxis=dict(title="", tickfont=dict(size=12), showgrid=False, autorange="reversed", ticklabelposition="inside"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(t=70, b=40, l=10, r=50),
            height=380,
        )

        chart_html = fig.to_html(
            full_html=False,
            include_plotlyjs="cdn",
            config={"displayModeBar": False},
        )

        return ui.div(
            ui.p(
                "Comparison against the reference circuit at the algorithm level "
                "(no transpilation / gate mapping applied).",
                class_="benchmark-subtitle",
            ),
            ui.HTML(chart_html),
        )


app = App(app_ui, server, static_assets=None)
