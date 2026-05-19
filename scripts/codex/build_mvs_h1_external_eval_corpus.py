#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "mvs-h1-external-eval-corpus"

SOURCE_SHORTLIST_JSON = TASK_DIR / "MVS_H1_EXTERNAL_EVAL_SOURCE_SHORTLIST_CURRENT.json"
SOURCE_SHORTLIST_MD = TASK_DIR / "MVS_H1_EXTERNAL_EVAL_SOURCE_SHORTLIST_CURRENT.md"
MANIFEST_JSON = TASK_DIR / "MVS_H1_EXTERNAL_EVAL_CORPUS_MANIFEST_CURRENT.json"
LICENSE_MATRIX_MD = TASK_DIR / "MVS_H1_EXTERNAL_EVAL_LICENSE_MATRIX_CURRENT.md"
DEDUPE_REPORT_MD = TASK_DIR / "MVS_H1_EXTERNAL_EVAL_DEDUPE_REPORT_CURRENT.md"

BUCKETS = [
    "correction",
    "ask_vs_answer_uncertainty",
    "failure_revision_later_change",
    "tool_risk_ambiguity",
    "continuity",
    "adversarial_constraints",
]

RUNNER_CONTRACT = {
    "baseline_id": "trial1_baseline_proto_self_mainline",
    "candidate_id": "trial1_candidate_mvs_aligned_compact",
    "ablation_ids": [
        "trial1_ablation_counterfactual_public_path_sever",
        "trial1_ablation_alternative_explanation_isolation",
    ],
    "challenger_id": "trial1_challenger_active_inference_self_model",
}


@dataclass(frozen=True)
class SourceDef:
    dataset_id: str
    dataset_card_url: str
    source_url: str
    license: str
    license_class: str
    preferred_eval_split: str
    split_note: str
    selection_status: str
    reserve_reason: str
    supported_buckets: List[str]


SOURCES: List[SourceDef] = [
    SourceDef(
        dataset_id="rajpurkar/squad_v2",
        dataset_card_url="https://huggingface.co/datasets/rajpurkar/squad_v2",
        source_url="https://huggingface.co/datasets/rajpurkar/squad_v2",
        license="cc-by-sa-4.0",
        license_class="sharealike_open",
        preferred_eval_split="validation",
        split_note="dataset card exposes train + validation; use validation only for held-out ambiguity/unanswerability rows.",
        selection_status="main_shortlist",
        reserve_reason="",
        supported_buckets=["ask_vs_answer_uncertainty"],
    ),
    SourceDef(
        dataset_id="sewon/ambig_qa",
        dataset_card_url="https://huggingface.co/datasets/sewon/ambig_qa",
        source_url="https://huggingface.co/datasets/sewon/ambig_qa",
        license="cc-by-sa-3.0",
        license_class="sharealike_open",
        preferred_eval_split="validation",
        split_note="dataset card exposes train + validation; use validation only for ambiguity-focused held-out rows.",
        selection_status="main_shortlist",
        reserve_reason="",
        supported_buckets=["ask_vs_answer_uncertainty"],
    ),
    SourceDef(
        dataset_id="osunlp/ConflictQA",
        dataset_card_url="https://huggingface.co/datasets/osunlp/ConflictQA",
        source_url="https://huggingface.co/datasets/osunlp/ConflictQA",
        license="apache-2.0",
        license_class="permissive_open",
        preferred_eval_split="dataset_defined_eval",
        split_note="viewer is disabled; use the dataset-defined evaluation configuration rather than inventing a local split.",
        selection_status="main_shortlist",
        reserve_reason="",
        supported_buckets=["correction"],
    ),
    SourceDef(
        dataset_id="THUIR/MemoryBench",
        dataset_card_url="https://huggingface.co/datasets/THUIR/MemoryBench",
        source_url="https://huggingface.co/datasets/THUIR/MemoryBench",
        license="mit",
        license_class="permissive_open",
        preferred_eval_split="test",
        split_note="dataset card states explicit training/testing sets; use test only for held-out continuity and revision rows.",
        selection_status="main_shortlist",
        reserve_reason="",
        supported_buckets=["failure_revision_later_change", "continuity"],
    ),
    SourceDef(
        dataset_id="liminghao1630/API-Bank",
        dataset_card_url="https://huggingface.co/datasets/liminghao1630/API-Bank",
        source_url="https://huggingface.co/datasets/liminghao1630/API-Bank",
        license="mit",
        license_class="permissive_open",
        preferred_eval_split="test",
        split_note="dataset card exposes train + test and preview references test-data/level-1-api.json; use test only.",
        selection_status="main_shortlist",
        reserve_reason="",
        supported_buckets=["tool_risk_ambiguity"],
    ),
    SourceDef(
        dataset_id="google/IFEval",
        dataset_card_url="https://huggingface.co/datasets/google/IFEval",
        source_url="https://huggingface.co/datasets/google/IFEval",
        license="apache-2.0",
        license_class="permissive_open",
        preferred_eval_split="train",
        split_note="dataset card exposes train only; reserve that source split exclusively for held-out eval in this repo.",
        selection_status="main_shortlist",
        reserve_reason="",
        supported_buckets=["adversarial_constraints"],
    ),
    SourceDef(
        dataset_id="LibrAI/do-not-answer",
        dataset_card_url="https://huggingface.co/datasets/LibrAI/do-not-answer",
        source_url="https://huggingface.co/datasets/LibrAI/do-not-answer",
        license="apache-2.0",
        license_class="permissive_open",
        preferred_eval_split="train",
        split_note="train-only source; excluded from default mainline because current ontology prefers safer public-behavior buckets over refusal-only datasets.",
        selection_status="restricted_reserve",
        reserve_reason="reserve-only for future safety-adjacent studies; not a first-choice fit for current MVS/H1 public-driver ontology.",
        supported_buckets=["adversarial_constraints"],
    ),
    SourceDef(
        dataset_id="sorry-bench/sorry-bench-202503",
        dataset_card_url="https://huggingface.co/datasets/sorry-bench/sorry-bench-202503",
        source_url="https://huggingface.co/datasets/sorry-bench/sorry-bench-202503",
        license="custom-dataset-license-agreement",
        license_class="custom_restricted",
        preferred_eval_split="dataset_defined",
        split_note="custom dataset agreement; record only as restricted reserve.",
        selection_status="restricted_reserve",
        reserve_reason="custom license agreement; exclude from default held-out manifest.",
        supported_buckets=["adversarial_constraints"],
    ),
]

