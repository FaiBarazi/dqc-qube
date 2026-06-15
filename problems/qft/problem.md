# Quantum Fourier Transform (QFT) State Preparation

Create a five-qubit circuit that prepares the Quantum Fourier Transform of
the computational basis state |13> (i.e. QFT|13>), where 13 is represented in
binary as `01101` (5 bits). The target state can be written as:

```math
\frac{1}{\sqrt{32}}\sum_{k=0}^{31} e^{2\pi i k \cdot 13 / 32} |k\rangle
```

## Requirements

- Implement a function named `solve`.
- Return a `qiskit.QuantumCircuit`.
- Use exactly 5 qubits.
- Do not add measurements.
- Your output state must have fidelity of at least `0.999` against the target
  QFT|13> state.

## Starter Signature

```python
from qiskit import QuantumCircuit

def solve() -> QuantumCircuit:
  circuit = QuantumCircuit(5)
  return circuit
```

