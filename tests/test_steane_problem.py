import json
from pathlib import Path

from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

from app import get_entry_point_config
from pipeline.benchmark_pipeline import benchmark_metrics
from pipeline.converters.qiskit_converter import source_to_circuit
from problems.steane_error_correction.reference_circuit import get_reference_circuit
from problems.steane_error_correction.tests import (
    validate,
)


PROBLEM_DIR = Path(__file__).resolve().parents[1] / "problems" / "steane_error_correction"


def _copy_quantum_prefix(
    target: QuantumCircuit,
    source: QuantumCircuit,
    stop: int,
) -> None:
    for instruction in source.data[:stop]:
        if instruction.operation.name in {"barrier", "measure"}:
            continue

        qubit_indices = [source.find_bit(qubit).index for qubit in instruction.qubits]
        target.append(instruction.operation.copy(), qubit_indices)


def _copy_instruction(
    target: QuantumCircuit,
    source: QuantumCircuit,
    instruction,
) -> None:
    qubit_indices = [source.find_bit(qubit).index for qubit in instruction.qubits]
    clbit_indices = [source.find_bit(clbit).index for clbit in instruction.clbits]
    target.append(instruction.operation.copy(), qubit_indices, clbit_indices)


def _get_permuted_syndrome_circuit() -> QuantumCircuit:
    data = QuantumRegister(7, "data")
    ancilla = QuantumRegister(6, "ancilla")
    syndrome = ClassicalRegister(6, "syndrome")
    circuit = QuantumCircuit(data, ancilla, syndrome)

    reference = get_reference_circuit()
    first_ancilla_instruction = next(
        index
        for index, instruction in enumerate(reference.data)
        if instruction.operation.name not in {"barrier", "measure"}
        and any(reference.find_bit(qubit).index >= 7 for qubit in instruction.qubits)
    )
    _copy_quantum_prefix(circuit, reference, first_ancilla_instruction)

    x_checks = ((6, 3, 1, 0), tuple(range(1, 5)), (5, 3, 2, 0))
    z_checks = ((6, 3, 1, 0), tuple(range(1, 5)), (5, 3, 2, 0))

    circuit.h(ancilla)
    for ancilla_index, support in enumerate(x_checks):
        circuit.cx(ancilla[ancilla_index], [data[index] for index in support])
    for offset, support in enumerate(z_checks, start=3):
        circuit.cz(ancilla[offset], [data[index] for index in support])
    circuit.h(ancilla)
    circuit.measure(ancilla, syndrome)

    return circuit


def _get_flipped_syndrome_circuit() -> QuantumCircuit:
    reference = get_reference_circuit()
    circuit = QuantumCircuit(*reference.qregs, *reference.cregs)
    first_measure = next(
        index
        for index, instruction in enumerate(reference.data)
        if instruction.operation.name == "measure"
    )

    for instruction in reference.data[:first_measure]:
        _copy_instruction(circuit, reference, instruction)
    circuit.x(7)
    for instruction in reference.data[first_measure:]:
        _copy_instruction(circuit, reference, instruction)

    return circuit


def test_steane_reference_passes_pauli_validation():
    validation = validate(get_reference_circuit())

    assert validation["passed"] is True
    assert validation["check_score"] == 1.0
    assert all(validation["checks"].values())
    assert validation["encoding_rank"] == 6
    assert validation["syndrome_rank"] == 6


def test_steane_permuted_syndrome_order_passes_pauli_validation():
    validation = validate(_get_permuted_syndrome_circuit())

    assert validation["passed"] is True
    assert validation["checks"]["syndrome_stabilizer_space"] is True


def test_steane_flipped_syndrome_bit_fails_pauli_validation():
    validation = validate(_get_flipped_syndrome_circuit())

    assert validation["passed"] is False
    assert validation["checks"]["encoding_stabilizer_space"] is True
    assert validation["checks"]["syndrome_stabilizer_space"] is False
    assert validation["syndrome_rank"] == 6


def test_steane_blank_circuit_fails_pauli_validation():
    data = QuantumRegister(7, "data")
    ancilla = QuantumRegister(6, "ancilla")
    syndrome = ClassicalRegister(6, "syndrome")
    circuit = QuantumCircuit(data, ancilla, syndrome)

    validation = validate(circuit)

    assert validation["passed"] is False
    assert validation["check_score"] == 0.0


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
