#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

LEGACY_MODULES = {
    "EgoCore",
    "OpenEmotion",
    "ego_desktop_lab",
    "openemotion",
    "emotiond",
}

PSPC_ADAPTER_MODULES = {
    "EgoOperator.adapters.pspc_lab_adapter",
    "EgoOperator.adapters.pspc_read_only_shadow_hook",
    "EgoOperator.adapters.pspc_disabled_runtime_shadow_hook",
    "EgoOperator.adapters.pspc_runtime_adjacent_observer",
}

PSPC_ADAPTER_CLASSES = {
    ROOT / "EgoOperator" / "adapters" / "pspc_lab_adapter.py": "PSPCLabAdapter",
    ROOT / "EgoOperator" / "adapters" / "pspc_read_only_shadow_hook.py": "PSPCReadOnlyShadowHook",
    ROOT / "EgoOperator" / "adapters" / "pspc_disabled_runtime_shadow_hook.py": "PSPCDisabledRuntimeShadowHook",
    ROOT / "EgoOperator" / "adapters" / "pspc_runtime_adjacent_observer.py": "PSPCRuntimeAdjacentObserver",
}

ACTIVE_RUNTIME_EXTRA_FILES = (
    ROOT / "scripts" / "ego_operator_desktop_turn.py",
)

RUNTIME_AUTHORITY_FIELDS = {
    "action",
    "tool_call",
    "command",
    "memory_write",
    "gate_decision",
    "approval_id",
    "transport",
    "send",
    "schedule",
    "runtime_registration",
    "mainline_authority",
}


def _module_hits(module_name: str, blocked: set[str]) -> list[str]:
    hits = []
    for item in blocked:
        if module_name == item or module_name.startswith(f"{item}."):
            hits.append(item)
    return hits


def _iter_active_python_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted((ROOT / "EgoOperator").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("EgoOperator/adapters/") or rel.startswith("EgoOperator/tests/"):
            continue
        if "__pycache__" in path.parts:
            continue
        files.append(path)
    for path in ACTIVE_RUNTIME_EXTRA_FILES:
        if path.exists():
            files.append(path)
    return files


def _literal_value(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _class_assignment_map(class_node: ast.ClassDef) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for stmt in class_node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                result[target.id] = _literal_value(stmt.value)
    return result


def _check_active_imports(errors: list[str]) -> None:
    for path in _iter_active_python_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            errors.append(f"{rel} syntax error while scanning imports: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    legacy_hits = _module_hits(alias.name, LEGACY_MODULES)
                    if legacy_hits:
                        errors.append(f"{rel} imports archived legacy module: {alias.name}")
                    pspc_hits = _module_hits(alias.name, PSPC_ADAPTER_MODULES)
                    if pspc_hits:
                        errors.append(f"{rel} imports PSPC adapter/hook module: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                legacy_hits = _module_hits(module, LEGACY_MODULES)
                if legacy_hits:
                    errors.append(f"{rel} imports archived legacy module: {module}")
                pspc_hits = _module_hits(module, PSPC_ADAPTER_MODULES)
                if pspc_hits:
                    errors.append(f"{rel} imports PSPC adapter/hook module: {module}")


def _check_pspc_adapter_defaults(errors: list[str]) -> None:
    for path, class_name in PSPC_ADAPTER_CLASSES.items():
        rel = path.relative_to(ROOT).as_posix()
        if not path.exists():
            errors.append(f"missing PSPC adapter/hook contract file: {rel}")
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        class_node = next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name), None)
        if class_node is None:
            errors.append(f"{rel} missing class {class_name}")
            continue
        assignments = _class_assignment_map(class_node)
        if assignments.get("enabled") is not False:
            errors.append(f"{rel}:{class_name}.enabled must default to False")
        if assignments.get("mainline_connected") is not False:
            errors.append(f"{rel}:{class_name}.mainline_connected must default to False")
        runtime_authority = assignments.get("runtime_authority")
        if runtime_authority not in ("none", None):
            errors.append(f"{rel}:{class_name}.runtime_authority must be none")
        if runtime_authority is None and "RUNTIME_AUTHORITY" not in path.read_text(encoding="utf-8"):
            errors.append(f"{rel}:{class_name}.runtime_authority must be declared")


def _check_active_runtime_field_literals(errors: list[str]) -> None:
    for path in _iter_active_python_files():
        rel = path.relative_to(ROOT).as_posix()
        if path.name == "ego_operator_desktop_turn.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "pspc" not in text.lower():
            continue
        for field in sorted(RUNTIME_AUTHORITY_FIELDS):
            if field in text:
                errors.append(f"{rel} mentions PSPC with runtime-authority field literal: {field}")


def main() -> int:
    errors: list[str] = []
    _check_active_imports(errors)
    _check_pspc_adapter_defaults(errors)
    _check_active_runtime_field_literals(errors)
    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({
        "status": "pass",
        "active_runtime_files_checked": len(_iter_active_python_files()),
        "pspc_adapter_contracts_checked": len(PSPC_ADAPTER_CLASSES),
        "claim_ceiling": "runtime authority boundary static check only",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
