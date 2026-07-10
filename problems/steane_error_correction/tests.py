"""Validate Steane circuits by comparing signed Pauli invariants over GF(2)."""

from dataclasses import dataclass
from functools import lru_cache

from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford, Pauli

from problems.steane_error_correction.reference_circuit import get_reference_circuit


EXPECTED_DATA_QUBITS = 7
EXPECTED_ANCILLA_QUBITS = 6
EXPECTED_QUBITS = EXPECTED_DATA_QUBITS + EXPECTED_ANCILLA_QUBITS
EXPECTED_CLBITS = EXPECTED_ANCILLA_QUBITS
ANCILLA_START = EXPECTED_DATA_QUBITS
IGNORED_INSTRUCTIONS = {"barrier", "measure"}


@dataclass(frozen=True)
class PauliInvariants:
    encoding_stabilizers: tuple[Pauli, ...]
    logical_x: Pauli
    logical_z: Pauli
    syndrome_stabilizers: tuple[Pauli, ...]


def _failure(message: str, **details) -> dict:
    return {
        "passed": False,
        "message": message,
        **details,
    }


def _find_encode_detection_boundary(circuit: QuantumCircuit) -> int:
    for index, instruction in enumerate(circuit.data):
        if instruction.operation.name in IGNORED_INSTRUCTIONS:
            continue

        qubit_indices = [
            circuit.find_bit(qubit).index for qubit in instruction.qubits
        ]
        if any(qubit_index >= ANCILLA_START for qubit_index in qubit_indices):
            return index

    raise ValueError("Could not find ancilla-based syndrome extraction.")


def _quantum_subcircuit(
    circuit: QuantumCircuit,
    start: int,
    stop: int,
) -> QuantumCircuit:
    subcircuit = QuantumCircuit(circuit.num_qubits)

    for instruction in circuit.data[start:stop]:
        if instruction.operation.name in IGNORED_INSTRUCTIONS:
            continue
        if instruction.clbits:
            raise ValueError(
                "Classically controlled operations are not supported in the "
                "Steane Pauli-tracking validator."
            )

        qubit_indices = [
            circuit.find_bit(qubit).index for qubit in instruction.qubits
        ]
        subcircuit.append(instruction.operation.copy(), qubit_indices)

    return subcircuit.decompose(reps=8)


def _pauli_on(num_qubits: int, kind: str, qubit: int) -> Pauli:
    x_bits = [False] * num_qubits
    z_bits = [False] * num_qubits

    if kind in {"x", "y"}:
        x_bits[qubit] = True
    if kind in {"z", "y"}:
        z_bits[qubit] = True

    return Pauli((z_bits, x_bits))


def _project_data_pauli(pauli: Pauli, *, allow_ancilla_z: bool = False) -> Pauli:
    x_bits = [bool(bit) for bit in pauli.x]
    z_bits = [bool(bit) for bit in pauli.z]

    if any(x_bits[ANCILLA_START:]):
        raise ValueError(
            "A tracked observable has X/Y support on an ancilla qubit, so it "
            "does not reduce to a Steane data-qubit Pauli."
        )

    if not allow_ancilla_z and any(z_bits[ANCILLA_START:]):
        raise ValueError(
            "A tracked encoding observable leaked onto an ancilla qubit."
        )

    return Pauli(
        (
            z_bits[:EXPECTED_DATA_QUBITS],
            x_bits[:EXPECTED_DATA_QUBITS],
            int(pauli.phase),
        )
    )


def _encoded_pauli(
    encoding_clifford: Clifford,
    circuit_num_qubits: int,
    kind: str,
    qubit: int,
) -> Pauli:
    return _project_data_pauli(
        _pauli_on(circuit_num_qubits, kind, qubit).evolve(
            encoding_clifford,
            frame="s",
        )
    )


