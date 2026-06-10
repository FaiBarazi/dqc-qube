import pennylane as pq
import pytest

from pipeline.converters.pennylane_converter import (
    ConversionError,
    export_pennylane_to_qasm2,
    export_pennylane_to_qasm3,
    pennylane_source_to_circuit,
    pennylane_source_to_qasm2,
    pennylane_source_to_qasm3,
    pennylane_to_qasm2,
    pennylane_to_qasm3,
)


def make_bell_qnode():
    dev = pq.device("default.qubit", wires=2)

    @pq.qnode(dev)
    def circuit():
        pq.Hadamard(wires=0)
        pq.CNOT(wires=[0, 1])
        return pq.probs(wires=[0, 1])

    return circuit


def test_pennylane_to_qasm2_exports_openqasm2():
    qasm = pennylane_to_qasm2(make_bell_qnode())

    assert "OPENQASM 2.0" in qasm
    assert "h q[0]" in qasm
    assert "cx q[0],q[1]" in qasm


def test_pennylane_to_qasm3_normalizes_openqasm2_export():
    qasm = pennylane_to_qasm3(make_bell_qnode())

    assert "OPENQASM 3" in qasm
    assert "h" in qasm
    assert "cx" in qasm


def test_export_pennylane_to_qasm2_writes_file(tmp_path):
    qasm_path = export_pennylane_to_qasm2(make_bell_qnode(), tmp_path / "bell.qasm")

    assert qasm_path.exists()
    assert "OPENQASM 2.0" in qasm_path.read_text(encoding="utf-8")


def test_export_pennylane_to_qasm3_writes_file(tmp_path):
    qasm_path = export_pennylane_to_qasm3(make_bell_qnode(), tmp_path / "bell.qasm")

    assert qasm_path.exists()
    assert "OPENQASM 3" in qasm_path.read_text(encoding="utf-8")


def test_pennylane_source_to_circuit_accepts_qnode_factory():
    source = """
import pennylane as pq


def solve():
    dev = pq.device("default.qubit", wires=2)

    @pq.qnode(dev)
    def circuit():
        pq.Hadamard(wires=0)
        pq.CNOT(wires=[0, 1])
        return pq.probs(wires=[0, 1])

    return circuit
"""

    circuit = pennylane_source_to_circuit(source)

    assert callable(circuit)


def test_pennylane_source_to_qasm2_returns_circuit_and_qasm():
    source = """
import pennylane as pq


def solve():
    dev = pq.device("default.qubit", wires=1)

    @pq.qnode(dev)
    def circuit():
        pq.PauliX(wires=0)
        return pq.probs(wires=0)

    return circuit
"""

    result = pennylane_source_to_qasm2(source)

    assert result.qasm_version == "2.0"
    assert "OPENQASM 2.0" in result.qasm
    assert "x q[0]" in result.qasm


def test_pennylane_source_to_qasm3_returns_circuit_and_qasm():
    source = """
import pennylane as pq


dev = pq.device("default.qubit", wires=1)


@pq.qnode(dev)
def solve():
    pq.PauliX(wires=0)
    return pq.probs(wires=0)
"""

    result = pennylane_source_to_qasm3(source)

    assert result.qasm_version == "3.0"
    assert "OPENQASM 3" in result.qasm
    assert "x" in result.qasm


def test_pennylane_source_to_circuit_requires_qnode_or_factory():
    with pytest.raises(ConversionError, match="QNode"):
        pennylane_source_to_circuit("def solve():\n    return 42\n")

