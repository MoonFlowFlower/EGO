from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import agent_base as agent
from memory_system import MemoryCompactor, OperatorMemoryStore


class CapturePromptLLM:
    provider = "fake"
    model = "capture"
    last_usage = {}
    last_reasoning_tokens = None

    def __init__(self) -> None:
        self.system_prompts = []
        self.seen_tools = []

    def chat(self, messages, *, system_prompt, policy_context="", tools=None, stream=None):
        self.system_prompts.append(system_prompt)
        self.seen_tools.append(tools or [])
        return agent.LLMChatResult(content="收到。", tool_calls=[])

    def complete(self, prompt, messages=None):
        self.system_prompts.append(prompt)
        return "收到。"


class BadCompactionLLM:
    def complete(self, prompt):
        return "not-json"


def test_cli_memory_default_on_writes_only_after_first_turn(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "EGO_HANDMADE_ROOT", tmp_path)
    memory_dir = tmp_path / "memory"
    runtime = agent.build_demo_runtime(enable_operator_memory=True, operator_memory_dir=memory_dir)
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")

    assert runtime.operator_memory_enabled() is True
    assert not memory_dir.exists()

    runtime.handle_user_message("你好，记一下上下文")

    assert (memory_dir / "history.jsonl").exists()
    assert (memory_dir / "telemetry" / "tokens.jsonl").exists()
    token_row = json.loads((memory_dir / "telemetry" / "tokens.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert token_row["approximate"] is True


def test_disabled_operator_memory_does_not_create_memory_dir(tmp_path):
    memory_dir = tmp_path / "memory"
    runtime = agent.build_demo_runtime(enable_operator_memory=False)
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")

    runtime.handle_user_message("hello")

    assert not memory_dir.exists()


def test_operator_memory_jsonl_preserves_utf8(tmp_path):
    store = OperatorMemoryStore(tmp_path / "memory", containment_root=tmp_path)

    store.append_raw_turn(session_id="s1", role="user", content="你好，记忆系统")

    raw = (tmp_path / "memory" / "history.jsonl").read_text(encoding="utf-8")
    row = json.loads(raw)
    assert row["content"] == "你好，记忆系统"
    assert "ä½" not in raw


def test_operator_memory_path_containment_blocks_escape(tmp_path):
    root = tmp_path / "root"
    outside = tmp_path / "outside" / "memory"

    with pytest.raises(ValueError, match="outside Ego_handmade workspace"):
        OperatorMemoryStore(outside, containment_root=root)


def test_core_memory_injected_as_candidate_local_context(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "EGO_HANDMADE_ROOT", tmp_path)
    runtime = agent.build_demo_runtime(enable_operator_memory=True, operator_memory_dir=tmp_path / "memory")
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")
    capture = CapturePromptLLM()
    runtime.planner.llm = capture

    result = runtime.remember_operator_note("用户偏好：中文、结论先行")
    assert result["status"] == "ok"

    runtime.handle_user_message("继续")

    prompt = capture.system_prompts[-1]
    assert "candidate-local Ego_handmade operator memory" in prompt
    assert "用户偏好：中文、结论先行" in prompt
    assert "PROGRAM_STATE_UNIFIED" not in prompt


def test_remember_gate_writes_core_and_normal_turn_does_not_overwrite(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "EGO_HANDMADE_ROOT", tmp_path)
    runtime = agent.build_demo_runtime(enable_operator_memory=True, operator_memory_dir=tmp_path / "memory")
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")
    runtime.planner.llm = CapturePromptLLM()

    result = runtime.remember_operator_note("稳定偏好：不要自动提升 claim ceiling")
    assert result["status"] == "ok"
    before = runtime.operator_memory.load_core()

    runtime.handle_user_message("普通对话不应该直接改 core memory")

    assert runtime.operator_memory.load_core() == before


def test_llm_exposes_only_gated_candidate_local_memory_write_tool(tmp_path, monkeypatch):
    monkeypatch.setattr(agent, "EGO_HANDMADE_ROOT", tmp_path)
    runtime = agent.build_demo_runtime(enable_operator_memory=True, operator_memory_dir=tmp_path / "memory")
    runtime.trace_store = agent.JsonlTraceStore(tmp_path / "trace.jsonl")
    capture = CapturePromptLLM()
    runtime.planner.llm = capture

    runtime.handle_user_message("看一下可用工具")

    offered = {
        schema["function"]["name"]
        for call_tools in capture.seen_tools
        for schema in call_tools
    }
    assert "remember_note" in offered
    assert "remember" not in offered
    assert "write_memory" not in offered
    assert "operator_memory" not in offered


def test_compaction_keeps_last_ten_writes_episode_and_preserves_raw(tmp_path):
    store = OperatorMemoryStore(tmp_path / "memory", containment_root=tmp_path)
    store.append_raw_turn(session_id="s1", role="user", content="原始对话不能删除")
    before_raw = store.history_file.read_text(encoding="utf-8")
    messages = [
        {"role": "user" if idx % 2 == 0 else "assistant", "content": f"消息{idx}"}
        for idx in range(12)
    ]
    compactor = MemoryCompactor(store, keep_last=10)

    result = compactor.compact(messages, session_id="s1", event_id="evt1", force=True)

    assert result["status"] == "compacted"
    assert len(result["kept_messages"]) == 10
    assert store.episode_path().exists()
    assert "消息0" in store.episode_path().read_text(encoding="utf-8")
    assert store.history_file.read_text(encoding="utf-8").startswith(before_raw)
    assert store.candidate_core_updates_file.exists()
    assert not store.core_file.exists()


def test_malformed_llm_compaction_records_structured_error(tmp_path):
    store = OperatorMemoryStore(tmp_path / "memory", containment_root=tmp_path)
    messages = [{"role": "user", "content": f"消息{idx}"} for idx in range(12)]
    compactor = MemoryCompactor(store, keep_last=10)

    result = compactor.compact(
        messages,
        session_id="s1",
        event_id="evt_bad",
        force=True,
        llm=BadCompactionLLM(),
    )

    assert result["status"] == "error"
    assert result["reason"] == "malformed_compaction_output"
    row = json.loads(store.candidate_core_updates_file.read_text(encoding="utf-8").splitlines()[0])
    assert row["status"] == "error"
    assert row["error"]["error_type"] in {"JSONDecodeError", "ValueError", "KeyError"}
    assert not store.episode_path().exists()