def _measured_syndrome_paulis(
    circuit: QuantumCircuit,
    boundary: int,
) -> tuple[Pauli, ...]:
    measured_paulis: list[Pauli] = []

    for index, instruction in enumerate(circuit.data[boundary:], start=boundary):
        if instruction.operation.name != "measure":
            continue

        measured_qubit = circuit.find_bit(instruction.qubits[0]).index
        if measured_qubit < ANCILLA_START:
            raise ValueError("Syndrome extraction must measure ancilla qubits only.")

        syndrome_clifford = Clifford(_quantum_subcircuit(circuit, boundary, index))
        observable = _pauli_on(circuit.num_qubits, "z", measured_qubit).evolve(
            syndrome_clifford,
            frame="h",
        )
        measured_paulis.append(
            _project_data_pauli(observable, allow_ancilla_z=True)
        )

    if len(measured_paulis) != EXPECTED_ANCILLA_QUBITS:
        raise ValueError(
            f"Expected {EXPECTED_ANCILLA_QUBITS} ancilla measurements, got "
            f"{len(measured_paulis)}."
        )

    return tuple(measured_paulis)


def _pauli_invariants(circuit: QuantumCircuit) -> PauliInvariants:
    boundary = _find_encode_detection_boundary(circuit)
    encoding_clifford = Clifford(_quantum_subcircuit(circuit, 0, boundary))

    return PauliInvariants(
        encoding_stabilizers=tuple(
            _encoded_pauli(encoding_clifford, circuit.num_qubits, "z", qubit)
            for qubit in range(1, EXPECTED_DATA_QUBITS)
        ),
        logical_x=_encoded_pauli(encoding_clifford, circuit.num_qubits, "x", 0),
        logical_z=_encoded_pauli(encoding_clifford, circuit.num_qubits, "z", 0),
        syndrome_stabilizers=_measured_syndrome_paulis(circuit, boundary),
    )


def _pauli_mask(pauli: Pauli) -> tuple[int, ...]:
    return tuple(int(bit) for bit in pauli.x) + tuple(int(bit) for bit in pauli.z)


def _pack_bits(bits: tuple[int, ...]) -> int:
    value = 0
    for index, bit in enumerate(bits):
        if bit:
            value |= 1 << index
    return value


def _gf2_rank(rows: tuple[tuple[int, ...], ...]) -> int:
    basis: dict[int, int] = {}

    for row in rows:
        value = _pack_bits(row)
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]

    return len(basis)


def _gf2_row_space_equal(
    left_rows: tuple[tuple[int, ...], ...],
    right_rows: tuple[tuple[int, ...], ...],
) -> bool:
    left_rank = _gf2_rank(left_rows)
    right_rank = _gf2_rank(right_rows)
    combined_rank = _gf2_rank(left_rows + right_rows)

    return left_rank == right_rank == combined_rank


def _signed_pauli_key(pauli: Pauli) -> tuple[int, tuple[int, ...], tuple[int, ...]]:
    phase = int(pauli.phase) % 4
    if phase not in {0, 2}:
        raise ValueError(
            f"Non-Hermitian Pauli product encountered: {pauli.to_label()}."
        )

    return (
        phase,
        tuple(int(bit) for bit in pauli.x),
        tuple(int(bit) for bit in pauli.z),
    )


def _assert_commuting(paulis: tuple[Pauli, ...], label: str) -> None:
    for left_index, left in enumerate(paulis):
        for right in paulis[left_index + 1 :]:
            if not left.commutes(right):
                raise ValueError(f"{label} generators do not commute.")


def _signed_pauli_group(paulis: tuple[Pauli, ...], label: str) -> dict:
    _assert_commuting(paulis, label)

    identity = Pauli(
        ([False] * EXPECTED_DATA_QUBITS, [False] * EXPECTED_DATA_QUBITS)
    )
    group = {_signed_pauli_key(identity): identity}

    for generator in paulis:
        for element in tuple(group.values()):
            product = element.compose(generator)
            group[_signed_pauli_key(product)] = product

    return group


