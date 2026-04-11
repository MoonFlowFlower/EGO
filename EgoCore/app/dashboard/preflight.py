from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.telegram_runtime_result import TelegramTurnReply, TelegramTurnResult


PARITY_WINDOW_MESSAGES: tuple[str, ...] = (
    "你好",
    "我现在有点卡住了，你先帮我理一下",
    "继续",
    "你刚才为什么那样回答",
)

HOLD_PROBE_WINDOW_MESSAGES: tuple[str, ...] = (
    "先把这个点记着，等下再继续也行。",
)


def build_dashboard_preflight_scripts() -> List[Dict[str, Any]]:
    return [
        {"name": "parity_window", "messages": list(PARITY_WINDOW_MESSAGES)},
        {"name": "hold_probe_window", "messages": list(HOLD_PROBE_WINDOW_MESSAGES)},
    ]


@dataclass(frozen=True)
class _PreflightTurnFixture:
    reply_text: str
    preferred_mode: str
    preferred_tone: str
    suggested_next_step: str
    chat_cadence_mode: str
    social_policy_hints: Dict[str, Any]
    embodied_policy_hints: Dict[str, Any]
    integrated_policy_hints: Dict[str, Any]
    initiative_policy_hints: Dict[str, Any]
    chat_expression_hint: Dict[str, Any]
    host_proactive_candidate: Optional[Dict[str, Any]] = None
    queue_followup: bool = False


_FIXTURE_BY_TEXT: Dict[str, _PreflightTurnFixture] = {
    "你好": _PreflightTurnFixture(
        reply_text="我在。先把你卡住的点说出来，我帮你拆开。",
        preferred_mode="ask",
        preferred_tone="cautious",
        suggested_next_step="clarify_focus",
        chat_cadence_mode="reply_now_short",
        social_policy_hints={"boundary_mode": "warm"},
        embodied_policy_hints={},
        integrated_policy_hints={"selected_priority": "clarify"},
        initiative_policy_hints={},
        chat_expression_hint={"reply_mode": "short", "tone_profile": "steady"},
    ),
    "我现在有点卡住了，你先帮我理一下": _PreflightTurnFixture(
        reply_text="先别一下子求全。把你现在最卡的一步说清，我先帮你拆成两层。",
        preferred_mode="ask",
        preferred_tone="supportive",
        suggested_next_step="decompose_blocker",
        chat_cadence_mode="reply_now_expand",
        social_policy_hints={"repair_bias": "elevated"},
        embodied_policy_hints={"resource_bias": "conserve"},
        integrated_policy_hints={"selected_priority": "repair"},
        initiative_policy_hints={"initiative_priority": "hold"},
        chat_expression_hint={"reply_mode": "expand", "tone_profile": "supportive"},
    ),
    "继续": _PreflightTurnFixture(
        reply_text="继续可以，但我先盯住失败点。你上一轮最容易滑掉的是哪一步？",
        preferred_mode="repair",
        preferred_tone="grounded",
        suggested_next_step="surface_failure_point",
        chat_cadence_mode="reply_now_normal",
        social_policy_hints={"repair_bias": "elevated"},
        embodied_policy_hints={"stabilization_bias": "elevated"},
        integrated_policy_hints={"selected_priority": "repair"},
        initiative_policy_hints={"initiative_priority": "bounded"},
        chat_expression_hint={"reply_mode": "normal", "tone_profile": "grounded"},
    ),
    "你刚才为什么那样回答": _PreflightTurnFixture(
        reply_text="因为你当时更需要的是缩小问题，而不是继续扩话题。我在优先保住闭环。",
        preferred_mode="ask",
        preferred_tone="reflective",
        suggested_next_step="explain_reasoning",
        chat_cadence_mode="reply_now_normal",
        social_policy_hints={"boundary_mode": "explanatory"},
        embodied_policy_hints={},
        integrated_policy_hints={"selected_priority": "explain"},
        initiative_policy_hints={"initiative_priority": "bounded"},
        chat_expression_hint={"reply_mode": "normal", "tone_profile": "reflective"},
    ),
    "先把这个点记着，等下再继续也行。": _PreflightTurnFixture(
        reply_text="行，我先把这个点挂住，不在这轮硬推。等下我再接回来。",
        preferred_mode="defer",
        preferred_tone="calm",
        suggested_next_step="hold_for_followup",
        chat_cadence_mode="hold_for_followup",
        social_policy_hints={"repair_bias": "bounded"},
        embodied_policy_hints={"resource_bias": "conserve"},
        integrated_policy_hints={"selected_priority": "hold"},
        initiative_policy_hints={"initiative_priority": "followup"},
        chat_expression_hint={"reply_mode": "normal", "tone_profile": "calm"},
        host_proactive_candidate={
            "candidate_label": "dashboard_preflight_followup",
            "behavioral_authority": "none",
            "host_lane_hint": "host_proactive_outbox",
        },
        queue_followup=True,
    ),
}


