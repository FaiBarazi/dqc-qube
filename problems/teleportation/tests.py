from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit
from qiskit.circuit import Clbit
from qiskit.circuit.controlflow import IfElseOp
from qiskit.quantum_info import Statevector, partial_trace, state_fidelity


FIDELITY_THRESHOLD = 0.999
EXPECTED_QUBITS = 3
EXPECTED_CLBITS = 2
TARGET_QUBIT = 2
MAX_BRANCHES = 64


@dataclass(frozen=True)
class _Branch:
    state: Statevector
    classical_values: tuple[int, ...]
    probability: float


def _failure(message: str) -> dict:
    return {"passed": False, "fidelity": 0.0, "message": message}


def _condition_matches(
    condition,
    circuit: QuantumCircuit,
    clbit_map: list[int],
    classical_values: tuple[int, ...],
) -> bool:
    target, expected = condition

    if isinstance(target, Clbit):
        local_index = circuit.find_bit(target).index
        actual = classical_values[clbit_map[local_index]]
    elif isinstance(target, ClassicalRegister):
        actual = 0
        for bit_position, bit in enumerate(target):
            local_index = circuit.find_bit(bit).index
            actual |= classical_values[clbit_map[local_index]] << bit_position
    else:
        raise ValueError("Only classical-bit and classical-register conditions are supported.")

    return actual == int(expected)


def _measure_branch(
    branch: _Branch,
    qubit: int,
    clbit: int,
) -> list[_Branch]:
    indices = np.arange(branch.state.data.size)
    output: list[_Branch] = []

    for outcome in (0, 1):
        selected = ((indices >> qubit) & 1) == outcome
        projected = np.where(selected, branch.state.data, 0.0)
        conditional_probability = float(np.vdot(projected, projected).real)
        if conditional_probability <= 1e-15:
            continue

        projected /= np.sqrt(conditional_probability)
        values = list(branch.classical_values)
        values[clbit] = outcome
        output.append(
            _Branch(
                state=Statevector(projected, dims=branch.state.dims()),
                classical_values=tuple(values),
                probability=branch.probability * conditional_probability,
            )
        )

    return output


def _execute_circuit(
    circuit: QuantumCircuit,
    branches: list[_Branch],
    qubit_map: list[int],
    clbit_map: list[int],
) -> list[_Branch]:
    for instruction in circuit.data:
        operation = instruction.operation
        qubits = [
            qubit_map[circuit.find_bit(qubit).index] for qubit in instruction.qubits
        ]
        clbits = [
            clbit_map[circuit.find_bit(clbit).index] for clbit in instruction.clbits
        ]

        if operation.name == "barrier":
            continue

        if operation.name == "measure":
            branches = [
                measured
                for branch in branches
                for measured in _measure_branch(branch, qubits[0], clbits[0])
            ]
        elif isinstance(operation, IfElseOp):
            updated: list[_Branch] = []
            for branch in branches:
                condition_is_true = _condition_matches(
                    operation.condition,
                    circuit,
                    clbit_map,
                    branch.classical_values,
                )
                block_index = 0 if condition_is_true else 1
                if block_index >= len(operation.blocks):
                    updated.append(branch)
                    continue

                updated.extend(
                    _execute_circuit(
                        operation.blocks[block_index],
                        [branch],
                        qubits,
                        clbits,
                    )
                )
            branches = updated
        else:
            condition = getattr(operation, "condition", None)
            updated = []
            for branch in branches:
                if condition is not None and not _condition_matches(
                    condition,
                    circuit,
                    clbit_map,
                    branch.classical_values,
                ):
                    updated.append(branch)
                    continue

                try:
                    evolved = branch.state.evolve(operation, qargs=qubits)
                except Exception as exc:
                    raise ValueError(
                        f"Unsupported operation '{operation.name}': {exc}"
                    ) from exc
                updated.append(
                    _Branch(evolved, branch.classical_values, branch.probability)
                )
            branches = updated

        if len(branches) > MAX_BRANCHES:
            raise ValueError("Circuit creates too many measurement branches.")

    return branches


def _sender_measurements(circuit: QuantumCircuit) -> list[tuple[int, int]]:
    measurements = []
    for instruction in circuit.data:
        if instruction.operation.name != "measure":
            continue
        measurements.append(
            (
                circuit.find_bit(instruction.qubits[0]).index,
                circuit.find_bit(instruction.clbits[0]).index,
            )
        )
    return measurements


def validate(circuit: QuantumCircuit) -> dict:
    if not isinstance(circuit, QuantumCircuit):
        return _failure("solve() must return a qiskit.QuantumCircuit.")

    if circuit.num_qubits != EXPECTED_QUBITS:
        return _failure(
            f"Expected {EXPECTED_QUBITS} qubits, got {circuit.num_qubits}."
        )

    if circuit.num_clbits != EXPECTED_CLBITS:
        return _failure(
            f"Expected {EXPECTED_CLBITS} classical bits, got {circuit.num_clbits}."
        )

    measurements = _sender_measurements(circuit)
    if sorted(measurements) != [(0, 0), (1, 1)]:
        return _failure(
            "Measure q0 into c0 and q1 into c1 exactly once; do not measure q2."
        )

    initial_branch = _Branch(
        state=Statevector.from_int(0, 2**EXPECTED_QUBITS),
        classical_values=(0,) * EXPECTED_CLBITS,
        probability=1.0,
    )

    try:
        branches = _execute_circuit(
            circuit,
            [initial_branch],
            list(range(EXPECTED_QUBITS)),
            list(range(EXPECTED_CLBITS)),
        )
    except Exception as exc:
        return _failure(f"Could not simulate circuit: {exc}")

    if not branches:
        return _failure("Circuit produced no measurement outcomes.")

    target_state = Statevector.from_label("+")
    average_fidelity = 0.0
    for branch in branches:
        reduced_target = partial_trace(
            branch.state,
            [qubit for qubit in range(EXPECTED_QUBITS) if qubit != TARGET_QUBIT],
        )
        average_fidelity += branch.probability * float(
            state_fidelity(target_state, reduced_target)
        )

    average_fidelity = min(1.0, max(0.0, average_fidelity))
    passed = average_fidelity >= FIDELITY_THRESHOLD
    return {
        "passed": passed,
        "fidelity": average_fidelity,
        "message": "Accepted" if passed else "Wrong answer",
    }
