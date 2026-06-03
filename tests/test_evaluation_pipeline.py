from pathlib import Path
import numpy as np
from vqe_h2 import run_gradient_optimizer
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from pipeline.evaluation_pipeline import compute_fidelity, evolve_state, load_circuit

current_dir = Path(__file__).parent


def test_full_adder_pipeline():
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


def test_deutsch_josza_pipeline():
    """
    The Oracle in this case is a parity function that depends on the number of
    1 bits in a state. 
    ex: 
    - |0000> -> 0, |0011> -> 0, |0101> -> 0, ...
    - |0001> -> 1, |0010> -> 1, ...

    The statevector without the measuring would be: 
    ∣ψ⟩= 1/(sqrt(2))(|01111⟩- |11111⟩)
    There is a rounding error with floating point depending on the machine, hence we 
    need to compare with a margin of errror. 
    """
    qasm_path = current_dir / "openqasm_circuits" / "dj_alg_5.qasm"

    dj_circuit = load_circuit(str(qasm_path))
    dj_circuit.decompose(reps=10).draw()
    assert dj_circuit.num_qubits == 5

    output_state = evolve_state(dj_circuit)
    # The max amplitude is for the state |01111> and |11111> with a value of 1/sqrt(2)
    # These are at index 15 and 31 respectively. Scramble the rest of the output_state
    # vector to generate a target and check if the fidelity is within a margin of error. 
    target_state = output_state.copy()
    noise_real = np.random.uniform(-0.01, 0.01, size=target_state.data.shape)
    noise_imag = np.random.uniform(-0.001, 0.001, size=target_state.data.shape)
    noise = noise_real + 1j * noise_imag
    target_state = target_state + noise

    # Re normalize to make sure we have a correct vector.
    target_state = target_state / np.linalg.norm(target_state)
    print("Fidelity is:", compute_fidelity(output_state, target_state))

    assert abs(1.0 - compute_fidelity(output_state, target_state)) <= 0.01


def test_qft_pipeline():
    qasm_path = current_dir / "openqasm_circuits" / "qft_alg_5.qasm"

    qft_circuit = load_circuit(str(qasm_path))
    assert qft_circuit.num_qubits == 5
    output_state = evolve_state(qft_circuit)

    # |01101>, big endian. Qiskit uses small endian,  that is |q4 q3 q2 q1 q0> = |10110>. 
    circuit = QuantumCircuit(qft_circuit.num_qubits, qft_circuit.num_clbits)
    # Compose the full adder circuit with the input state |0110>
    for i in [0,2,3]:
        circuit.x(i)
    circuit.compose(qft_circuit, inplace=True)
    output_state = evolve_state(circuit)

    n_qubits = qft_circuit.num_qubits
    num_basis_states = 2**n_qubits 
    j = 13 # state |01101>
    k = np.arange(num_basis_states)

    # Compare the result against a methatmically calculated equivalent target state. 
    target_state = (1 / np.sqrt(num_basis_states)) * np.exp(2j * np.pi * j * k / num_basis_states)
    assert  abs(1.0 - compute_fidelity(output_state, target_state)) <= 0.01

# This test is not necessarily useful. In an actual senario, in the case of 
# heuristic, one way to check could be to check the result agains a known measurable value. 
# In opitmization problems, were answers are not known, normally these are in the contest 
# style such as Kaggle ..etc.
def test_h2_vqe(energy_threshold= 0.01):
    """
    Test the result of an optimization against a calculated value. This example a ground state.
    Note that VQE is a heuristic algorithm and the result can 
    vary based on the optimizer, the number of steps, and the initial parameters.
    """
    # H2 molecule has an estimated ground state energy of −1.13619 Ha 
    h2_energy = -1.13619
    assert (run_gradient_optimizer() - h2_energy) <= energy_threshold




