import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector


theta_1 = 0.0 # First param here. 
theta_2 = 0.0 # Second param here. 

def hamiltonian():
    """
    Define the Hamiltonian. Construct and return the A sparse Pauli matrix 
    representing the H2 molecule.
    Note: Qiskit uses little-endian qubit ordering (Qubit 1 (tensor) Qubit 0).
    """
    # Your code here.
    
    pass

def ansatz(theta_1, theta_2):
    """
    Ansatz preparation. Construct and return the 2-qubit parameterized circuit
    """
    qc = QuantumCircuit(2)
    # Your code here.
    return qc

def expectation_value(theta_1, theta_2):
    """
    Return the expectation value <(θ)Ψ|H|Ψ(θ)>. 
    """

def solve(theta_1, theta_2)-> float:
    """
    Return the expectation value given the 2 params theta_1 and theta_2
    """
    pass

