from neogui.ecmo_workspace import EcmoWorkspace


def test_learner_workspace_declares_simulation_training_positioning():
    assert EcmoWorkspace.POSITIONING_LABEL == "SIMULATION / TRAINING ONLY"
