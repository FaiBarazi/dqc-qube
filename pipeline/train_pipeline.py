from mqt.predictor.rl import Predictor as RL_Predictor
from mqt.bench.targets import get_device
import mqt.predictor.rl.actions as actions

# openQASM 3.0 includes classical control flow which is not 
# supported by BQSKIT. By passing BQSKIT syntehsizer and compiler altogether
# in the training. 
for name, action in list(actions._ACTIONS.items()):
    if action.origin == actions.CompilationOrigin.BQSKIT:
        actions.remove_action(name)

device = get_device("ibm_falcon_27")
rl_pred = RL_Predictor(device=device, figure_of_merit="expected_fidelity")
rl_pred.train_model(timesteps=1000)