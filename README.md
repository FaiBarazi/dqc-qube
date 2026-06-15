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

## Training Pipeline
[MQT predictor](https://pypi.org/project/mqt.predictor/) is used for best device prediction. The training is in 2 steps: 
- Reinforcement Learning step, training for circuit specific compilers. The current available compilers are: QISKIT, TKET and BQSKIT. 
- Machine Learning (Random Forest) That predicts a target (device) based on a circuit. 

### Current issues with the training pipeline: 
-  When this was written, BQSKIT has issues with OpenQASM3 classical control flow. In OpenQASM3, classical control flow are added to the definition(e.g: "else_if"). 
- BQSKIT compiler can be removed from actions in RL through code. Refer to `train_pipeline`
- For the ML pass, the above does not work and BQSKIT needs to be commented out from the site-packages. `<VirtualEnv>/lib/python3.<version>/site-packages/mqt/predictor/rl/actions.py` were the list of registered actions can be found.
- There are as well some issues with certain gates mapping depending on the target device.  

