#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional


ROOT = Path(__file__).resolve().parents[2]
SOURCE_TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "mvs-h1-external-eval-corpus"
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "mvs-h1-external-raw-extraction-replay"
MANIFEST_JSON = SOURCE_TASK_DIR / "MVS_H1_EXTERNAL_EVAL_CORPUS_MANIFEST_CURRENT.json"
OUTPUT_ROOT = ROOT / "artifacts" / "external_eval_replay_v1"
CASES_ROOT = OUTPUT_ROOT / "cases"
HELDOUT_CASES_DIR = CASES_ROOT / "heldout_eval"
RESERVE_CASES_DIR = CASES_ROOT / "restricted_reserve"
REPORTS_DIR = OUTPUT_ROOT / "reports"

EXTRACTION_MAP_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_EXTRACTION_MAP_CURRENT.json"
EXTRACTION_MAP_MD = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_EXTRACTION_MAP_CURRENT.md"
BUCKET_REPORT_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_BUCKET_REPORT_CURRENT.json"
BUCKET_REPORT_MD = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_BUCKET_REPORT_CURRENT.md"
FAILURES_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_FAILURES_CURRENT.json"
FAILURES_MD = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_FAILURES_CURRENT.md"
DEDUPE_RECHECK_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_DEDUPE_RECHECK_CURRENT.json"
DEDUPE_RECHECK_MD = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_DEDUPE_RECHECK_CURRENT.md"
RESTRICTED_RESERVE_JSON = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_RESTRICTED_RESERVE_CURRENT.json"
RESTRICTED_RESERVE_MD = REPORTS_DIR / "MVS_H1_EXTERNAL_REPLAY_RESTRICTED_RESERVE_CURRENT.md"

