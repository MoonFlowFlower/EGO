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


def test_telegram_bridge_short_probe_is_programmatic_status_query():
    """短探针应由程序化入口直接识别，避免前置 parser LLM。"""
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    state.task_status = "running"
    state.current_goal = "修改 hello.html 配色"

    decision = bridge.inspect_ingress("还在吗", state)
    assert decision.is_short_probe is True
    assert decision._runtime_action == "return_runtime_status"
    assert decision._parsed_intent_graph.primary_intent == "status_query"


def test_telegram_bridge_presence_probe_when_idle_falls_back_to_chat():
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    decision = bridge.inspect_ingress("在吗", state)
    assert decision.is_short_probe is False
    assert decision._runtime_action == "chat"
    assert decision._parsed_intent_graph.primary_intent == "chat"


def test_telegram_bridge_marks_challenge_turn_programmatically():
    """挑战轮次应由程序化入口直接识别，避免前置 parser LLM。"""
    bridge = RuntimeV2TelegramBridge()
    state = RuntimeV2State(session_id="telegram:dm:1")
    state.task_status = "running"
    state.current_goal = "修改 hello.html 配色"

    decision = bridge.inspect_ingress("你没改啊", state)
    assert decision.is_challenge_turn is True
    assert decision._runtime_action == "repair_or_reframe"
    assert decision._parsed_intent_graph.primary_intent == "correction"


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
