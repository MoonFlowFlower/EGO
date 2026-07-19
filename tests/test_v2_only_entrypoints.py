from __future__ import annotations

from labs.ego_life_playground_v0 import app, controller, terminal, visual_console
from scripts.codex import verify_route_convergence
from scripts.codex.verify_route_convergence import scan_single_execution_path
from scripts.run_ego_life_playground_v0 import build_parser


def test_compatibility_app_reexports_the_only_controller_and_views() -> None:
    assert app.PlaygroundController is controller.PlaygroundController
    assert app.TerminalPlayground is terminal.TerminalPlayground
    assert app.PlaygroundWindow is visual_console.PlaygroundWindow
    assert app.run_app is visual_console.run_app


def test_view_modules_do_not_define_a_second_controller() -> None:
    assert "PlaygroundController" not in terminal.__dict__ or (
        terminal.PlaygroundController is controller.PlaygroundController
    )
    assert "PlaygroundController" not in visual_console.__dict__ or (
        visual_console.PlaygroundController is controller.PlaygroundController
    )


def test_launcher_exposes_quick_check_as_the_single_headless_acceptance_mode() -> None:
    args = build_parser().parse_args(["--quick-check"])
    assert args.quick_check is True


def test_active_ast_has_one_controller_reducer_store_dispatch_and_replay() -> None:
    result = scan_single_execution_path()
    assert result["verdict"] == "pass", result["errors"]


def test_default_retirement_check_is_clean_clone_portable(monkeypatch) -> None:
    def forbidden_local_quarantine_check(*_args, **_kwargs):
        raise AssertionError("default verification must not require external quarantine")

    monkeypatch.setattr(
        verify_route_convergence,
        "verify_preserved_untracked_inventory",
        forbidden_local_quarantine_check,
    )
    result = verify_route_convergence.build_retirement_evidence(
        full_local_recovery=False
    )
    assert result["verdict"] == "pass"
    assert result["full_local_recovery_requested"] is False
    assert result["untracked_recovery"] is None
