"""Path resolution and freeze guard for the read-only joi-demo corpus."""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Iterable

FROZEN_TAG = "frozen-reference-corpus-20260706"
PINNED_COMMIT = "52714ed9f7ede8dfd14da7f4c310a9e9db28c834"


class CorpusUnavailable(RuntimeError):
    """Raised when the sibling frozen corpus is not available locally."""


class CorpusFrozenStateError(RuntimeError):
    """Raised when the corpus is present but not in the admitted state."""


def ego_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_corpus_root(
    corpus_path: str | os.PathLike[str] | None = None,
    *,
    env: dict[str, str] | None = None,
) -> Path:
    env_map = os.environ if env is None else env
    raw = corpus_path or env_map.get("JOI_CORPUS_PATH")
    root = Path(raw) if raw else ego_root().parent / "joi-demo"
    root = root.expanduser().resolve()
    if not root.exists():
        raise CorpusUnavailable(f"frozen joi-demo corpus not present: {root}")
    if not (root / ".git").exists():
        raise CorpusUnavailable(f"joi-demo corpus is not a git worktree: {root}")
    return root


def _git(corpus_root: Path, args: Iterable[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(corpus_root), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise CorpusFrozenStateError(
            f"git {' '.join(args)} failed in {corpus_root}: {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _status_digest(lines: list[str]) -> str:
    payload = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def snapshot(corpus_path: str | os.PathLike[str] | None = None) -> dict:
    root = resolve_corpus_root(corpus_path)
    porcelain = _git(root, ["status", "--porcelain=v1"]).splitlines()
    tag_commit = _git(root, ["rev-parse", FROZEN_TAG])
    return {
        "corpus_root": str(root),
        "frozen_tag": FROZEN_TAG,
        "tag_commit": tag_commit,
        "expected_tag_commit": PINNED_COMMIT,
        "head": _git(root, ["rev-parse", "HEAD"]),
        "branch": _git(root, ["branch", "--show-current"]),
        "status_porcelain": porcelain,
        "status_sha256": _status_digest(porcelain),
        "untracked_count": sum(1 for line in porcelain if line.startswith("?? ")),
        "disallowed_status_entries": [
            line for line in porcelain if not line.startswith("?? ")
        ],
    }


def assert_frozen(corpus_path: str | os.PathLike[str] | None = None) -> dict:
    snap = snapshot(corpus_path)
    if snap["tag_commit"] != PINNED_COMMIT:
        raise CorpusFrozenStateError(
            f"{FROZEN_TAG}={snap['tag_commit']} != expected {PINNED_COMMIT}"
        )
    if snap["disallowed_status_entries"]:
        raise CorpusFrozenStateError(
            "corpus has modified/staged/deleted entries: "
            + repr(snap["disallowed_status_entries"])
        )
    return snap
