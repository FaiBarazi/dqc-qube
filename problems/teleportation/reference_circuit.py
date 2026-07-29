from qiskit import QuantumCircuit


MESSAGE_QUBIT = 0
ALICE_QUBIT = 1
TARGET_QUBIT = 2


def get_reference_circuit() -> QuantumCircuit:
    """Return the reference circuit for the quantum teleportation problem."""
    circuit = QuantumCircuit(3, 2)

    # Prepare |psi> = |+> on Alice's message qubit.
    circuit.h(MESSAGE_QUBIT)

    # Share a Bell pair between Alice and Bob.
    circuit.h(ALICE_QUBIT)
    circuit.cx(ALICE_QUBIT, TARGET_QUBIT)

    # Alice changes to the Bell basis and measures her two qubits.
    circuit.cx(MESSAGE_QUBIT, ALICE_QUBIT)
    circuit.h(MESSAGE_QUBIT)
    circuit.measure(MESSAGE_QUBIT, 0)
    circuit.measure(ALICE_QUBIT, 1)

    # Bob corrects his target according to Alice's two classical bits.
    with circuit.if_test((circuit.clbits[1], True)):
        circuit.x(TARGET_QUBIT)
    with circuit.if_test((circuit.clbits[0], True)):
        circuit.z(TARGET_QUBIT)

    return circuit
