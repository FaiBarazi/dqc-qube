from qiskit import QuantumCircuit
from mqt.bench import get_benchmark
from mqt.bench.benchmark_generation import BenchmarkLevel
from mqt.bench.benchmarks import get_benchmark_catalog


def get_alg_benchmark(circuit: QuantumCircuit) -> dict:
    """
    Return stats for a circuit on the algorithm level.
    Since there is no gates mapping / optimization at this stage, the information
    can be extracted directly from the circuit.
    Return:
        dict: {
            "num_qubits": int,
            "depth": int,
            "total_num_gates": int,
            "num_single_gates": int,
            "controlled_gates": int,
        }
    """
    num_qubits = circuit.num_qubits
    depth = circuit.depth()
    total_num_gates = circuit.size()
    single_q = sum(1 for inst in circuit.data if len(inst.qubits) == 1)
    ctrl_q = sum(1 for inst in circuit.data if len(inst.qubits) > 1)

    return {
        "num_qubits": num_qubits,
        "depth": depth,
        "total_num_gates": total_num_gates,
        "num_single_gates": single_q,
        "controlled_gates": ctrl_q,
    }


def benchmark_metrics(mqt_bench_key: str, submitted_circuit: QuantumCircuit) -> dict:
    """
    Compare a submitted circuit against the equivalent MQT Bench reference circuit.

    Fetches the MQT Bench ALG-level circuit for *mqt_bench_key* at the same
    qubit count as *submitted_circuit*, computes ``get_alg_benchmark`` for both,
    and returns a side-by-side comparison.

    Args:
        mqt_bench_key: The MQT Bench benchmark identifier (e.g. ``"dj"``, ``"qft"``).
        submitted_circuit: The user's compiled QuantumCircuit.

    Returns:
        dict with keys ``"submitted"`` and ``"mqt_bench"``, each containing the
        metrics produced by :func:`get_alg_benchmark`::

            {
                "submitted": {"depth": ..., "num_single_gates": ..., ...},
                "mqt_bench":  {"depth": ..., "num_single_gates": ..., ...},
            }
    """
    num_qubits = submitted_circuit.num_qubits
    mqt_circuit = get_benchmark(
        mqt_bench_key,
        BenchmarkLevel.ALG,
        circuit_size=num_qubits,
    )
    return {
        "submitted": get_alg_benchmark(submitted_circuit),
        "mqt_bench": get_alg_benchmark(mqt_circuit),
    }


def get_mqt_catalog() -> dict:
    return get_benchmark_catalog()