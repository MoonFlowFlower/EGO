"""Inventory and recovery verifier for pre-V2 runtime retirement."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Iterable
import uuid


RETIRED_ROOTS = (
    "EgoDesktop/",
    "EgoOperator/",
    ".agents/skills/ego-operator-devloop/",
)
RETIRED_EXACT = frozenset(
    {
        "scripts/ego_desktop_pspc_signal_extract.py",
        "scripts/ego_desktop_tts_worker.py",
        "scripts/ego_operator_desktop_turn.py",
        "scripts/ego_operator_devloop.py",
        "scripts/pspc_shadow_contracts.py",
        "scripts/run_devloop_smoke_e2e.py",
        "scripts/run_ego_experience_trial.py",
        "scripts/run_live2d_desktop.py",
        "scripts/run_runtime_mainline_observation.py",
        "scripts/runtime_mainline_observation_common.py",
        "scripts/codex/audit_worktree_noise.py",
        "scripts/codex/build_capability_registry.py",
        "scripts/codex/check_program_state_integrity.py",
        "scripts/codex/check_runtime_authority_boundaries.py",
        "scripts/codex/generate_program_state_views.py",
        "scripts/codex/generate_route_convergence_views.py",
        "scripts/codex/program_state_common.py",
        "scripts/codex/route_convergence_common.py",
        "scripts/codex/verify_mainline_clarity.py",
        "scripts/codex/tests/test_route_governance_supersession.py",
        "scripts/tests/test_route_governance_supersession.py",
    }
)
RETIRED_PREFIXES = (
    "scripts/run_pspc_",
    "scripts/codex/build_egodesktop_",
    "scripts/codex/materialize_egodesktop_",
    "scripts/codex/run_egodesktop_",
    "scripts/codex/run_egooperator_",
    "scripts/tests/test_build_egodesktop_",
    "scripts/tests/test_materialize_egodesktop_",
    "scripts/tests/test_run_egodesktop_",
    "scripts/tests/test_run_egooperator_",
    "scripts/tests/test_ego_operator_devloop",
    "scripts/tests/test_run_ego_experience_trial",
    "tests/test_ego_operator_",
    "tests/test_ego_desktop_",
    "tests/test_egodesktop_",
    "tests/test_pspc_",
)
SOURCE_SUFFIXES = frozenset({".py", ".js", ".mjs", ".cjs", ".ts", ".tsx"})
SCAN_EXCLUDED_ROOTS = frozenset(
    {".git", ".venv", "node_modules", "dist", "artifacts", "docs", "legacy", "Tasks", ".repo-quarantine", "EgoDesktop", "EgoOperator"}
)


@dataclass(frozen=True)
class RecoveryVerification:
    verdict: str
    errors: tuple[str, ...]
    producer_function: str
    input_artifacts: tuple[str, ...]
    run_id: str
    aggregation_rule: str
    code_path_hash: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["errors"] = list(self.errors)
        payload["input_artifacts"] = list(self.input_artifacts)
        return payload


def _run(repo: Path, *args: str, text: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.decode("utf-8") if text else result.stdout


def _tree(repo: Path, ref: str) -> dict[str, dict[str, str]]:
    raw = _run(repo, "ls-tree", "-r", "-z", ref)
    assert isinstance(raw, bytes)
    rows: dict[str, dict[str, str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        rows[raw_path.decode("utf-8")] = {"mode": mode, "kind": kind, "oid": oid}
    return rows


def _cat_file_blobs(repo: Path, object_oids: list[str]) -> list[tuple[str, bytes]]:
    """Read many Git blobs through one binary-safe batch process."""

    if not object_oids:
        return []
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input=("\n".join(object_oids) + "\n").encode("ascii"),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output = result.stdout
    offset = 0
    blobs: list[tuple[str, bytes]] = []
    for expected_oid in object_oids:
        newline = output.find(b"\n", offset)
        if newline < 0:
            raise ValueError("truncated cat-file batch header")
        header = output[offset:newline].decode("ascii")
        parts = header.split()
        if len(parts) != 3 or parts[1] != "blob":
            raise ValueError(f"unexpected cat-file batch header: {header}")
        actual_oid, _kind, size_text = parts
        size = int(size_text)
        start = newline + 1
        end = start + size
        if end >= len(output) or output[end : end + 1] != b"\n":
            raise ValueError("truncated cat-file batch body")
        if actual_oid != expected_oid:
            raise ValueError("cat-file batch order mismatch")
        blobs.append((actual_oid, output[start:end]))
        offset = end + 1
    if offset != len(output):
        raise ValueError("unexpected trailing cat-file batch bytes")
    return blobs


def _is_retired(path: str) -> bool:
    return (
        path in RETIRED_EXACT
        or any(path.startswith(prefix) for prefix in RETIRED_ROOTS)
        or any(path.startswith(prefix) for prefix in RETIRED_PREFIXES)
    )


def select_retired_paths(repo_root: str | Path, *, ref: str = "HEAD") -> tuple[str, ...]:
    tree = _tree(Path(repo_root).resolve(), ref)
    return tuple(sorted(path for path in tree if _is_retired(path)))


def _python_import_hits(path: str, raw: bytes) -> list[str]:
    try:
        tree = ast.parse(raw.decode("utf-8"), filename=path)
    except (SyntaxError, UnicodeDecodeError):
        return []
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "EgoOperator" or alias.name.startswith("EgoOperator."):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "EgoOperator" or module.startswith("EgoOperator."):
                hits.append(module)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"import_module", "spec_from_file_location"} and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if "EgoOperator" in arg.value or "EgoDesktop" in arg.value:
                        hits.append(arg.value)
    return sorted(set(hits))


JS_CALLER = re.compile(
    r"(?:from\s+|require\s*\(\s*|import\s*\(\s*)['\"][^'\"]*(?:EgoOperator|EgoDesktop)[^'\"]*['\"]",
    re.I,
)


def _source_hits(path: str, raw: bytes) -> list[str]:
    if path.endswith(".py"):
        return _python_import_hits(path, raw)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return []
    return sorted(set(match.group(0) for match in JS_CALLER.finditer(text)))


def _iter_current_source(root: Path) -> Iterable[tuple[str, bytes]]:
    for directory, names, files in os.walk(root, topdown=True, onerror=lambda _exc: None):
        names[:] = [name for name in names if name not in SCAN_EXCLUDED_ROOTS]
        base = Path(directory)
        for name in files:
            path = base / name
            if path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            try:
                rel = path.relative_to(root).as_posix()
                raw = path.read_bytes()
            except OSError:
                continue
            yield rel, raw


def scan_current_legacy_callers(repo_root: str | Path) -> tuple[dict[str, Any], ...]:
    findings: list[dict[str, Any]] = []
    for path, raw in _iter_current_source(Path(repo_root).resolve()):
        hits = _source_hits(path, raw)
        if hits:
            findings.append({"path": path, "hits": hits})
    return tuple(sorted(findings, key=lambda row: row["path"]))


def _tag_callers(repo: Path, ref: str, tree: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, meta in sorted(tree.items()):
        if (
            Path(path).suffix.lower() not in SOURCE_SUFFIXES
            or path.split("/", 1)[0] in SCAN_EXCLUDED_ROOTS
        ):
            continue
        raw = _run(repo, "cat-file", "blob", meta["oid"])
        assert isinstance(raw, bytes)
        hits = _source_hits(path, raw)
        if hits:
            rows.append({"path": path, "hits": hits, "retired_with_target": _is_retired(path)})
    return rows


def build_retirement_manifest(
    repo_root: str | Path,
    *,
    tag: str,
    task_id: str,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    commit = str(_run(repo, "rev-parse", f"{tag}^{{commit}}", text=True)).strip()
    tree_oid = str(_run(repo, "rev-parse", f"{commit}^{{tree}}", text=True)).strip()
    tree = _tree(repo, tag)
    removed: list[dict[str, Any]] = []
    for path in select_retired_paths(repo, ref=tag):
        meta = tree[path]
        raw = _run(repo, "cat-file", "blob", meta["oid"])
        assert isinstance(raw, bytes)
        removed.append(
            {
                "path": path,
                "mode": meta["mode"],
                "object_type": meta["kind"],
                "object_oid": meta["oid"],
                "byte_length": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "legacy_import_or_caller_hits": _source_hits(path, raw),
                "classification": "retired_pre_v2_runtime_current_tree_path",
                "rollback": f"git show {tag}:{path}",
                "claim_boundary": "historical implementation only; no current runtime or mechanism authority",
            }
        )
    manifest = {
        "schema_version": "ego.pre_v2_runtime_retirement_manifest.v1",
        "task_id": task_id,
        "producer_function": "build_retirement_manifest",
        "input_artifacts": [f"{tag}^{{commit}}", f"{tag}^{{tree}}"],
        "run_id": f"retired-runtime-inventory-{uuid.uuid4().hex}",
        "aggregation_rule": "include every tracked path selected by the frozen retirement rules at the local rollback tag",
        "code_path_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rollback_tag": tag,
        "rollback_commit": commit,
        "rollback_tree": tree_oid,
        "publication": "local_only_forbidden_to_push",
        "removed_path_count": len(removed),
        "removed_paths": removed,
        "caller_inventory": _tag_callers(repo, tag, tree),
        "claim_ceiling": "local current-tree retirement and Git-object recovery provenance only",
    }
    manifest["removed_path_set_sha256"] = hashlib.sha256(
        ("\n".join(row["path"] for row in removed) + "\n").encode()
    ).hexdigest()
    return manifest


def verify_manifest_recoverable(repo_root: str | Path, manifest: dict[str, Any]) -> RecoveryVerification:
    repo = Path(repo_root).resolve()
    errors: list[str] = []
    tag = str(manifest.get("rollback_tag", ""))
    try:
        commit = str(_run(repo, "rev-parse", f"{tag}^{{commit}}", text=True)).strip()
        if commit != manifest.get("rollback_commit"):
            errors.append("rollback_commit_mismatch")
        tree = _tree(repo, tag)
        rows = list(manifest.get("removed_paths", []))
        object_oids: list[str] = []
        for row in rows:
            path = row["path"]
            oid = tree.get(path, {}).get("oid", "")
            if oid != row["object_oid"]:
                errors.append(f"object_oid_mismatch:{path}")
            object_oids.append(oid)
        for row, (oid, raw) in zip(rows, _cat_file_blobs(repo, object_oids), strict=True):
            path = row["path"]
            if hashlib.sha256(raw).hexdigest() != row["sha256"]:
                errors.append(f"sha256_mismatch:{path}")
    except (OSError, KeyError, subprocess.SubprocessError, ValueError) as exc:
        errors.append(f"recovery_error:{type(exc).__name__}")
    return RecoveryVerification(
        verdict="pass" if not errors else "fail",
        errors=tuple(errors),
        producer_function="verify_manifest_recoverable",
        input_artifacts=(tag, "artifacts/archive/pre_v2_runtime_retirement_manifest.json"),
        run_id=f"retired-runtime-recovery-{uuid.uuid4().hex}",
        aggregation_rule="pass iff tag commit and every recorded blob OID/SHA are independently recoverable",
        code_path_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )


def write_manifest(path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_untracked_retired_files(
    repo_root: str | Path,
    *,
    quarantine_root: str | Path,
    tracked_ref: str,
) -> dict[str, Any]:
    """Hash every untracked file under retired roots before moving it."""

    repo = Path(repo_root).resolve()
    quarantine = Path(quarantine_root).resolve()
    if quarantine == repo or repo in quarantine.parents:
        raise ValueError("quarantine root must be outside the Ego repository")
    tracked = set(_tree(repo, tracked_ref))
    entries: list[dict[str, Any]] = []
    for root_text in RETIRED_ROOTS:
        base = repo / root_text.rstrip("/")
        if not base.exists():
            continue
        for directory, _names, files in os.walk(base, followlinks=False):
            for name in files:
                path = Path(directory) / name
                relative = path.relative_to(repo).as_posix()
                if relative in tracked:
                    continue
                if path.is_symlink():
                    link_text = os.readlink(path)
                    raw = link_text.encode("utf-8", errors="surrogateescape")
                    kind = "symlink"
                    sha = hashlib.sha256(raw).hexdigest()
                    size = len(raw)
                else:
                    kind = "file"
                    sha = _file_sha256(path)
                    size = path.stat().st_size
                target = quarantine / relative
                entries.append(
                    {
                        "source_path": relative,
                        "kind": kind,
                        "byte_length": size,
                        "sha256": sha,
                        "quarantine_path": str(target),
                        "rollback": f"move {target} -> {repo / relative}",
                        "claim_boundary": "untracked local data preserved outside active repo; no evidence or runtime authority",
                    }
                )
    entries.sort(key=lambda row: row["source_path"])
    return {
        "producer_function": "inventory_untracked_retired_files",
        "input_artifacts": list(RETIRED_ROOTS),
        "aggregation_rule": "enumerate and hash every non-tag-tracked file below the retired roots before moving any root",
        "code_path_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "quarantine_root": str(quarantine),
        "file_count": len(entries),
        "total_bytes": sum(row["byte_length"] for row in entries),
        "entries": entries,
        "entry_set_sha256": hashlib.sha256(
            ("\n".join(row["source_path"] for row in entries) + "\n").encode()
        ).hexdigest(),
    }


def move_preserved_untracked_roots(
    repo_root: str | Path,
    inventory: dict[str, Any],
) -> dict[str, Any]:
    """Move post-deletion retired roots to the verified external quarantine."""

    repo = Path(repo_root).resolve()
    quarantine = Path(inventory["quarantine_root"]).resolve()
    if quarantine == repo or repo in quarantine.parents:
        raise ValueError("quarantine root must remain outside the Ego repository")
    expected = {row["source_path"] for row in inventory.get("entries", [])}
    remaining: set[str] = set()
    for root_text in RETIRED_ROOTS:
        source = (repo / root_text.rstrip("/")).resolve()
        if source.exists():
            if repo not in source.parents:
                raise ValueError(f"retired source outside repo: {source}")
            for directory, _names, files in os.walk(source, followlinks=False):
                for name in files:
                    remaining.add((Path(directory) / name).relative_to(repo).as_posix())
    if remaining != expected:
        raise ValueError("remaining retired-root file set does not equal the preserved untracked inventory")
    moved_roots: list[dict[str, str]] = []
    quarantine.mkdir(parents=True, exist_ok=True)
    for root_text in RETIRED_ROOTS:
        source = (repo / root_text.rstrip("/")).resolve()
        if not source.exists():
            continue
        target = (quarantine / root_text.rstrip("/")).resolve()
        if quarantine not in target.parents or target.exists():
            raise ValueError(f"unsafe or occupied quarantine target: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        moved_roots.append({"source": str(source), "target": str(target)})
    errors: list[str] = []
    for row in inventory.get("entries", []):
        target = Path(row["quarantine_path"])
        if not target.exists():
            errors.append(f"missing:{row['source_path']}")
            continue
        actual = (
            hashlib.sha256(os.readlink(target).encode("utf-8", errors="surrogateescape")).hexdigest()
            if row["kind"] == "symlink"
            else _file_sha256(target)
        )
        if actual != row["sha256"]:
            errors.append(f"sha256:{row['source_path']}")
    return {
        "verdict": "pass" if not errors else "fail",
        "producer_function": "move_preserved_untracked_roots",
        "aggregation_rule": "move only after remaining file set equality, then recompute every quarantine hash",
        "moved_roots": moved_roots,
        "errors": errors,
    }


def verify_preserved_untracked_inventory(
    repo_root: str | Path,
    inventory: dict[str, Any],
) -> dict[str, Any]:
    """Recompute quarantine completeness and hashes after the retired roots moved."""

    repo = Path(repo_root).resolve()
    quarantine = Path(inventory["quarantine_root"]).resolve()
    errors: list[str] = []
    if quarantine == repo or repo in quarantine.parents:
        errors.append("quarantine_inside_repo")

    for root_text in RETIRED_ROOTS:
        if (repo / root_text.rstrip("/")).exists():
            errors.append(f"active_retired_root:{root_text.rstrip('/')}")

    expected_rows = {
        str(row["source_path"]): row for row in inventory.get("entries", [])
    }
    actual_paths: set[str] = set()
    if quarantine.is_dir():
        for directory, _names, files in os.walk(quarantine, followlinks=False):
            for name in files:
                target = Path(directory) / name
                actual_paths.add(target.relative_to(quarantine).as_posix())
    else:
        errors.append("quarantine_missing")

    expected_paths = set(expected_rows)
    for path in sorted(expected_paths - actual_paths):
        errors.append(f"missing:{path}")
    for path in sorted(actual_paths - expected_paths):
        errors.append(f"unexpected:{path}")

    for source_path in sorted(expected_paths & actual_paths):
        row = expected_rows[source_path]
        target = quarantine / source_path
        if row["kind"] == "symlink":
            if not target.is_symlink():
                errors.append(f"kind:{source_path}")
                continue
            raw = os.readlink(target).encode("utf-8", errors="surrogateescape")
            actual_sha = hashlib.sha256(raw).hexdigest()
            actual_size = len(raw)
        else:
            if not target.is_file() or target.is_symlink():
                errors.append(f"kind:{source_path}")
                continue
            actual_sha = _file_sha256(target)
            actual_size = target.stat().st_size
        if actual_size != int(row["byte_length"]):
            errors.append(f"byte_length:{source_path}")
        if actual_sha != row["sha256"]:
            errors.append(f"sha256:{source_path}")

    path_set_sha = hashlib.sha256(
        ("\n".join(sorted(actual_paths)) + "\n").encode()
    ).hexdigest()
    if path_set_sha != inventory.get("entry_set_sha256"):
        errors.append("entry_set_sha256")
    if len(actual_paths) != int(inventory.get("file_count", -1)):
        errors.append("file_count")

    return {
        "verdict": "pass" if not errors else "fail",
        "producer_function": "verify_preserved_untracked_inventory",
        "input_artifacts": [
            "artifacts/archive/pre_v2_runtime_retirement_manifest.json",
            str(quarantine),
        ],
        "run_id": f"retired-untracked-recovery-{uuid.uuid4().hex}",
        "aggregation_rule": "pass iff active retired roots are absent and quarantine path set, byte lengths, and every SHA-256 equal the frozen inventory",
        "code_path_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "quarantine_root": str(quarantine),
        "file_count": len(actual_paths),
        "total_bytes": sum(int(row["byte_length"]) for row in expected_rows.values()),
        "entry_set_sha256": path_set_sha,
        "errors": errors,
    }
