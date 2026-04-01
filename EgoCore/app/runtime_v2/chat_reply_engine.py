from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import ConfigError, get_config
from app.llm_client import get_llm_client
from app.response_contract.memory_claim_gate import evaluate_memory_claim
from app.restore_runtime import PendingRestoreObservation

from .chat_state import normalize_chat_reply
from .runtime_reply import RuntimeV2Reply, RuntimeV2TurnResult
from .state import RuntimeV2State

logger = logging.getLogger(__name__)


CHAT_MAINLINE_SYSTEM_PROMPT = """你是 EgoCore runtime_v2 的 chat mainline。
你的职责只有一件事：对普通聊天生成自然语言回复。

硬规则：
1. 这是普通聊天，不输出 JSON，不调用工具，不编造执行结果。
2. 不要主动把聊天拉回任务，不要说“请说任务/请说任务内容/开始任务”，除非用户明确要求进入任务。
3. 如果当前 turn 是 presence_check / social_keepalive，就自然回应“我在/我看到了你”，但不要机械复读。
4. 如果用户在抱怨重复、语气或说辞，先吸收这个反馈，再自然回应，不要辩解。
5. 不要回放旧的目录正文、文件内容、工具输出或任务总结，除非用户明确在追问那条证据。
6. 允许简短，但要像人在聊天，不像控制面固定模板。
7. 当前若存在 active task，它只作为背景信息，不是你必须提起的主题。
8. 回复 1 到 2 句，默认简洁。
9. 如果当前没有明确 restore authority，不要声称“已经恢复成功”“还记得用户”“跨对话持续记忆已经就绪”；此时自然回答当下互动即可。
"""


