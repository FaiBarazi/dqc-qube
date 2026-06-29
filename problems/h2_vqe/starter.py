import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector


theta_1 = 0.0 # First param here. 
theta_2 = 0.0 # Second param here. 
class Solve:
    def __init__(self, angles: list):
        assert len(angles) == 2
        for angle in angles:
            assert -2*np.pi <= angle <= 2*np.pi

        self.theta_1 = angles[0]
        self.theta_2 = angles[1]

    def hamiltonians(self):
        """
        Define the Hamiltonian. Construct and return the A sparse Pauli matrix 
        representing the H2 molecule.
        Note: Qiskit uses little-endian qubit ordering (Qubit 1 (tensor) Qubit 0).
        """
        # Your code here.
        
        pass

    def ansatz(self):
        """
        Ansatz preparation. Construct and return the 2-qubit parameterized circuit
        """
        qc = QuantumCircuit(2)
        # Your code here.
        return qc

    def expectation_value(self, theta_1, theta_2):
        """
        Return the expectation value <(θ)Ψ|H|Ψ(θ)>. 
        """

if __name__ == "__main__":
    angles = [] #instantaite the 2 angles/params here. 
    Solve(angles)
