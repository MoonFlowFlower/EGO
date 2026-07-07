from __future__ import annotations

import ast
from pathlib import Path

from .constants import FORBIDDEN_IMPORT_MODULES, PACKAGE_ROOT


def package_forbidden_imports() -> dict:
    hits: list[dict[str, str | int]] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in FORBIDDEN_IMPORT_MODULES:
                        hits.append({"path": str(path), "line": node.lineno, "module": alias.name})
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                if root in FORBIDDEN_IMPORT_MODULES:
                    hits.append({"path": str(path), "line": node.lineno, "module": node.module})
    return {"producer_function": "package_forbidden_imports", "status": "pass" if not hits else "fail", "hits": hits}
