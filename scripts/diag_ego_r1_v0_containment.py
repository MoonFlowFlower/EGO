from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
V0 = ROOT / "artifacts" / "ego_r1_memory_ownership_001a"
OUT = ROOT / "artifacts" / "ego_r1_memory_ownership_instrument_repair_001a"
RUN_ID = "ego_r1_memory_ownership_instrument_repair_001a_r_diag"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _code_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _fixture_poison_index(fixture: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    rows: dict[tuple[int, int], dict[str, Any]] = {}
    for row in fixture:
        suggestion = row.get("suggestion")
        if suggestion and suggestion.get("is_poison"):
            rows[(int(row["tick"]), int(suggestion["topic"]))] = {
                "tick": int(row["tick"]),
                "topic": int(suggestion["topic"]),
                "poison_claimed_option": int(suggestion["claimed_option"]),
                "clean_claimed_option": int(suggestion["clean_claimed_option"]),
                "content_payload": suggestion.get("content_payload", ""),
            }
    return rows


def _entry_digest(entry: dict[str, Any] | None) -> dict[str, Any] | None:
    if not entry:
        return None
    provenance = entry.get("provenance") or {}
    promotion = entry.get("promotion") or {}
    return {
        "entry_id": entry.get("entry_id"),
        "topic": entry.get("topic"),
        "claimed_option": entry.get("claimed_option"),
        "is_poison": entry.get("is_poison"),
        "content_hash": provenance.get("content_hash"),
        "source_tick": provenance.get("tick"),
        "promotion_tick": promotion.get("promotion_tick"),
        "evidence_ticks": promotion.get("evidence_ticks", []),
        "policy_id": promotion.get("policy_id"),
    }


def _lineage_key(entry: dict[str, Any] | None) -> tuple[Any, ...] | None:
    if not entry:
        return None
    provenance = entry.get("provenance") or {}
    return (
        int(entry.get("topic", -1)),
        int(entry.get("claimed_option", -1)),
        bool(entry.get("is_poison")),
        provenance.get("content_hash"),
        provenance.get("tick"),
    )


def _map_to_poison(entry: dict[str, Any] | None, poison_rows: dict[tuple[int, int], dict[str, Any]]) -> dict[str, Any] | None:
    if not entry:
        return None
    provenance = entry.get("provenance") or {}
    key = (int(provenance.get("tick", -1)), int(entry.get("topic", -1)))
    poison = poison_rows.get(key)
    if not poison:
        return None
    clean_twin = not bool(entry.get("is_poison")) and int(entry.get("claimed_option", -1)) == poison["clean_claimed_option"]
    poison_row = bool(entry.get("is_poison")) and int(entry.get("claimed_option", -1)) == poison["poison_claimed_option"]
    if not (clean_twin or poison_row):
        return None
    return {"fixture_poison_row": poison, "relation": "clean_twin" if clean_twin else "poison_row"}


def _history_before(rows: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    entries: dict[str, dict[str, Any]] = {}
    promoted: list[dict[str, Any]] = []
    before: list[list[dict[str, Any]]] = []
    for row in rows:
        before.append(json.loads(json.dumps(promoted, sort_keys=True)))
        events = row["component_attribution"]["memory_events_v0"]
        write = events.get("write_event")
        if write and write.get("entry"):
            entry = write["entry"]
            entries[entry["entry_id"]] = entry
        for event in events.get("promotion_events", []):
            entry = json.loads(json.dumps(entries.get(event["entry_id"], {}), sort_keys=True))
            if not entry:
                entry = {"entry_id": event["entry_id"], "provenance": event.get("provenance"), "is_poison": event.get("is_poison")}
            entry["promotion"] = event
            promoted.append(entry)
    return before


def _governing(entries: list[dict[str, Any]], topic: int) -> dict[str, Any] | None:
    matches = [entry for entry in entries if int(entry.get("topic", -1)) == int(topic)]
    return matches[-1] if matches else None


def _diagnose(
    inj_entry: dict[str, Any] | None,
    clean_entry: dict[str, Any] | None,
    inj_use: dict[str, Any] | None,
    clean_use: dict[str, Any] | None,
    poison_rows: dict[tuple[int, int], dict[str, Any]],
) -> tuple[str, list[dict[str, Any]], str]:
    inj_map = _map_to_poison(inj_entry, poison_rows)
    clean_map = _map_to_poison(clean_entry, poison_rows)
    mapped = [x for x in (inj_map, clean_map) if x]
    if mapped and _lineage_key(inj_entry) != _lineage_key(clean_entry):
        return "H-displacement", mapped, "governing owned entries differ and at least one lineage is the poison row or its clean twin"
    if inj_use and inj_use.get("is_poison"):
        return "H-displacement", mapped, "injected-arm use event directly cites a poison row"
    if _lineage_key(inj_entry) == _lineage_key(clean_entry):
        return "H-nondeterminism", mapped, "actions differ while governing owned entry lineage is identical"
    if inj_entry or clean_entry or inj_use or clean_use:
        return "H-indirect-bookkeeping", mapped, "actions differ through memory lineage/use state but no poison-row mapping was found"
    return "untraceable", mapped, "no governing memory lineage or use event explains the mismatch"


def _episode_diagnosis(episode_id: str) -> dict[str, Any]:
    fixture_path = V0 / "input_fixtures" / f"{episode_id}.json"
    inj_path = V0 / "traces" / "candidate_injected" / f"{episode_id}.jsonl"
    clean_path = V0 / "traces" / "candidate_clean" / f"{episode_id}.jsonl"
    fixture = _read_json(fixture_path)
    injected = _read_jsonl(inj_path)
    clean = _read_jsonl(clean_path)
    poison_rows = _fixture_poison_index(fixture)
    inj_before = _history_before(injected)
    clean_before = _history_before(clean)
    mismatches: list[dict[str, Any]] = []
    for index, (inj_row, clean_row) in enumerate(zip(injected, clean)):
        if inj_row["action"] == clean_row["action"]:
            continue
        topic = int(inj_row["observation"]["topic"])
        inj_entry = _governing(inj_before[index], topic)
        clean_entry = _governing(clean_before[index], topic)
        diagnosis, mapped, reason = _diagnose(
            inj_entry,
            clean_entry,
            inj_row["component_attribution"].get("memory_use_event"),
            clean_row["component_attribution"].get("memory_use_event"),
            poison_rows,
        )
        mismatches.append(
            {
                "tick": int(inj_row["observation"]["tick"]),
                "step_index": index,
                "topic": topic,
                "true_option": int(inj_row["observation"]["true_option"]),
                "injected_action": inj_row["action"],
                "clean_action": clean_row["action"],
                "injected_governing_entry": _entry_digest(inj_entry),
                "clean_governing_entry": _entry_digest(clean_entry),
                "injected_use_event": inj_row["component_attribution"].get("memory_use_event"),
                "clean_use_event": clean_row["component_attribution"].get("memory_use_event"),
                "poison_row_mapping": mapped,
                "diagnosis": diagnosis,
                "diagnosis_reason": reason,
            }
        )
    counts = Counter(row["diagnosis"] for row in mismatches)
    return {
        "episode_id": episode_id,
        "input_artifacts": [str(fixture_path.relative_to(ROOT)), str(inj_path.relative_to(ROOT)), str(clean_path.relative_to(ROOT))],
        "mismatch_count": len(mismatches),
        "diagnosis_counts": dict(sorted(counts.items())),
        "mismatches": mismatches,
    }


def build_report() -> dict[str, Any]:
    episodes = sorted(path.stem for path in (V0 / "input_fixtures").glob("seed_*_episode_*.json"))
    per_episode = [_episode_diagnosis(episode) for episode in episodes]
    target = next(item for item in per_episode if item["episode_id"] == "seed_31_episode_1")
    all_mismatch_diagnoses = [row["diagnosis"] for item in per_episode for row in item["mismatches"]]
    blocking = any(label in {"H-nondeterminism", "untraceable"} for label in all_mismatch_diagnoses)
    overall = "H-displacement" if set(all_mismatch_diagnoses) <= {"H-displacement"} else "H-indirect-bookkeeping"
    if "H-nondeterminism" in all_mismatch_diagnoses:
        overall = "H-nondeterminism"
    if "untraceable" in all_mismatch_diagnoses:
        overall = "untraceable"
    return {
        "task_id": "EGO-R1-MEMORY-OWNERSHIP-INSTRUMENT-REPAIR-001A",
        "phase": "R-DIAG",
        "producer_function": "build_report",
        "run_id": RUN_ID,
        "code_path_hash": _code_hash(),
        "input_artifacts": [artifact for item in per_episode for artifact in item["input_artifacts"]],
        "primary_episode": "seed_31_episode_1",
        "primary_mismatch_ticks": [row["tick"] for row in target["mismatches"]],
        "diagnosis": overall,
        "overall_verdict": "stop_required" if blocking else "traceable_poison_row_displacement",
        "self_gate_stop_required": blocking,
        "per_episode": per_episode,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT / "v0_containment_diagnosis.json"))
    args = parser.parse_args()
    report = build_report()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "diagnosis": report["diagnosis"], "self_gate_stop_required": report["self_gate_stop_required"]}, sort_keys=True))
    return 1 if report["self_gate_stop_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
