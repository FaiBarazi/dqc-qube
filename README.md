# dqc-qube
This project is a quantum "leetcode" service targeted to quantum circuits developers. It runs as a web application in the browser, evaluates a submitted circuits output against a benchmark and as well provides metrics on number of 1 qubit gates, 2 qubit gates, circuit depth ..etc. 

## Current Capabilities

- 5 problem sets: 
    - Simple bell state. 
    - Deutsch Josza 
    - H2 VQE
    - Qunatum Fourier Transformation (QFT)
    - Steane Error Correction (7 qubit)
    - Teleportation
- The evaluation can be done on functions and classes
- Evaluation output based on Statevectors, Exceptation value and Galois Field.

## Getting Started

1. Install dependencies:

```bash
uv sync
```

2. Run tests:

```bash
uv run pytest
```
## Repo Structure
- pipeline: Functions used in the benchmarking and evaluation.
- problems: Problemsets as described below. 
- app: The app is a 'shiny' dashboard app that runs the application. To run: `shiny run app.py`
- run_server + dockerfiles:  Sepcific to running the service in a containarized environment.
- uv (uv.lock + pyproject.toml): The project is managed through [uv](https://docs.astral.sh/uv/). 

## Problems Structure
Each of the problems in the problem folder has: 
- metadata.json: includes information about the problems and the entry point to be evaluated, whether a function or a method of a class. 
- problem.md: The description of the problem
- reference_circuit: Benchmark circuit to compare against. 
- starter: starter code displayed in the code area. 
- tests: Runs the submitted circuit and evaluates the circuit against the benchmark based on coded evaluation criteria. the output is displayed in the web app. 

**Note**: The evaulation criteria is not an absolute measure of the "correctness" of a circuit. It is a measure of how close a solution is to a reference circuit. 

## Training Pipeline [WIP]
[MQT predictor](https://pypi.org/project/mqt.predictor/) is used for best device prediction. The training is in 2 steps: 
- Reinforcement Learning step, training for circuit specific compilers. The current available compilers are: QISKIT, TKET and BQSKIT. 
- Machine Learning (Random Forest) That predicts a target (device) based on a circuit. 

### Current issues with the training pipeline: 
-  When this was written, BQSKIT has issues with OpenQASM3 classical control flow. In OpenQASM3, classical control flow are added to the definition(e.g: "else_if"). 
- BQSKIT compiler can be removed from actions in RL through code. Refer to `train_pipeline`
- For the ML pass, the above does not work and BQSKIT needs to be commented out from the site-packages. `<VirtualEnv>/lib/python3.<version>/site-packages/mqt/predictor/rl/actions.py` were the list of registered actions can be found.
- There are as well some issues with certain gates mapping depending on the target device.  

