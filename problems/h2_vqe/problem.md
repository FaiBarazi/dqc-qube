**$H_2$ Ground State using the Variational Quantum Eigensolver (VQE)**

In this problem, we will use a two-qubit system to estimate the ground-state
energy of an $H_2$ molecule.

While a direct simulation of $H_2$ typically requires four qubits to represent
its four spin orbitals, this exercise uses an optimized two-qubit Hamiltonian.
By exploiting the molecule's physical symmetries—specifically conservation of
electron number and total spin—we can mathematically freeze and remove two
qubits from the equation.

For an $H_2$ molecule at a bond length of $0.735\,\text{Å}$, the simplified
two-qubit Hamiltonian $H$, mapped through the Jordan–Wigner transformation, is:

$$
\begin{aligned}
H ={}& -1.052(I \otimes I)
       + 0.398(Z \otimes I)
       - 0.398(I \otimes Z)
       - 0.011(Z \otimes Z)
       + 0.181(X \otimes X)
       + 0.181(Y \otimes Y).
\end{aligned}
$$

**Requirements**

- Construct the Hamiltonian using the mapping above in the `hamiltonian` function.
- Construct the ansatz using two angles, two Y-rotation gates, and a CNOT gate
  in the `ansatz` function.
- Calculate the expectation value in the `expectation_value` function.
- Use exactly 2 qubits.

**Constraints**

- Each angle is constrained by $-2\pi \leq \theta_i \leq 2\pi$.
- Use only two parameters, $\theta_0$ and $\theta_1$.
