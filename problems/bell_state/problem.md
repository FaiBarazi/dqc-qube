# Bell State Preparation

Create a two-qubit circuit that prepares the Bell state:

```text
(|00> + |11>) / sqrt(2)
```

## Requirements

- Implement a function named `solve`.
- Return a `qiskit.QuantumCircuit`.
- Use exactly 2 qubits.
- Do not add measurements.
- Your output state must have fidelity of at least `0.999` against the target
  state.

## Starter Signature

```python
from qiskit import QuantumCircuit

def solve() -> QuantumCircuit:
    circuit = QuantumCircuit(2)
    return circuit
```

