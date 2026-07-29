import json
from pathlib import Path

import pytest
from qiskit import QuantumCircuit

from app import get_entry_point_config, get_problems
from pipeline.benchmark_pipeline import benchmark_metrics
from pipeline.converters.qiskit_converter import source_to_circuit
from pipeline.evaluation_pipeline import get_reference_circuit as resolve_reference
from problems.teleportation.reference_circuit import get_reference_circuit
from problems.teleportation.tests import validate


PROBLEM_ID = "teleportation"
PROBLEM_DIR = Path(__file__).resolve().parents[1] / "problems" / PROBLEM_ID


def _load_metadata() -> dict:
    return json.loads((PROBLEM_DIR / "metadata.json").read_text(encoding="utf-8"))


def _build_uncorrected_circuit() -> QuantumCircuit:
    circuit = QuantumCircuit(3, 2)
    circuit.h(0)
    circuit.h(1)
    circuit.cx(1, 2)
    circuit.cx(0, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    circuit.measure(1, 1)
    return circuit


def test_reference_teleports_target_state_for_every_measurement_branch():
    validation = validate(get_reference_circuit())

    assert validation["passed"] is True
    assert validation["fidelity"] == pytest.approx(1.0)
    assert validation["message"] == "Accepted"


def test_missing_classical_corrections_fails_target_qubit_fidelity():
    validation = validate(_build_uncorrected_circuit())

    assert validation["passed"] is False
    assert validation["fidelity"] == pytest.approx(0.5)
    assert validation["message"] == "Wrong answer"


@pytest.mark.parametrize(
    ("submission", "expected_message"),
    [
        ("not a circuit", "solve() must return a qiskit.QuantumCircuit."),
        (QuantumCircuit(2, 2), "Expected 3 qubits, got 2."),
        (QuantumCircuit(3), "Expected 2 classical bits, got 0."),
        (
            QuantumCircuit(3, 2),
            "Measure q0 into c0 and q1 into c1 exactly once; do not measure q2.",
        ),
    ],
)
def test_teleportation_rejects_invalid_submissions(submission, expected_message):
    validation = validate(submission)

    assert validation["passed"] is False
    assert validation["fidelity"] == 0.0
    assert validation["message"] == expected_message


def test_target_qubit_measurement_is_rejected():
    circuit = QuantumCircuit(3, 2)
    circuit.measure(0, 0)
    circuit.measure(2, 1)

    validation = validate(circuit)

    assert validation["passed"] is False
    assert "do not measure q2" in validation["message"]


def test_teleportation_starter_runs_with_metadata_entry_point():
    metadata = _load_metadata()
    starter_source = (PROBLEM_DIR / "starter.py").read_text(encoding="utf-8")

    circuit = source_to_circuit(
        starter_source,
        entry_point_config=get_entry_point_config(metadata),
    )

    assert circuit.num_qubits == 3
    assert circuit.num_clbits == 2


def test_teleportation_is_discovered_and_resolves_custom_reference():
    metadata = _load_metadata()

    assert PROBLEM_ID in get_problems()
    assert resolve_reference(PROBLEM_ID, metadata) == get_reference_circuit()


def test_teleportation_benchmark_accepts_dynamic_reference_circuit():
    result = benchmark_metrics(get_reference_circuit(), _build_uncorrected_circuit())

    assert set(result) == {"submitted", "reference"}
    assert result["reference"]["num_qubits"] == 3
    assert result["submitted"]["num_qubits"] == 3
