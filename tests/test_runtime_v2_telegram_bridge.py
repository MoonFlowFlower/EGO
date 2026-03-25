from app.runtime_v2 import RuntimeV2TelegramBridge
from app.runtime_v2.state import RuntimeV2State


def test_telegram_bridge_path_is_reference_material():
    """
    路径应被识别为 reference_material，不等于自动执行。
    
    这是设计合同的正确行为：
    - 显式路径默认为 reference_material
    - 只有语义明确请求执行时才是 task_request
    - heuristic parser 不处理自然语言语义
    """
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    decision = bridge.inspect_ingress("/home/moonlight/test.html 配色不太好看,你换一个好看的颜色", state)
    
    # 路径被识别为 reference_material
    assert decision.looks_like_task is False
    assert decision._parsed_intent_graph.primary_intent == "reference_material"
    assert decision._parsed_intent_graph.requires_clarification is True
    assert decision.ack_text is None  # 不再发送 generic ACK
    
    # runtime action 应该是 waiting_input
    assert decision._runtime_action == "waiting_input"


def test_telegram_bridge_short_probe_requires_async():
    """
    短探针识别需要 LLM 语义解析（async 版本）。
    
    同步版本（heuristic parser）不处理自然语言语义。
    这是设计合同的正确行为：heuristic 只处理显式硬信号。
    """
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    state.task_status = "running"
    state.current_goal = "修改 hello.html 配色"
    
    # 同步版本不识别自然语言
    decision = bridge.inspect_ingress("还在吗", state)
    assert decision.is_short_probe is False  # heuristic 不识别


def test_telegram_bridge_marks_challenge_turn_requires_async():
    """
    挑战轮次识别需要 LLM 语义解析（async 版本）。
    """
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    state.task_status = "running"
    state.current_goal = "修改 hello.html 配色"
    
    # 同步版本不识别自然语言
    decision = bridge.inspect_ingress("你没改啊", state)
    assert decision.is_challenge_turn is False  # heuristic 不识别


def test_telegram_bridge_discussion_not_task():
    """heuristic parser 只处理显式硬信号。讨论性句式需要 LLM 识别。"""
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    
    decision = bridge.inspect_ingress("你觉得要怎么实现比较好？", state)
    assert decision.looks_like_task is False
    assert decision.ack_text is None


def test_telegram_bridge_explicit_command():
    """显式命令应该被 heuristic 识别为 task_request"""
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    decision = bridge.inspect_ingress("/status", state)
    assert decision.looks_like_task is True
    assert decision._parsed_intent_graph.primary_intent == "task_request"


def test_telegram_bridge_attachment_is_reference_material():
    """附件应该被识别为 reference_material"""
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    decision = bridge.inspect_ingress("[用户发送了文件: test.html]", state)
    
    assert decision.looks_like_task is False
    assert decision._parsed_intent_graph.primary_intent == "reference_material"
    assert decision._parsed_intent_graph.requires_clarification is True


def test_telegram_bridge_chat_default():
    """普通聊天应该被识别为 chat"""
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    decision = bridge.inspect_ingress("你好", state)
    
    assert decision.looks_like_task is False
    assert decision._parsed_intent_graph.primary_intent == "chat"
