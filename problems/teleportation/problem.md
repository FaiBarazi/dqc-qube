### Quantum Teleportation

Build a three-qubit circuit that teleports the state

$$
\lvert \psi \rangle
= \frac{\lvert 0 \rangle + \lvert 1 \rangle}{\sqrt{2}}
= \lvert + \rangle
$$

from Alice's message qubit, `q0`, to Bob's target qubit, `q2`. Qubit `q1`
is Alice's half of the entangled pair.

Implement the complete protocol:

1. Prepare `q0` in $\lvert \psi \rangle$.
2. Create a Bell pair between `q1` and `q2`.
3. Apply Alice's Bell-basis operations to `q0` and `q1`.
4. Measure `q0` into `c0` and `q1` into `c1`.
5. Use those classical results to apply the appropriate Pauli corrections to
   `q2`.

### Requirements

- Implement a function named `solve`.
- Return a `qiskit.QuantumCircuit`.
- Use exactly 3 qubits and 2 classical bits.
- Measure `q0` into `c0` and `q1` into `c1`.
- Do not measure the target qubit, `q2`.
- After the outcome-dependent corrections, `q2` must be in
  $\lvert \psi \rangle$ for every measurement outcome.
- The target-qubit state must have an average fidelity of at least `0.999`
  against $\lvert \psi \rangle$.

Because teleportation includes measurement, the complete three-qubit circuit
does not have one final statevector. The evaluator follows every measurement
branch and verifies the reduced state of the target qubit, `q2`.

### Starter Signature

```python
from qiskit import QuantumCircuit

def solve() -> QuantumCircuit:
    circuit = QuantumCircuit(3, 2)
    return circuit
```
