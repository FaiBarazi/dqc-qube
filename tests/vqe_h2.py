"""
Based losely on the pennylane example here: https://www.pennylane.ai/demos/tutorial_vqe.
libre text is a source for coordinates and symbols. https://chem.libretexts.org/
"""

import pennylane as qp
import pennylane.numpy as np 

# Hydrogen molecule instantiation. 
symbols = ["H", "H"]

coordinates = np.array([[-0.70108983, 0.0, 0.0], [0.70108983, 0.0, 0.0]], requires_grad=False)

H, qubits = qp.qchem.molecular_hamiltonian(symbols, coordinates)

# Hartee-Fock State prep. 
electrons = 2
hf_state = qp.qchem.hf_state(electrons, qubits)

# Quantum part 
dev = qp.device("lightning.qubit", wires=qubits)

@qp.qnode(dev)
def circuit(param, wires):
    qp.BasisState(hf_state, wires=wires)
    qp.DoubleExcitation(param, wires=[0, 1, 2, 3])
    return qp.expval(H)

def cost_fn(param):
    return circuit(param, wires=range(qubits))

# Classical optimization part.

def optimization(optimizer: object, stepsize: float, num_steps: int, params: np.tensor, print_step=10)->float:
    opt = optimizer(stepsize)
    for i in range(num_steps):
        params = opt.step(cost_fn, params)
        if i % print_step == 0:
            energy = cost_fn(params)
            print(f"Step {i:3d} | Energy = {energy:.8f} Ha")
    
    energy = cost_fn(params)
    print(f"\nEstimated ground state energy (VQE): {energy:.8f}")
    return energy

def run_gradient_optimizer():
    stepsize = 0.01 
    num_steps = 100
    print_step = 10
    optimizer = qp.AdamOptimizer
    

    theta = np.array(0.001, requires_grad=True)
    
    energy = optimization(optimizer, stepsize, num_steps, theta, print_step)
    return energy

