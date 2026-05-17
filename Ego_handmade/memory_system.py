"""
Candidate-local operator memory for Ego_handmade.

This module is deliberately scoped to Ego_handmade. It is not the EGO formal
memory authority and must not write PROJECT_MEMORY, OpenEmotion memory, or the
repo evidence ledger.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import json


DEFAULT_CORE_MAX_CHARS = 3000
DEFAULT_EPISODE_MAX_CHARS = 3000
DEFAULT_KEEP_LAST_MESSAGES = 10
DEFAULT_MAX_CONTEXT_TOKENS = 200_000
DEFAULT_COMPACTION_THRESHOLD = 0.7


Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now(clock: Clock) -> str:
    return clock().astimezone(timezone.utc).isoformat(timespec="seconds")


def _date_key(clock: Clock) -> str:
    return clock().astimezone(timezone.utc).strftime("%Y-%m-%d")


def _time_key(clock: Clock) -> str:
    return clock().astimezone(timezone.utc).strftime("%H:%M")


def _resolve_under(path: str | Path, root: str | Path) -> Path:
    resolved = Path(path).resolve()
    root_path = Path(root).resolve()
    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise ValueError(f"memory path outside Ego_handmade workspace: {resolved}") from exc
    return resolved


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except (TypeError, ValueError):
        pass

    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    if hasattr(value, "__dict__"):
        return {
            str(k): _json_safe(v)
            for k, v in value.__dict__.items()
            if not str(k).startswith("_")
        }
    return str(value)


def _bounded(text: str, max_chars: int) -> str:
    clean = (text or "").strip()
    if max_chars <= 0 or len(clean) <= max_chars:
        return clean
    return clean[:max_chars] + "\n...[truncated]"


@dataclass
class MemoryContext:
    core: str = ""
    today_episode: str = ""
    memory_dir: str = ""
    core_max_chars: int = DEFAULT_CORE_MAX_CHARS
    episode_max_chars: int = DEFAULT_EPISODE_MAX_CHARS

    def render_for_prompt(self) -> str:
        core = _bounded(self.core, self.core_max_chars)
        episode = _bounded(self.today_episode, self.episode_max_chars)
        if not core and not episode:
            return ""

        parts = [
            "[Operator Memory Context]",
            "Scope: candidate-local Ego_handmade operator memory only.",
            "Authority: not repo authority, not OpenEmotion memory, not evidence ledger.",
        ]
        if self.memory_dir:
            parts.append(f"Storage: {self.memory_dir}")
        if core:
            parts.append("\n[Core MEMORY.md]\n" + core)
        if episode:
            parts.append("\n[Today Episodic Summary]\n" + episode)
        return "\n".join(parts).strip()


class OperatorMemoryStore:
    def __init__(
        self,
        memory_dir: str | Path,
        *,
        containment_root: str | Path,
        clock: Clock = _utc_now,
    ) -> None:
        self.memory_dir = _resolve_under(memory_dir, containment_root)
        self.clock = clock
        self.history_file = self.memory_dir / "history.jsonl"
        self.episodic_dir = self.memory_dir / "episodic"
        self.core_file = self.memory_dir / "MEMORY.md"
        self.telemetry_dir = self.memory_dir / "telemetry"
        self.tokens_file = self.telemetry_dir / "tokens.jsonl"
        self.candidate_core_updates_file = self.memory_dir / "candidate_core_updates.jsonl"

    def _ensure_parent(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def append_raw_turn(
        self,
        *,
        session_id: str,
        role: str,
        content: Any,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        row = {
            "ts": timestamp or _iso_now(self.clock),
            "session_id": session_id,
            "role": role,
            "content": _json_safe(content),
            "metadata": _json_safe(metadata or {}),
        }
        self._ensure_parent(self.history_file)
        with self.history_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row

    def append_compact_marker(
        self,
        *,
        session_id: str,
        event_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        row = {
            "ts": _iso_now(self.clock),
            "session_id": session_id,
            "event_id": event_id,
            "type": "compact_event",
            "metadata": _json_safe(metadata or {}),
        }
        self._ensure_parent(self.history_file)
        with self.history_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row

    def load_core(self) -> str:
        if not self.core_file.exists():
            return ""
        return self.core_file.read_text(encoding="utf-8")

    def save_core(self, content: str, *, source: str = "manual") -> Dict[str, Any]:
        if source not in {"manual", "operator", "test"}:
            raise ValueError("core memory can only be written by an explicit operator gate")
        text = (content or "").strip()
        self._ensure_parent(self.core_file)
        self.core_file.write_text(text + ("\n" if text else ""), encoding="utf-8")
        return {
            "status": "ok",
            "path": str(self.core_file),
            "source": source,
            "chars": len(text),
        }

    def remember(self, text: str, *, source: str = "operator") -> Dict[str, Any]:
        clean = (text or "").strip()
        if not clean:
            return {"status": "failed", "reason": "empty_memory_note"}

        current = self.load_core().strip()
        if not current:
            current = (
                "# Ego_handmade Operator Memory\n\n"
                "Candidate-local notes only. This file is not EGO repo authority.\n"
            )
        note = f"- {_iso_now(self.clock)} [{source}] {clean}"
        return self.save_core(current.rstrip() + "\n\n" + note, source="operator")

    def episode_path(self, date_key: Optional[str] = None) -> Path:
        return self.episodic_dir / f"{date_key or _date_key(self.clock)}.md"

    def load_today_episode(self) -> str:
        path = self.episode_path()
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def write_episodic(
        self,
        summary: str,
        *,
        date_key: Optional[str] = None,
        source: str,
        input_refs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        clean = (summary or "").strip()
        if not clean:
            return {"status": "skipped", "reason": "empty_episode"}
        path = self.episode_path(date_key)
        if path.exists():
            existing = path.read_text(encoding="utf-8").rstrip()
        else:
            existing = f"# {path.stem} Episodic Memory"
        block = (
            f"## {_time_key(self.clock)} {source}\n\n"
            f"{clean}\n\n"
            f"refs: `{json.dumps(_json_safe(input_refs or {}), ensure_ascii=False, sort_keys=True)}`"
        )
        self._ensure_parent(path)
        path.write_text(existing + "\n\n" + block.strip() + "\n", encoding="utf-8")
        return {
            "status": "ok",
            "path": str(path),
            "source": source,
            "chars": len(clean),
        }

    def append_candidate_core_update(
        self,
        content: str,
        *,
        source: str,
        status: str = "candidate",
        event_id: Optional[str] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        row = {
            "ts": _iso_now(self.clock),
            "event_id": event_id,
            "source": source,
            "status": status,
            "content": content,
            "error": _json_safe(error or {}),
        }
        self._ensure_parent(self.candidate_core_updates_file)
        with self.candidate_core_updates_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row

    def build_context(
        self,
        *,
        core_max_chars: int = DEFAULT_CORE_MAX_CHARS,
        episode_max_chars: int = DEFAULT_EPISODE_MAX_CHARS,
    ) -> MemoryContext:
        return MemoryContext(
            core=self.load_core(),
            today_episode=self.load_today_episode(),
            memory_dir=str(self.memory_dir),
            core_max_chars=core_max_chars,
            episode_max_chars=episode_max_chars,
        )


class TokenTelemetry:
    def __init__(self, log_file: str | Path, *, clock: Clock = _utc_now) -> None:
        self.log_file = Path(log_file)
        self.clock = clock
        self._last_input_tokens = 0

    @staticmethod
    def estimate_tokens_from_messages(messages: List[Dict[str, Any]]) -> int:
        total_chars = 0
        for message in messages:
            total_chars += len(str(message.get("role", "")))
            total_chars += len(str(message.get("content", "")))
        return max(1, total_chars // 4) if total_chars else 0

    @staticmethod
    def _int_from(usage: Dict[str, Any], keys: List[str]) -> int:
        for key in keys:
            value = usage.get(key)
            if isinstance(value, int):
                return value
        return 0

    def record(
        self,
        *,
        event_id: str,
        model: str,
        provider: str,
        usage: Optional[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        compact_triggered: bool = False,
    ) -> Dict[str, Any]:
        usage_data = usage or {}
        input_tokens = self._int_from(usage_data, ["input_tokens", "prompt_tokens", "input"])
        output_tokens = self._int_from(usage_data, ["output_tokens", "completion_tokens", "output"])
        cache_read = self._int_from(usage_data, ["cache_read_input_tokens", "cache_read"])
        cache_create = self._int_from(usage_data, ["cache_creation_input_tokens", "cache_create"])
        total_tokens = self._int_from(usage_data, ["total_tokens", "total"])

        approx = False
        if input_tokens <= 0:
            input_tokens = self.estimate_tokens_from_messages(messages)
            approx = True
        if total_tokens <= 0:
            total_tokens = input_tokens + output_tokens + cache_read + cache_create

        self._last_input_tokens = input_tokens + cache_read + cache_create
        row = {
            "ts": _iso_now(self.clock),
            "event_id": event_id,
            "provider": provider or "unknown",
            "model": model or "unknown",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_create,
            "total_tokens": total_tokens,
            "approximate": approx,
            "compact_triggered": compact_triggered,
        }
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row

    def should_compact(
        self,
        *,
        max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
        threshold: float = DEFAULT_COMPACTION_THRESHOLD,
    ) -> bool:
        return self._last_input_tokens > max_context_tokens * threshold


class MemoryCompactor:
    def __init__(
        self,
        store: OperatorMemoryStore,
        *,
        keep_last: int = DEFAULT_KEEP_LAST_MESSAGES,
        max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
        threshold: float = DEFAULT_COMPACTION_THRESHOLD,
    ) -> None:
        self.store = store
        self.keep_last = keep_last
        self.max_context_tokens = max_context_tokens
        self.threshold = threshold

    def should_compact(
        self,
        messages: List[Dict[str, Any]],
        *,
        usage: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> bool:
        if force:
            return len(messages) > self.keep_last
        if len(messages) <= self.keep_last:
            return False
        usage_data = usage or {}
        input_tokens = TokenTelemetry._int_from(usage_data, ["input_tokens", "prompt_tokens", "input"])
        if input_tokens <= 0:
            input_tokens = TokenTelemetry.estimate_tokens_from_messages(messages)
        return input_tokens > self.max_context_tokens * self.threshold

    def compact(
        self,
        messages: List[Dict[str, Any]],
        *,
        session_id: str,
        event_id: str,
        usage: Optional[Dict[str, Any]] = None,
        force: bool = False,
        llm: Optional[Any] = None,
    ) -> Dict[str, Any]:
        if not self.should_compact(messages, usage=usage, force=force):
            return {"status": "skipped", "reason": "below_compaction_threshold"}
        if len(messages) <= self.keep_last:
            return {"status": "skipped", "reason": "not_enough_messages"}

        old_messages = messages[:-self.keep_last]
        recent_messages = messages[-self.keep_last :]

        if llm is not None:
            llm_result = self._compact_with_llm(old_messages, session_id=session_id, event_id=event_id, llm=llm)
            if llm_result["status"] != "ok":
                return {
                    "status": "error",
                    "reason": "malformed_compaction_output",
                    "kept_messages": messages,
                    "error": llm_result,
                }
            episode = llm_result["episode"]
            candidate = llm_result["candidate_core_update"]
            source = "llm_compactor"
        else:
            episode = self._deterministic_episode(old_messages)
            candidate = self._deterministic_candidate(old_messages)
            source = "deterministic_compactor"

        episode_result = self.store.write_episodic(
            episode,
            source=source,
            input_refs={
                "event_id": event_id,
                "old_message_count": len(old_messages),
                "kept_message_count": len(recent_messages),
            },
        )
        candidate_result = self.store.append_candidate_core_update(
            candidate,
            source=source,
            status="candidate",
            event_id=event_id,
        )
        self.store.append_compact_marker(
            session_id=session_id,
            event_id=event_id,
            metadata={
                "old_message_count": len(old_messages),
                "kept_message_count": len(recent_messages),
                "source": source,
            },
        )
        return {
            "status": "compacted",
            "source": source,
            "old_message_count": len(old_messages),
            "kept_message_count": len(recent_messages),
            "kept_messages": recent_messages,
            "episode": episode_result,
            "candidate_core_update": {
                "path": str(self.store.candidate_core_updates_file),
                "status": candidate_result["status"],
            },
        }

    def _compact_with_llm(
        self,
        old_messages: List[Dict[str, Any]],
        *,
        session_id: str,
        event_id: str,
        llm: Any,
    ) -> Dict[str, Any]:
        prompt = (
            "Compress these Ego_handmade operator-memory messages into strict JSON.\n"
            "Return exactly: {\"episode\": \"...\", \"candidate_core_update\": \"...\"}.\n"
            "Do not overwrite MEMORY.md. Candidate core update is for operator review only.\n\n"
            f"session_id={session_id}\nevent_id={event_id}\n"
            f"messages={json.dumps(_json_safe(old_messages), ensure_ascii=False)}"
        )
        try:
            text = llm.complete(prompt)
            data = json.loads(text)
            episode = str(data["episode"]).strip()
            candidate = str(data["candidate_core_update"]).strip()
            if not episode:
                raise ValueError("empty episode")
        except Exception as exc:
            error = {
                "error_type": type(exc).__name__,
                "error": repr(exc),
            }
            self.store.append_candidate_core_update(
                "",
                source="llm_compactor",
                status="error",
                event_id=event_id,
                error=error,
            )
            return {"status": "error", **error}
        return {
            "status": "ok",
            "episode": episode,
            "candidate_core_update": candidate,
        }

    def _deterministic_episode(self, old_messages: List[Dict[str, Any]]) -> str:
        lines = ["Deterministic compaction summary:"]
        for message in old_messages:
            role = str(message.get("role", "?"))
            content = _bounded(str(message.get("content", "")), 240).replace("\n", " ")
            lines.append(f"- {role}: {content}")
        return "\n".join(lines)

    def _deterministic_candidate(self, old_messages: List[Dict[str, Any]]) -> str:
        return (
            "Candidate core update generated by deterministic compaction. "
            f"Review before promotion. old_message_count={len(old_messages)}"
        )
