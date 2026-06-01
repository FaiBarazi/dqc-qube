from pathlib import Path
from qiskit.quantum_info import Statevector
from pipeline.evaluation_pipeline import compute_fidelity, evolve_state, load_circuit


def test_load_circuit_full_adder_qasm():
    qasm_path = (
        Path(__file__).resolve().parents[1] / "pipeline" / "full_adder_alg_4.qasm"
    )
    circuit = load_circuit(str(qasm_path))

    assert circuit.num_qubits == 4
    assert circuit.num_clbits == 4
    assert len(circuit.data) == 2
    assert circuit.data[0].operation.name == "FullAdder"


def test_evolve_state_and_compute_fidelity_zero_state():
    qasm_path = (
        Path(__file__).resolve().parents[1] / "pipeline" / "full_adder_alg_4.qasm"
    )
    circuit = load_circuit(str(qasm_path))
    output_state = evolve_state(circuit)
    target_state = Statevector.from_label("0" * circuit.num_qubits)

    assert output_state == target_state
    assert compute_fidelity(output_state, target_state) - 1.0 <= 0.001