def _signed_logical_coset(
    logical: Pauli,
    stabilizer_group: dict,
) -> set[tuple[int, tuple[int, ...], tuple[int, ...]]]:
    return {
        _signed_pauli_key(stabilizer.compose(logical))
        for stabilizer in stabilizer_group.values()
    }


def _compare_invariants(
    submitted: PauliInvariants,
    reference: PauliInvariants,
) -> tuple[dict, dict]:
    submitted_encoding_masks = tuple(
        _pauli_mask(pauli) for pauli in submitted.encoding_stabilizers
    )
    reference_encoding_masks = tuple(
        _pauli_mask(pauli) for pauli in reference.encoding_stabilizers
    )
    submitted_syndrome_masks = tuple(
        _pauli_mask(pauli) for pauli in submitted.syndrome_stabilizers
    )
    reference_syndrome_masks = tuple(
        _pauli_mask(pauli) for pauli in reference.syndrome_stabilizers
    )

    submitted_encoding_group = _signed_pauli_group(
        submitted.encoding_stabilizers,
        "encoding stabilizer",
    )
    reference_encoding_group = _signed_pauli_group(
        reference.encoding_stabilizers,
        "reference encoding stabilizer",
    )
    submitted_syndrome_group = _signed_pauli_group(
        submitted.syndrome_stabilizers,
        "syndrome stabilizer",
    )
    reference_syndrome_group = _signed_pauli_group(
        reference.syndrome_stabilizers,
        "reference syndrome stabilizer",
    )

    checks = {
        "encoding_stabilizer_space": _gf2_row_space_equal(
            submitted_encoding_masks,
            reference_encoding_masks,
        )
        and set(submitted_encoding_group) == set(reference_encoding_group),
        "logical_x": _signed_pauli_key(submitted.logical_x)
        in _signed_logical_coset(reference.logical_x, reference_encoding_group),
        "logical_z": _signed_pauli_key(submitted.logical_z)
        in _signed_logical_coset(reference.logical_z, reference_encoding_group),
        "syndrome_stabilizer_space": _gf2_row_space_equal(
            submitted_syndrome_masks,
            reference_syndrome_masks,
        )
        and set(submitted_syndrome_group) == set(reference_syndrome_group),
    }
    diagnostics = {
        "encoding_rank": _gf2_rank(submitted_encoding_masks),
        "reference_encoding_rank": _gf2_rank(reference_encoding_masks),
        "syndrome_rank": _gf2_rank(submitted_syndrome_masks),
        "reference_syndrome_rank": _gf2_rank(reference_syndrome_masks),
    }

    return checks, diagnostics


@lru_cache(maxsize=1)
def _reference_invariants() -> PauliInvariants:
    return _pauli_invariants(get_reference_circuit())


def validate(circuit: QuantumCircuit) -> dict:
    if not isinstance(circuit, QuantumCircuit):
        return _failure(
            "solve() must return a qiskit.QuantumCircuit.",
            check_score=0.0,
        )

    if circuit.num_qubits != EXPECTED_QUBITS:
        return _failure(
            f"Expected {EXPECTED_QUBITS} qubits, got {circuit.num_qubits}.",
            check_score=0.0,
        )

    if circuit.num_clbits != EXPECTED_CLBITS:
        return _failure(
            f"Expected {EXPECTED_CLBITS} classical bits, got {circuit.num_clbits}.",
            check_score=0.0,
        )

    try:
        submitted_invariants = _pauli_invariants(circuit)
        reference_invariants = _reference_invariants()
        checks, diagnostics = _compare_invariants(
            submitted_invariants,
            reference_invariants,
        )
    except Exception as exc:
        return _failure(
            f"Could not Pauli-track Steane circuit: {exc}",
            check_score=0.0,
        )

    passed_checks = sum(1 for passed in checks.values() if passed)
    check_score = passed_checks / len(checks)
    passed = all(checks.values())

    return {
        "passed": passed,
        "message": "Accepted" if passed else "Wrong answer",
        "check_score": float(check_score),
        "checks": checks,
        **diagnostics,
    }
