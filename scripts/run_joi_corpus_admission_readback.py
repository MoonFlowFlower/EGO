"""Produce read-only JOI demo frozen-reference admission artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from joi_corpus.corpus_path import CorpusFrozenStateError, CorpusUnavailable, assert_frozen, snapshot
from joi_corpus.manifest_verifier import verify_manifests
from joi_corpus.reader import read_artifact_tree
from joi_corpus.schema_catalog import build_shape_catalog, render_schema_contract

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "joi_demo_reference_admission_001a"
CONTRACT_PATH = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "joi-demo-history-to-ego-reference-admission-001a"
    / "CORPUS_SCHEMA_CONTRACT.md"
)
CLAIM_CEILING = "frozen_reference_corpus_admission_only"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def default_off_scan() -> dict:
    roots = [ROOT / "EgoOperator", ROOT / "EgoDesktop"]
    patterns = ["scripts.joi_corpus", "joi_corpus", "run_joi_corpus_admission_readback"]
    suffixes = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
    matches: list[dict] = []
    scanned = 0
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in suffixes):
            scanned += 1
            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), start=1):
                for pattern in patterns:
                    if pattern in line:
                        matches.append(
                            {
                                "path": path.relative_to(ROOT).as_posix(),
                                "line": line_no,
                                "pattern": pattern,
                                "text": line.strip(),
                            }
                        )
    return {
        "scanned_roots": [p.relative_to(ROOT).as_posix() for p in roots if p.exists()],
        "scanned_file_count": scanned,
        "patterns": patterns,
        "match_count": len(matches),
        "matches": matches,
        "clean": not matches,
    }


def _no_mutation(before: dict, after: dict) -> dict:
    checks = {
        "tag_commit_identical": before["tag_commit"] == after["tag_commit"],
        "status_porcelain_identical": before["status_porcelain"] == after["status_porcelain"],
        "status_sha256_identical": before["status_sha256"] == after["status_sha256"],
    }
    return {"checks": checks, "passed": all(checks.values()), "before": before, "after": after}


def run(corpus_path: str | None = None, out_dir: Path = OUT_DIR) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    before = assert_frozen(corpus_path)
    readback = read_artifact_tree(corpus_path)
    pin_report = verify_manifests(corpus_path)
    shape_catalog = build_shape_catalog(corpus_path)
    CONTRACT_PATH.write_text(render_schema_contract(shape_catalog), encoding="utf-8")
    after = snapshot(corpus_path)
    mutation = _no_mutation(before, after)
    off_scan = default_off_scan()

    hard_failures: list[str] = []
    if readback["critical_parse_error_count"]:
        hard_failures.append("reader_critical_parse_errors")
    if not mutation["passed"]:
        hard_failures.append("corpus_mutation_detected")
    if not off_scan["clean"]:
        hard_failures.append("default_off_scan_runtime_reference_found")

    verdict = "reference_admission_readback_pass" if not hard_failures else "reference_admission_readback_fail"
    result = {
        "task_id": "JOI-DEMO-HISTORY-TO-EGO-REFERENCE-ADMISSION-001A",
        "verdict": verdict,
        "claim_ceiling": CLAIM_CEILING,
        "created_at": started,
        "corpus_tag": before["frozen_tag"],
        "corpus_tag_commit": before["tag_commit"],
        "readback_summary": {
            "artifact_dir_count": readback["artifact_dir_count"],
            "file_count": readback["file_count"],
            "json_count": readback["json_count"],
            "jsonl_count": readback["jsonl_count"],
            "jsonl_total_lines": readback["jsonl_total_lines"],
            "parse_error_count": readback["parse_error_count"],
            "critical_parse_error_count": readback["critical_parse_error_count"],
        },
        "pin_verification_counts": pin_report["counts"],
        "shape_result_count": shape_catalog["result_count"],
        "no_mutation_passed": mutation["passed"],
        "default_off_scan_clean": off_scan["clean"],
        "hard_failures": hard_failures,
        "what_this_does_not_prove": [
            "mechanism validity",
            "transfer of any joi-demo Bar-1 result to Ego scale",
            "runtime integration safety",
            "durable memory efficacy",
            "learning headroom",
            "stable user benefit",
            "live autonomy",
            "functional selfhood",
            "consciousness",
            "subjective experience",
            "real emotion",
        ],
    }

    _write_json(out_dir / "readback_report.json", readback)
    _write_json(out_dir / "pin_verification_report.json", pin_report)
    _write_json(out_dir / "shape_catalog.json", shape_catalog)
    _write_json(out_dir / "no_mutation_proof.json", mutation)
    _write_json(out_dir / "default_off_scan.json", off_scan)
    if hard_failures:
        _write_json(out_dir / "failure_manifest.json", {"verdict": verdict, "hard_failures": hard_failures})
    _write_json(out_dir / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-path", default=None)
    parser.add_argument("--out", default=str(OUT_DIR))
    args = parser.parse_args()
    out_dir = Path(args.out).resolve()
    try:
        result = run(args.corpus_path, out_dir)
    except (CorpusUnavailable, CorpusFrozenStateError, Exception) as exc:
        payload = {
            "task_id": "JOI-DEMO-HISTORY-TO-EGO-REFERENCE-ADMISSION-001A",
            "verdict": "reference_admission_readback_fail",
            "claim_ceiling": CLAIM_CEILING,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        _write_json(out_dir / "failure_manifest.json", payload)
        _write_json(out_dir / "result.json", payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["verdict"] == "reference_admission_readback_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
