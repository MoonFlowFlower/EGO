from __future__ import annotations

from pathlib import Path

from app.agent_core.native_loop import NativeToolCallingLoop
from app.llm_client import LLMResponse


class FakeLLMClient:
    def chat_with_tools(self, messages, tools, **kwargs):
        return LLMResponse(
            content="",
            model="fake",
            provider="fake",
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "name": "file",
                    "arguments": {
                        "operation": "write",
                        "path": kwargs["messages_target_path"] if "messages_target_path" in kwargs else "",
                        "content": "<!DOCTYPE html><html><body>EgoCore</body></html>",
                    },
                }
            ],
        )

    def generate_with_messages(self, messages, **kwargs):
        return LLMResponse(
            content="页面已创建。",
            model="fake",
            provider="fake",
        )


def test_native_loop_returns_contract_and_verification(monkeypatch, tmp_path):
    target = tmp_path / "egocore_intro.html"

    client = FakeLLMClient()
    loop = NativeToolCallingLoop(llm_client=client)

    def fake_chat_with_tools(messages, tools, **kwargs):
        return LLMResponse(
            content="",
            model="fake",
            provider="fake",
            tool_calls=[
                {
                    "id": "call_1",
                    "type": "function",
                    "name": "file",
                    "arguments": {
                        "operation": "write",
                        "path": str(target),
                        "content": "<!DOCTYPE html><html><body>EgoCore</body></html>",
                    },
                }
            ],
        )

    monkeypatch.setattr(client, "chat_with_tools", fake_chat_with_tools)
    monkeypatch.setattr(
        "app.agent_core.contract_runtime.execute_tool",
        lambda *args, **kwargs: type(
            "ToolExecution",
            (),
            {
                "to_dict": lambda self: {
                    "success": True,
                    "output": "ok",
                    "error": None,
                    "status": "success",
                    "metadata": {"path": str(target)},
                    "execution_time_ms": 1.0,
                }
            },
        )(),
    )
    target.write_text("<!DOCTYPE html><html><body>EgoCore</body></html>", encoding="utf-8")

    result = loop.run_turn(
        session_key="telegram:dm:1",
        user_input=f"请在 {target} 创建介绍 EgoCore 的 html 页面",
        ingress_context={
            "runtime_action": "execute_task",
            "requested_output": {
                "effective_path": str(target),
                "target_path": str(target),
                "format": "html",
                "topic": "EgoCore",
            },
        },
        proto_self_context=None,
    )

    import asyncio

    result = asyncio.run(result)

    assert result.task_contract is not None
    assert result.next_step_decision is not None
    assert result.verification_result is not None
    assert result.verification_result["expected_signal_matched"] is True
    assert "页面已创建" in result.reply_text
