from tools.verify_mvp15_mainline_wiring import inspect_wiring


def test_mvp15_static_verifier_reports_shadow_only_mainline_gap():
    report = inspect_wiring()

    assert report["formal_owner"]["reflection_engine_present"] is True
    assert report["formal_owner"]["counterfactual_module_present"] is True

    assert report["core"]["uses_reflection_shadow"] is True
    assert report["core"]["uses_reflection_engine_directly"] is False
    assert report["core"]["uses_counterfactual_consumer"] is False

    assert report["api"]["uses_reflection_engine_directly"] is False
    assert report["api"]["uses_counterfactual_consumer"] is False

    assert report["workspace"]["uses_reflection_engine_directly"] is False
    assert report["workspace"]["uses_counterfactual_consumer"] is False

    assert report["mainline"]["writeback_consumer_present"] is False
    assert report["status"] == "shadow_only_mainline_writeback_missing"
