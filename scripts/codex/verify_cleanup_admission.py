#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = ROOT / "docs" / "codex" / "tasks" / "repo-authority-cleanup"
CANONICAL_DOCS_INDEX = TASK_ROOT / "CANONICAL_DOCS_INDEX.md"
ARTIFACT_LOG_INVENTORY = TASK_ROOT / "ARTIFACT_LOG_INVENTORY.md"
DIRTY_WORKTREE_BOUNDARY = TASK_ROOT / "DIRTY_WORKTREE_BOUNDARY.md"
CLEAN_CLONE_CLOSEOUT_PROOF = TASK_ROOT / "CLEAN_CLONE_CLOSEOUT_PROOF.md"
DOCS_CANONICAL = ROOT / "docs" / "canonical" / "README.md"
DOCS_ARCHIVE = ROOT / "docs" / "archive" / "README.md"
ARTIFACTS_CURRENT = ROOT / "artifacts" / "current" / "README.md"
ARTIFACTS_ARCHIVE = ROOT / "artifacts" / "archive" / "README.md"
GENERATED_README = ROOT / "EgoCore" / "docs" / "generated" / "README.md"


REQUIRED_SNIPPETS = {
    CANONICAL_DOCS_INDEX: [
        "| `README.md` | repo-level public authority summary |",
        "| `docs/CURRENT_PROJECT_LOGIC_FLOW.md` | current formal logic/call chain summary |",
        "| `docs/PROTO_SELF_SINGLE_AUTHORITY_DECISION.md` | prescriptive authority decision layer |",
        "| `EgoCore/docs/generated/README.md` | generated inventory boundary marker |",
        "| `docs/codex/tasks/repo-authority-cleanup/DIRTY_WORKTREE_BOUNDARY.md` | dirty-worktree boundary note |",
        "| `docs/codex/tasks/repo-authority-cleanup/CLEAN_CLONE_CLOSEOUT_PROOF.md` | clean-clone final proof note |",
        "| `docs/codex/tasks/repo-authority-cleanup/CANONICAL_DOCS_INDEX.md` | cleanup execution ledger |",
        "| `docs/canonical/README.md` | canonical boundary marker |",
        "| `docs/archive/README.md` | archive boundary marker |",
    ],
    ARTIFACT_LOG_INVENTORY: [
        "| `artifacts/telegram_real_mainline_v1/*` | current Telegram mainline evidence |",
        "| `artifacts/acceptance_chains/*` | current generated acceptance outputs |",
        "| `OpenEmotion/artifacts/mvp12/*CURRENT*`, `mvp13/*CURRENT*`, `mvp14/*CURRENT*`, `mvp15/*CURRENT*`, `mvp16/*CURRENT*` | current owner-axis evidence |",
        "| `EgoCore/docs/generated/README.md` | generated inventory boundary marker |",
        "| `artifacts/current/README.md` | current artifact boundary marker |",
        "| `artifacts/archive/README.md` | archive artifact boundary marker |",
    ],
    DOCS_CANONICAL: [
        "Physical canonical migration is not complete yet.",
        "Use `docs/codex/tasks/repo-authority-cleanup/CANONICAL_DOCS_INDEX.md` as the current canonical index.",
        "Generated inventory is rebuild-only and not part of the canonical authority set.",
        "The final closeout proof must run in a clean clone or CI workspace.",
    ],
    DOCS_ARCHIVE: [
        "Archive relocation is admission-controlled.",
        "Do not move files here until caller and gate references are cleared.",
        "Dirty worktree noise is non-authority.",
        "Archive relocation remains admission-controlled until clean-clone / CI proof is available.",
    ],
    ARTIFACTS_CURRENT: [
        "Current artifact boundary marker.",
        "Do not move current evidence bundles until caller migration is complete.",
        "Current evidence stays protected until the clean-clone / CI final closeout proof passes.",
        "Generated inventory is rebuild-only and must not be treated as current evidence.",
    ],
    ARTIFACTS_ARCHIVE: [
        "Archive artifact boundary marker.",
        "Do not archive replay / trace / audit evidence without explicit admission proof.",
        "Archive moves still require explicit admission proof from a clean clone or CI workspace.",
    ],
    DIRTY_WORKTREE_BOUNDARY: [
        "Dirty worktree noise is non-authority.",
        "Final closeout proof must run in a clean clone or CI workspace.",
    ],
    CLEAN_CLONE_CLOSEOUT_PROOF: [
        "This is the final closeout proof surface.",
        "The proof must be reproducible in a clean clone or CI workspace.",
    ],
    GENERATED_README: [
        "Rebuild-only generated inventory boundary.",
        "Do not treat generated inventory as an authority source.",
        "The clean-clone / CI final closeout proof must rebuild this directory, not trust dirty worktree residue.",
    ],
}


def main() -> int:
    errors: list[str] = []
    for path, snippets in REQUIRED_SNIPPETS.items():
        if not path.exists():
            errors.append(f"missing cleanup admission surface: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                errors.append(f"{path.relative_to(ROOT)} missing required cleanup admission snippet: {snippet}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("cleanup admission gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
