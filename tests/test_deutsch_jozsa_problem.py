import json
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

from app import get_entry_point_config, get_problems
from pipeline.benchmark_pipeline import benchmark_metrics
from pipeline.converters.qiskit_converter import source_to_circuit
from pipeline.evaluation_pipeline import get_reference_circuit as resolve_reference
from problems.deutsch_jozsa.reference_circuit import get_reference_circuit
from problems.deutsch_jozsa.tests import validate


PROBLEM_ID = "deutsch_jozsa"
PROBLEM_DIR = Path(__file__).resolve().parents[1] / "problems" / PROBLEM_ID


def _load_metadata() -> dict:
    return json.loads((PROBLEM_DIR / "metadata.json").read_text(encoding="utf-8"))


def _build_equivalent_solution() -> QuantumCircuit:
    circuit = QuantumCircuit(5)
    circuit.x(4)
    circuit.h(range(5))

    # Complementing two inputs before and after the oracle leaves the parity
    # function unchanged while producing a structurally different circuit.
    circuit.x([0, 1])
    for input_qubit in range(4):
        circuit.cx(input_qubit, 4)
    circuit.x([0, 1])

    circuit.h(range(4))
    return circuit


def test_deutsch_jozsa_reference_has_expected_state_and_passes_validation():
    reference = get_reference_circuit()
    state = Statevector.from_instruction(reference)
    expected = np.zeros(2**5, dtype=complex)
    expected[15] = 1 / np.sqrt(2)
    expected[31] = -1 / np.sqrt(2)

    assert state_fidelity(state, expected) == pytest.approx(1.0)

    validation = validate(reference)
    assert validation["passed"] is True
    assert validation["fidelity"] == pytest.approx(1.0)
    assert validation["message"] == "Accepted"


def test_deutsch_jozsa_equivalent_solution_passes_fidelity_validation():
    validation = validate(_build_equivalent_solution())

    assert validation["passed"] is True
    assert validation["fidelity"] == pytest.approx(1.0)


def test_deutsch_jozsa_blank_circuit_fails_validation():
    validation = validate(QuantumCircuit(5))

    assert validation["passed"] is False
    assert validation["fidelity"] < 0.999
    assert validation["message"] == "Wrong answer"


@pytest.mark.parametrize(
    ("submission", "expected_message"),
    [
        ("not a circuit", "solve() must return a qiskit.QuantumCircuit."),
        (QuantumCircuit(4), "Expected 5 qubits, got 4."),
        (
            QuantumCircuit(5, 1),
            "Classical bits and measurements are not allowed for this problem.",
        ),
    ],
)
def test_deutsch_jozsa_rejects_invalid_submissions(submission, expected_message):
    validation = validate(submission)

    assert validation["passed"] is False
    assert validation["fidelity"] == 0.0
    assert validation["message"] == expected_message


def test_deutsch_jozsa_starter_runs_with_metadata_entry_point():
    metadata = _load_metadata()
    starter_source = (PROBLEM_DIR / "starter.py").read_text(encoding="utf-8")

    circuit = source_to_circuit(
        starter_source,
        entry_point_config=get_entry_point_config(metadata),
    )

    assert circuit.num_qubits == 5
    assert circuit.num_clbits == 0


def test_deutsch_jozsa_is_discovered_and_resolves_custom_reference():
    metadata = _load_metadata()

    assert PROBLEM_ID in get_problems()

    resolved_reference = resolve_reference(PROBLEM_ID, metadata)
    fidelity = state_fidelity(
        Statevector.from_instruction(get_reference_circuit()),
        Statevector.from_instruction(resolved_reference),
    )
    assert fidelity == pytest.approx(1.0)


def test_deutsch_jozsa_benchmark_compares_submission_against_reference():
    reference = get_reference_circuit()
    result = benchmark_metrics(reference, _build_equivalent_solution())

    assert set(result) == {"submitted", "reference"}
    assert result["reference"] == {
        "num_qubits": 5,
        "depth": 7,
        "total_num_gates": 14,
        "num_single_gates": 10,
        "controlled_gates": 4,
    }
    assert result["submitted"] == {
        "num_qubits": 5,
        "depth": 7,
        "total_num_gates": 18,
        "num_single_gates": 14,
        "controlled_gates": 4,
    }
