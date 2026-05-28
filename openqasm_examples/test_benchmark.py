from mqt.bench import get_benchmark, BenchmarkLevel
from qiskit import qasm3
from qiskit.circuit import QuantumCircuit


def test_benchmarks(qasm_path, level=BenchmarkLevel.ALG) -> QuantumCircuit:
    circuit = qasm3.load(qasm_path)
    benchmark_result = get_benchmark(circuit, level=level)
    return benchmark_result


qasm_path = "full_adder_alg_4.qasm"
benchmark_result = test_benchmarks(qasm_path)
print(f"Circuit depth: {benchmark_result.depth()}")
print(f"Circuit size: {benchmark_result.size()}")
