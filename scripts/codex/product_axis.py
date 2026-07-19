"""Pinned ITL product-axis mirror and active-view rendering.

The mirror is data, not a second route writer.  Verification always reads the
pinned ``commit:path`` Git object and therefore does not trust sibling worktree
bytes or status.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping
import uuid


AXIS_RELATIVE_PATH = Path("artifacts/ROUTE-STATE-MACHINE-001A/product_axis_state.json")
PIN_RELATIVE_PATH = Path("artifacts/ROUTE-STATE-MACHINE-001A/product_axis_source_pin.json")
ENTRYPOINT = "scripts/run_ego_life_playground_v0.py"
ACTIVE_VIEW_PATHS = (
    "AGENTS.md",
    "README.md",
    "artifacts/reports/program_state_summary.md",
    "docs/ACTIVE_CONTEXT_PACK.md",
    "docs/MAINLINE_QUICKSTART.md",
    "docs/PROGRAM_STATE_UNIFIED.yaml",
    "docs/REPO_SURFACE_MAP.md",
    "docs/STATUS.md",
    "docs/codex/tasks/TASK_LANE_INDEX.md",
)


@dataclass(frozen=True)
class VerificationResult:
    verdict: str
    errors: tuple[str, ...]
    producer_function: str
    input_artifacts: tuple[str, ...]
    run_id: str
    aggregation_rule: str
    source_commit: str | None
    source_blob_oid: str | None
    source_sha256: str | None
    mirror_sha256: str | None
    code_path_hash: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["errors"] = list(self.errors)
        payload["input_artifacts"] = list(self.input_artifacts)
        return payload


def _code_path_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def load_product_axis(root: str | Path) -> dict[str, Any]:
    """Load the local authority object (ITL) or exact read-only mirror (Ego)."""

    return _read_json(Path(root).resolve() / AXIS_RELATIVE_PATH)


def _git_object(repo: Path, commit: str, path: str) -> tuple[str, bytes]:
    blob = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", f"{commit}:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    raw = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "blob", blob],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    return blob, raw


def sync_pinned_itl_mirror(
    ego_root: str | Path,
    itl_repo: str | Path,
    source_commit: str,
) -> dict[str, Any]:
    """Copy one committed ITL Git blob and write its independently checked pin."""

    root = Path(ego_root).resolve()
    source_repo = Path(itl_repo).resolve()
    source_path = str(AXIS_RELATIVE_PATH).replace("\\", "/")
    blob, raw = _git_object(source_repo, source_commit, source_path)
    # Parse before writing so a non-object or malformed authority never becomes
    # the local reader surface.
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("pinned ITL product axis must be a JSON object")
    mirror_path = root / AXIS_RELATIVE_PATH
    pin_path = root / PIN_RELATIVE_PATH
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    mirror_path.write_bytes(raw)
    pin = {
        "schema_version": "ego.itl_product_axis_pin.v1",
        "source_repo_hint": str(source_repo),
        "source_commit": source_commit,
        "source_path": source_path,
        "source_blob_oid": blob,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "mirror_policy": "read_only_exact_git_blob_bytes",
    }
    pin_path.write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return pin


def verify_pinned_itl_mirror(
    ego_root: str | Path,
    itl_repo: str | Path | None = None,
) -> VerificationResult:
    """Compare Ego mirror bytes with the pinned ITL Git object.

    ``itl_repo`` is an explicit clean-clone override.  When omitted, the pin's
    repository hint is used only to locate the Git object database; no worktree
    file is read.
    """

    root = Path(ego_root).resolve()
    mirror_path = root / AXIS_RELATIVE_PATH
    pin_path = root / PIN_RELATIVE_PATH
    errors: list[str] = []
    source_commit: str | None = None
    source_blob: str | None = None
    source_sha: str | None = None
    mirror_sha: str | None = None
    inputs = [str(AXIS_RELATIVE_PATH).replace("\\", "/"), str(PIN_RELATIVE_PATH).replace("\\", "/")]
    try:
        pin = _read_json(pin_path)
        source_commit = str(pin["source_commit"])
        source_path = str(pin["source_path"])
        expected_blob = str(pin["source_blob_oid"])
        expected_sha = str(pin["source_sha256"])
        source_repo = Path(itl_repo or pin["source_repo_hint"]).resolve()
        inputs.append(f"{source_repo}@{source_commit}:{source_path}")
        source_blob, source_raw = _git_object(source_repo, source_commit, source_path)
        mirror_raw = mirror_path.read_bytes()
        source_sha = hashlib.sha256(source_raw).hexdigest()
        mirror_sha = hashlib.sha256(mirror_raw).hexdigest()
        if source_blob != expected_blob:
            errors.append("source_blob_oid_mismatch")
        if source_sha != expected_sha:
            errors.append("source_sha256_mismatch")
        if mirror_raw != source_raw:
            errors.append("mirror_bytes_mismatch")
        # Parse both bytes through the same structured path as a schema sanity check.
        if json.loads(mirror_raw) != json.loads(source_raw):
            errors.append("mirror_fields_mismatch")
    except (OSError, KeyError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        errors.append(f"verification_error:{type(exc).__name__}")
    return VerificationResult(
        verdict="pass" if not errors else "fail",
        errors=tuple(errors),
        producer_function="verify_pinned_itl_mirror",
        input_artifacts=tuple(inputs),
        run_id=f"product-axis-mirror-{uuid.uuid4().hex}",
        aggregation_rule=(
            "pass iff pinned commit:path resolves to the pinned blob/hash and its raw "
            "bytes and parsed object exactly equal the Ego mirror"
        ),
        source_commit=source_commit,
        source_blob_oid=source_blob,
        source_sha256=source_sha,
        mirror_sha256=mirror_sha,
        code_path_hash=_code_path_hash(),
    )


def _selector(state: Mapping[str, Any]) -> Mapping[str, Any]:
    selector = state.get("product_development_axis")
    if not isinstance(selector, Mapping):
        raise ValueError("missing product_development_axis")
    return selector


def _truth_lines(selector: Mapping[str, Any], source_pin: Mapping[str, Any] | None) -> list[str]:
    pin_commit = "unknown"
    pin_blob = "unknown"
    if source_pin:
        pin_commit = str(source_pin.get("source_commit", "unknown"))
        pin_blob = str(source_pin.get("source_blob_oid", "unknown"))
    retired = selector.get("retired_projects") or {}
    return [
        f"product_mainline: {str(bool(selector.get('product_mainline'))).lower()}",
        f"interactive_entrypoint: {selector.get('interactive_entrypoint', 'unknown')}",
        f"enabled: {str(bool(selector.get('enabled'))).lower()}",
        f"default_enabled: {str(bool(selector.get('default_enabled'))).lower()}",
        f"autostart: {str(bool(selector.get('autostart'))).lower()}",
        f"background_dispatch: {str(bool(selector.get('background_dispatch'))).lower()}",
        f"network: {str(bool(selector.get('network'))).lower()}",
        f"llm: {str(bool(selector.get('llm'))).lower()}",
        f"science_weight: {selector.get('science_weight', 'unknown')}",
        f"runtime_authority: {selector.get('runtime_authority', 'unknown')}",
        f"repository_main_placement_complete: {str(bool(selector.get('repository_main_placement_complete'))).lower()}",
        f"retired_pre_v2_operator: {retired.get('EgoOperator', 'unknown')}",
        f"retired_pre_v2_desktop: {retired.get('EgoDesktop', 'unknown')}",
        f"itl_source_commit: {pin_commit}",
        f"itl_source_blob: {pin_blob}",
    ]


def render_active_views(
    state: Mapping[str, Any],
    source_pin: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Render every active reader view from one product-axis object.

    Static reader instructions are deliberately short.  All dynamic truth is
    rendered from ``state`` and the optional immutable source pin.
    """

    selector = _selector(state)
    truth = "\n".join(_truth_lines(selector, source_pin))
    next_actions = selector.get("next_actions") or []
    next_action = str(next_actions[0]) if next_actions else "none"
    claim = str(
        selector.get(
            "claim_ceiling",
            "local explicit V2 product entry and evidence hygiene only",
        )
    )
    header = "<!-- GENERATED by scripts/codex/render_active_views.py; do not hand edit. -->"
    compact = f"""{header}
# Active product context

```text
{truth}
next_action: {next_action}
claim_ceiling: {claim}
```

The product runs only after an explicit user launch. It has no autostart,
background dispatch, network, LLM, or science authority. Historical materials
are excluded from this active view; query the archive/history indexes only when
prior evidence is required.
"""
    agents = f"""{header}
# Agent entry contract

Read in this order:

1. this file;
2. `artifacts/ROUTE-STATE-MACHINE-001A/product_axis_state.json` and
   `product_axis_source_pin.json`;
3. `docs/ACTIVE_CONTEXT_PACK.md`.

Current machine-derived truth:

```text
{truth}
next_action: {next_action}
claim_ceiling: {claim}
```

Use exact bounded task cards and scoped staging. Do not treat UI behavior,
tests, traces, or replay as consciousness, subjectivity, emotion, agency,
autonomy, general learning, memory causality, or stable user-benefit evidence.
Do not push, tag, or remote-anchor unless a later operator card authorizes it.
Historical task cards/artifacts are evidence records, not current route writers.
"""
    readme = f"""{header}
# Ego V2 product

The repository has one explicit local product entry:

```powershell
python {selector.get('interactive_entrypoint', ENTRYPOINT)}
```

For a non-visual check:

```powershell
python {selector.get('interactive_entrypoint', ENTRYPOINT)} --quick-check
```

Machine-derived boundary:

```text
{truth}
claim_ceiling: {claim}
```

See `docs/MAINLINE_QUICKSTART.md` for terminal commands and
`docs/ACTIVE_CONTEXT_PACK.md` for the compact agent context.
"""
    quickstart = f"""{header}
# V2 quickstart

```powershell
python {selector.get('interactive_entrypoint', ENTRYPOINT)} --quick-check
python {selector.get('interactive_entrypoint', ENTRYPOINT)} --terminal
python {selector.get('interactive_entrypoint', ENTRYPOINT)}
```

Terminal commands: `step [event]`, `run N`, `pause`, `inspect`, `save PATH`,
`load RUN_ID`, `reset [RUN_ID]`, `replay`, `quit`.

```text
{truth}
```
"""
    surface = f"""{header}
# Current repository surface

- Product source: `labs/ego_life_playground_v0/`
- Explicit launcher: `{selector.get('interactive_entrypoint', ENTRYPOINT)}`
- Product state mirror: `artifacts/ROUTE-STATE-MACHINE-001A/`
- Active generated context: `AGENTS.md`, `README.md`, `docs/ACTIVE_CONTEXT_PACK.md`
- Historical evidence: `artifacts/`, `docs/codex/tasks/`, and `legacy/` (not
  default agent context)
- Offline science/evidence authority: sibling ITL repository only

```text
{truth}
```
"""
    lanes = f"""{header}
# Active lane index

1. `v2_product`: Ego-local bounded source tasks that preserve every boundary
   below.
2. `boundary_transition`: ITL Red transition only when product entry,
   enablement, mainline, runtime authority, network/LLM, science weight, or
   retirement state changes.
3. `science_evidence`: ITL-only; no Ego runtime wiring.

```text
{truth}
next_action: {next_action}
```
"""
    program = {
        "schema_version": "ego.program_state_compat.v2",
        "generated_from": "artifacts/ROUTE-STATE-MACHINE-001A/product_axis_state.json",
        "source_pin": {
            "commit": "unknown" if source_pin is None else source_pin.get("source_commit", "unknown"),
            "blob": "unknown" if source_pin is None else source_pin.get("source_blob_oid", "unknown"),
        },
        "phase": selector.get("state", "V2_ONLY_EXPLICIT_PRODUCT_MAINLINE"),
        "entrypoint": selector.get("interactive_entrypoint", ENTRYPOINT),
        "switches": {
            key: selector.get(key)
            for key in (
                "enabled",
                "default_enabled",
                "autostart",
                "background_dispatch",
                "network",
                "llm",
                "science_weight",
                "runtime_authority",
            )
        },
        "retired_projects": selector.get("retired_projects", {}),
        "next_action": next_action,
        "claim_ceiling": claim,
    }
    program_text = header + "\n" + json.dumps(program, indent=2, sort_keys=True) + "\n"
    summary = compact.replace("# Active product context", "# Program-state summary")
    status = compact.replace("# Active product context", "# Status")
    return {
        "AGENTS.md": agents,
        "README.md": readme,
        "artifacts/reports/program_state_summary.md": summary,
        "docs/ACTIVE_CONTEXT_PACK.md": compact,
        "docs/MAINLINE_QUICKSTART.md": quickstart,
        "docs/PROGRAM_STATE_UNIFIED.yaml": program_text,
        "docs/REPO_SURFACE_MAP.md": surface,
        "docs/STATUS.md": status,
        "docs/codex/tasks/TASK_LANE_INDEX.md": lanes,
    }


def load_source_pin(root: str | Path) -> dict[str, Any]:
    return _read_json(Path(root).resolve() / PIN_RELATIVE_PATH)
