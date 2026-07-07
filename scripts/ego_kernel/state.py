from __future__ import annotations

from dataclasses import dataclass, field
import copy
import hashlib
import json
from typing import Any


KERNEL_STATE_SCHEMA_VERSION = "kernel_state_v0"


def canonical_json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_dumps(value).encode("utf-8")).hexdigest()


def _json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


@dataclass(frozen=True)
class KernelState:
    task_id: str
    run_id: str
    episode_id: str
    step_id: int
    substates: dict[str, Any]
    seed_registry: dict[str, dict[str, int]]
    ablations: dict[str, str] = field(default_factory=dict)
    schema_version: str = KERNEL_STATE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "episode_id": self.episode_id,
            "step_id": int(self.step_id),
            "substates": _json_copy(self.substates),
            "seed_registry": _json_copy(self.seed_registry),
            "ablations": _json_copy(self.ablations),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KernelState":
        if payload.get("schema_version") != KERNEL_STATE_SCHEMA_VERSION:
            raise ValueError("invalid kernel state schema_version")
        return cls(
            task_id=str(payload["task_id"]),
            run_id=str(payload["run_id"]),
            episode_id=str(payload["episode_id"]),
            step_id=int(payload["step_id"]),
            substates=_json_copy(payload.get("substates", {})),
            seed_registry=_json_copy(payload.get("seed_registry", {})),
            ablations=_json_copy(payload.get("ablations", {})),
            schema_version=str(payload["schema_version"]),
        )

    def canonical_json(self) -> str:
        return canonical_json_dumps(self.to_dict())

    def state_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def seed_context(self) -> dict[str, Any]:
        return _json_copy(self.seed_registry)

    def with_updates(
        self,
        *,
        step_id: int | None = None,
        substates: dict[str, Any] | None = None,
        seed_registry: dict[str, dict[str, int]] | None = None,
        ablations: dict[str, str] | None = None,
    ) -> "KernelState":
        next_substates = _json_copy(self.substates)
        if substates:
            for name, value in substates.items():
                next_substates[str(name)] = _json_copy(value)
        next_registry = _json_copy(self.seed_registry)
        if seed_registry:
            for name, value in seed_registry.items():
                next_registry[str(name)] = _json_copy(value)
        next_ablations = _json_copy(self.ablations)
        if ablations:
            for name, value in ablations.items():
                next_ablations[str(name)] = str(value)
        return KernelState(
            task_id=self.task_id,
            run_id=self.run_id,
            episode_id=self.episode_id,
            step_id=self.step_id if step_id is None else int(step_id),
            substates=next_substates,
            seed_registry=next_registry,
            ablations=next_ablations,
            schema_version=self.schema_version,
        )

    def replace_substates(self, substates: dict[str, Any]) -> "KernelState":
        return KernelState(
            task_id=self.task_id,
            run_id=self.run_id,
            episode_id=self.episode_id,
            step_id=self.step_id,
            substates=_json_copy(substates),
            seed_registry=_json_copy(self.seed_registry),
            ablations=_json_copy(self.ablations),
            schema_version=self.schema_version,
        )


def deep_copy(value: Any) -> Any:
    return copy.deepcopy(value)
