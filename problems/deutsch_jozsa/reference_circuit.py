from qiskit import QuantumCircuit


NUM_INPUT_QUBITS = 4
OUTPUT_QUBIT = NUM_INPUT_QUBITS
NUM_QUBITS = NUM_INPUT_QUBITS + 1


def get_reference_circuit() -> QuantumCircuit:
    """Return the benchmark circuit for the Deutsch-Jozsa problem.

    The balanced oracle computes the parity of the four input qubits into the
    output qubit. Phase kickback followed by the final Hadamards leaves the
    input register in |1111> and the output qubit in |->.
    """
    circuit = QuantumCircuit(NUM_QUBITS)

    circuit.x(OUTPUT_QUBIT)
    circuit.h(range(NUM_QUBITS))

    for input_qubit in range(NUM_INPUT_QUBITS):
        circuit.cx(input_qubit, OUTPUT_QUBIT)

    circuit.h(range(NUM_INPUT_QUBITS))
    return circuit
