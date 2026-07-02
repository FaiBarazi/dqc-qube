from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp


def get_reference_circuit() -> QuantumCircuit:
    """
    Constructs the 2-qubit parameterized ansatz.
    """
    # note the values for the thetas are dummy values
    # Is this is only used for gate stats. 
    theta_0 = 0.2
    theta_1 = 0.4
    
    qc = QuantumCircuit(2)
    
    qc.ry(theta_0, 0)
    qc.ry(theta_1, 1)
    qc.cx(0, 1)
    return qc

def hamiltonian():
    """
    Constructs the 2-qubit Hamiltonian for the H2 molecule.
    """
    pauli_strings = ['II', 'ZI', 'IZ', 'ZZ', 'XX', 'YY']
    coefficients = [-1.052, 0.398, -0.398, -0.011, 0.181, 0.181]
    
    # Create the Hamiltonian operator
    H = SparsePauliOp(pauli_strings, coefficients)
    return H