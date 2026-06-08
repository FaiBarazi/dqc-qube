from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity


FIDELITY_THRESHOLD = 0.999
EXPECTED_QUBITS = 2


def target_state() -> Statevector:
    circuit = QuantumCircuit(EXPECTED_QUBITS)
    circuit.h(0)
    circuit.cx(0, 1)
    return Statevector.from_instruction(circuit)


def validate(circuit: QuantumCircuit) -> dict:
    if not isinstance(circuit, QuantumCircuit):
        return {
            "passed": False,
            "fidelity": 0.0,
            "message": "solve() must return a qiskit.QuantumCircuit.",
        }

    if circuit.num_qubits != EXPECTED_QUBITS:
        return {
            "passed": False,
            "fidelity": 0.0,
            "message": f"Expected {EXPECTED_QUBITS} qubits, got {circuit.num_qubits}.",
        }

    if circuit.num_clbits != 0:
        return {
            "passed": False,
            "fidelity": 0.0,
            "message": "Measurements are not allowed for this problem.",
        }

    try:
        output_state = Statevector.from_instruction(circuit)
    except Exception as exc:
        return {
            "passed": False,
            "fidelity": 0.0,
            "message": f"Could not simulate circuit: {exc}",
        }

    fidelity = float(state_fidelity(target_state(), output_state))

    return {
        "passed": fidelity >= FIDELITY_THRESHOLD,
        "fidelity": fidelity,
        "message": "Accepted" if fidelity >= FIDELITY_THRESHOLD else "Wrong answer",
    }