SOURCE_BY_ID = {source.dataset_id: source for source in SOURCES}

BUCKET_SPECS: Dict[str, Dict[str, object]] = {
    "correction": {
        "target_mechanism": "structured corrective trace after contradiction",
        "expected_observable": "corrective_trace_presence and a later correction-oriented public shift on a related follow-up",
        "source_dataset_id": "osunlp/ConflictQA",
        "source_split": "dataset_defined_eval",
        "selection_hints": [
            "pick a conflict pair where parametric_memory and counter_memory disagree on entity identity and evidence favors the counter answer",
            "pick a conflict pair where memory_answer conflicts with retrieved evidence on occupation or role",
            "pick a conflict pair where date or year disagreement forces evidence-backed correction",
            "pick a conflict pair where location disagreement should trigger explicit revision rather than confident reuse",
            "pick a conflict pair where numeric disagreement should force acknowledgement of prior error",
            "pick a conflict pair where popularity is high but the evidence-backed answer contradicts the default memory answer",
            "pick a conflict pair with short question wording so correction must be driven by evidence not verbosity",
            "pick a conflict pair where counter evidence is strongly named and easy to replay in a follow-up turn",
            "pick a conflict pair where the correction target is a single factual slot and later replay can test whether the slot changed",
            "pick a conflict pair where memory-aligned evidence looks superficially plausible but the gold answer follows counter evidence",
        ],
    },
    "ask_vs_answer_uncertainty": {
        "target_mechanism": "low-success guard and abstain-or-ask behavior under uncertainty",
        "expected_observable": "host-consumable ask/clarify tendency or bounded no-answer when answerability is weak or ambiguity remains unresolved",
        "source_rows": [
            ("rajpurkar/squad_v2", "validation", "select an unanswerable validation item where answers.text is empty despite relevant context"),
            ("rajpurkar/squad_v2", "validation", "select an adversarial unanswerable validation item that tempts span copying"),
            ("rajpurkar/squad_v2", "validation", "select a validation item where the context topic overlaps but no exact answer exists"),
            ("rajpurkar/squad_v2", "validation", "select a validation item where entity overlap invites overconfident guessing"),
            ("rajpurkar/squad_v2", "validation", "select a validation item where the safest observable is clarification or explicit uncertainty"),
            ("sewon/ambig_qa", "validation", "select a multipleQAs validation item where the surface question decomposes into at least two latent questions"),
            ("sewon/ambig_qa", "validation", "select a validation item whose annotations mark multiple plausible answers that require disambiguation"),
            ("sewon/ambig_qa", "validation", "select a validation item where one answer is underspecified without asking which interpretation is wanted"),
            ("sewon/ambig_qa", "validation", "select a validation item that should invite a narrowing question before a final answer"),
            ("sewon/ambig_qa", "validation", "select a validation item where a single direct answer would collapse distinct interpretations"),
        ],
    },
    "failure_revision_later_change": {
        "target_mechanism": "plastic writeback after failure and later decision change",
        "expected_observable": "downstream decision change on a paired follow-up after explicit or implicit negative feedback",
        "source_dataset_id": "THUIR/MemoryBench",
        "source_split": "test",
        "selection_hints": [
            "select a test dialog with explicit negative feedback after an incorrect answer and a later related retry",
            "select a test dialog where implicit_feedback indicates dissatisfaction and the next similar turn should adapt",
            "select a test dialog where the assistant repeats a mistake before receiving corrective evidence",
            "select a test dialog where later success depends on carrying forward the user's correction",
            "select a test dialog where memory update should change a later plan or retrieval choice",
            "select a test dialog where prior failure should reduce confidence and alter subsequent response style",
            "select a test dialog where the later turn reuses the same constraint after the user corrects it",
            "select a test dialog where feedback changes not only content but also the next action tendency",
            "select a test dialog where a failed assumption becomes explicit and should not be repeated later",
            "select a test dialog where later change can be judged by behavior rather than narrative apology",
        ],
    },
    "tool_risk_ambiguity": {
        "target_mechanism": "boundary-sensitive tool caution under underspecification or risk",
        "expected_observable": "host policy hint or public tendency shifts toward clarify, constrain, or avoid unsafe direct tool action",
        "source_dataset_id": "liminghao1630/API-Bank",
        "source_split": "test",
        "selection_hints": [
            "select a test item where the requested API call is missing a required parameter and should not be guessed",
            "select a test item where multiple APIs could satisfy the request and clarification should precede action",
            "select a test item with destructive or irreversible side effects unless scope is narrowed",
            "select a test item where authentication or account identity is underspecified",
            "select a test item where file or record overwrite risk should suppress direct execution",
            "select a test item where location/date ambiguity should block immediate tool commitment",
            "select a test item where financial or booking side effects require confirmation before action",
            "select a test item where the correct API family depends on a missing entity identifier",
            "select a test item where tool selection can be wrong even if the user intent is broadly clear",
            "select a test item where the safest public observable is a clarifying question or bounded refusal to act",
        ],
    },
    "continuity": {
        "target_mechanism": "sustained continuity across low-cue or delayed follow-up turns",
        "expected_observable": "stable public behavior or response tendency across resumed context without full restatement",
        "source_dataset_id": "THUIR/MemoryBench",
        "source_split": "test",
        "selection_hints": [
            "select a test dialog where a later turn depends on recalling a preference introduced much earlier",
            "select a test dialog where identity or persona-relevant constraints must persist across topic shift",
            "select a test dialog where low-cue follow-up references an earlier plan without restating it",
            "select a test dialog where continuity requires carrying forward session-specific facts",
            "select a test dialog where later behavior should remain aligned with a previously chosen mode",
            "select a test dialog where continuity is challenged by an intervening unrelated subtask",
            "select a test dialog where a restart-like gap still expects stable reference to earlier user goals",
            "select a test dialog where a corrected fact must remain corrected across subsequent turns",
            "select a test dialog where continuity is visible in action tendency rather than only in surface recall",
            "select a test dialog where missing continuity would look like a reset to generic assistant behavior",
        ],
    },
    "adversarial_constraints": {
        "target_mechanism": "constraint retention under pressure without opportunistic completion",
        "expected_observable": "downstream decision or response-form change that preserves constraints despite tempting alternative completions",
        "source_dataset_id": "google/IFEval",
        "source_split": "train",
        "selection_hints": [
            "select a train item with JSON-only or exact format constraints that are easy to violate when content pressure rises",
            "select a train item with case or punctuation constraints that require deliberate inhibition",
            "select a train item with exact bullet-count or section-count requirements",
            "select a train item with minimum or maximum word constraints that punish generic completion",
            "select a train item with paired constraints such as keywords plus formatting and no-comma restrictions",
            "select a train item with start/end wrapper constraints like quotation or delimiters",
            "select a train item requiring prompt repetition before answer, where shortcutting is tempting",
            "select a train item requiring exactly two responses with a strict separator",
            "select a train item where constraint adherence is more important than exhaustive content coverage",
            "select a train item where the correct public observable is bounded completion that visibly honors all explicit constraints",
        ],
    },
}

