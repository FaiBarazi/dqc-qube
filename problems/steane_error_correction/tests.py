from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

from problems.steane_error_correction.reference_circuit import get_reference_circuit


FIDELITY_THRESHOLD = 0.999
EXPECTED_DATA_QUBITS = 7
EXPECTED_ANCILLA_QUBITS = 6
EXPECTED_QUBITS = EXPECTED_DATA_QUBITS + EXPECTED_ANCILLA_QUBITS
EXPECTED_CLBITS = EXPECTED_ANCILLA_QUBITS
ANCILLA_START = EXPECTED_DATA_QUBITS
IGNORED_INSTRUCTIONS = {"barrier", "measure"}
SINGLE_ERROR_CASES = (
    ("bit_flip_data_0", "x", 0),
    ("bit_flip_data_3", "x", 3),
    ("phase_flip_data_0", "z", 0),
    ("phase_flip_data_3", "z", 3),
)


def _failure(message: str, **details) -> dict:
    return {
        "passed": False,
        "message": message,
        **details,
    }


def _find_encode_detection_boundary(circuit: QuantumCircuit) -> int:
    for index, instruction in enumerate(circuit.data):
        if instruction.operation.name in IGNORED_INSTRUCTIONS:
            continue

        qubit_indices = [circuit.find_bit(qubit).index for qubit in instruction.qubits]
        if any(qubit_index >= ANCILLA_START for qubit_index in qubit_indices):
            return index

    raise ValueError("Could not find ancilla-based syndrome extraction.")


def _append_without_classical_bits(
    target: QuantumCircuit,
    source: QuantumCircuit,
    instruction,
) -> None:
    if instruction.operation.name in IGNORED_INSTRUCTIONS:
        return

    qubit_indices = [source.find_bit(qubit).index for qubit in instruction.qubits]
    target.append(instruction.operation.copy(), qubit_indices, [])


def _circuit_with_single_error(
    circuit: QuantumCircuit,
    error_gate: str,
    data_qubit: int,
) -> QuantumCircuit:
    boundary = _find_encode_detection_boundary(circuit)
    probe = QuantumCircuit(circuit.num_qubits)

    for instruction in circuit.data[:boundary]:
        _append_without_classical_bits(probe, circuit, instruction)

    if error_gate == "x":
        probe.x(data_qubit)
    elif error_gate == "z":
        probe.z(data_qubit)
    else:
        raise ValueError(f"Unsupported error gate: {error_gate}")

    for instruction in circuit.data[boundary:]:
        _append_without_classical_bits(probe, circuit, instruction)

    return probe


def _statevector_for_case(
    circuit: QuantumCircuit,
    error_gate: str,
    data_qubit: int,
) -> Statevector:
    return Statevector.from_instruction(
        _circuit_with_single_error(circuit, error_gate, data_qubit)
    )


def validate(circuit: QuantumCircuit) -> dict:
    if not isinstance(circuit, QuantumCircuit):
        return _failure(
            "solve() must return a qiskit.QuantumCircuit.",
            min_fidelity=0.0,
            fidelity_threshold=FIDELITY_THRESHOLD,
        )

    if circuit.num_qubits != EXPECTED_QUBITS:
        return _failure(
            f"Expected {EXPECTED_QUBITS} qubits, got {circuit.num_qubits}.",
            min_fidelity=0.0,
            fidelity_threshold=FIDELITY_THRESHOLD,
        )

    if circuit.num_clbits != EXPECTED_CLBITS:
        return _failure(
            f"Expected {EXPECTED_CLBITS} classical bits, got {circuit.num_clbits}.",
            min_fidelity=0.0,
            fidelity_threshold=FIDELITY_THRESHOLD,
        )

    reference_circuit = get_reference_circuit()
    case_fidelities = {}

    try:
        for case_name, error_gate, data_qubit in SINGLE_ERROR_CASES:
            reference_state = _statevector_for_case(
                reference_circuit, error_gate, data_qubit
            )
            submitted_state = _statevector_for_case(circuit, error_gate, data_qubit)
            case_fidelities[case_name] = float(
                state_fidelity(reference_state, submitted_state)
            )
    except Exception as exc:
        return _failure(
            f"Could not simulate single-error cases: {exc}",
            min_fidelity=0.0,
            fidelity_threshold=FIDELITY_THRESHOLD,
            case_fidelities=case_fidelities,
        )

    min_fidelity = min(case_fidelities.values())
    passed = min_fidelity >= FIDELITY_THRESHOLD

    return {
        "passed": passed,
        "message": "Accepted" if passed else "Wrong answer",
        "min_fidelity": float(min_fidelity),
        "fidelity_threshold": FIDELITY_THRESHOLD,
        "case_fidelities": case_fidelities,
    }
