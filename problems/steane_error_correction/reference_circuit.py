from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

def get_reference_circuit() -> QuantumCircuit:
    # For the steane code, we need 
    data = QuantumRegister(7, 'data')
    ancilla = QuantumRegister(6, 'ancilla')
    # Used to store the measurments to get the syndrome.
    syndrome = ClassicalRegister(6, 'syndrome')
    qc = QuantumCircuit(data, ancilla, syndrome)

    # Encoding: maps input state at data[0] to Steane 7 qubit. 
    qc.cx(data[0], [data[1],data[2]])
    qc.h([data[i] for i in range(4,7)])
    qc.cx(data[6], [data[i] for i in (3,1,0)])
    qc.cx(data[5], [data[i] for i in (3,2,0)])
    qc.cx(data[4], [data[i] for i in (3,2,1)])

    # Error Detection
    ## sandwiched between 2 Hadamards.
    qc.h(ancilla[i] for i in range(0,6))
    # Bit flip error
    qc.cx(ancilla[0], [data[i] for i in range(1,5)])
    qc.cx(ancilla[1], [data[i] for i in (5,3,2,0)])
    qc.cx(ancilla[2], [data[i] for i in (6,4,3,0)])

    # Phase flip error
    qc.cx(ancilla[3], [data[i] for i in range(1,5)])
    qc.cx(ancilla[4], [data[i] for i in (5,3,2,0)])
    qc.cx(ancilla[5], [data[i] for i in (6,4,3,0)])

    ## End of sandwich
    qc.h(ancilla[i] for i in range(0,6))

    qc.barrier()

    qc.measure(ancilla, syndrome)
    return qc
