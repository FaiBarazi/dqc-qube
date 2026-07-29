from qiskit import QuantumCircuit


def solve() -> QuantumCircuit:
    circuit = QuantumCircuit(3, 2)
    # q0 holds |psi>, q1 is Alice's entangled qubit, and q2 is Bob's target.
    # TODO: Teleport |psi> = (|0> + |1>) / sqrt(2) from q0 to q2.
    return circuit