RESERVE_ROWS = [
    {
        "sample_id": "reserve_adversarial_constraints_01",
        "bucket": "adversarial_constraints",
        "source_dataset_id": "LibrAI/do-not-answer",
        "source_split": "train",
        "selection_hint": "reserve a refusal-style train item where explicit harmful completion pressure is present but current ontology would over-index on safety refusal rather than MVS/H1 public drivers",
        "target_mechanism": "constraint retention under unsafe pressure",
        "expected_observable": "bounded refusal or refusal-style public response without claiming internal self-model efficacy",
        "selection_status": "selected_restricted_reserve",
        "local_partition": "restricted_reserve",
    },
    {
        "sample_id": "reserve_adversarial_constraints_02",
        "bucket": "adversarial_constraints",
        "source_dataset_id": "sorry-bench/sorry-bench-202503",
        "source_split": "dataset_defined",
        "selection_hint": "reserve a custom-license unsafe instruction item for future separate legal review only",
        "target_mechanism": "constraint retention under unsafe pressure",
        "expected_observable": "bounded refusal or constraint-preserving non-completion under harmful instruction pressure",
        "selection_status": "selected_restricted_reserve",
        "local_partition": "restricted_reserve",
    },
]


def _ensure_task_dir() -> None:
    TASK_DIR.mkdir(parents=True, exist_ok=True)


