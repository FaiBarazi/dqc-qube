from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

import qiskit
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, qasm3
from qiskit.circuit import Parameter, ParameterVector

from pipeline.converters.errors import ConversionError
from pipeline.converters.sandbox import SAFE_BUILTINS, ALLOWED_IMPORT_ROOTS_QISKIT as ALLOWED_IMPORT_ROOTS


@dataclass(frozen=True)
class QiskitConversionResult:
    circuit: QuantumCircuit
    qasm: str


# SAFE_BUILTINS and ALLOWED_IMPORT_ROOTS are provided by pipeline.converters.sandbox


def circuit_to_qasm3(circuit: QuantumCircuit) -> str:
    """Convert a Qiskit QuantumCircuit into an OpenQASM 3 string."""
    _ensure_quantum_circuit(circuit)

    try:
        return qasm3.dumps(circuit)
    except Exception as exc:
        raise ConversionError(f"Could not convert circuit to OpenQASM 3: {exc}") from exc


def export_circuit_to_qasm3(circuit: QuantumCircuit, output_path: Union[str, Path]) -> Path:
    """Convert a Qiskit circuit to OpenQASM 3 and write it to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(circuit_to_qasm3(circuit), encoding="utf-8")
    return path


def source_to_circuit(source: str, function_name: str = "solve") -> QuantumCircuit:
    """
    Execute Qiskit source code and return the circuit produced by `function_name`.

    This is intended for local conversion and MVP judging only. Production user
    submissions should run in a separate sandboxed process or container.
    """
    namespace = _build_execution_namespace()

    try:
        exec(compile(source, "<qiskit-submission>", "exec"), namespace)
    except Exception as exc:
        raise ConversionError(f"Could not execute Qiskit source: {exc}") from exc

    solve = namespace.get(function_name)
    if not callable(solve):
        raise ConversionError(f"Submission must define a callable `{function_name}` function.")

    try:
        circuit = solve()
    except Exception as exc:
        raise ConversionError(f"`{function_name}` failed while building the circuit: {exc}") from exc

    _ensure_quantum_circuit(circuit)
    return circuit


def source_to_qasm3(source: str, function_name: str = "solve") -> QiskitConversionResult:
    """Execute Qiskit source code and convert the returned circuit to OpenQASM 3."""
    circuit = source_to_circuit(source, function_name=function_name)
    return QiskitConversionResult(circuit=circuit, qasm=circuit_to_qasm3(circuit))


def _ensure_quantum_circuit(circuit: Any) -> None:
    if not isinstance(circuit, QuantumCircuit):
        raise ConversionError("Expected a qiskit.QuantumCircuit.")


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".")[0]
    if root in ALLOWED_IMPORT_ROOTS:
        return __import__(name, globals, locals, fromlist, level)

    raise ImportError(f"Import of module '{name}' is not allowed during conversion.")


def _build_execution_namespace() -> dict[str, Any]:
    safe_builtins = dict(SAFE_BUILTINS)
    safe_builtins["__import__"] = _safe_import

    return {
        "__builtins__": safe_builtins,
        "__name__": "__qiskit_submission__",
        "ClassicalRegister": ClassicalRegister,
        "Parameter": Parameter,
        "ParameterVector": ParameterVector,
        "QuantumCircuit": QuantumCircuit,
        "QuantumRegister": QuantumRegister,
        "qiskit": qiskit,
    }
