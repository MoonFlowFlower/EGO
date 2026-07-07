from __future__ import annotations

import pytest

from scripts.joi_corpus.corpus_path import CorpusUnavailable, assert_frozen, snapshot
from scripts.joi_corpus.manifest_verifier import verify_manifests
from scripts.joi_corpus.reader import read_artifact_tree
from scripts.joi_corpus.schema_catalog import build_shape_catalog, extract_canonical_fields, load_result


REQUIRED_DIRS = {
    "JOI-DEMO-S2-LOADBEARING-SELFMODEL-001A",
    "JOI-DEMO-S2-LOADBEARING-SELFMODEL-002A",
    "JOI-DEMO-LP-AUTOTELIC-COMPETENCE-001A",
    "JOI-DEMO-LP-AUTOTELIC-COMPETENCE-002A",
    "JOI-DEMO-G4-USER-MODEL-001B",
    "JOI-DEMO-G4G0-COUPLING-SPIKE-001A",
    "JOI-DEMO-OPERATION-LEARNING-GATE-001A",
    "JOI-DEMO-CAPACITY-SCALABLE-LEARNER-001C",
    "JOI-DEMO-CURIOSITY-OPEN-ENDED-GROWTH-001A",
    "JOI-DEMO-GENERALITY-EXTENSIBILITY-001A",
}


@pytest.fixture(scope="session")
def corpus_readback():
    try:
        before = assert_frozen()
    except CorpusUnavailable as exc:
        pytest.skip(f"frozen corpus not present: {exc}")
    reader = read_artifact_tree()
    verifier = verify_manifests()
    catalog = build_shape_catalog()
    after = snapshot()
    return {"before": before, "reader": reader, "verifier": verifier, "catalog": catalog, "after": after}


def _canonical(artifact_dir: str) -> dict:
    return extract_canonical_fields(load_result(None, artifact_dir))


def _contains_value(value, needle: str) -> bool:
    if isinstance(value, str):
        return needle in value
    if isinstance(value, dict):
        return any(_contains_value(v, needle) for v in value.values())
    if isinstance(value, list):
        return any(_contains_value(v, needle) for v in value)
    return False


def test_reader_parses_required_frozen_dirs(corpus_readback):
    reader = corpus_readback["reader"]
    assert reader["critical_parse_error_count"] == 0
    parsed_dirs = {entry["artifact_dir"] for entry in reader["entries"]}
    assert REQUIRED_DIRS <= parsed_dirs
    required_entries = [entry for entry in reader["entries"] if entry["artifact_dir"] in REQUIRED_DIRS]
    assert sum(entry["parse_error_count"] for entry in required_entries) == 0
    jsonl_entries = [entry for entry in reader["entries"] if entry["kind"] == "jsonl"]
    assert jsonl_entries
    assert all(entry["jsonl_line_count"] > 0 for entry in jsonl_entries)


def test_manifest_verifier_includes_creaturestate_v0_2_named_pins(corpus_readback):
    verifier = corpus_readback["verifier"]
    assert verifier["manifest_count"] >= 1
    assert verifier["pin_count"] >= 1
    assert verifier["named_checks"]["creaturestate_v0_2_card"]["verdict"] == "match"
    assert verifier["named_checks"]["creaturestate_v0_2_schema"]["verdict"] == "match"


def test_schema_catalog_maps_observed_core_fields(corpus_readback):
    catalog = corpus_readback["catalog"]
    assert catalog["result_count"] >= len(REQUIRED_DIRS)
    assert catalog["canonical_field_coverage"]["verdict"] == catalog["result_count"]
    assert catalog["canonical_field_coverage"]["claim_ceiling"] == catalog["result_count"]


def test_golden_values_from_frozen_reference_index():
    g4b = _canonical("JOI-DEMO-G4-USER-MODEL-001B")
    assert g4b["verdict"]["value"] == "g4b_bar1_pass"
    assert g4b["run_id"]["value"] == "4c7af0d391d9"

    g4g0 = _canonical("JOI-DEMO-G4G0-COUPLING-SPIKE-001A")
    assert g4g0["verdict"]["value"] == "coupling_bar1_pass_same_access_saturated"
    assert g4g0["candidate_brier"]["value"] == pytest.approx(0.1071578320428436)

    op = _canonical("JOI-DEMO-OPERATION-LEARNING-GATE-001A")
    assert "same_access_saturated_bar1_only" in op["verdict"]["value"]

    s2 = _canonical("JOI-DEMO-S2-LOADBEARING-SELFMODEL-002A")
    assert s2["verdict"]["value"] == "s2_self_model_not_load_bearing"

    for lp_dir in (
        "JOI-DEMO-LP-AUTOTELIC-COMPETENCE-001A",
        "JOI-DEMO-LP-AUTOTELIC-COMPETENCE-002A",
    ):
        assert "LP_DEGENERATE" in _canonical(lp_dir)["verdict"]["value"]

    cap = _canonical("JOI-DEMO-CAPACITY-SCALABLE-LEARNER-001C")
    assert cap["verdict"]["value"] == "capacity_is_binding_constraint"

    growth = load_result(None, "JOI-DEMO-CURIOSITY-OPEN-ENDED-GROWTH-001A")
    assert _contains_value(growth, "curiosity_harmful")

    gen = _canonical("JOI-DEMO-GENERALITY-EXTENSIBILITY-001A")
    assert gen["verdict"]["value"] == "generality_present_separable"


def test_corpus_snapshot_is_not_mutated_by_readback(corpus_readback):
    before = corpus_readback["before"]
    after = corpus_readback["after"]
    assert before["tag_commit"] == after["tag_commit"]
    assert before["status_sha256"] == after["status_sha256"]
    assert before["status_porcelain"] == after["status_porcelain"]