def _heldout_row(
    *,
    bucket: str,
    ordinal: int,
    source_dataset_id: str,
    source_split: str,
    selection_hint: str,
    target_mechanism: str,
    expected_observable: str,
) -> Dict[str, object]:
    source = SOURCE_BY_ID[source_dataset_id]
    sample_id = f"{bucket}_{ordinal:02d}"
    dedupe_key = f"{source_dataset_id}|{source_split}|{bucket}|{selection_hint}".lower()
    return {
        "sample_id": sample_id,
        "bucket": bucket,
        "source_dataset_id": source_dataset_id,
        "source_url": source.source_url,
        "dataset_card_url": source.dataset_card_url,
        "license": source.license,
        "license_class": source.license_class,
        "source_split": source_split,
        "local_partition": "heldout_eval",
        "target_mechanism": target_mechanism,
        "expected_observable": expected_observable,
        "selection_hint": selection_hint,
        "dedupe_key": dedupe_key,
        "selection_status": "selected_heldout",
        "runner_contract": RUNNER_CONTRACT,
    }


def _reserve_row(row: Dict[str, str]) -> Dict[str, object]:
    source = SOURCE_BY_ID[row["source_dataset_id"]]
    dedupe_key = f"{row['source_dataset_id']}|{row['source_split']}|{row['bucket']}|{row['selection_hint']}".lower()
    payload = dict(row)
    payload.update(
        {
            "source_url": source.source_url,
            "dataset_card_url": source.dataset_card_url,
            "license": source.license,
            "license_class": source.license_class,
            "dedupe_key": dedupe_key,
            "runner_contract": RUNNER_CONTRACT,
        }
    )
    return payload


def build_manifest() -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    for bucket in BUCKETS:
        spec = BUCKET_SPECS[bucket]
        if bucket == "ask_vs_answer_uncertainty":
            source_rows = spec["source_rows"]
            for idx, (dataset_id, split_name, hint) in enumerate(source_rows, start=1):
                rows.append(
                    _heldout_row(
                        bucket=bucket,
                        ordinal=idx,
                        source_dataset_id=dataset_id,
                        source_split=split_name,
                        selection_hint=hint,
                        target_mechanism=str(spec["target_mechanism"]),
                        expected_observable=str(spec["expected_observable"]),
                    )
                )
            continue

        for idx, hint in enumerate(spec["selection_hints"], start=1):
            rows.append(
                _heldout_row(
                    bucket=bucket,
                    ordinal=idx,
                    source_dataset_id=str(spec["source_dataset_id"]),
                    source_split=str(spec["source_split"]),
                    selection_hint=hint,
                    target_mechanism=str(spec["target_mechanism"]),
                    expected_observable=str(spec["expected_observable"]),
                )
            )

    reserve_rows = [_reserve_row(row) for row in RESERVE_ROWS]
    return {
        "schema_version": "mvs_h1.external_eval_corpus.v1",
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "task_slug": "mvs-h1-external-eval-corpus",
        "buckets": BUCKETS,
        "runner_contract": RUNNER_CONTRACT,
        "rows": rows + reserve_rows,
        "summary": {
            "heldout_eval_count": len(rows),
            "restricted_reserve_count": len(reserve_rows),
            "bucket_count": len(BUCKETS),
        },
    }


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _render_source_shortlist_md() -> str:
    lines = [
        "# MVS H1 External Eval Source Shortlist",
        "",
        "| dataset | status | license | preferred_eval_split | supported buckets | note |",
        "|---|---|---|---|---|---|",
    ]
    for source in SOURCES:
        note = source.reserve_reason or source.split_note
        buckets = ", ".join(f"`{bucket}`" for bucket in source.supported_buckets)
        lines.append(
            f"| [{source.dataset_id}]({source.dataset_card_url}) | `{source.selection_status}` | `{source.license}` | "
            f"`{source.preferred_eval_split}` | {buckets} | {note} |"
        )
    return "\n".join(lines) + "\n"


