from tools.summarize_experiment_matrix import _both_reached_target


def test_both_reached_target_true_when_both_true():
    assert _both_reached_target({"baseline_target_reached": True, "dedup_target_reached": True}) is True


def test_both_reached_target_false_when_any_false():
    assert _both_reached_target({"baseline_target_reached": True, "dedup_target_reached": False}) is False
    assert _both_reached_target({"baseline_target_reached": False, "dedup_target_reached": True}) is False
