from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


def solve(num_encoding_qubits, num_ancilla_qubits) -> QuantumCircuit:
    # For the steane code, we need 
    data = QuantumRegister(num_encoding_qubits, 'data')
    ancilla = QuantumRegister(num_ancilla_qubits, 'ancilla')
    # Used to store the measurments to get the syndrome.
    syndrome = ClassicalRegister(num_ancilla_qubits, 'syndrome')
    qc = QuantumCircuit(data, ancilla, syndrome)

    # 1. Input Encoding here.


    # 2.Error Detection Code here.
 

    #3. Measure Syndrome here.

    return qc