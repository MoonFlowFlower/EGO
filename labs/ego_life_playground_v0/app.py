"""Compatibility exports for the split V2 controller and views."""

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
