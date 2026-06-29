# H2 Ground State using Variational Quantum Eigensolver(VQE)

In this problem we will use a 2 qubit system to estimate the ground energy of an $H_2$ atom. 
Note: 
While a direct simulation of the $H_2$ molecule typically requires 4 qubits to represent its 4 spin-orbitals, this exercise uses an optimized 2-qubit Hamiltonian. By exploiting the inherent physical symmetries of the molecule—specifically, the conservation of both the number of electrons and their total spin—we can mathematically "freeze" and remove two qubits from the equation.

For an $H_2$ molecule at a bond length of 0.735 Å, the simplified 2-qubit Hamiltonian H, mapped via the Jordan-Wigner transformation, is given by the following sum of Pauli operators:

$H=−1.052(I \otimes I)+0.398(Z \otimes I)−0.398(I \otimes Z)−0.011(Z \otimes Z)+0.181(X \otimes X)+0.181(Y \otimes Y)$

## Requirements

- Construct the Hamiltonian using the mapping above in the `hamiltonian` function. 
- Construct the ansatz using 2 angles, 2 Y Rotation Gates and a CNOT gate in the `ansatz`fucntion.  
- Calculate the expectation value in the `expectation_value` function. 
- Use exactly 2 qubits.

## Constraints
- The angles, theta, are constrained by the lower and upper bound: `-2 * pi <= θ <= 2 * pi`
- Use only 2 parameters, $\theta_{0} and \theta_{1}$

