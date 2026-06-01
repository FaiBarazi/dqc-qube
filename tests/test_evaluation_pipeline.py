from pathlib import Path
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from pipeline.evaluation_pipeline import compute_fidelity, evolve_state, load_circuit


def test_pipeline():
    qasm_path = (
        Path(__file__).resolve().parents[1] / "pipeline" / "full_adder_alg_4.qasm"
    )
    # Compose the full adder circuit with the input state |1010>
    adder_circuit = load_circuit(str(qasm_path))
    assert circuit.num_qubits == 4
    assert circuit.num_clbits == 4
    
    circuit = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)
    circuit.x(1)
    circuit.x(2)
    circuit.compose(adder_circuit, inplace=True)
   
    
    assert len(circuit.data) == 2
    assert circuit.data[0].operation.name == "FullAdder"

    output_state = evolve_state(circuit)
    # Target state is |1010> after applying the full adder circuit to the input state |1010>.
    target_state = Statevector.from_label("1010")

    assert output_state == target_state
    assert compute_fidelity(output_state, target_state) - 1.0 <= 0.001
