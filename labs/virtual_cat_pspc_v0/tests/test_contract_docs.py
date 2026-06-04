from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_stage_card_freezes_lab_only_forbidden_runtime_boundary():
    text = (ROOT / "docs/codex/tasks/virtual-cat-pspc-v0/STAGE_CARD.md").read_text(encoding="utf-8")

    required = [
        "lane: `lab-only`",
        "runtime authority: `none`",
        "EgoOperator integration: `forbidden in v0`",
        "claim ceiling: `proto-self mechanism experiment only`",
        "mainline mutation: `forbidden`",
        "LLM action selection: `forbidden`",
    ]

    for marker in required:
        assert marker in text


def test_acceptance_preregisters_ablation_failures_and_non_claims():
    text = (ROOT / "docs/codex/tasks/virtual-cat-pspc-v0/ACCEPTANCE.md").read_text(encoding="utf-8")

    for marker in [
        "Different Histories",
        "Dangerous-Object Generalization",
        "Memory Deletion",
        "Frozen World Model",
        "Frozen Self Model",
        "No Prediction-Error Learning",
        "Replay Determinism",
        "This does not prove stable real user benefit",
    ]:
        assert marker in text


def test_admission_packet_contract_freezes_proposal_only_schema():
    text = (ROOT / "docs/codex/tasks/virtual-cat-pspc-v0/ADMISSION_PACKET_CONTRACT.md").read_text(encoding="utf-8")

    for marker in [
        '"source": "virtual_cat_pspc_v0"',
        '"claim_level": "lab_only_proto_self_mechanism_candidate"',
        '"mainline_connected": false',
        '"enabled": false',
        '"trace_refs": []',
        '"runtime_gate_bypass": true',
        "no EgoOperator runtime import",
        "no adapter created",
        "What This Proves",
        "What This Does Not Prove",
    ]:
        assert marker in text
