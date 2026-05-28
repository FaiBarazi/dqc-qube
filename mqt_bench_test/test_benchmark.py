"""
Note:
This module is intended for testing the benchmarking and predictor
provided by MQT.
"""

from mqt.bench import get_benchmark, BenchmarkLevel
from mqt.predictor import qcompile
from qiskit import qasm3
from qiskit import circuit
from qiskit.circuit import QuantumCircuit


def test_benchmarks(circuit, level=BenchmarkLevel.INDEP) -> QuantumCircuit:
    benchmark_result = get_benchmark(circuit, level=level)
    print(f"Circuit size: {benchmark_result.size()}")
    print(f"Circuit Depth: {benchmark_result.depth()}")
    print(f"Total Operations: {len(benchmark_result.data)}")
    print(f"Gate Breakdown: {dict(benchmark_result.count_ops())}")
    return benchmark_result


def test_predictor(circuit: QuantumCircuit)->tuple[QuantumCircuit, dict, str]:
    qc_compiled, compilation_information, quantum_device = qcompile(circuit, figure_of_merit="expected_fidelity")
    print(quantum_device)
    print(compilation_information)
    qc_compiled.draw()
    return qc_compiled, compilation_information, quantum_device


def main():
    qasm_path = "openqasm_examples/full_adder_alg_4.qasm"
    circuit = qasm3.load(qasm_path)
    test_benchmarks(circuit)
    test_predictor(circuit)



if __name__ == "__main__":
    main()
