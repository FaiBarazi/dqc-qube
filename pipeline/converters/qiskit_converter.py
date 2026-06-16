from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

import qiskit
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, qasm3
from qiskit.circuit import Parameter, ParameterVector

from pipeline.converters.errors import ConversionError
from pipeline.converters.sandbox import (
    ALLOWED_IMPORT_ROOTS_QISKIT as ALLOWED_IMPORT_ROOTS,
    build_execution_namespace,
    execute_submission_source,
)


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
    """Execute Qiskit source code and return the circuit produced by `function_name`."""
    namespace = build_execution_namespace(
        allowed_import_roots=ALLOWED_IMPORT_ROOTS,
        extra_symbols={
            "ClassicalRegister": ClassicalRegister,
            "Parameter": Parameter,
            "ParameterVector": ParameterVector,
            "QuantumCircuit": QuantumCircuit,
            "QuantumRegister": QuantumRegister,
            "qiskit": qiskit,
        },
    )

    return execute_submission_source(
        source=source,
        function_name=function_name,
        namespace=namespace,
        type_validator=lambda value: isinstance(value, QuantumCircuit),
        type_error_message="Expected a qiskit.QuantumCircuit.",
        allow_direct_submission=False,
    )


def source_to_qasm3(source: str, function_name: str = "solve") -> QiskitConversionResult:
    """Execute Qiskit source code and convert the returned circuit to OpenQASM 3."""
    circuit = source_to_circuit(source, function_name=function_name)
    return QiskitConversionResult(circuit=circuit, qasm=circuit_to_qasm3(circuit))


def _ensure_quantum_circuit(circuit: Any) -> None:
    if not isinstance(circuit, QuantumCircuit):
        raise ConversionError("Expected a qiskit.QuantumCircuit.")


