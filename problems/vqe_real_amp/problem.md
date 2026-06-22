# VQE Real Amplitudes Ansatz

Implement a 5-qubit **VQE RealAmplitudes ansatz** circuit with 3 repetitions
(`reps=3`) and linear entanglement. This is the hardware-efficient ansatz used
inside the Variational Quantum Eigensolver (VQE) algorithm, built from `RY`
rotation layers interleaved with `CX` entangling layers.

## Circuit Structure

The ansatz has **4 RY layers** (one before each of the 3 entangling blocks, plus
one final rotation layer) and **3 CNOT layers** forming a linear chain
`q[3]→q[4], q[2]→q[3], q[1]→q[2], q[0]→q[1]`.

```text
Layer 0 (RY)  →  Entangle (CX chain)
Layer 1 (RY)  →  Entangle (CX chain)
Layer 2 (RY)  →  Entangle (CX chain)
Layer 3 (RY)
```

## Fixed Parameter Values

Use the following pre-optimised angles (in radians), indexed as `angles[layer][qubit]`:

```python
angles = [
    #  q[0]                 q[1]                 q[2]                 q[3]                 q[4]
    [6.006735895579343,  1.304903297657757,  5.205272730965009,  0.9379672423735244, 3.2220464314480877],  # layer 0
    [0.8540080589393146, 4.329343885871547,  5.288856933750764,  2.6735518805676657, 6.012543404956273 ],  # layer 1
    [5.185719590928789,  2.125069481984559,  3.6176102152986354, 4.733135208207287,  5.196847304624584 ],  # layer 2
    [5.864966885210837,  0.9110285368422897, 4.684618627355123,  0.8755706304852969, 5.695888160944528 ],  # layer 3
]
```

> **Source:** MQT Bench `vqe_real_amp_alg_5` benchmark (2025-10-16),
> Qiskit 2.1.1, OpenQASM 3.0.

## Requirements

- Implement a function named `solve`.
- Return a `qiskit.QuantumCircuit`.
- Use exactly **5 qubits**.
- Do **not** add measurements.
- Your output statevector must have fidelity of at least `0.999` against the
  reference state.

## Starter Signature

```python
from qiskit import QuantumCircuit

def solve() -> QuantumCircuit:
    circuit = QuantumCircuit(5)
    return circuit
```
