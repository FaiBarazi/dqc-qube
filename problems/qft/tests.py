from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity
import numpy as np


FIDELITY_THRESHOLD = 0.999
EXPECTED_QUBITS = 5


def target_state() -> Statevector:
    # Construct the analytic QFT|13> state for n=5 qubits
    n = EXPECTED_QUBITS
    N = 2 ** n
    j = 13
    phases = np.exp(2j * np.pi * np.arange(N) * j / N)
    vec = phases / np.sqrt(N)
    return Statevector(vec)


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
