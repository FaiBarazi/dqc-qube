
import importlib

from qiskit import QuantumCircuit, qasm3
from qiskit.quantum_info import Statevector, state_fidelity


def load_circuit(qasm_file: str) -> QuantumCircuit:
    return qasm3.load(qasm_file)


def evolve_state(circuit: QuantumCircuit) -> Statevector:
    statevector_output = Statevector(circuit)
    return statevector_output


def compute_fidelity(output_state, target_state) -> float:
    fidelity = state_fidelity(target_state, output_state)
    return fidelity


def get_reference_circuit(
    problem_name: str,
    metadata: dict,
    num_qubits: int | None = None,
) -> QuantumCircuit:
    """Return the reference QuantumCircuit for a problem.

    Routing is driven by ``metadata["evaluation_target"]``:

    ``"custom"``
        Imports ``problems.<problem_name>.reference_circuit`` and calls
        ``get_reference_circuit()``.

    ``"mqt"``
        Fetches the MQT Bench ALG-level circuit identified by
        ``metadata["mqt_bench_key"]`` at *num_qubits* size.
        *num_qubits* is required for this target.

    Args:
        problem_name: Directory name of the problem (e.g. ``"bell_state"``)
        metadata:     Contents of the problem's ``metadata.json``.
        num_qubits:   Required only when ``evaluation_target`` is ``"mqt"``.

    Returns:
        The reference :class:`~qiskit.QuantumCircuit`.

    Raises:
        ValueError: If the target is unknown, or ``num_qubits`` / ``mqt_bench_key``
                    are missing for the ``"mqt"`` target.
    """
    evaluation_target = metadata.get("evaluation_target", "custom")

    if evaluation_target == "custom":
        module = importlib.import_module(f"problems.{problem_name}.reference_circuit")
        return module.get_reference_circuit()

    if evaluation_target == "mqt":
        if num_qubits is None:
            raise ValueError(
                "num_qubits is required when evaluation_target is 'mqt'"
            )
        mqt_bench_key = metadata.get("mqt_bench_key")
        if not mqt_bench_key:
            raise ValueError(
                "mqt_bench_key must be set in metadata when evaluation_target is 'mqt'"
            )
        from mqt.bench import get_benchmark  # noqa: PLC0415
        from mqt.bench.benchmark_generation import BenchmarkLevel  # noqa: PLC0415

        return get_benchmark(
            mqt_bench_key, BenchmarkLevel.ALG, circuit_size=num_qubits
        )

    raise ValueError(
        f"Unknown evaluation_target '{evaluation_target}'. Expected 'custom' or 'mqt'."
    )


def get_reference_statevector(
    problem_name: str,
    metadata: dict,
    num_qubits: int | None = None,
) -> Statevector:
    """Return the reference Statevector for a problem.

    Obtains the reference circuit via :func:`get_reference_circuit` and
    simulates it.  See that function for argument details.
    """
    ref_circuit = get_reference_circuit(problem_name, metadata, num_qubits)
    return Statevector.from_instruction(ref_circuit)
