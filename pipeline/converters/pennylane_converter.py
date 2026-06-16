from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence, Union

import pennylane as pq
from pennylane.tape import QuantumScript
from pennylane.workflow import QNode
from qiskit import QuantumCircuit

from pipeline.converters.errors import ConversionError
from pipeline.converters.qiskit_converter import circuit_to_qasm3
from pipeline.converters.sandbox import (
    ALLOWED_IMPORT_ROOTS_PENNYLANE as ALLOWED_IMPORT_ROOTS,
    build_execution_namespace,
    execute_submission_source,
)


PennyLaneCircuit = Union[QNode, QuantumScript]


@dataclass(frozen=True)
class PennyLaneConversionResult:
    circuit: PennyLaneCircuit
    qasm: str
    qasm_version: str


# SAFE_BUILTINS and ALLOWED_IMPORT_ROOTS are provided by pipeline.converters.sandbox


def pennylane_to_qasm2(
    circuit: PennyLaneCircuit,
    circuit_args: Optional[Sequence[Any]] = None,
    circuit_kwargs: Optional[dict[str, Any]] = None,
    wires=None,
    rotations: bool = True,
    measure_all: bool = True,
    precision: Optional[int] = None,
) -> str:
    """Convert a PennyLane QNode or QuantumScript into an OpenQASM 2.0 string."""
    _ensure_pennylane_circuit(circuit)
    circuit_args = tuple(circuit_args or ())
    circuit_kwargs = circuit_kwargs or {}

    try:
        qasm_export = pq.to_openqasm(
            circuit,
            wires=wires,
            rotations=rotations,
            measure_all=measure_all,
            precision=precision,
        )

        if callable(qasm_export):
            return qasm_export(*circuit_args, **circuit_kwargs)

        return qasm_export
    except Exception as exc:
        raise ConversionError(f"Could not convert PennyLane circuit to OpenQASM 2.0: {exc}") from exc


def pennylane_to_qasm3(
    circuit: PennyLaneCircuit,
    circuit_args: Optional[Sequence[Any]] = None,
    circuit_kwargs: Optional[dict[str, Any]] = None,
    wires=None,
    rotations: bool = True,
    measure_all: bool = True,
    precision: Optional[int] = None,
) -> str:
    """Convert PennyLane to OpenQASM 3 by normalizing its OpenQASM 2.0 export."""
    qasm2 = pennylane_to_qasm2(
        circuit,
        circuit_args=circuit_args,
        circuit_kwargs=circuit_kwargs,
        wires=wires,
        rotations=rotations,
        measure_all=measure_all,
        precision=precision,
    )
    return qasm2_to_qasm3(qasm2)


def qasm2_to_qasm3(qasm: str) -> str:
    """Convert OpenQASM 2.0 into OpenQASM 3 using Qiskit as the parser/exporter."""
    try:
        circuit = QuantumCircuit.from_qasm_str(qasm)
    except Exception as exc:
        raise ConversionError(f"Could not parse OpenQASM 2.0 for QASM 3 conversion: {exc}") from exc

    return circuit_to_qasm3(circuit)


def export_pennylane_to_qasm2(
    circuit: PennyLaneCircuit,
    output_path: Union[str, Path],
    circuit_args: Optional[Sequence[Any]] = None,
    circuit_kwargs: Optional[dict[str, Any]] = None,
    wires=None,
    rotations: bool = True,
    measure_all: bool = True,
    precision: Optional[int] = None,
) -> Path:
    """Convert a PennyLane circuit to OpenQASM 2.0 and write it to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        pennylane_to_qasm2(
            circuit,
            circuit_args=circuit_args,
            circuit_kwargs=circuit_kwargs,
            wires=wires,
            rotations=rotations,
            measure_all=measure_all,
            precision=precision,
        ),
        encoding="utf-8",
    )
    return path


def export_pennylane_to_qasm3(
    circuit: PennyLaneCircuit,
    output_path: Union[str, Path],
    circuit_args: Optional[Sequence[Any]] = None,
    circuit_kwargs: Optional[dict[str, Any]] = None,
    wires=None,
    rotations: bool = True,
    measure_all: bool = True,
    precision: Optional[int] = None,
) -> Path:
    """Convert a PennyLane circuit to OpenQASM 3 and write it to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        pennylane_to_qasm3(
            circuit,
            circuit_args=circuit_args,
            circuit_kwargs=circuit_kwargs,
            wires=wires,
            rotations=rotations,
            measure_all=measure_all,
            precision=precision,
        ),
        encoding="utf-8",
    )
    return path


def pennylane_source_to_circuit(source: str, function_name: str = "solve") -> PennyLaneCircuit:
    """
    Execute PennyLane source code and return a QNode or QuantumScript.

    The submission can define `solve` as a QNode directly, or as a no-argument
    factory function that returns a QNode or QuantumScript.
    """
    namespace = build_execution_namespace(
        allowed_import_roots=ALLOWED_IMPORT_ROOTS,
        extra_symbols={
            "pennylane": pq,
            "pq": pq,
        },
    )

    circuit = execute_submission_source(
        source=source,
        function_name=function_name,
        namespace=namespace,
        type_validator=lambda value: isinstance(value, (QNode, QuantumScript)),
        type_error_message="Expected a PennyLane QNode or QuantumScript.",
        allow_direct_submission=True,
    )

    _ensure_pennylane_circuit(circuit)
    return circuit


def pennylane_source_to_qasm2(
    source: str,
    function_name: str = "solve",
    circuit_args: Optional[Sequence[Any]] = None,
    circuit_kwargs: Optional[dict[str, Any]] = None,
    wires=None,
    rotations: bool = True,
    measure_all: bool = True,
    precision: Optional[int] = None,
) -> PennyLaneConversionResult:
    """Execute PennyLane source code and convert the circuit to OpenQASM 2.0."""
    circuit = pennylane_source_to_circuit(source, function_name=function_name)
    qasm = pennylane_to_qasm2(
        circuit,
        circuit_args=circuit_args,
        circuit_kwargs=circuit_kwargs,
        wires=wires,
        rotations=rotations,
        measure_all=measure_all,
        precision=precision,
    )
    return PennyLaneConversionResult(circuit=circuit, qasm=qasm, qasm_version="2.0")


def pennylane_source_to_qasm3(
    source: str,
    function_name: str = "solve",
    circuit_args: Optional[Sequence[Any]] = None,
    circuit_kwargs: Optional[dict[str, Any]] = None,
    wires=None,
    rotations: bool = True,
    measure_all: bool = True,
    precision: Optional[int] = None,
) -> PennyLaneConversionResult:
    """Execute PennyLane source code and convert the circuit to OpenQASM 3."""
    circuit = pennylane_source_to_circuit(source, function_name=function_name)
    qasm = pennylane_to_qasm3(
        circuit,
        circuit_args=circuit_args,
        circuit_kwargs=circuit_kwargs,
        wires=wires,
        rotations=rotations,
        measure_all=measure_all,
        precision=precision,
    )
    return PennyLaneConversionResult(circuit=circuit, qasm=qasm, qasm_version="3.0")


def _ensure_pennylane_circuit(circuit: Any) -> None:
    if not _is_pennylane_circuit(circuit):
        raise ConversionError("Expected a PennyLane QNode or QuantumScript.")


def _is_pennylane_circuit(value: Any) -> bool:
    return isinstance(value, (QNode, QuantumScript))



