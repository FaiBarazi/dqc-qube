**Steane Code Logical $\lvert 0 \rangle$ State Preparation**

Create a seven-qubit circuit that prepares the logical zero state
$\lvert 0 \rangle_L$ for the Steane $[7,1,3]$ quantum error-correction code.
The Steane code encodes one logical qubit into seven physical qubits. The target
logical zero state is an equal superposition of all even-weight codewords from
the classical $[7,1,3]$ Hamming code:

$$
\begin{aligned}
\lvert 0 \rangle_L = \frac{1}{\sqrt{8}}\bigl(&
    \lvert 0000000 \rangle + \lvert 1010101 \rangle
    + \lvert 0110011 \rangle + \lvert 1100110 \rangle
    + \lvert 0001111 \rangle + \lvert 1011010 \rangle
    + \lvert 0111100 \rangle + \lvert 1101001 \rangle
\bigr).
\end{aligned}
$$

**Requirements**

- Implement a function named `solve`.
- Implement only the encoding and error-detection parts of the code.
- Return a `qiskit.QuantumCircuit`.
