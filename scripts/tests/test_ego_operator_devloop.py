from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "ego_operator_devloop.py"
spec = importlib.util.spec_from_file_location("ego_operator_devloop", MODULE_PATH)
ego_operator_devloop = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = ego_operator_devloop
spec.loader.exec_module(ego_operator_devloop)


class FakeRunner(ego_operator_devloop.CommandRunner):
    def __init__(self, returncodes: list[int]) -> None:
        self.returncodes = list(returncodes)
        self.calls: list[tuple[list[str], dict[str, str] | None]] = []

    def run(self, command: list[str], *, env: dict[str, str] | None = None):
        self.calls.append((command, env))
        returncode = self.returncodes.pop(0) if self.returncodes else 0
        return ego_operator_devloop.CommandResult(
            label="",
            command=command,
            returncode=returncode,
            elapsed_seconds=0.01,
            stdout_tail="ok" if returncode == 0 else "failed",
            stderr_tail="" if returncode == 0 else "boom",
        )


def run_cli(argv: list[str], *, runner: FakeRunner | None = None) -> tuple[int, dict]:
    out = io.StringIO()
    code = ego_operator_devloop.main(argv, runner=runner, stdout=out)
    return code, json.loads(out.getvalue())


def test_target_verify_runs_fast_tier_and_allows_local_closeout() -> None:
    runner = FakeRunner([0, 0])

    code, payload = run_cli(["verify", "target"], runner=runner)

    assert code == 0
    assert payload["status"] == "ok"
    assert payload["mode"] == "target"
    assert payload["allow_claim_closeout"] is True
    assert [entry["label"] for entry in payload["commands"]] == ["py_compile", "targeted_pytest"]
    assert len(runner.calls) == 2


def test_full_verify_stops_on_failure_and_blocks_closeout_claim() -> None:
    runner = FakeRunner([0, 1, 0])

    code, payload = run_cli(["verify", "full"], runner=runner)

    assert code == 1
    assert payload["status"] == "failed"
    assert payload["allow_claim_closeout"] is False
    assert [entry["label"] for entry in payload["commands"]] == ["py_compile", "ego_operator_tests"]
    assert len(runner.calls) == 2


def test_packet_classifies_path_intent_mismatch_and_extracts_tools() -> None:
    log = r'''> 在D:\Project\AIProject\MyProject\Test3创建一个测试网页
[执行工具]: propose_file_write {"path": "Test/index.html", "content": "x"}
"execution": {"status": "ok", "path": "D:\\Project\\AIProject\\MyProject\\Ego\\EgoOperator\\Test\\index.html"}
'''

    code, payload = run_cli(["packet", "--text", log, "--candidate-issue", "#13"])

    assert code == 0
    assert payload["status"] == "ok"
    assert payload["prompt"] == r"在D:\Project\AIProject\MyProject\Test3创建一个测试网页"
    assert payload["expected_path_or_action"] == r"D:\Project\AIProject\MyProject\Test3"
    assert payload["observed_tool_calls"][0]["tool"] == "propose_file_write"
    assert payload["failure_class"] == "path_intent_mismatch"
    assert payload["candidate_issue"] == "#13"
    assert "path-intent" in payload["repair_surface"]


def test_packet_classifies_approval_hallucination() -> None:
    log = "模型刚才生成了待审批文本，但 runtime 没有对应的真实 proposal，所以我没有把它当成可批准操作。"

    code, payload = run_cli(["packet", "--text", log])

    assert code == 0
    assert payload["failure_class"] == "approval_hallucination"
    assert payload["recommended_test"] == "test_hallucinated_approval_card_triggers_repair_and_real_proposal"