class ChatReplyEngine:
    def __init__(self) -> None:
        self.llm_client = None

    async def reply(self, state: RuntimeV2State) -> RuntimeV2TurnResult:
        ingress = dict(state.ingress_context or {})
        chat_act = str(ingress.get("conversation_act") or "light_chitchat").strip() or "light_chitchat"
        restore_observation = _resolve_restore_observation(state)
        state.prepare_chat_turn(user_text=state.last_user_turn or "", chat_act=chat_act)

        try:
            candidate = await self._generate_reply(state)
            if self._should_regenerate(candidate, state, chat_act):
                candidate = await self._generate_reply(
                    state,
                    extra_system_hint=(
                        "上一条候选与最近回复完全重复。保持同语义，但换一种自然说法；"
                        "不要拉回任务，不要回放旧证据。"
                    ),
                )
            if _should_regenerate_for_memory_claim(candidate, restore_observation):
                candidate = await self._generate_reply(
                    state,
                    extra_system_hint=_build_memory_claim_regeneration_hint(chat_act),
                )
            reply_text = str(candidate or "").strip()
            if not reply_text:
                raise RuntimeError("empty_chat_reply")
            reply_authority = "model_chat"
        except Exception as exc:
            logger.warning("runtime_v2.chat_mainline.degraded err=%s", exc)
            reply_text = "我在。刚才聊天生成出了点问题，你可以继续说。"
            reply_authority = "host_degraded_fallback"

        state.finalize_chat_turn(assistant_reply=reply_text, chat_act=chat_act)
        state.last_model_action = {
            "type": "chat",
            "message": reply_text,
            "chat_act": chat_act,
            "reply_authority": reply_authority,
        }
        state.record(
            "assistant",
            {
                "type": "chat_reply",
                "text": reply_text,
                "chat_act": chat_act,
                "reply_authority": reply_authority,
                "reply_origin": "chat_mainline",
            },
        )
        state.last_delivery_type = "chat"
        return RuntimeV2TurnResult(
            status="chat",
            state=state,
            reply=RuntimeV2Reply(
                reply_text=reply_text,
                delivery_kind="chat",
                status="chat",
                metadata={
                    "chat_act": chat_act,
                    "reply_origin": "chat_mainline",
                    "reply_authority": reply_authority,
                },
            ),
            finish_reason="chat_mainline",
        )

    async def _generate_reply(self, state: RuntimeV2State, *, extra_system_hint: Optional[str] = None) -> str:
        messages = self._build_messages(state, extra_system_hint=extra_system_hint)
        response = await self._generate_with_fallback(
            messages,
            temperature=self._resolve_temperature(),
            max_tokens=self._resolve_max_tokens(),
            timeout_seconds=self._resolve_timeout_seconds(),
        )
        if response.usage:
            prompt_tokens = response.usage.get("prompt_tokens", 0) or response.usage.get("input_tokens", 0)
            completion_tokens = response.usage.get("completion_tokens", 0) or response.usage.get("output_tokens", 0)
            state.record_token_usage(prompt_tokens, completion_tokens)
        return str(response.content or "").strip()

    def _build_messages(self, state: RuntimeV2State, *, extra_system_hint: Optional[str] = None) -> List[Dict[str, str]]:
        context = state.to_chat_prompt_context()
        relationship = dict(context.get("relationship_context") or {})
        style = dict(context.get("style_profile") or {})
        proto_self = dict(context.get("proto_self_context") or {})
        tendency = dict(proto_self.get("response_tendency") or {})
        policy_hint = dict(proto_self.get("policy_hint") or {})

        system_prompt = CHAT_MAINLINE_SYSTEM_PROMPT
        if extra_system_hint:
            system_prompt += "\n" + extra_system_hint.strip() + "\n"

        payload = {
            "chat_context": {
                "conversation_act": context.get("conversation_act") or "light_chitchat",
                "last_user_turn": context.get("last_user_turn"),
                "recent_user_turns": context.get("recent_user_turns") or [],
                "recent_assistant_replies": context.get("recent_assistant_replies") or [],
                "last_user_tone_feedback": context.get("last_user_tone_feedback"),
                "active_task_summary": context.get("active_task_summary"),
            },
            "relationship_context": {
                "conversation_temperature": relationship.get("conversation_temperature"),
                "current_social_arc": relationship.get("current_social_arc"),
                "last_user_feedback_about_tone": relationship.get("last_user_feedback_about_tone"),
                "recent_social_modes": list((relationship.get("recent_social_modes") or [])[-4:]),
            },
            "style_profile": {
                "dimensions": style.get("dimensions") or {},
                "preferred_markers": style.get("preferred_markers") or [],
                "avoid_markers": style.get("avoid_markers") or [],
            },
            "proto_self_context": {
                "subject_profile": proto_self.get("subject_profile"),
                "response_tendency": tendency,
                "policy_hint": {
                    "subject_profile": policy_hint.get("subject_profile"),
                    "ask_preferred": policy_hint.get("ask_preferred"),
                    "closure_bias": policy_hint.get("closure_bias"),
                    "risk_bias": policy_hint.get("risk_bias"),
                },
            },
            "memory_claim_contract": _build_memory_claim_contract(state),
            "reply_rules": {
                "do_not_task_bridge_by_default": True,
                "do_not_replay_evidence": True,
                "anti_repeat_window": list(state.get_chat_state().recent_assistant_replies[-3:]),
            },
        }
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "基于下面结构化上下文直接回复用户。不要解释规则，不要输出 JSON。\n\n"
                    + json.dumps(payload, ensure_ascii=False, indent=2)
                ),
            },
        ]

    def _should_regenerate(self, reply_text: str, state: RuntimeV2State, chat_act: str) -> bool:
        if chat_act not in {"presence_check", "social_keepalive"}:
            return False
        normalized = normalize_chat_reply(reply_text)
        if not normalized:
            return False
        return normalized in state.get_chat_state().recent_normalized_replies(limit=3)

    def _resolve_chat_use_case(self) -> Dict[str, Any]:
        config = get_config()
        return config.get_llm_config_for_use_case("chat")

    def _resolve_temperature(self) -> float:
        try:
            use_case = self._resolve_chat_use_case()
            return float(use_case.get("temperature") or 0.8)
        except (ConfigError, TypeError, ValueError):
            return 0.8

    def _resolve_max_tokens(self) -> int:
        try:
            use_case = self._resolve_chat_use_case()
            return int(use_case.get("max_tokens") or 400)
        except (ConfigError, TypeError, ValueError):
            return 400

    def _resolve_timeout_seconds(self) -> int:
        try:
            config = get_config()
            request_cfg = config.llm.get("request") or {}
            return max(30, int(request_cfg.get("timeout") or 60))
        except (ConfigError, TypeError, ValueError):
            return 60

    def _resolve_primary_spec(self) -> Tuple[str, str]:
        config = get_config()
        use_case = config.get_llm_config_for_use_case("chat")
        provider = use_case.get("provider") or config.llm.get("default_provider", "qianfan")
        model = use_case.get("model") or config.llm.get("default_model", "glm-5")
        return str(provider), str(model)

    def _resolve_provider_default_model(self, provider: str) -> Optional[str]:
        config = get_config()
        provider_cfg = (config.llm.get("providers") or {}).get(provider) or {}
        if provider_cfg.get("enabled") is False:
            return None
        for item in provider_cfg.get("models") or []:
            model_id = item.get("id")
            if model_id:
                return str(model_id)
        return None

    def _resolve_chat_client_specs(self) -> List[Tuple[str, str]]:
        primary_provider, primary_model = self._resolve_primary_spec()
        specs: List[Tuple[str, str]] = [(primary_provider, primary_model)]
        config = get_config()
        fallback_cfg = config.llm.get("fallback") or {}
        if not fallback_cfg.get("enabled"):
            return specs
        for provider in fallback_cfg.get("providers") or []:
            provider_name = str(provider)
            if provider_name == primary_provider:
                continue
            model = self._resolve_provider_default_model(provider_name)
            if model:
                specs.append((provider_name, model))
        return specs

    def _resolve_clients(self) -> List[Tuple[str, str, object]]:
        if self.llm_client is not None:
            return [("injected", "injected", self.llm_client)]
        clients: List[Tuple[str, str, object]] = []
        for provider, model in self._resolve_chat_client_specs():
            try:
                clients.append((provider, model, get_llm_client(provider=provider, model=model)))
            except Exception as exc:
                logger.warning(
                    "runtime_v2.chat.client_unavailable provider=%s model=%s err=%s",
                    provider,
                    model,
                    exc,
                )
        return clients

    def _is_transient_error(self, error: Exception) -> bool:
        if isinstance(error, httpx.HTTPStatusError):
            response = getattr(error, "response", None)
            status_code = getattr(response, "status_code", None)
            return status_code in {408, 429, 500, 502, 503, 504}
        return isinstance(error, (httpx.TimeoutException, httpx.NetworkError, TimeoutError, ConnectionError))

    def _is_auth_or_config_error(self, error: Exception) -> bool:
        if isinstance(error, ValueError):
            return True
        if isinstance(error, httpx.HTTPStatusError):
            response = getattr(error, "response", None)
            status_code = getattr(response, "status_code", None)
            return status_code in {401, 403}
        return False

    async def _generate_with_fallback(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        timeout_seconds: int,
    ):
        candidates = self._resolve_clients()
        if not candidates:
            raise RuntimeError("No configured chat providers are available")

        primary_error: Optional[Exception] = None
        last_error: Optional[Exception] = None
        for index, (provider, model, client) in enumerate(candidates):
            try:
                return await asyncio.to_thread(
                    client.generate_with_messages,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout_seconds,
                )
            except Exception as exc:
                last_error = exc
                is_primary = index == 0
                if is_primary:
                    primary_error = exc
                    if not self._is_transient_error(exc):
                        raise
                    if index + 1 >= len(candidates):
                        raise
                    next_provider, next_model, _ = candidates[index + 1]
                    logger.warning(
                        "runtime_v2.chat.transient provider=%s model=%s fallback_provider=%s fallback_model=%s err=%s",
                        provider,
                        model,
                        next_provider,
                        next_model,
                        exc,
                    )
                    continue

                if self._is_auth_or_config_error(exc) or self._is_transient_error(exc):
                    logger.warning(
                        "runtime_v2.chat.fallback_skipped provider=%s model=%s err=%s",
                        provider,
                        model,
                        exc,
                    )
                    continue
                continue

        if primary_error is not None:
            raise primary_error
        if last_error is not None:
            raise last_error
        raise RuntimeError("Runtime v2 chat fallback exhausted without candidates")


