from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Optional, Sequence, Union

import pennylane as qml
from pennylane.tape import QuantumScript
from pennylane.workflow import QNode
from qiskit import QuantumCircuit

from pipeline.converters.errors import ConversionError
from pipeline.converters.qiskit_converter import circuit_to_qasm3


PennyLaneCircuit = Union[QNode, QuantumScript]


@dataclass(frozen=True)
class PennyLaneConversionResult:
    circuit: PennyLaneCircuit
    qasm: str
    qasm_version: str


ALLOWED_IMPORT_ROOTS = frozenset({"cmath", "math", "numpy", "pennylane", "random"})

SAFE_BUILTINS = MappingProxyType(
    {
        "abs": abs,
        "all": all,
        "any": any,
        "bin": bin,
        "bool": bool,
        "chr": chr,
        "complex": complex,
        "dict": dict,
        "divmod": divmod,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "format": format,
        "frozenset": frozenset,
        "int": int,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "next": next,
        "object": object,
        "pow": pow,
        "range": range,
        "repr": repr,
        "reversed": reversed,
        "round": round,
        "set": set,
        "slice": slice,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "type": type,
        "zip": zip,
    }
)


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
        qasm_export = qml.to_openqasm(
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
    namespace = _build_execution_namespace()

    try:
        exec(compile(source, "<pennylane-submission>", "exec"), namespace)
    except Exception as exc:
        raise ConversionError(f"Could not execute PennyLane source: {exc}") from exc

    submission = namespace.get(function_name)
    if _is_pennylane_circuit(submission):
        return submission

    if not callable(submission):
        raise ConversionError(
            f"Submission must define `{function_name}` as a PennyLane QNode or circuit factory."
        )

    try:
        circuit = submission()
    except Exception as exc:
        raise ConversionError(f"`{function_name}` failed while building the PennyLane circuit: {exc}") from exc

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
        "__name__": "__pennylane_submission__",
        "pennylane": qml,
        "qml": qml,
    }

