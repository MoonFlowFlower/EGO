#!/usr/bin/env python3
"""Run the #80 strict suite against the next non-baseline local sidecar.

This wrapper is intentionally thin: it does not download models and does not
change EgoOperator state. It selects a loaded text-generation model, excluding
the known Cydonia baseline by default, then delegates to
run_ego_experience_trial.py through the real EgoOperator path.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import configure_adult_fiction_sidecar as sidecar  # noqa: E402


DEFAULT_SCENARIO_NAME = "ego_adult_fiction_private_scenario.json"


def _safe_slug(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")
    return slug or "candidate"


def default_temp_dir() -> Path:
    return Path(os.getenv("TEMP") or os.getenv("TMP") or "/tmp")


def default_scenario_file() -> Path:
    return default_temp_dir() / DEFAULT_SCENARIO_NAME


def default_output_dir(model: str) -> Path:
    return default_temp_dir() / f"ego_adult_fiction_acceptance_{_safe_slug(model)}"


def build_trial_env(args: argparse.Namespace, model: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "ADULT_FICTION_PROVIDER": "openai_compatible",
            "ADULT_FICTION_BASE_URL": sidecar.normalize_base_url(args.base_url),
            "ADULT_FICTION_API_KEY": args.api_key,
            "ADULT_FICTION_MODEL": model,
            "ADULT_FICTION_EXPRESSIVENESS": args.expressiveness,
            "ADULT_FICTION_PROMPT_PROFILE": args.prompt_profile,
            "ADULT_FICTION_TIMEOUT_SECONDS": str(args.adult_timeout_seconds),
            "ADULT_FICTION_MAX_TOKENS": str(args.max_tokens),
            "ADULT_FICTION_CONTEXT_TURNS": str(args.context_turns),
            "ADULT_FICTION_MESSAGE_CHAR_LIMIT": str(args.message_char_limit),
        }
    )
    if args.temperature is not None:
        env["ADULT_FICTION_TEMPERATURE"] = str(args.temperature)
    if args.top_p is not None:
        env["ADULT_FICTION_TOP_P"] = str(args.top_p)
    return env


def build_trial_command(args: argparse.Namespace, output_dir: Path) -> list[str]:
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_ego_experience_trial.py"),
        "--adult-fiction-acceptance-suite",
        "--scenario-file",
        str(args.scenario_file),
        "--repeat-runs",
        str(args.repeat_runs),
        "--suite-timeout-seconds",
        str(args.suite_timeout_seconds),
        "--out",
        str(output_dir),
    ]
    if args.settings_matrix:
        command.extend(["--settings-matrix", str(args.settings_matrix)])
    if args.judge_with_codex:
        command.extend(["--judge-with-codex", "--judge-model", args.judge_model])
    return command


def load_acceptance_report(output_dir: Path) -> dict[str, Any] | None:
    path = output_dir / "adult_fiction_acceptance_report.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def classify_acceptance_report(report: dict[str, Any] | None, returncode: int) -> dict[str, Any]:
    if not isinstance(report, dict):
        return {
            "status": "unknown",
            "recommendation": "inspect_stdout_stderr",
            "reason": "acceptance_report_missing_or_unreadable",
        }
    status = str(report.get("status") or "")
    repeat_summary = report.get("repeat_run_summary") if isinstance(report.get("repeat_run_summary"), dict) else {}
    settings_summary = report.get("settings_matrix_summary") if isinstance(report.get("settings_matrix_summary"), dict) else {}
    timeout = report.get("suite_timeout") if isinstance(report.get("suite_timeout"), dict) else {}
    failure_counts = repeat_summary.get("failure_counts") if isinstance(repeat_summary.get("failure_counts"), dict) else {}
    recommendation = "keep_80_blocked"
    reason = status or f"returncode_{returncode}"
    if status == "scripted_adult_fiction_acceptance_judge_pass":
        recommendation = "ready_for_human_sanity_and_closeout_packet"
        reason = "strict_suite_and_gpt55_judge_pass"
    elif status == "scripted_adult_fiction_acceptance_needs_judge":
        recommendation = "ready_for_gpt55_judge"
        reason = "mechanical_strict_suite_pass"
    elif status == "scripted_adult_fiction_acceptance_judge_partial":
        recommendation = "keep_80_blocked_judge_partial"
        reason = "gpt55_judge_partial"
    elif status == "scripted_adult_fiction_acceptance_judge_failed":
        recommendation = "keep_80_blocked_judge_failed"
        reason = "gpt55_judge_failed"
    elif timeout.get("triggered"):
        recommendation = "keep_80_blocked_timeout_or_capacity"
        reason = f"timeout_at_{timeout.get('stage') or 'unknown'}"
    elif settings_summary.get("status") != "pass":
        recommendation = "keep_80_blocked_model_capability"
        reason = "settings_matrix_no_passing_route"
    elif repeat_summary.get("status") != "pass":
        recommendation = "keep_80_blocked_repeat_instability"
        reason = "strict_repeat_runs_failed"
    return {
        "status": status,
        "recommendation": recommendation,
        "reason": reason,
        "selected_setting_id": settings_summary.get("selected_setting_id"),
        "repeat_status": repeat_summary.get("status"),
        "passed_run_count": repeat_summary.get("passed_run_count"),
        "required_runs": repeat_summary.get("required_runs"),
        "failure_counts": failure_counts,
        "timeout": timeout,
        "judge_verdict": (report.get("gpt55_judge") or {}).get("verdict") if isinstance(report.get("gpt55_judge"), dict) else None,
        "strict_judge_score_gate": (report.get("strict_judge_score_gate") or {}).get("status") if isinstance(report.get("strict_judge_score_gate"), dict) else None,
    }


def _ps_arg(value: str | Path) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(ch.isspace() for ch in text) or any(ch in text for ch in ['"', "'", "`"]):
        return '"' + text.replace("`", "``").replace('"', '`"') + '"'
    return text


def _unique_nonempty(values: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = (value or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def recommended_wrapper_command(args: argparse.Namespace, *, wait: bool) -> str:
    lines = ["C:\\Python313\\python.exe .\\scripts\\run_adult_fiction_candidate_suite.py `"]
    for exclusion in _unique_nonempty(tuple(args.exclude_model or ())):
        lines.append(f"  --exclude-model {_ps_arg(exclusion)} `")
    if wait:
        lines.extend(
            [
                "  --wait-for-candidate `",
                f"  --wait-timeout-seconds {args.wait_timeout_seconds} `",
                f"  --poll-seconds {args.poll_seconds} `",
            ]
        )
    if args.judge_with_codex:
        lines.extend(
            [
                "  --judge-with-codex `",
                f"  --judge-model {_ps_arg(args.judge_model)} `",
            ]
        )
    if args.scenario_file != default_scenario_file():
        lines.append(f"  --scenario-file {_ps_arg(args.scenario_file)} `")
    if args.settings_matrix:
        lines.append(f"  --settings-matrix {_ps_arg(args.settings_matrix)} `")
    if args.temperature is not None:
        lines.append(f"  --temperature {args.temperature} `")
    if args.top_p is not None:
        lines.append(f"  --top-p {args.top_p} `")
    if args.out:
        lines.append(f"  --out {_ps_arg(args.out)} `")
    lines.append("  --json")
    return "\n".join(lines)


def no_candidate_result(args: argparse.Namespace, models: list[str]) -> dict[str, Any]:
    text_models = sidecar.text_generation_model_ids(models)
    exclusions = tuple(args.exclude_model or ())
    next_action = (
        "Load a non-excluded text-generation GGUF model in LM Studio, then rerun this wrapper."
        if exclusions and text_models
        else "Load a text-generation GGUF model in LM Studio, then rerun this wrapper."
    )
    return {
        "status": "no_candidate_text_generation_models",
        "provider": "openai_compatible",
        "base_url": sidecar.normalize_base_url(args.base_url),
        "models_url": sidecar.models_url(args.base_url),
        "model_count": len(models),
        "models": models,
        "text_generation_model_count": len(text_models),
        "text_generation_models": text_models,
        "ignored_non_text_models": [model for model in models if model not in text_models],
        "excluded_text_generation_models": [
            model for model in text_models if sidecar.model_matches_exclusion(model, exclusions)
        ],
        "recommended_next_models": sidecar.recommended_next_models(exclusions),
        "recommended_direct_command": recommended_wrapper_command(args, wait=False),
        "recommended_wait_command": recommended_wrapper_command(args, wait=True),
        "next_action": next_action,
    }


def fetch_models_result(args: argparse.Namespace) -> tuple[int, list[str] | None, dict[str, Any] | None]:
    try:
        models = sidecar.fetch_model_ids(args.base_url, args.configure_timeout_seconds)
    except (OSError, TimeoutError) as exc:
        return 2, None, {
            "status": "server_unavailable",
            "provider": "openai_compatible",
            "base_url": sidecar.normalize_base_url(args.base_url),
            "models_url": sidecar.models_url(args.base_url),
            "error": str(exc),
            "next_action": "Start LM Studio server, load a candidate text-generation model, then rerun this wrapper.",
        }
    return 0, models, None


def wait_for_candidate(args: argparse.Namespace) -> tuple[int, list[str] | None, str | None, dict[str, Any] | None]:
    deadline = time.monotonic() + max(0, args.wait_timeout_seconds)
    attempts = 0
    last_result: dict[str, Any] | None = None
    while True:
        attempts += 1
        code, models, error_result = fetch_models_result(args)
        if error_result is not None:
            last_result = error_result
        elif models is not None:
            selected = sidecar.choose_model(models, args.model, tuple(args.exclude_model or ()))
            if selected:
                return 0, models, selected, {
                    "wait_status": "candidate_found",
                    "wait_attempts": attempts,
                    "selected_model": selected,
                }
            last_result = no_candidate_result(args, models)

        if not args.wait_for_candidate or time.monotonic() >= deadline:
            if last_result is not None:
                last_result = dict(last_result)
                last_result["wait_status"] = "candidate_not_found" if args.wait_for_candidate else "not_waiting"
                last_result["wait_attempts"] = attempts
            return code if code else 3, models, None, last_result
        time.sleep(max(1, args.poll_seconds))


def run_candidate_suite(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    code, models, selected, wait_result = wait_for_candidate(args)
    if not selected:
        return code, wait_result or {
            "status": "no_candidate_text_generation_models",
            "next_action": "Load a second text-generation GGUF model in LM Studio, then rerun this wrapper.",
        }

    assert models is not None

    scenario_file = Path(args.scenario_file)
    if not scenario_file.exists():
        return 2, {
            "status": "scenario_file_missing",
            "scenario_file": str(scenario_file),
            "next_action": "Create the private scenario file or pass --scenario-file with an existing local path.",
        }

    output_dir = Path(args.out) if args.out else default_output_dir(selected)
    command = build_trial_command(args, output_dir)
    env = build_trial_env(args, selected)
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=args.wrapper_timeout_seconds if args.wrapper_timeout_seconds > 0 else None,
    )

    child_summary: dict[str, Any] | None = None
    stdout = completed.stdout.strip()
    if stdout:
        try:
            child_summary = json.loads(stdout)
        except json.JSONDecodeError:
            child_summary = {"raw_stdout": stdout}
    acceptance_report = load_acceptance_report(output_dir)
    promotion = classify_acceptance_report(acceptance_report, completed.returncode)

    result = {
        "status": "candidate_suite_finished" if completed.returncode == 0 else "candidate_suite_failed",
        "selected_model": selected,
        "excluded_model_filters": _unique_nonempty(tuple(args.exclude_model or ())),
        "wait_result": wait_result,
        "output_dir": str(output_dir),
        "acceptance_report_path": str(output_dir / "adult_fiction_acceptance_report.json"),
        "promotion_recommendation": promotion,
        "command": command,
        "returncode": completed.returncode,
        "child_summary": child_summary,
        "stderr": completed.stderr.strip(),
    }
    return completed.returncode, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run #80 strict suite against a loaded non-baseline local sidecar candidate.")
    parser.add_argument("--base-url", default=sidecar.DEFAULT_BASE_URL)
    parser.add_argument("--api-key", default=sidecar.DEFAULT_API_KEY)
    parser.add_argument("--model", default="", help="Explicit loaded model id. Overrides automatic candidate selection.")
    parser.add_argument("--exclude-model", action="append", default=["cydonia"], help="Baseline model substring to exclude from automatic selection.")
    parser.add_argument("--configure-timeout-seconds", type=float, default=5.0)
    parser.add_argument("--scenario-file", type=Path, default=default_scenario_file())
    parser.add_argument("--settings-matrix", type=Path, default=None, help="Optional settings matrix passed through to the strict suite.")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--repeat-runs", type=int, default=3)
    parser.add_argument("--suite-timeout-seconds", type=int, default=1800)
    parser.add_argument("--wrapper-timeout-seconds", type=int, default=0, help="Optional timeout around the delegated strict suite; 0 disables wrapper timeout.")
    parser.add_argument("--wait-for-candidate", action="store_true", help="Poll LM Studio until a non-excluded text-generation model appears, then run the strict suite.")
    parser.add_argument("--wait-timeout-seconds", type=int, default=1800)
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--expressiveness", default="explicit")
    parser.add_argument("--prompt-profile", default="direct_fiction")
    parser.add_argument("--adult-timeout-seconds", type=int, default=180)
    parser.add_argument("--max-tokens", type=int, default=120)
    parser.add_argument("--context-turns", type=int, default=3)
    parser.add_argument("--message-char-limit", type=int, default=420)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--judge-with-codex", action="store_true")
    parser.add_argument("--judge-model", default="gpt-5.5")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    code, result = run_candidate_suite(args)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
