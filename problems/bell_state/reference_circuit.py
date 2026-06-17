from qiskit import QuantumCircuit


def get_reference_circuit() -> QuantumCircuit:
    """Return the reference circuit for the Bell State problem.

    Applies H on qubit 0 then CNOT(0→1), producing |Φ+⟩ = (|00⟩ + |11⟩) / √2.
    """
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return qc
