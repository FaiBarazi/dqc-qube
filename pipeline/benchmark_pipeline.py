from qiskit import QuantumCircuit
def get_alg_benchmark(circuit: QuantumCircuit)->dict:
    """
    Return stats for a circuit on the algorithm level. 
    Since there is no gates mapping / optimization at this stage, the information 
    can be extracted directly from the circuit.
    Return:
        dict: {
            "num_qubits": int,
            "depth": int,
            "total_num_gates": int,
            "single_qubit_gates": int,
        }
    """
    num_qubits = circuit.num_qubits
    depth = circuit.depth()
    total_num_gates = circuit.size()
    single_q = sum(1 for inst in circuit.data if len(inst.qubits) == 1)
    ctrl_q = sum(1 for inst in circuit.data if len(inst.qubits) > 1)


    return {
        "num_qubits": num_qubits,
        "depth": depth,
        "total_num_gates": total_num_gates,
        "num_single_gates": single_q,
        "controlled_gates": ctrl_q,
    }