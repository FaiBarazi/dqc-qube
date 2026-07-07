import json
from pathlib import Path

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

from app import get_entry_point_config
from pipeline.benchmark_pipeline import benchmark_metrics
from pipeline.converters.qiskit_converter import source_to_circuit
from problems.steane_error_correction.reference_circuit import get_reference_circuit
from problems.steane_error_correction.tests import (
    FIDELITY_THRESHOLD,
    SINGLE_ERROR_CASES,
    validate,
)


PROBLEM_DIR = Path(__file__).resolve().parents[1] / "problems" / "steane_error_correction"


def test_steane_reference_passes_single_error_validation():
    validation = validate(get_reference_circuit())

    assert validation["passed"] is True
    assert validation["min_fidelity"] >= FIDELITY_THRESHOLD
    assert set(validation["case_fidelities"]) == {
        case_name for case_name, _, _ in SINGLE_ERROR_CASES
    }


def test_steane_blank_circuit_fails_single_error_validation():
    data = QuantumRegister(7, "data")
    ancilla = QuantumRegister(6, "ancilla")
    syndrome = ClassicalRegister(6, "syndrome")
    circuit = QuantumCircuit(data, ancilla, syndrome)

    validation = validate(circuit)

    assert validation["passed"] is False
    assert validation["min_fidelity"] == 0.0


def test_steane_starter_uses_metadata_entry_point_args():
    metadata = json.loads((PROBLEM_DIR / "metadata.json").read_text(encoding="utf-8"))
    starter_source = (PROBLEM_DIR / "starter.py").read_text(encoding="utf-8")

    circuit = source_to_circuit(
        starter_source,
        entry_point_config=get_entry_point_config(metadata),
    )

    assert circuit.num_qubits == 13
    assert circuit.num_clbits == 6


def test_steane_benchmark_compares_submission_against_reference():
    reference = get_reference_circuit()
    result = benchmark_metrics(reference, reference)

    assert set(result) == {"submitted", "reference"}
    assert result["submitted"] == result["reference"]
    assert result["reference"]["num_qubits"] == 13
