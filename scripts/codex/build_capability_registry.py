#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "CAPABILITY_REGISTRY.md"


def render_markdown() -> str:
    return """# Capability Registry

This file is a current-tree tombstone for the old pre-EgoOperator capability registry.

Current authority:

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/MAINLINE_QUICKSTART.md`
- `EgoOperator/`

Archived legacy reference:

- Archive pointer: `legacy-pre-operator-mainline-before-purge`
- Tombstone: `legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md`
- Algorithm inventory: `docs/archive/LEGACY_ALGORITHM_INVENTORY.md`
- Manifest: `artifacts/archive/legacy_pre_operator_mainline_manifest.json`

The old generated capability table named `EgoCore`, `OpenEmotion`, and related provider/runtime gates. That table is historical only and has no current runtime authority, default path, maintenance authority, fallback authority, or task-routing authority.

Any reuse of old capability ideas requires a new Stage Card and evidence gate.
"""


def main() -> int:
    OUTPUT.write_text(render_markdown(), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
