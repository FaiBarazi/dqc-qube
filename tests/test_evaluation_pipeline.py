from pathlib import Path
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from pipeline.evaluation_pipeline import compute_fidelity, evolve_state, load_circuit

current_dir = Path(__file__).parent


def test_pipeline():
    qasm_path = current_dir / "openqasm_circuits" / "full_adder_alg_4.qasm"

    adder_circuit = load_circuit(str(qasm_path))
    assert adder_circuit.num_qubits == 4
    assert adder_circuit.num_clbits == 4

    circuit = QuantumCircuit(adder_circuit.num_qubits, adder_circuit.num_clbits)
    # Compose the full adder circuit with the input state |0110>
    circuit.x(1)
    circuit.x(2)
    circuit.compose(adder_circuit, inplace=True)

    output_state = evolve_state(circuit)
    # Target state is |1010> after applying the full adder circuit to the input state |1010>.
    target_state = Statevector.from_label("1010")

    assert output_state == target_state
    assert compute_fidelity(output_state, target_state) - 1.0 <= 0.001
