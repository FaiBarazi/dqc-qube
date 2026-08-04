**Deutsch-Jozsa Algorithm**

Build the Deutsch-Jozsa circuit for a balanced parity oracle with four input
qubits. The oracle acts on input qubits `q0` through `q3` and the output
qubit `q4`:

$$
f(x_0, x_1, x_2, x_3) = x_0 \oplus x_1 \oplus x_2 \oplus x_3.
$$

Apply the complete algorithm: prepare the output qubit in $\lvert 1 \rangle$,
create the required superposition, apply the oracle, and finish with Hadamard
gates on the input register. Do not measure the circuit; it is evaluated as a
statevector.

For this balanced oracle, the four input qubits finish in
$\lvert 1111 \rangle$ and the output qubit remains in $\lvert - \rangle$.
In Qiskit's basis-state ordering, the complete target state is:

$$
\frac{\lvert 01111 \rangle - \lvert 11111 \rangle}{\sqrt{2}}.
$$

**Requirements**

- Implement a function named `solve`.
- Return a `qiskit.QuantumCircuit`.
- Use exactly 5 qubits: four input qubits and one output qubit.
- Do not add classical bits or measurements.
- Your output state must have fidelity of at least `0.999` against the
  benchmark circuit.

**Starter Signature**

```python
from qiskit import QuantumCircuit

def solve() -> QuantumCircuit:
    circuit = QuantumCircuit(5)
    return circuit
```
