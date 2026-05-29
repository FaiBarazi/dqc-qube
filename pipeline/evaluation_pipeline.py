"""
Note:
This module is intended for testing the benchmarking and predictor
provided by MQT.
"""

from qiskit import QuantumCircuit, qasm3
from qiskit.quantum_info import Statevector, state_fidelity


def load_circuit(qasm_file: str) -> QuantumCircuit:
    return qasm3.load(qasm_file)


def evolve_state(circuit: QuantumCircuit) -> Statevector:
    statevector_output = Statevector(circuit)
    return statevector_output


def compute_fidelity(output_state, target_state) -> float:
    fidelity = state_fidelity(target_state, output_state)
    return fidelity
