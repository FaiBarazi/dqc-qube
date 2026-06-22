# Problems

Each challenge lives in its own directory and contains the files needed to show
the prompt, seed the editor, and evaluate a submission.

Recommended layout:

```text
problems/
  problem_id/
    metadata.json
    problem.md
    starter.py
    tests.py
```

## File Roles

- `metadata.json`: machine-readable problem details such as title, difficulty,
  required framework, qubit count, tags, and fidelity threshold.
- `problem.md`: user-facing problem statement.
- `starter.py`: code loaded into the editor before the user begins.
- `tests.py`: problem-specific validation helpers for the evaluator.

For the MVP, submissions should expose a Qiskit function named `solve`:

```python
from qiskit import QuantumCircuit

def solve() -> QuantumCircuit:
    circuit = QuantumCircuit(2)
    return circuit
```

## Available Problems

| ID              | Title                        | Difficulty | Qubits | Tags                                          |
|-----------------|------------------------------|------------|--------|-----------------------------------------------|
| `bell_state`    | Bell State Preparation       | easy       | 2      | state-preparation, entanglement               |
| `qft`           | Quantum Fourier Transform    | easy       | 5      | qft, state-preparation                        |
| `vqe_real_amp`  | VQE Real Amplitudes Ansatz   | medium     | 5      | variational, ansatz, vqe, real-amplitudes     |