class DeterministicDashboardPreflightRunner:
    async def run_turn(
        self,
        *,
        session_key: str,
        user_input: str,
        state,
        source: str = "api:dashboard",
        evidence_collector=None,
    ) -> TelegramTurnResult:
        fixture = _FIXTURE_BY_TEXT.get(user_input)
        if fixture is None:
            fixture = _PreflightTurnFixture(
                reply_text=f"收到：{user_input}",
                preferred_mode="ask",
                preferred_tone="cautious",
                suggested_next_step="clarify_focus",
                chat_cadence_mode="reply_now_normal",
                social_policy_hints={},
                embodied_policy_hints={},
                integrated_policy_hints={},
                initiative_policy_hints={},
                chat_expression_hint={"reply_mode": "normal", "tone_profile": "steady"},
            )

        proto_self_context = dict(getattr(state, "proto_self_context", None) or {})
        proto_self_context.update(
            {
                "policy_hint": {"guard_reason": "bounded_preflight"},
                "response_tendency": {
                    "preferred_mode": fixture.preferred_mode,
                    "preferred_tone": fixture.preferred_tone,
                    "suggested_next_step": fixture.suggested_next_step,
                    "ask_needed": fixture.preferred_mode in {"ask", "repair", "defer"},
                },
                "social_policy_hints": dict(fixture.social_policy_hints),
                "embodied_policy_hints": dict(fixture.embodied_policy_hints),
                "integrated_policy_hints": dict(fixture.integrated_policy_hints),
                "initiative_policy_hints": dict(fixture.initiative_policy_hints),
                "chat_cadence_mode": fixture.chat_cadence_mode,
                "host_proactive_candidate": dict(fixture.host_proactive_candidate or {}) or None,
            }
        )
        state.proto_self_context = proto_self_context
        state.task_status = "chat"
        state.waiting_for_user_input = False

        if fixture.queue_followup:
            state.push_proactive_outbox_event(
                {
                    "schema_version": "dashboard.preflight.outbox.v1",
                    "initiative_candidate_id": "dashboard-preflight-followup",
                    "outbox_lane": "host_proactive_outbox",
                    "outbox_status": "queued",
                    "reply_text": "我按你的节奏先挂起，稍后再接。",
                    "text_length": 15,
                    "delivery_kind": "chat",
                    "reply_authority": "model_chat",
                    "reply_origin": "proactive_followup",
                    "authority_source": "dashboard.preflight",
                    "chat_cadence_mode": fixture.chat_cadence_mode,
                    "response_tendency_summary": {
                        "preferred_mode": fixture.preferred_mode,
                        "preferred_tone": fixture.preferred_tone,
                        "suggested_next_step": fixture.suggested_next_step,
                        "chat_cadence_mode": fixture.chat_cadence_mode,
                    },
                    "chat_expression_hint": dict(fixture.chat_expression_hint),
                }
            )

        return TelegramTurnResult(
            status="chat",
            state=state,
            reply=TelegramTurnReply(
                reply_text=fixture.reply_text,
                delivery_kind="chat",
                status="chat",
                metadata={
                    "reply_authority": "model_chat",
                    "reply_origin": "chat_mainline",
                    "chat_expression_hint": dict(fixture.chat_expression_hint),
                    "response_tendency_summary": {
                        "preferred_mode": fixture.preferred_mode,
                        "preferred_tone": fixture.preferred_tone,
                        "suggested_next_step": fixture.suggested_next_step,
                        "chat_cadence_mode": fixture.chat_cadence_mode,
                    },
                    "social_policy_hints": dict(fixture.social_policy_hints),
                    "embodied_policy_hints": dict(fixture.embodied_policy_hints),
                    "integrated_policy_hints": dict(fixture.integrated_policy_hints),
                    "initiative_policy_hints": dict(fixture.initiative_policy_hints),
                    "host_proactive_candidate": dict(fixture.host_proactive_candidate or {}) or None,
                    "chat_cadence_mode": fixture.chat_cadence_mode,
                },
            ),
        )


def execute_dashboard_preflight(service: Any, *, session_name: str = "preflight-live-ingress") -> Dict[str, Any]:
    session = service.ensure_session(session_name)
    turn_records: List[Dict[str, Any]] = []
    for script in build_dashboard_preflight_scripts():
        for text in script["messages"]:
            payload = service.send_message(session.session_id, text)
            turn_records.append(
                {
                    "window": script["name"],
                    "user_text": text,
                    "payload": payload,
                }
            )
    session_payload = service.get_session_payload(session.session_id)
    return {
        "session_id": session.session_id,
        "session_name": session.session_name,
        "scripts": build_dashboard_preflight_scripts(),
        "turn_records": turn_records,
        "session_payload": session_payload,
    }


