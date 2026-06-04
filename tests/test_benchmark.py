from pipeline.benchmark_pipeline import get_alg_benchmark
from qiskit import QuantumCircuit

def test_get_alg_benchmark():
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.x(2)

    expected_output = {
        "num_qubits": 3,
        "depth": 4,
        "total_num_gates": 4,
        "num_single_gates": 2,
        "controlled_gates": 2,
    }

    assert get_alg_benchmark(circuit) == expected_output 