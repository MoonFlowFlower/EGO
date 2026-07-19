"""One-shot structured splitter for the pre-V2-only monolithic app module.

This tool operates on top-level Python AST nodes rather than line-number string
replacement.  It is retained as migration provenance; normal development does
not invoke it.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "labs" / "ego_life_playground_v0"
SOURCE = PACKAGE / "app.py"

CONTROLLER_NAMES = {
    "DISCLOSURE",
    "public_state_projection",
    "public_state_hash",
    "DispatchResult",
    "PlaygroundController",
}
TERMINAL_NAMES = {
    "_timeline_from_recovery",
    "build_terminal_snapshot",
    "TerminalPlayground",
}

CONTROLLER_HEADER = '''"""The V2 product's only dispatch/controller implementation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
import uuid

from .engine import (
    DEFAULT_PRIVATE_WORLD_SEED,
    EngineInvariantError,
    StepResult,
    canonical_hash,
    compute_step,
    initial_state,
    make_command,
    make_run_metadata,
)
from .microworld import LAYOUTS, public_world_projection
from .store import CommitReceipt, RecoveryResult, SQLiteEventStore

'''

TERMINAL_HEADER = '''"""Terminal view routed through the single PlaygroundController."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .controller import DispatchResult, PlaygroundController, public_state_hash
from .engine import DEFAULT_INTERVENTIONS, EngineInvariantError
from .microworld import (
    ALLOWED_WORLD_EVENTS,
    cue_for_event,
    default_event_for_sequence,
    event_for_cue,
    make_public_frame,
)
from .store import RecoveryResult

'''

VISUAL_HEADER = '''"""Tk visual view routed through the single PlaygroundController."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, Callable, Mapping

from .controller import (
    DISCLOSURE,
    PlaygroundController,
    public_state_hash,
)
from .engine import (
    ACTIONS,
    CUES,
    DEFAULT_INTERVENTIONS,
    DEFAULT_PRIVATE_WORLD_SEED,
    EngineInvariantError,
)
from .microworld import (
    ALLOWED_WORLD_EVENTS,
    cue_for_event,
    default_event_for_sequence,
    event_for_cue,
    make_public_frame,
)
from .store import RecoveryFrame, SQLiteEventStore, default_db_path
from .terminal import _timeline_from_recovery, build_terminal_snapshot

'''

APP_TEXT = '''"""Compatibility exports for the split V2 controller and views."""

from .controller import (
    DISCLOSURE,
    DispatchResult,
    PlaygroundController,
    public_state_hash,
    public_state_projection,
)
from .terminal import TerminalPlayground, build_terminal_snapshot
from .visual_console import (
    PlaygroundWindow,
    build_advanced_details,
    build_chinese_causal_view,
    build_tk_trace_payload,
    filedialog,
    messagebox,
    recorded_waypoints,
    run_app,
    simpledialog,
    tk,
    ttk,
    validate_scheduled_waypoints,
)

__all__ = [
    "DISCLOSURE",
    "DispatchResult",
    "PlaygroundController",
    "PlaygroundWindow",
    "TerminalPlayground",
    "build_advanced_details",
    "build_chinese_causal_view",
    "build_terminal_snapshot",
    "build_tk_trace_payload",
    "public_state_hash",
    "public_state_projection",
    "recorded_waypoints",
    "run_app",
    "validate_scheduled_waypoints",
]
'''


def _node_name(node: ast.AST) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                return target.id
    return None


def _segment(lines: list[str], node: ast.AST) -> str:
    assert hasattr(node, "lineno") and hasattr(node, "end_lineno")
    start = node.lineno
    decorators = getattr(node, "decorator_list", ())
    if decorators:
        start = min(start, *(decorator.lineno for decorator in decorators))
    return "".join(lines[start - 1 : node.end_lineno]) + "\n\n"


def split() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    buckets = {"controller": [], "terminal": [], "visual": []}
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        name = _node_name(node)
        if name in CONTROLLER_NAMES:
            buckets["controller"].append(_segment(lines, node))
        elif name in TERMINAL_NAMES:
            buckets["terminal"].append(_segment(lines, node))
        else:
            buckets["visual"].append(_segment(lines, node))
    required = {
        "controller": CONTROLLER_NAMES,
        "terminal": TERMINAL_NAMES,
        "visual": {"PlaygroundWindow", "run_app", "build_tk_trace_payload"},
    }
    found = {
        key: {
            _node_name(ast.parse(segment).body[0])
            for segment in segments
            if ast.parse(segment).body
        }
        for key, segments in buckets.items()
    }
    for bucket, names in required.items():
        missing = names - found[bucket]
        if missing:
            raise RuntimeError(f"split missing {bucket} nodes: {sorted(missing)}")
    (PACKAGE / "controller.py").write_text(
        CONTROLLER_HEADER + "".join(buckets["controller"]), encoding="utf-8"
    )
    (PACKAGE / "terminal.py").write_text(
        TERMINAL_HEADER + "".join(buckets["terminal"]), encoding="utf-8"
    )
    (PACKAGE / "visual_console.py").write_text(
        VISUAL_HEADER + "".join(buckets["visual"]), encoding="utf-8"
    )
    SOURCE.write_text(APP_TEXT, encoding="utf-8")
    for path in (
        PACKAGE / "controller.py",
        PACKAGE / "terminal.py",
        PACKAGE / "visual_console.py",
        SOURCE,
    ):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


if __name__ == "__main__":
    split()