def build_dashboard_preflight_report(preflight_result: Dict[str, Any], *, git_commit_short: str) -> Dict[str, Any]:
    turn_records = list(preflight_result.get("turn_records") or [])
    assistant_turns: List[Dict[str, Any]] = []
    tendency_values = set()
    cadence_values = set()

    for item in turn_records:
        payload = dict(item.get("payload") or {})
        debug = dict(payload.get("debug") or {})
        response_plan = dict(debug.get("response_plan") or {})
        proto_self = dict(debug.get("proto_self") or {})
        runtime_reply_surface = dict(debug.get("runtime_reply_surface") or {})
        session_state = dict(payload.get("session_state") or {})
        assistant = payload.get("messages", {}).get("assistant")
        if not assistant:
            continue
        response_tendency = dict(proto_self.get("response_tendency") or {})
        richer_fields = {
            "social_policy_hints": dict(
                proto_self.get("social_policy_hints")
                or runtime_reply_surface.get("social_policy_hints")
                or {}
            ),
            "embodied_policy_hints": dict(
                proto_self.get("embodied_policy_hints")
                or runtime_reply_surface.get("embodied_policy_hints")
                or {}
            ),
            "integrated_policy_hints": dict(
                proto_self.get("integrated_policy_hints")
                or runtime_reply_surface.get("integrated_policy_hints")
                or {}
            ),
            "initiative_policy_hints": dict(
                proto_self.get("initiative_policy_hints")
                or runtime_reply_surface.get("initiative_policy_hints")
                or {}
            ),
        }
        cadence_mode = response_plan.get("chat_cadence_mode")
        if cadence_mode:
            cadence_values.add(str(cadence_mode))
        tendency_signature = (
            response_tendency.get("preferred_mode"),
            response_tendency.get("preferred_tone"),
            response_tendency.get("suggested_next_step"),
        )
        tendency_values.add(tendency_signature)
        assistant_turns.append(
            {
                "window": item.get("window"),
                "user_text": item.get("user_text"),
                "assistant_text": assistant.get("text"),
                "response_plan_kind": response_plan.get("kind"),
                "reply_authority": response_plan.get("reply_authority"),
                "reply_origin": response_plan.get("reply_origin")
                or (response_plan.get("metadata") or {}).get("reply_origin"),
                "chat_cadence_mode": cadence_mode,
                "subject_gate_ingress_ok": bool(((debug.get("subject_gate") or {}).get("ingress") or {}).get("ok")),
                "runtime_subject_finalize_ok": bool(
                    (((debug.get("subject_gate") or {}).get("runtime_finalized_result") or {}).get("ok"))
                ),
                "runtime_subject_response_plan_ok": bool(
                    (((debug.get("subject_gate") or {}).get("runtime_response_plan") or {}).get("ok"))
                ),
                "output_check_passed": bool((debug.get("output_check") or {}).get("passed")),
                "response_tendency": response_tendency,
                "richer_fields": richer_fields,
                "host_proactive_candidate_present": bool(
                    proto_self.get("host_proactive_candidate_present")
                    or runtime_reply_surface.get("host_proactive_candidate_present")
                ),
                "pending_proactive_outbox_count": int(session_state.get("pending_proactive_outbox_count") or 0),
                "debug": debug,
                "session_state": session_state,
            }
        )

    ordinary_chat_turns = [
        turn
        for turn in assistant_turns
        if turn["response_plan_kind"] == "chat" and turn["reply_authority"] == "model_chat"
    ]
    ordinary_chat_with_richer_fields = [
        turn
        for turn in ordinary_chat_turns
        if any(bool(value) for value in turn["richer_fields"].values())
    ]
    tendency_delta_present = len({value for value in tendency_values if any(part is not None for part in value)}) >= 2
    cadence_delta_present = len({value for value in cadence_values if value}) >= 2
    hold_for_followup_artifact = any(
        turn["chat_cadence_mode"] == "hold_for_followup"
        or turn["host_proactive_candidate_present"]
        or turn["pending_proactive_outbox_count"] > 0
        for turn in assistant_turns
    )
    subject_gate_all_ingress_ok = all(turn["subject_gate_ingress_ok"] for turn in assistant_turns)
    response_contract_present = all(
        turn["output_check_passed"] and turn["response_plan_kind"] is not None for turn in ordinary_chat_turns
    )
    no_raw_send_without_finalize = all(
        turn["runtime_subject_finalize_ok"] and turn["runtime_subject_response_plan_ok"]
        for turn in ordinary_chat_turns
    )
    acceptance_met = (
        bool(ordinary_chat_turns)
        and bool(ordinary_chat_with_richer_fields)
        and tendency_delta_present
        and (cadence_delta_present or hold_for_followup_artifact)
        and subject_gate_all_ingress_ok
        and response_contract_present
        and no_raw_send_without_finalize
    )

    return {
        "generated_at": preflight_result.get("session_payload", {}).get("session", {}).get("updated_at"),
        "git_commit_short": git_commit_short,
        "source": "dashboard_local_preflight",
        "claim_ceiling": "preflight_only",
        "runner_mode": "deterministic_dashboard_backend",
        "session_id": preflight_result.get("session_id"),
        "session_name": preflight_result.get("session_name"),
        "scripts": preflight_result.get("scripts") or [],
        "turn_records": turn_records,
        "transcript": preflight_result.get("session_payload", {}).get("transcript") or [],
        "session_state": preflight_result.get("session_payload", {}).get("session_state") or {},
        "assistant_turns": assistant_turns,
        "aggregate": {
            "ordinary_chat_mainline": len(ordinary_chat_turns),
            "ordinary_chat_with_richer_fields": len(ordinary_chat_with_richer_fields),
            "tendency_delta_present": tendency_delta_present,
            "cadence_delta_present": cadence_delta_present,
            "hold_for_followup_artifact": hold_for_followup_artifact,
            "subject_gate_all_ingress_ok": subject_gate_all_ingress_ok,
            "response_contract_present": response_contract_present,
            "no_raw_send_without_finalize": no_raw_send_without_finalize,
            "acceptance_met": acceptance_met,
        },
        "verdict": (
            "dashboard preflight passed"
            if acceptance_met
            else "dashboard preflight blocked: bounded ordinary-chat simulation still misses richer/tendency/cadence or contract signals"
        ),
        "remaining_gap": [
            "fresh real Telegram proof is still required",
            "dashboard preflight does not replace proactive/background transport proof",
            "dashboard preflight does not prove unexpected_subject_miss = 0 on live Telegram",
        ],
    }