def _render_license_matrix_md() -> str:
    lines = [
        "# MVS H1 External Eval License Matrix",
        "",
        "| dataset | license | class | default inclusion |",
        "|---|---|---|---|",
    ]
    for source in SOURCES:
        inclusion = "heldout main manifest" if source.selection_status == "main_shortlist" else "restricted reserve only"
        lines.append(
            f"| [{source.dataset_id}]({source.dataset_card_url}) | `{source.license}` | `{source.license_class}` | {inclusion} |"
        )
    return "\n".join(lines) + "\n"


def _render_dedupe_report_md(manifest: Dict[str, object]) -> str:
    rows = manifest["rows"]  # type: ignore[index]
    heldout_rows = [row for row in rows if row["local_partition"] == "heldout_eval"]  # type: ignore[index]
    reserve_rows = [row for row in rows if row["local_partition"] == "restricted_reserve"]  # type: ignore[index]
    dedupe_keys = [row["dedupe_key"] for row in rows]  # type: ignore[index]
    duplicates = sorted({key for key in dedupe_keys if dedupe_keys.count(key) > 1})
    bucket_counts = {bucket: 0 for bucket in BUCKETS}
    for row in heldout_rows:
        bucket_counts[row["bucket"]] += 1

    lines = [
        "# MVS H1 External Eval Dedupe Report",
        "",
        f"- heldout_eval_count: `{len(heldout_rows)}`",
        f"- restricted_reserve_count: `{len(reserve_rows)}`",
        f"- duplicate_dedupe_keys: `{len(duplicates)}`",
        f"- runner_candidate_id: `{manifest['runner_contract']['candidate_id']}`",
        "",
        "## Held-out Bucket Counts",
        "",
    ]
    for bucket in BUCKETS:
        lines.append(f"- `{bucket}`: `{bucket_counts[bucket]}`")
    lines.extend(
        [
            "",
            "## Duplicate Keys",
            "",
        ]
    )
    if duplicates:
        lines.extend(f"- `{key}`" for key in duplicates)
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    _ensure_task_dir()
    source_payload = {
        "schema_version": "mvs_h1.external_eval_sources.v1",
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "sources": [
            {
                "dataset_id": source.dataset_id,
                "dataset_card_url": source.dataset_card_url,
                "source_url": source.source_url,
                "license": source.license,
                "license_class": source.license_class,
                "preferred_eval_split": source.preferred_eval_split,
                "split_note": source.split_note,
                "selection_status": source.selection_status,
                "reserve_reason": source.reserve_reason,
                "supported_buckets": source.supported_buckets,
            }
            for source in SOURCES
        ],
    }
    manifest = build_manifest()

    _write_json(SOURCE_SHORTLIST_JSON, source_payload)
    SOURCE_SHORTLIST_MD.write_text(_render_source_shortlist_md(), encoding="utf-8")
    _write_json(MANIFEST_JSON, manifest)
    LICENSE_MATRIX_MD.write_text(_render_license_matrix_md(), encoding="utf-8")
    DEDUPE_REPORT_MD.write_text(_render_dedupe_report_md(manifest), encoding="utf-8")

    print(f"source_shortlist_json={SOURCE_SHORTLIST_JSON.relative_to(ROOT)}")
    print(f"source_shortlist_md={SOURCE_SHORTLIST_MD.relative_to(ROOT)}")
    print(f"manifest_json={MANIFEST_JSON.relative_to(ROOT)}")
    print(f"license_matrix_md={LICENSE_MATRIX_MD.relative_to(ROOT)}")
    print(f"dedupe_report_md={DEDUPE_REPORT_MD.relative_to(ROOT)}")
    print(f"heldout_eval_count={manifest['summary']['heldout_eval_count']}")
    print(f"restricted_reserve_count={manifest['summary']['restricted_reserve_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
