from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT


def get_reference_circuit() -> QuantumCircuit:
    """Return the reference circuit for the QFT problem.

    Prepares the 5-qubit computational basis state |01101⟩ (= |13⟩ in
    little-endian ordering, qubits 0, 2, 3 set to |1⟩) and applies the
    Quantum Fourier Transform, matching the analytic target QFT|13⟩.
    """
    n = 5
    qc = QuantumCircuit(n)
    # Prepare |13⟩ in little-endian: 13 = 1 + 4 + 8 → qubits 0, 2, 3
    for qubit in [0, 2, 3]:
        qc.x(qubit)
    qc.compose(QFT(n), inplace=True)
    return qc
