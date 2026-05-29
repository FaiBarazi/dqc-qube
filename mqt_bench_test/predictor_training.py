"""
This is a one time run. When installing the qmt.predictor
using pip, the weights are not included.
Refer to qmt.predictor framework setup docs: https://mqt.readthedocs.io/projects/predictor/en/latest/setup.html

Note: There is an issue with the RL training pipeline, mapping gates
"""

from mqt.predictor.rl import Predictor as RL_Predictor
from mqt.bench.targets import get_device
import os

DEVICES = [
    "ibm_eagle_127",
    "ibm_falcon_127",
    "ibm_falcon_27",
    "ibm_heron_133",
    "ibm_heron_156",
    "ionq_aria_25",
    "ionq_forte_36",
    "iqm_crystal_20",
    "iqm_crystal_5",
    "iqm_crystal_54",
    "quantinuum_h2_56",
    "rigetti_ankaa_84",
]

figure_of_merit = [
    "expected_fidelity",
    "critical_depth",
    "estimated_success_probability",
    "hellinger_distance",
    "estimated_hellinger_distance",
]


def train_for_devices(devices_names: list, merit: str = "expected_fidelity"):
    for device_name in devices_names:
        print(f"Training predictor for {device_name}...")
        device = get_device(device_name)
        rl_pred = RL_Predictor(device=device, figure_of_merit=merit)
        rl_pred.train_model(timesteps=1000, model_name=device_name)
    print("Training complete. Hard exiting to avoid segfault.")
    os._exit(0)


def main():
    # Change these based on the devices to be trained on for optimization.
    devices_names = ["ibm_eagle_127"]
    train_for_devices(devices_names)


if __name__ == "__main__":
    main()
