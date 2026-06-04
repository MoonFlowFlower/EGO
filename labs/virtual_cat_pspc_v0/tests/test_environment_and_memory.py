from labs.virtual_cat_pspc_v0.environment import Action, GridObject, ObjectFeatures, VirtualCatGridWorld
from labs.virtual_cat_pspc_v0.memory import EpisodicMemory


def test_gridworld_feedback_uses_object_features_not_names():
    env = VirtualCatGridWorld(seed=7)
    red_cup = GridObject(
        object_id="red_cup_seen",
        name="red cup",
        position=(2, 1),
        features=ObjectFeatures(instability=0.9, height=0.9, fragility=0.8, novelty=0.2),
    )
    blue_bottle = GridObject(
        object_id="blue_bottle_unseen",
        name="blue bottle",
        position=(3, 1),
        features=ObjectFeatures(instability=0.9, height=0.9, fragility=0.8, novelty=0.7),
    )

    red_result = env.simulate_action(red_cup, Action.APPROACH)
    blue_result = env.simulate_action(blue_bottle, Action.APPROACH)

    assert red_result.actual["danger_contact"] is True
    assert blue_result.actual["danger_contact"] is True
    assert red_result.actual["noise"] is True
    assert blue_result.actual["noise"] is True


def test_memory_deletion_removes_feature_relevant_episodes():
    memory = EpisodicMemory()
    memory.add_transition(
        episode_id="ep_001",
        seed=101,
        object_id="red_cup_seen",
        action="approach",
        object_features={"instability": 0.9, "height": 0.9, "fragility": 0.8, "novelty": 0.2},
        prediction={"danger_contact": 0.1},
        actual={"danger_contact": True, "noise": True},
        self_delta={"stress_delta": 0.6},
        prediction_error=0.8,
        model_update_ref="train_step_001",
    )
    memory.add_transition(
        episode_id="ep_002",
        seed=101,
        object_id="stable_ball",
        action="approach",
        object_features={"instability": 0.1, "height": 0.2, "fragility": 0.1, "novelty": 0.5},
        prediction={"danger_contact": 0.1},
        actual={"danger_contact": False, "noise": False},
        self_delta={"stress_delta": 0.0},
        prediction_error=0.05,
        model_update_ref="train_step_002",
    )

    removed = memory.delete_relevant("unstable_tall_object")

    assert removed == 1
    remaining_ids = {transition.object_id for transition in memory.transitions}
    assert remaining_ids == {"stable_ball"}
