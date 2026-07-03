import math
from collections.abc import Callable

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from problems.h2_vqe.reference_circuit import hamiltonian


EXPECTED_QUBITS = 2
EXPECTATION_TOLERANCE = 1e-10
TEST_ANGLES = (
    (0.2, 0.4),
    (-0.7, 1.1),
    (math.pi / 3, -math.pi / 5),
)
VALIDATION_TARGET = "entry_point"


def _failure(message: str, **details) -> dict:
    return {
        "passed": False,
        "message": message,
        **details,
    }


def _success(message: str = "Accepted", **details) -> dict:
    return {
        "passed": True,
        "message": message,
        **details,
    }


def _reference_ansatz(theta_1: float, theta_2: float) -> QuantumCircuit:
    circuit = QuantumCircuit(EXPECTED_QUBITS)
    circuit.ry(theta_1, 0)
    circuit.ry(theta_2, 1)
    circuit.cx(0, 1)
    return circuit


def _reference_expectation(theta_1: float, theta_2: float) -> float:
    reference_state = Statevector.from_instruction(_reference_ansatz(theta_1, theta_2))
    return float(complex(reference_state.expectation_value(hamiltonian())).real)


def _make_instance(user_solve_class: Callable, theta_1: float, theta_2: float):
    try:
        return user_solve_class([theta_1, theta_2])
    except Exception as exc:
        raise RuntimeError(
            f"Could not instantiate Solve with angles [{theta_1}, {theta_2}]: {exc}"
        ) from exc


def validate_expectation(user_solution, theta_1: float, theta_2: float) -> dict:
    """Compare submitted expectation_value() against the reference value."""
    solve_instance = (
        user_solution
        if not isinstance(user_solution, type)
        else _make_instance(user_solution, theta_1, theta_2)
    )

    expectation_method = getattr(solve_instance, "expectation_value", None)
    if not callable(expectation_method):
        return _failure(
            "Solve must define a callable `expectation_value` method.",
            expectation_close=False,
            expectation_threshold=EXPECTATION_TOLERANCE,
        )

    try:
        submitted_expectation = complex(expectation_method(theta_1, theta_2))
    except Exception as exc:
        return _failure(
            f"expectation_value({theta_1}, {theta_2}) failed: {exc}",
            expectation_close=False,
            expectation_threshold=EXPECTATION_TOLERANCE,
        )

    if abs(submitted_expectation.imag) > EXPECTATION_TOLERANCE:
        return _failure(
            "expectation_value() must return a real scalar.",
            submitted_expectation_real=float(submitted_expectation.real),
            submitted_expectation_imag=float(submitted_expectation.imag),
            expectation_close=False,
            expectation_threshold=EXPECTATION_TOLERANCE,
        )

    reference_expectation = _reference_expectation(theta_1, theta_2)
    expectation_difference = abs(submitted_expectation.real - reference_expectation)
    expectation_close = expectation_difference <= EXPECTATION_TOLERANCE

    result = {
        "submitted_expectation": float(submitted_expectation.real),
        "reference_expectation": reference_expectation,
        "expectation_difference": float(expectation_difference),
        "expectation_threshold": EXPECTATION_TOLERANCE,
        "expectation_close": expectation_close,
    }

    if not expectation_close:
        return _failure("Failed", **result)

    return _success("Accepted", **result)


def validate(user_solve_class: Callable) -> dict:
    """Validate the submitted H2 VQE Solve class by expectation value only."""
    if not callable(user_solve_class):
        return _failure("validate() expects the submitted Solve class.")

    expectation_comparisons = {}
    max_difference = 0.0
    max_difference_angles = ""

    for theta_1, theta_2 in TEST_ANGLES:
        try:
            expectation_result = validate_expectation(
                user_solve_class, theta_1, theta_2
            )
        except RuntimeError as exc:
            return _failure(str(exc))

        angle_key = f"theta=({theta_1}, {theta_2})"
        if not expectation_result["passed"]:
            return {
                **expectation_result,
                "expectation_difference": expectation_result.get(
                    "expectation_difference"
                ),
                "expectation_difference_angles": angle_key,
            }

        expectation_difference = expectation_result["expectation_difference"]
        expectation_comparisons[angle_key] = {
            key: expectation_result[key]
            for key in (
                "submitted_expectation",
                "reference_expectation",
                "expectation_difference",
                "expectation_threshold",
                "expectation_close",
            )
        }

        if expectation_difference >= max_difference:
            max_difference = expectation_difference
            max_difference_angles = angle_key

    passed = max_difference <= EXPECTATION_TOLERANCE
    return {
        "passed": passed,
        "message": "Accepted" if passed else "Failed",
        "expectation_close": passed,
        "expectation_difference": float(max_difference),
        "expectation_difference_angles": max_difference_angles,
        "expectation_threshold": EXPECTATION_TOLERANCE,
        "expectation_comparisons": expectation_comparisons,
    }
