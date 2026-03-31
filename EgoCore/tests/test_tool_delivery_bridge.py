from app.tools.delivery_bridge import build_tool_delivery_bridge_decision


def test_tool_delivery_bridge_marks_successful_path_write_as_delivery_ready() -> None:
    decision = build_tool_delivery_bridge_decision(
        {
            "success": True,
            "tool": "file",
            "stdout": "wrote file",
            "metadata": {"path": r"D:\Project\AIProject\MyProject\Test2\demo.txt"},
        },
        reply_text="已写入 demo.txt。",
        delivery_kind="final",
        source="runtime_v2",
    )

    assert decision is not None
    assert decision.requires_user_delivery is True
    assert decision.delivery_ready is True
    assert decision.delivery_gap is False
    assert decision.target_path == r"D:\Project\AIProject\MyProject\Test2\demo.txt"


def test_tool_delivery_bridge_detects_delivery_gap_for_success_without_reply() -> None:
    decision = build_tool_delivery_bridge_decision(
        {
            "success": True,
            "tool": "file",
            "stdout": "wrote file",
            "metadata": {"path": r"D:\Project\AIProject\MyProject\Test2\demo.txt"},
        },
        reply_text="",
        delivery_kind="final",
        source="runtime_v2",
    )

    assert decision is not None
    assert decision.requires_user_delivery is True
    assert decision.delivery_ready is False
    assert decision.delivery_gap is True
