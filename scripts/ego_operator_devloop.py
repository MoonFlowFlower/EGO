#!/usr/bin/env python3
"""Small developer-loop helpers for EgoOperator repair work."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO


ROOT = Path(__file__).resolve().parents[1]

TARGET_COMMANDS = [
    {
        "label": "py_compile",
        "cmd": [
            sys.executable,
            "-m",
            "py_compile",
            "EgoOperator/agent_base.py",
            "EgoOperator/tests/test_operator_runtime_contract.py",
            "scripts/github_project_task.py",
            "scripts/ego_operator_devloop.py",
        ],
    },
    {
        "label": "targeted_pytest",
        "cmd": [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "EgoOperator/tests/test_operator_runtime_contract.py",
        ],
        "env": {"TMPDIR": "/tmp"},
    },
]

FULL_COMMANDS = [
    TARGET_COMMANDS[0],
    {
        "label": "ego_operator_tests",
        "cmd": [sys.executable, "-m", "pytest", "-q", "EgoOperator/tests"],
        "env": {"TMPDIR": "/tmp"},
    },
    {
        "label": "diff_check",
        "cmd": [
            "git",
            "diff",
            "--check",
            "--",
            "EgoOperator",
            "scripts/github_project_task.py",
            "scripts/ego_operator_devloop.py",
            "scripts/tests",
        ],
    },
]

WINDOWS_PATH_RE = re.compile(r"([A-Za-z]:\\[^\s\"'`<>|]+)")
POSIX_PATH_RE = re.compile(r"((?:/mnt/[A-Za-z]|/tmp|/home|/var|/opt)/[^\s\"'`<>|]+)")
TOOL_CALL_RE = re.compile(r"\[执行工具\]:\s*(\w+)\s+(\{.*?\})(?:\n|$)")
EXECUTION_PATH_RE = re.compile(r'"execution"\s*:\s*\{.*?"path"\s*:\s*"([^"]+)"', re.DOTALL)
APPROVAL_OK_RE = re.compile(r'"execution"\s*:\s*\{.*?"status"\s*:\s*"ok"', re.DOTALL)


@dataclass
class CommandResult:
    label: str
    command: list[str]
    returncode: int
    elapsed_seconds: float
    stdout_tail: str
    stderr_tail: str

    @property
    def status(self) -> str:
        return "pass" if self.returncode == 0 else "fail"

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "command": self.command,
            "status": self.status,
            "returncode": self.returncode,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
        }


class CommandRunner:
    def run(self, command: list[str], *, env: dict[str, str] | None = None) -> CommandResult:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        started = time.monotonic()
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=merged_env,
            capture_output=True,
            text=True,
            check=False,
        )
        return CommandResult(
            label="",
            command=command,
            returncode=completed.returncode,
            elapsed_seconds=time.monotonic() - started,
            stdout_tail=_tail(completed.stdout),
            stderr_tail=_tail(completed.stderr),
        )


def _tail(text: str, limit: int = 2000) -> str:
    text = text or ""
    return text[-limit:]


def run_verify(mode: str, *, runner: CommandRunner) -> dict[str, Any]:
    if mode not in {"target", "full"}:
        raise ValueError(f"unknown verify mode: {mode}")
    commands = TARGET_COMMANDS if mode == "target" else FULL_COMMANDS
    results: list[dict[str, Any]] = []
    started = time.monotonic()
    for item in commands:
        result = runner.run(item["cmd"], env=item.get("env"))
        result.label = item["label"]
        results.append(result.to_dict())
        if result.returncode != 0:
            break
    passed = all(entry["status"] == "pass" for entry in results) and len(results) == len(commands)
    return {
        "status": "ok" if passed else "failed",
        "mode": mode,
        "allow_claim_closeout": bool(passed),
        "claim_scope": (
            "local workflow verification only; real-provider or human-observable pass must be recorded separately"
        ),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "commands": results,
    }


def latest_prompt(text: str) -> str:
    prompts = [
        line[1:].strip()
        for line in (text or "").splitlines()
        if line.strip().startswith(">") and line[1:].strip()
    ]
    return prompts[-1] if prompts else ""


def first_path(text: str) -> str:
    match = WINDOWS_PATH_RE.search(text or "") or POSIX_PATH_RE.search(text or "")
    return _trim_path_suffix(match.group(1)) if match else ""


def _trim_path_suffix(path: str) -> str:
    value = (path or "").rstrip(".,;:，。；：")
    # Human trial prompts often omit whitespace after a path, e.g.
    # D:\...\Test3创建一个网页. Keep extraction useful for common action verbs
    # without trying to become a full natural-language path parser.
    value = re.sub(r"(创建|新建|写入|生成|再创建|修改|删除).*$", "", value)
    return value.rstrip("\\/.,;:，。；：")


def observed_tool_calls(text: str) -> list[dict[str, Any]]:
    calls = []
    for match in TOOL_CALL_RE.finditer(text or ""):
        raw_args = match.group(2)
        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            args = {"raw": raw_args}
        calls.append({"tool": match.group(1), "args": args})
    return calls


def classify_failure(text: str, expected_path: str, execution_path: str) -> str:
    lowered = (text or "").lower()
    if "429" in lowered or "too many requests" in lowered:
        return "provider_rate_limit"
    if "空回复" in text or "empty" in lowered:
        return "empty_llm_response"
    if "没有对应的真实 proposal" in text or "fake approval" in lowered:
        return "approval_hallucination"
    if expected_path and execution_path and _normalize_path(expected_path) not in _normalize_path(execution_path):
        return "path_intent_mismatch"
    if "blocked" in lowered or "被拒" in text or "阻断" in text:
        return "gate_blocked"
    return "unknown"


def _normalize_path(path: str) -> str:
    return (path or "").replace("\\\\", "\\").replace("/", "\\").casefold()


def recommended_test(failure_class: str) -> str:
    mapping = {
        "approval_hallucination": "test_hallucinated_approval_card_triggers_repair_and_real_proposal",
        "path_intent_mismatch": "test_file_path_intent_corrects_wrong_relative_proposal",
        "provider_rate_limit": "test_provider_429_in_tool_loop_returns_chinese_error_not_nollm_fallback",
        "empty_llm_response": "test_empty_llm_response_triggers_repair_turn_and_can_generate_proposal",
        "gate_blocked": "add a focused gate-result recovery test for the blocked tool",
    }
    return mapping.get(failure_class, "add a minimal fake-LLM regression for the observed failure")


def repair_surface(failure_class: str) -> str:
    mapping = {
        "approval_hallucination": "EgoOperator approval-card detection and tool-loop repair branch",
        "path_intent_mismatch": "EgoOperator path-intent extraction/correction before file tools",
        "provider_rate_limit": "EgoOperator provider error recovery in the LLM tool loop",
        "empty_llm_response": "EgoOperator empty-response repair branch",
        "gate_blocked": "EgoOperator SafetyGate/tool result recovery messaging",
    }
    return mapping.get(failure_class, "unknown; inspect latest tool trace and prompt contract")


def build_failure_packet(text: str, *, candidate_issue: str = "") -> dict[str, Any]:
    prompt = latest_prompt(text)
    expected_path = first_path(prompt) or first_path(text)
    calls = observed_tool_calls(text)
    execution_match = EXECUTION_PATH_RE.search(text or "")
    execution_path = execution_match.group(1).replace("\\\\", "\\") if execution_match else ""
    approval_result = "ok" if APPROVAL_OK_RE.search(text or "") else "unknown"
    failure_class = classify_failure(text, expected_path, execution_path)
    return {
        "status": "ok",
        "prompt": prompt,
        "expected_path_or_action": expected_path,
        "observed_tool_calls": calls,
        "approval_result": approval_result,
        "execution_path": execution_path,
        "failure_class": failure_class,
        "candidate_issue": candidate_issue,
        "recommended_test": recommended_test(failure_class),
        "repair_surface": repair_surface(failure_class),
        "note": "packet is advisory; it must not be treated as proof without a deterministic regression or real-provider observation",
    }


def read_packet_input(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.log_file:
        return Path(args.log_file).read_text(encoding="utf-8")
    return sys.stdin.read()


def write_json(payload: dict[str, Any], stream: TextIO) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    stream.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EgoOperator developer-loop helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="Run EgoOperator verification tiers")
    verify.add_argument("mode", choices=["target", "full"])

    packet = subparsers.add_parser("packet", help="Build a human-trial failure packet from pasted logs")
    packet.add_argument("--log-file")
    packet.add_argument("--text")
    packet.add_argument("--candidate-issue", default="")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    runner: CommandRunner | None = None,
    stdout: TextIO | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    out = stdout or sys.stdout
    try:
        if args.command == "verify":
            payload = run_verify(args.mode, runner=runner or CommandRunner())
        elif args.command == "packet":
            payload = build_failure_packet(read_packet_input(args), candidate_issue=args.candidate_issue)
        else:
            raise ValueError(f"unknown command: {args.command}")
        write_json(payload, out)
        return 0 if payload.get("status") == "ok" else 1
    except Exception as exc:
        write_json({"status": "error", "error": type(exc).__name__, "message": str(exc)}, out)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