TRIAL1_HARD_SET_JSON = (
    ROOT / "docs" / "codex" / "tasks" / "ai-self-awareness-minimal-framework" / "TRIAL1_COUNTERFACTUAL_HARD_SET.json"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_json(payload: Any) -> str:
    return _sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _normalize_overlap_text(text: str) -> str:
    lowered = str(text or "").strip().lower()
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9\u4e00-\u9fff ]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _fetch_json_url(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def _fetch_text_url(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8", "replace")


def _rows_url(*, dataset: str, config: str, split: str, offset: int, length: int) -> str:
    return (
        "https://datasets-server.huggingface.co/rows?"
        f"dataset={urllib.parse.quote(dataset, safe='')}"
        f"&config={urllib.parse.quote(config, safe='')}"
        f"&split={urllib.parse.quote(split, safe='')}"
        f"&offset={offset}&length={length}"
    )


def _iter_dataset_rows(*, dataset: str, config: str, split: str, batch_size: int = 100) -> Iterator[Dict[str, Any]]:
    offset = 0
    while True:
        payload = _fetch_json_url(_rows_url(dataset=dataset, config=config, split=split, offset=offset, length=batch_size))
        rows = list(payload.get("rows") or [])
        if not rows:
            return
        for row in rows:
            yield dict(row.get("row") or {})
        if len(rows) < batch_size:
            return
        offset += len(rows)


def _extract_last_user_turn(text: str) -> str:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("User:"):
            return line.split("User:", 1)[1].strip()
    return str(text or "").strip()


def _safe_json_loads(raw: Any) -> Any:
    if isinstance(raw, (dict, list)):
        return raw
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


def _trim(text: Any, limit: int = 1200) -> str:
    value = str(text or "")
    return value if len(value) <= limit else value[: limit - 3] + "..."


@dataclass
class CandidateRecord:
    source_dataset_id: str
    dataset_config: Optional[str]
    source_split: str
    access_method: str
    locator: Dict[str, Any]
    payload: Dict[str, Any]
    source_ref: str


def _conflictqa_candidates(limit: int) -> List[CandidateRecord]:
    url = "https://huggingface.co/datasets/osunlp/ConflictQA/resolve/main/conflictQA-popQA-chatgpt.json"
    text = _fetch_text_url(url)
    records: List[CandidateRecord] = []
    for idx, line in enumerate(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if not row.get("question") or not row.get("ground_truth"):
            continue
        records.append(
            CandidateRecord(
                source_dataset_id="osunlp/ConflictQA",
                dataset_config=None,
                source_split="dataset_defined_eval",
                access_method="hf_raw_file_jsonl",
                locator={"line_index": idx, "file": "conflictQA-popQA-chatgpt.json"},
                payload=row,
                source_ref=url,
            )
        )
        if len(records) >= limit:
            break
    return records


def _squad_unanswerable_candidates(limit: int) -> List[CandidateRecord]:
    records: List[CandidateRecord] = []
    for offset, row in enumerate(_iter_dataset_rows(dataset="rajpurkar/squad_v2", config="squad_v2", split="validation")):
        if (row.get("answers") or {}).get("text"):
            continue
        records.append(
            CandidateRecord(
                source_dataset_id="rajpurkar/squad_v2",
                dataset_config="squad_v2",
                source_split="validation",
                access_method="datasets_server_rows",
                locator={"row_offset": offset, "row_id": row.get("id")},
                payload=row,
                source_ref="https://datasets-server.huggingface.co/rows?dataset=rajpurkar%2Fsquad_v2&config=squad_v2&split=validation",
            )
        )
        if len(records) >= limit:
            break
    return records


def _ambigqa_candidates(limit: int) -> List[CandidateRecord]:
    records: List[CandidateRecord] = []
    for offset, row in enumerate(_iter_dataset_rows(dataset="sewon/ambig_qa", config="full", split="validation")):
        annotations = dict(row.get("annotations") or {})
        answers = list(annotations.get("answer") or [])
        qa_pairs = list(annotations.get("qaPairs") or [])
        ambiguous = len(answers) > 1 or any(len(list(item or [])) > 1 for item in answers)
        ambiguous = ambiguous or len(qa_pairs) > 1
        if not ambiguous:
            continue
        records.append(
            CandidateRecord(
                source_dataset_id="sewon/ambig_qa",
                dataset_config="full",
                source_split="validation",
                access_method="datasets_server_rows",
                locator={"row_offset": offset, "row_id": row.get("id")},
                payload=row,
                source_ref="https://datasets-server.huggingface.co/rows?dataset=sewon%2Fambig_qa&config=full&split=validation",
            )
        )
        if len(records) >= limit:
            break
    return records


def _memorybench_candidates(*, config: str, limit: int) -> List[CandidateRecord]:
    records: List[CandidateRecord] = []
    for offset, row in enumerate(_iter_dataset_rows(dataset="THUIR/MemoryBench", config=config, split="test")):
        if not row.get("input_prompt"):
            continue
        records.append(
            CandidateRecord(
                source_dataset_id="THUIR/MemoryBench",
                dataset_config=config,
                source_split="test",
                access_method="datasets_server_rows",
                locator={"row_offset": offset, "test_idx": row.get("test_idx")},
                payload=row,
                source_ref=(
                    "https://datasets-server.huggingface.co/rows?"
                    f"dataset=THUIR%2FMemoryBench&config={urllib.parse.quote(config, safe='')}&split=test"
                ),
            )
        )
        if len(records) >= limit:
            break
    return records


def _memorybench_multi_config_candidates(*, configs: Sequence[str], limit: int) -> List[CandidateRecord]:
    records: List[CandidateRecord] = []
    for config in configs:
        if len(records) >= limit:
            break
        records.extend(_memorybench_candidates(config=config, limit=max(limit - len(records), 0)))
    return records[:limit]


def _api_bank_candidates(limit: int) -> List[CandidateRecord]:
    url = "https://huggingface.co/datasets/liminghao1630/API-Bank/resolve/main/test-data/level-1-api.json"
    rows = list(_fetch_json_url(url))
    records: List[CandidateRecord] = []
    for idx, row in enumerate(rows):
        if not row.get("input") or not row.get("expected_output"):
            continue
        records.append(
            CandidateRecord(
                source_dataset_id="liminghao1630/API-Bank",
                dataset_config="default",
                source_split="test",
                access_method="hf_raw_file_json",
                locator={"row_index": idx, "file": "test-data/level-1-api.json", "record_id": row.get("id")},
                payload=row,
                source_ref=url,
            )
        )
        if len(records) >= limit:
            break
    return records


def _ifeval_candidates(limit: int) -> List[CandidateRecord]:
    records: List[CandidateRecord] = []
    for offset, row in enumerate(_iter_dataset_rows(dataset="google/IFEval", config="default", split="train")):
        if not row.get("prompt"):
            continue
        records.append(
            CandidateRecord(
                source_dataset_id="google/IFEval",
                dataset_config="default",
                source_split="train",
                access_method="datasets_server_rows",
                locator={"row_offset": offset, "row_key": row.get("key")},
                payload=row,
                source_ref="https://datasets-server.huggingface.co/rows?dataset=google%2FIFEval&config=default&split=train",
            )
        )
        if len(records) >= limit:
            break
    return records


def _build_conflictqa_case(manifest_row: Dict[str, Any], candidate: CandidateRecord) -> Dict[str, Any]:
    row = candidate.payload
    evidence = str(row.get("counter_memory_aligned_evidence") or row.get("counter_memory") or "")
    return {
        "case_type": "correction_then_retry",
        "initial_prompt": str(row.get("question") or ""),
        "supporting_material": {
            "conflicting_memory_answer": str(row.get("memory_answer") or ""),
            "evidence_for_revision": _trim(evidence, 1800),
        },
        "reference_bundle": {
            "gold_answer_candidates": list(row.get("ground_truth") or []),
            "counter_answer": str(row.get("counter_answer") or ""),
            "memory_answer": str(row.get("memory_answer") or ""),
        },
        "replay_recipe": {
            "family": "correction_then_retry",
            "feedback_turn": (
                "The previous answer conflicts with the following evidence. "
                f"Revise using this evidence only: { _trim(evidence, 700) }"
            ),
            "followup_turn": "Answer the same question again in a short phrase.",
        },
    }


def _build_squad_case(manifest_row: Dict[str, Any], candidate: CandidateRecord) -> Dict[str, Any]:
    row = candidate.payload
    return {
        "case_type": "qa_with_context_unanswerable",
        "initial_prompt": str(row.get("question") or ""),
        "supporting_material": {"context": str(row.get("context") or "")},
        "reference_bundle": {"answerable": False, "gold_answer_candidates": []},
        "replay_recipe": {
            "family": "uncertainty_gate",
            "followup_turn": None,
            "clarification_expected": True,
        },
    }


def _build_ambigqa_case(manifest_row: Dict[str, Any], candidate: CandidateRecord) -> Dict[str, Any]:
    row = candidate.payload
    annotations = dict(row.get("annotations") or {})
    answer_groups = list(annotations.get("answer") or [])
    flattened_answers: List[str] = []
    for group in answer_groups:
        flattened_answers.extend(str(item) for item in list(group or []))
    return {
        "case_type": "ambiguous_qa",
        "initial_prompt": str(row.get("question") or ""),
        "supporting_material": {
            "viewed_doc_titles": list(row.get("viewed_doc_titles") or []),
            "nq_doc_title": str(row.get("nq_doc_title") or ""),
        },
        "reference_bundle": {
            "ambiguous_answer_candidates": flattened_answers,
            "clarification_expected": True,
        },
        "replay_recipe": {
            "family": "ambiguity_clarification",
            "followup_turn": "Clarify which interpretation you mean before giving a final answer.",
        },
    }


def _build_memorybench_failure_case(manifest_row: Dict[str, Any], candidate: CandidateRecord) -> Dict[str, Any]:
    row = candidate.payload
    info = _safe_json_loads(row.get("info"))
    golden = info.get("golden_answer")
    return {
        "case_type": "memory_feedback_retry",
        "initial_prompt": str(row.get("input_prompt") or ""),
        "supporting_material": {
            "dataset_name": str(row.get("dataset_name") or ""),
            "origin_question": str(row.get("origin_question") or ""),
            "dialog_context": str(row.get("dialog_bm25_dialog") or ""),
        },
        "reference_bundle": {"gold_answer": golden, "info": info},
        "replay_recipe": {
            "family": "failure_revision_later_change",
            "feedback_turn": f"That answer was incorrect. The correct answer is: {golden}. Keep that correction.",
            "followup_turn": str(row.get("origin_question") or "Answer the same question again in a short phrase."),
        },
    }


def _build_memorybench_continuity_case(manifest_row: Dict[str, Any], candidate: CandidateRecord) -> Dict[str, Any]:
    row = candidate.payload
    info = _safe_json_loads(row.get("info"))
    golden = info.get("golden_answer")
    return {
        "case_type": "memory_continuity",
        "initial_prompt": str(row.get("input_prompt") or ""),
        "supporting_material": {
            "dataset_name": str(row.get("dataset_name") or ""),
            "origin_question": str(row.get("origin_question") or ""),
            "dialog_context": str(row.get("dialog_bm25_dialog") or ""),
        },
        "reference_bundle": {"gold_answer": golden, "info": info},
        "replay_recipe": {
            "family": "low_cue_continuation",
            "followup_turn": "Continue with the same answer target and no new facts. Give the same short answer target again.",
        },
    }


def _build_api_bank_case(manifest_row: Dict[str, Any], candidate: CandidateRecord) -> Dict[str, Any]:
    row = candidate.payload
    return {
        "case_type": "tool_api_request_generation",
        "initial_prompt": _extract_last_user_turn(str(row.get("input") or "")),
        "supporting_material": {
            "instruction": str(row.get("instruction") or ""),
            "full_input": str(row.get("input") or ""),
        },
        "reference_bundle": {"expected_output": str(row.get("expected_output") or "")},
        "replay_recipe": {
            "family": "tool_risk_ambiguity",
            "followup_turn": "If required parameters are missing or multiple tools fit, ask before committing to a direct API request.",
        },
    }


def _build_ifeval_case(manifest_row: Dict[str, Any], candidate: CandidateRecord) -> Dict[str, Any]:
    row = candidate.payload
    return {
        "case_type": "instruction_following_constraints",
        "initial_prompt": str(row.get("prompt") or ""),
        "supporting_material": {
            "instruction_id_list": list(row.get("instruction_id_list") or []),
            "kwargs": list(row.get("kwargs") or []),
        },
        "reference_bundle": {
            "instruction_ids": list(row.get("instruction_id_list") or []),
        },
        "replay_recipe": {
            "family": "adversarial_constraints",
            "followup_turn": None,
        },
    }


def _case_builder_for_row(manifest_row: Dict[str, Any]):
    bucket = str(manifest_row.get("bucket") or "")
    dataset_id = str(manifest_row.get("source_dataset_id") or "")
    if bucket == "correction":
        return _build_conflictqa_case
    if bucket == "ask_vs_answer_uncertainty" and dataset_id == "rajpurkar/squad_v2":
        return _build_squad_case
    if bucket == "ask_vs_answer_uncertainty" and dataset_id == "sewon/ambig_qa":
        return _build_ambigqa_case
    if bucket == "failure_revision_later_change":
        return _build_memorybench_failure_case
    if bucket == "continuity":
        return _build_memorybench_continuity_case
    if bucket == "tool_risk_ambiguity":
        return _build_api_bank_case
    if bucket == "adversarial_constraints":
        return _build_ifeval_case
    raise ValueError(f"unsupported manifest row mapping: bucket={bucket} dataset_id={dataset_id}")


def _candidate_pool_key(manifest_row: Dict[str, Any]) -> tuple[str, str]:
    bucket = str(manifest_row.get("bucket") or "")
    dataset_id = str(manifest_row.get("source_dataset_id") or "")
    if bucket == "failure_revision_later_change":
        return (bucket, "THUIR/MemoryBench:DialSim-bigbang")
    if bucket == "continuity":
        return (bucket, "THUIR/MemoryBench:continuity_multiconfig")
    return (bucket, dataset_id)


def _build_candidate_pools() -> Dict[tuple[str, str], List[CandidateRecord]]:
    return {
        ("correction", "osunlp/ConflictQA"): _conflictqa_candidates(limit=10),
        ("ask_vs_answer_uncertainty", "rajpurkar/squad_v2"): _squad_unanswerable_candidates(limit=5),
        ("ask_vs_answer_uncertainty", "sewon/ambig_qa"): _ambigqa_candidates(limit=5),
        ("failure_revision_later_change", "THUIR/MemoryBench:DialSim-bigbang"): _memorybench_candidates(
            config="DialSim-bigbang", limit=10
        ),
        ("continuity", "THUIR/MemoryBench:continuity_multiconfig"): _memorybench_multi_config_candidates(
            configs=("Locomo-0", "Locomo-1", "Locomo-2", "Locomo-3"),
            limit=10,
        ),
        ("tool_risk_ambiguity", "liminghao1630/API-Bank"): _api_bank_candidates(limit=10),
        ("adversarial_constraints", "google/IFEval"): _ifeval_candidates(limit=10),
    }


def _render_map_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# MVS H1 External Replay Extraction Map",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- heldout_success_count: `{payload['summary']['heldout_success_count']}`",
        f"- heldout_failure_count: `{payload['summary']['heldout_failure_count']}`",
        f"- restricted_reserve_count: `{payload['summary']['restricted_reserve_count']}`",
        "",
        "## Heldout Cases",
    ]
    for row in payload.get("heldout_rows") or []:
        lines.append(
            f"- `{row['sample_id']}` | bucket=`{row['bucket']}` | status=`{row['status']}` | "
            f"source=`{row['source_dataset_id']}` | case_file=`{row.get('case_file') or 'n/a'}`"
        )
    lines.append("")
    lines.append("## Restricted Reserve")
    for row in payload.get("restricted_reserve_rows") or []:
        lines.append(
            f"- `{row['sample_id']}` | bucket=`{row['bucket']}` | status=`{row['status']}` | source=`{row['source_dataset_id']}`"
        )
    return "\n".join(lines) + "\n"


def _render_bucket_report_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# MVS H1 External Replay Bucket Report",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        "",
        "| bucket | selected | extracted | failures | sources |",
        "|---|---:|---:|---:|---|",
    ]
    for bucket in payload.get("buckets") or []:
        lines.append(
            f"| `{bucket['bucket']}` | `{bucket['selected_count']}` | `{bucket['success_count']}` | "
            f"`{bucket['failure_count']}` | `{', '.join(bucket['sources'])}` |"
        )
    return "\n".join(lines) + "\n"


def _render_failures_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# MVS H1 External Replay Extraction Failures",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- failure_count: `{payload['failure_count']}`",
    ]
    for item in payload.get("failures") or []:
        lines.append(
            f"- `{item['sample_id']}` | bucket=`{item['bucket']}` | classification=`{item['classification']}` | detail=`{item['detail']}`"
        )
    return "\n".join(lines) + "\n"