def _resolve_restore_observation(state: RuntimeV2State) -> Optional[PendingRestoreObservation]:
    ingress = dict(state.ingress_context or {})
    payload = ingress.get("restore_observation")
    if isinstance(payload, PendingRestoreObservation):
        return payload
    if isinstance(payload, dict) and payload.get("restore_status"):
        return PendingRestoreObservation(**payload)
    return None


def _should_regenerate_for_memory_claim(
    reply_text: str,
    restore_observation: Optional[PendingRestoreObservation],
) -> bool:
    verdict = evaluate_memory_claim(reply_text, restore_observation=restore_observation)
    return verdict.claim_detected and not verdict.allowed


def _build_memory_claim_regeneration_hint(chat_act: str) -> str:
    if chat_act == "presence_check":
        return (
            "上一条候选越界声称了已恢复或记住用户。请直接自然回应你现在在线、在回应对方，"
            "但不要声称“已恢复成功”“还记得你”“我记得你”。不要解释规则，不要回避。"
        )
    return (
        "上一条候选越界声称了已恢复、记住用户或跨对话持续记忆。请改写为自然聊天，"
        "只回应当下互动，不要声称“已恢复成功”“还记得你”“我记得你”。"
        "可以表达你此刻在线、在认真回应、愿意继续聊。"
    )


def _build_memory_claim_contract(state: RuntimeV2State) -> Dict[str, Any]:
    ingress = dict(state.ingress_context or {})
    restore_payload = ingress.get("restore_observation")
    restore_status: Optional[str] = None
    restore_authority = False
    if isinstance(restore_payload, dict):
        restore_status = str(restore_payload.get("restore_status") or "").strip() or None
        restore_authority = restore_status in {"success", "partial"}
    return {
        "restore_authority_available": restore_authority,
        "restore_status": restore_status,
        "disallow_claiming_restore_or_cross_session_memory": not restore_authority,
        "safe_alternative": "自然回应当下互动，表达此刻在线、在认真回应、可以继续聊。",
    }
