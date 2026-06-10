from mqt.predictor.rl import Predictor as RL_Predictor
from mqt.bench.targets import get_device
import mqt.predictor.rl.actions as actions
from mqt.predictor.reward import figure_of_merit


TARGETS = [
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
    "rigetti_ankaa_84"
]


# openQASM 3.0 includes classical control flow which is not 
# supported by BQSKIT. By passing BQSKIT syntehsizer and compiler altogether
# in the training. 
for name, action in list(actions._ACTIONS.items()):
    if action.origin == actions.CompilationOrigin.BQSKIT:
        actions.remove_action(name)
def train_predctor(device_name:str, figure_of_merit:str, timesteps:int):
    device = get_device(device_name)
    rl_pred = RL_Predictor(device=device, figure_of_merit=figure_of_merit)
    rl_pred.train_model(timesteps=timesteps)