def _render_dedupe_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# MVS H1 External Replay Dedupe Re-check",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- duplicate_initial_prompt_digests: `{len(payload['duplicate_initial_prompt_digests'])}`",
        f"- overlap_hits_with_trial1_hard_set: `{len(payload['trial1_hard_set_overlap_hits'])}`",
        f"- reserve_mixed_into_heldout: `{payload['reserve_mixed_into_heldout']}`",
    ]
    return "\n".join(lines) + "\n"


def _render_restricted_reserve_markdown(payload: Dict[str, Any]) -> str:
    lines = [
        "# MVS H1 External Replay Restricted Reserve",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- reserve_count: `{len(payload.get('rows') or [])}`",
    ]
    for row in payload.get("rows") or []:
        lines.append(
            f"- `{row['sample_id']}` | source=`{row['source_dataset_id']}` | license=`{row['license']}` | status=`{row['status']}`"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    manifest = _load_json(MANIFEST_JSON)
    rows = list(manifest.get("rows") or [])
    heldout_rows = [dict(row) for row in rows if row.get("local_partition") == "heldout_eval"]
    reserve_rows = [dict(row) for row in rows if row.get("local_partition") == "restricted_reserve"]

    HELDOUT_CASES_DIR.mkdir(parents=True, exist_ok=True)
    RESERVE_CASES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    pools = _build_candidate_pools()
    pool_positions: Dict[tuple[str, str], int] = defaultdict(int)
    extraction_rows: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    for manifest_row in heldout_rows:
        sample_id = str(manifest_row["sample_id"])
        bucket = str(manifest_row["bucket"])
        pool_key = _candidate_pool_key(manifest_row)
        pool = pools.get(pool_key) or []
        pos = pool_positions[pool_key]
        if pos >= len(pool):
            failure = {
                "sample_id": sample_id,
                "bucket": bucket,
                "source_dataset_id": manifest_row["source_dataset_id"],
                "classification": "candidate_pool_exhausted",
                "detail": f"pool_key={pool_key!r} available={len(pool)} requested_index={pos}",
            }
            failures.append(failure)
            extraction_rows.append(
                {
                    "sample_id": sample_id,
                    "bucket": bucket,
                    "source_dataset_id": manifest_row["source_dataset_id"],
                    "status": "failed",
                    "failure": failure,
                }
            )
            continue

        candidate = pool[pos]
        pool_positions[pool_key] += 1
        builder = _case_builder_for_row(manifest_row)
        try:
            normalized_case = builder(manifest_row, candidate)
            case_payload = {
                "schema_version": "mvs_h1.external_replay_case.v1",
                "sample_id": sample_id,
                "bucket": bucket,
                "local_partition": manifest_row["local_partition"],
                "runner_contract": dict(manifest_row.get("runner_contract") or manifest.get("runner_contract") or {}),
                "source": {
                    "source_dataset_id": manifest_row["source_dataset_id"],
                    "source_url": manifest_row["source_url"],
                    "dataset_card_url": manifest_row["dataset_card_url"],
                    "license": manifest_row["license"],
                    "license_class": manifest_row["license_class"],
                    "source_split": manifest_row["source_split"],
                    "selection_hint": manifest_row["selection_hint"],
                    "target_mechanism": manifest_row["target_mechanism"],
                    "expected_observable": manifest_row["expected_observable"],
                },
                "provenance": {
                    "access_method": candidate.access_method,
                    "dataset_config": candidate.dataset_config,
                    "source_ref": candidate.source_ref,
                    "locator": candidate.locator,
                    "source_record_digest": _sha256_json(candidate.payload),
                    "extracted_at": _utc_now(),
                    "selection_resolution": {
                        "method": "deterministic_bucket_filtered_stream",
                        "selection_status": "resolved_from_frozen_manifest_order",
                        "selection_hint_preserved": True,
                    },
                },
                "raw_source_record": candidate.payload,
                "normalized_case": normalized_case,
            }
            case_path = HELDOUT_CASES_DIR / f"{sample_id}.json"
            _write_json(case_path, case_payload)
            extraction_rows.append(
                {
                    "sample_id": sample_id,
                    "bucket": bucket,
                    "source_dataset_id": manifest_row["source_dataset_id"],
                    "status": "extracted",
                    "case_file": str(case_path.relative_to(ROOT)),
                    "access_method": candidate.access_method,
                    "dataset_config": candidate.dataset_config,
                    "locator": candidate.locator,
                    "source_record_digest": case_payload["provenance"]["source_record_digest"],
                }
            )
        except Exception as exc:  # pragma: no cover - explicit failure accounting
            failure = {
                "sample_id": sample_id,
                "bucket": bucket,
                "source_dataset_id": manifest_row["source_dataset_id"],
                "classification": "normalization_error",
                "detail": str(exc),
            }
            failures.append(failure)
            extraction_rows.append(
                {
                    "sample_id": sample_id,
                    "bucket": bucket,
                    "source_dataset_id": manifest_row["source_dataset_id"],
                    "status": "failed",
                    "failure": failure,
                }
            )

    reserve_payload = {
        "schema_version": "mvs_h1.external_restricted_reserve.v1",
        "generated_at": _utc_now(),
        "rows": [
            {
                **row,
                "status": "reserved_not_extracted",
                "reason": "restricted_reserve kept separate from default heldout extraction",
            }
            for row in reserve_rows
        ],
    }
    _write_json(RESTRICTED_RESERVE_JSON, reserve_payload)
    _write_text(RESTRICTED_RESERVE_MD, _render_restricted_reserve_markdown(reserve_payload))

    success_rows = [row for row in extraction_rows if row.get("status") == "extracted"]
    bucket_counter = Counter(row["bucket"] for row in heldout_rows)
    success_counter = Counter(row["bucket"] for row in success_rows)
    failure_counter = Counter(row["bucket"] for row in failures)
    bucket_report = {
        "schema_version": "mvs_h1.external_replay_bucket_report.v1",
        "generated_at": _utc_now(),
        "buckets": [
            {
                "bucket": bucket,
                "selected_count": bucket_counter.get(bucket, 0),
                "success_count": success_counter.get(bucket, 0),
                "failure_count": failure_counter.get(bucket, 0),
                "sources": sorted({str(row["source_dataset_id"]) for row in heldout_rows if row["bucket"] == bucket}),
            }
            for bucket in manifest.get("buckets") or []
        ],
    }
    _write_json(BUCKET_REPORT_JSON, bucket_report)
    _write_text(BUCKET_REPORT_MD, _render_bucket_report_markdown(bucket_report))

    failures_payload = {
        "schema_version": "mvs_h1.external_replay_failures.v1",
        "generated_at": _utc_now(),
        "failure_count": len(failures),
        "failures": failures,
    }
    _write_json(FAILURES_JSON, failures_payload)
    _write_text(FAILURES_MD, _render_failures_markdown(failures_payload))

    extraction_map = {
        "schema_version": "mvs_h1.external_replay_extraction_map.v1",
        "generated_at": _utc_now(),
        "summary": {
            "heldout_selected_count": len(heldout_rows),
            "heldout_success_count": len(success_rows),
            "heldout_failure_count": len(failures),
            "restricted_reserve_count": len(reserve_rows),
        },
        "heldout_rows": extraction_rows,
        "restricted_reserve_rows": reserve_payload["rows"],
    }
    _write_json(EXTRACTION_MAP_JSON, extraction_map)
    _write_text(EXTRACTION_MAP_MD, _render_map_markdown(extraction_map))

    hard_set = _load_json(TRIAL1_HARD_SET_JSON)
    hard_set_terms = {
        _normalize_overlap_text(step.get("user_input", ""))
        for case in hard_set.get("cases") or []
        for step in case.get("steps") or []
        if step.get("user_input")
    }
    prompt_digest_map: Dict[str, List[str]] = defaultdict(list)
    overlap_hits: List[Dict[str, Any]] = []
    for row in success_rows:
        case_path = ROOT / row["case_file"]
        case_payload = _load_json(case_path)
        initial_prompt = _normalize_overlap_text(case_payload["normalized_case"].get("initial_prompt", ""))
        digest = _sha256_text(initial_prompt)
        prompt_digest_map[digest].append(case_payload["sample_id"])
        if initial_prompt in hard_set_terms:
            overlap_hits.append({"sample_id": case_payload["sample_id"], "matched_text": initial_prompt})

    duplicate_digests = [
        {"digest": digest, "sample_ids": sample_ids}
        for digest, sample_ids in sorted(prompt_digest_map.items())
        if len(sample_ids) > 1
    ]
    dedupe_payload = {
        "schema_version": "mvs_h1.external_replay_dedupe_recheck.v1",
        "generated_at": _utc_now(),
        "duplicate_initial_prompt_digests": duplicate_digests,
        "trial1_hard_set_overlap_hits": overlap_hits,
        "reserve_mixed_into_heldout": any(
            row.get("selection_status") == "resolved_from_frozen_manifest_order"
            for row in reserve_payload["rows"]
        ),
    }
    _write_json(DEDUPE_RECHECK_JSON, dedupe_payload)
    _write_text(DEDUPE_RECHECK_MD, _render_dedupe_markdown(dedupe_payload))

    print(f"heldout_selected_count={len(heldout_rows)}")
    print(f"heldout_success_count={len(success_rows)}")
    print(f"heldout_failure_count={len(failures)}")
    print(f"restricted_reserve_count={len(reserve_rows)}")
    print(f"extraction_map_json={EXTRACTION_MAP_JSON.relative_to(ROOT)}")
    print(f"bucket_report_json={BUCKET_REPORT_JSON.relative_to(ROOT)}")
    print(f"failures_json={FAILURES_JSON.relative_to(ROOT)}")
    print(f"dedupe_recheck_json={DEDUPE_RECHECK_JSON.relative_to(ROOT)}")
    print(f"restricted_reserve_json={RESTRICTED_RESERVE_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
