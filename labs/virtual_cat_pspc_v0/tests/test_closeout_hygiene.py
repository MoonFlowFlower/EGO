from labs.virtual_cat_pspc_v0.run_experiments import run_experiments


def test_summary_separates_pspc_local_success_from_repo_wide_evidence_gap(tmp_path):
    summary = run_experiments(tmp_path, seeds=[101])

    assert summary["pspc_local_status"] == "E4_passed"
    assert summary["repo_wide_evidence_level"] == "E3"
    assert summary["repo_wide_evidence_remains"] == "E3"
    assert summary["mainline_connected"] is False
    assert summary["enabled"] is False

    verify_gap = summary["repo_wide_verify_gap"]
    assert verify_gap["command"] == "python scripts\\codex\\verify_repo.py --mode fast"
    assert verify_gap["status"] == "unavailable"
    assert verify_gap["reason"] == "legacy/root OpenEmotion WinError 267"
    assert verify_gap["counts_as_pspc_pass"] is False
    assert verify_gap["upgrades_repo_wide_pass"] is False
