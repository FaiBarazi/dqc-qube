from qiskit import QuantumCircuit, qasm3
import pytest

from pipeline.converters.qiskit_converter import (
    ConversionError,
    circuit_to_qasm3,
    export_circuit_to_qasm3,
    source_to_circuit,
    source_to_qasm3,
)


def test_circuit_to_qasm3_exports_openqasm3():
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)

    qasm = circuit_to_qasm3(circuit)

    assert "OPENQASM 3" in qasm
    assert "h" in qasm
    assert "cx" in qasm


def test_export_circuit_to_qasm3_writes_loadable_file(tmp_path):
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)

    qasm_path = export_circuit_to_qasm3(circuit, tmp_path / "bell.qasm")
    loaded_circuit = qasm3.load(str(qasm_path))

    assert qasm_path.exists()
    assert loaded_circuit.num_qubits == 2


def test_source_to_circuit_runs_solve_function():
    source = """
from qiskit import QuantumCircuit


def solve():
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    return circuit
"""

    circuit = source_to_circuit(source)

    assert circuit.num_qubits == 2
    assert len(circuit.data) == 2


def test_source_to_qasm3_returns_circuit_and_qasm():
    source = """
from qiskit import QuantumCircuit


def solve():
    circuit = QuantumCircuit(1)
    circuit.x(0)
    return circuit
"""

    result = source_to_qasm3(source)

    assert result.circuit.num_qubits == 1
    assert "OPENQASM 3" in result.qasm
    assert "x" in result.qasm


def test_source_to_circuit_requires_callable_solve():
    with pytest.raises(ConversionError, match="solve"):
        source_to_circuit("answer = 42")


def test_source_to_circuit_requires_quantum_circuit_return_value():
    source = """
def solve():
    return "not a circuit"
"""

    with pytest.raises(ConversionError, match="QuantumCircuit"):
        source_to_circuit(source)