def render_dashboard_preflight_markdown(report: Dict[str, Any]) -> str:
    aggregate = dict(report.get("aggregate") or {})
    lines = [
        "# Dashboard Chat Preflight",
        "",
        f"- source: `{report.get('source')}`",
        f"- claim_ceiling: `{report.get('claim_ceiling')}`",
        f"- git_commit_short: `{report.get('git_commit_short')}`",
        f"- session_id: `{report.get('session_id')}`",
        f"- verdict: `{report.get('verdict')}`",
        "",
        "## Aggregate",
        "",
        f"- ordinary_chat_mainline: `{aggregate.get('ordinary_chat_mainline')}`",
        f"- ordinary_chat_with_richer_fields: `{aggregate.get('ordinary_chat_with_richer_fields')}`",
        f"- tendency_delta_present: `{aggregate.get('tendency_delta_present')}`",
        f"- cadence_delta_present: `{aggregate.get('cadence_delta_present')}`",
        f"- hold_for_followup_artifact: `{aggregate.get('hold_for_followup_artifact')}`",
        f"- subject_gate_all_ingress_ok: `{aggregate.get('subject_gate_all_ingress_ok')}`",
        f"- response_contract_present: `{aggregate.get('response_contract_present')}`",
        f"- no_raw_send_without_finalize: `{aggregate.get('no_raw_send_without_finalize')}`",
        f"- acceptance_met: `{aggregate.get('acceptance_met')}`",
        "",
        "## Assistant Turns",
        "",
    ]
    for turn in list(report.get("assistant_turns") or []):
        tendency = dict(turn.get("response_tendency") or {})
        lines.extend(
            [
                f"### `{turn.get('window')}` / `{turn.get('user_text')}`",
                f"- reply_authority: `{turn.get('reply_authority')}`",
                f"- response_plan_kind: `{turn.get('response_plan_kind')}`",
                f"- chat_cadence_mode: `{turn.get('chat_cadence_mode')}`",
                f"- tendency: `{tendency}`",
                f"- richer_fields_present: `{any(bool(value) for value in (turn.get('richer_fields') or {}).values())}`",
                f"- runtime_subject_finalize_ok: `{turn.get('runtime_subject_finalize_ok')}`",
                f"- runtime_subject_response_plan_ok: `{turn.get('runtime_subject_response_plan_ok')}`",
                f"- host_proactive_candidate_present: `{turn.get('host_proactive_candidate_present')}`",
                f"- pending_proactive_outbox_count: `{turn.get('pending_proactive_outbox_count')}`",
                f"- assistant_text: {turn.get('assistant_text')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Remaining Gap",
            "",
            *[f"- {item}" for item in list(report.get("remaining_gap") or [])],
            "",
        ]
    )
    return "\n".join(lines)
