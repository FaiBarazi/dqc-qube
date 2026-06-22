from qiskit import QuantumCircuit


# Pre-optimised RY angles from MQT Bench vqe_real_amp_alg_5 (2025-10-16).
# Layout: 4 layers × 5 qubits = 20 parameters, reps=3, linear entanglement.
_ANGLES = [
    # Layer 0
    [6.006735895579343, 1.304903297657757, 5.205272730965009,
     0.9379672423735244, 3.2220464314480877],
    # Layer 1
    [0.8540080589393146, 4.329343885871547, 5.288856933750764,
     2.6735518805676657, 6.012543404956273],
    # Layer 2
    [5.185719590928789, 2.125069481984559, 3.6176102152986354,
     4.733135208207287, 5.196847304624584],
    # Layer 3
    [5.864966885210837, 0.9110285368422897, 4.684618627355123,
     0.8755706304852969, 5.695888160944528],
]

# Linear CNOT chain: q[3]→q[4], q[2]→q[3], q[1]→q[2], q[0]→q[1]
_CX_PAIRS = [(3, 4), (2, 3), (1, 2), (0, 1)]


def get_reference_circuit() -> QuantumCircuit:
    """Return the reference VQE RealAmplitudes ansatz circuit (no measurements).

    5 qubits, reps=3, linear entanglement.  Reproduces the statevector
    defined by MQT Bench vqe_real_amp_alg_5.qasm.
    """
    n = 5
    qc = QuantumCircuit(n)

    for layer_idx, angles in enumerate(_ANGLES):
        # RY rotation layer
        for qubit, theta in enumerate(angles):
            qc.ry(theta, qubit)

        # Entangling layer (skip after the last RY layer)
        if layer_idx < len(_ANGLES) - 1:
            for ctrl, tgt in _CX_PAIRS:
                qc.cx(ctrl, tgt)

    return qc
