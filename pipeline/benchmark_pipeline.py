from qiskit import QuantumCircuit
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


def benchmark_metrics(reference_circuit: QuantumCircuit, submitted_circuit: QuantumCircuit) -> dict:
    """
    Compare a submitted circuit against a reference circuit.

    Computes :func:`get_alg_benchmark` for both circuits and returns a
    side-by-side comparison.  The reference circuit is obtained externally
    (e.g. via :func:`pipeline.evaluation_pipeline.get_reference_circuit`) so
    that this function stays agnostic of whether the reference comes from a
    custom ``reference_circuit.py`` or from MQT Bench.

    Args:
        reference_circuit: The reference / gold-standard QuantumCircuit.
        submitted_circuit: The user's compiled QuantumCircuit.

    Returns:
        dict with keys ``"submitted"`` and ``"reference"``, each containing
        the metrics produced by :func:`get_alg_benchmark`::

            {
                "submitted":  {"depth": ..., "num_single_gates": ..., ...},
                "reference":  {"depth": ..., "num_single_gates": ..., ...},
            }
    """
    return {
        "submitted": get_alg_benchmark(submitted_circuit),
        "reference": get_alg_benchmark(reference_circuit),
    }


def get_mqt_catalog() -> dict:
    return get_benchmark_catalog()