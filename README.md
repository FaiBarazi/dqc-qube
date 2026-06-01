# dqc-qube

> **Work in progress:** this repository is still being built. 


## Current Capabilities

- Load OpenQASM 3 circuit files using Qiskit
- Simulate a circuit statevector
- Compute fidelity between output and target states
- Include a sample test for full-adder circuit definition in `pipeline/full_adder_alg_4.qasm`

## Getting Started

1. Install dependencies:

```bash
uv sync
```

2. Run tests:

```bash
uv run pytest
```

