from __future__ import annotations

import hashlib
from pathlib import Path

TASK_ID = "ego-r2-controlled-initiative-001a"
ARTIFACT_ROOT = Path("artifacts") / "ego-r2-controlled-initiative-001a"
PACKAGE_ROOT = Path(__file__).resolve().parent

CLAIM_CEILING = (
    "bounded offline-simulator engineering evidence that, in env family r2_sim_v0, "
    "a learning-based gated-initiative controller's timing behavior is a control-flow "
    "property whose measured net utility exceeds the frozen static baseline family "
    "under the stated gates."
)
NOT_PROVEN = (
    "This is NOT evidence of initiative desire, motivation, wanting, autonomy, "
    "agency, self-awareness, user benefit, or live-product readiness. Live proactive "
    "/ self-DM remain closed regardless of outcome."
)

GRID_8 = (0, 62, 125, 187, 250, 312, 375, 437)
TICKS_PER_EPISODE = 500
WINDOW_OFFSETS = (90, 250, 410)
WINDOW_WIDTH = 40
DIP_OFFSET = 170
DIP_WIDTH = 60
U_IDEAL_ANALYTIC = 18.48

DEV_SEEDS = (31, 47)
HELDOUT_SEEDS = (61, 79)
DEFAULT_N_EP = 40
DOUBLED_N_EP = 80

UTILITY = {
    "accept": 1.0,
    "reject": -1.0,
    "ignore": -0.2,
    "silent": 0.0,
}

FORBIDDEN_VISIBLE_KEYS = {
    "s",
    "s_t",
    "latent_s",
    "receptivity",
    "receptivity_label",
    "o_t",
    "judge_s",
    "window_phase",
    "dynamics_timer",
}

FORBIDDEN_IMPORT_MODULES = ("torch", "tensorflow", "jax")


def code_path_hash() -> str:
    """Hash the executable R2 package paths for provenance records."""
    digest = hashlib.sha256()
    for path in sorted(PACKAGE_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        if path.suffix not in {".py", ".md"}:
            continue
        rel = path.relative_to(PACKAGE_ROOT).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def provenance_record(*, producer_function: str, run_id: str, seeds: list[int], n_ep: int) -> dict:
    return {
        "producer_function": producer_function,
        "input_artifacts": [
            "docs/codex/tasks/ego-r2-controlled-initiative-001a/STAGE_CARD.md",
            "docs/codex/tasks/ego-r2-controlled-initiative-001a/MUTATION_SCOPE.yaml",
        ],
        "run_id": run_id,
        "seed_context": {"seeds": seeds, "episodes_per_seed": n_ep},
        "aggregation_rule": "common-random-number episode means, pooled and held-out block reported separately",
        "code_path_hash": code_path_hash(),
    }
