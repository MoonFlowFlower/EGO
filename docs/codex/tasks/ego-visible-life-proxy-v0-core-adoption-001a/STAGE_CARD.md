# EGO-VISIBLE-LIFE-PROXY-V0-CORE-ADOPTION-001A — authority-sync revision

## Operator authorization

The operator authorized the ITL product-core adoption at commit
`619bff5fd9400bba00002af26f65ce73894a9dce`, then authorized the necessary
Ego-side repair/synchronization while asking that effort return to product
development rather than further version-control churn.

This card therefore executes only the ITL-authorized action:

```text
sync_EGO_visible_life_proxy_v0_product_core_authority_under_separate_task
```

ITL already selected Ego commit
`546e3639299d7b11b599df3d00645666a6953bac` as the immutable Git-object
baseline and sole visible-life product-development lineage. Ego does not make
that decision again. This task transcribes the committed product-axis packet,
validates it against Git objects, preserves the old Card2/K0 closures, and
banks a separate Ego-local replayable product-trigger receipt.

## Problem definition

The current dirty candidate was drafted before ITL committed the product-axis
decision. It still binds ITL `55706c...`, requests the stale local `adopt_*`
action, conflates ITL trigger status with Ego-local trigger evidence, and
exposes a shortened V1 action. Committing that candidate would create a second
authority path. The bounded repair is to synchronize the exact committed ITL
packet and keep product evidence, runtime authority, and science claims
separate.

## Current layer

Layer 2 — engineering implementation and cross-repo evidence-governance.

## Mainline target

- Product-development lineage: `ego_life_playground_v0`, as selected by ITL.
- Runtime mainline: unchanged; EgoOperator remains the sole active default.
- V0: `enabled=false`, `default_enabled=false`,
  `runtime_mainline_connected=false`, `runtime_authority=none`.
- Science: `science_weight=0`; no K0/Card2/science successor is reopened.

## Enabled-state requirement

No service, autostart, EgoOperator/EgoDesktop registration, LLM/network path,
runtime authority, or V1 implementation may be enabled. The explicit V0 local
launcher remains callable only by an operator.

## Real-trigger evidence requirement

Two non-interchangeable fields are required:

```text
ITL transition: UNVERIFIED_IN_THIS_ITL_TRANSITION
Ego local product trigger: BANKED_RECOMPUTING_PRODUCT_TRIGGER
```

The Ego-local receipt must recompute controller -> durable SQLite -> restart /
recover -> re-export and byte-compare the committed trace. It is product-clock
engineering evidence only and must never replace or upgrade the ITL field.

## Hypothesis

An exact Git-object pin set, exhaustive product-axis/state/closure crosswalk,
callable sync validator, and separate local trigger receipt can remove the
parallel-authority ambiguity without rewriting V0 or delaying the next bounded
product-development card.

## Strongest baseline / shortcut explanation

1. A prose sentence saying "V0 is core".
2. Ego locally self-declaring `SOLE` without the ITL packet.
3. A commit string without per-object blob and payload checks.
4. Treating the visible replayable demo as mechanism or science evidence.

Any of these can reproduce the appearance of governance closure without
binding the real authority or causal evidence.

## Ablation / mutation requirement

Callable checks must reject:

- the stale `adopt_EGO-*` action or shortened V1 action;
- wrong ITL commit, object OID, payload SHA-256, state, closure, event, report,
  transition card, or Red receipt;
- any omitted/extra/non-verbatim product-axis crosswalk leaf;
- ITL/Ego trigger conflation;
- a second visible-life core or reopened predecessor action;
- V1 implementation, runtime/mainline/default enablement, non-empty targets,
  nonzero science weight, or changed EgoOperator/EgoDesktop authority;
- missing/tampered SQLite, trace, manifest, report, or committed replay path.

The crosswalk omission positive control and evidence-tamper controls must fire.

## Trace / replay requirement

The banked product trace must be regenerated from serialized initial state plus
typed commands in SQLite. `recover_run` and `export_run` must reproduce it
byte-for-byte using code loaded from the pinned V0 Git objects. Stored selected
actions alone are not replay evidence.

## Computed-evidence provenance gate

All source pins are read with `git rev-parse` / `git cat-file`; the crosswalk is
rebuilt from committed ITL payload leaves; the V0 baseline/trigger report is
produced by `verify_ego_life_core_v0_baseline.validate_baseline`. Reports must
record producer function, input artifacts, run ID, seed/episode, aggregation
rule, and code-path hash. Hand-shaped pass literals are insufficient.

## Acceptance gate

1. ITL commit `619bff5f...` is present and the seven product-axis objects match
   their frozen blob OIDs and raw payload SHA-256 values.
2. The old Card2/K0 committed-object packet remains unchanged and closed.
3. Product axis, adoption state, and closure are transcribed exhaustively;
   event/report/transition-card/Red-receipt semantics pass callable checks.
4. The exact sync action is consumed; the stale adopt action is rejected.
5. ITL trigger status and Ego-local product trigger are distinct and exact.
6. The full conditional V1 card-draft action is exposed only after this sync
   validator passes; V1 implementation remains unauthorized.
7. V0 Git-object and SQLite restart/re-export evidence recompute successfully.
8. Program-state integrity, route convergence, mainline clarity, focused tests,
   fast verification, and independent Claude Red review of the exact staged
   non-receipt diff pass.
9. One local exact-20-path commit is created; worktree/index are clean; no
   push, tag, or remote anchor occurs.

## Claim ceiling

> Local Ego synchronization to the committed ITL V0 product-axis authority,
> immutable V0 Git-object engineering boundary, and replayable Ego-local
> product trigger only; no runtime-mainline, learning, or mechanism claim.

## Stop condition

STOP before commit if any pin, ancestry, crosswalk, route action, generated
view, Red-review binding, replay/tamper control, runtime/science firewall, or
exact path-set check fails. Do not repair old K0/Card2 packets, modify V0 source,
or widen into V1 implementation.

## Rollback plan

Before commit, remove only task-owned newly created files if this task is
abandoned. Preserve all pre-existing user work and never reset/checkout the
dirty candidate. After commit, corrections require a new additive authorized
task; do not amend or rewrite the baseline.

## Expected changed files

Exactly these 20 paths (19 reviewed paths plus the Red receipt):

- `docs/codex/tasks/ego-visible-life-proxy-v0-core-adoption-001a/STAGE_CARD.md`
- `docs/codex/tasks/ego-visible-life-proxy-v0-core-adoption-001a/COLLISION_RECORD.md`
- `docs/codex/tasks/ego-visible-life-proxy-v0-core-adoption-001a/MUTATION_SCOPE.yaml`
- `docs/codex/tasks/ego-visible-life-proxy-v0-core-adoption-001a/ITL_AUTHORITY_CROSSWALK.json`
- `docs/codex/tasks/ego-visible-life-proxy-v0-core-adoption-001a/PHASE_A_RED_REVIEW.json`
- `artifacts/EGO-LIFE-CORE-V0-DEVELOPMENT-BASELINE-001A/core_baseline_manifest.json`
- `artifacts/EGO-LIFE-CORE-V0-DEVELOPMENT-BASELINE-001A/core_trigger.sqlite3`
- `artifacts/EGO-LIFE-CORE-V0-DEVELOPMENT-BASELINE-001A/core_trigger_trace.jsonl`
- `artifacts/EGO-LIFE-CORE-V0-DEVELOPMENT-BASELINE-001A/core_baseline_validation_report.json`
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/reports/program_state_summary.md`
- `docs/STATUS.md`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `docs/REPO_SURFACE_MAP.md`
- `scripts/codex_session_guard.py`
- `scripts/codex/verify_route_convergence.py`
- `scripts/codex/verify_ego_life_core_v0_baseline.py`
- `scripts/tests/test_codex_session_guard.py`
- `scripts/tests/test_route_governance_supersession.py`
- `scripts/tests/test_verify_ego_life_core_v0_baseline.py`

## Forbidden changes

- all six pinned V0 implementation/test paths;
- `EgoOperator/`, `EgoDesktop/`, LLM/network/runtime registration;
- ITL repository files or historical K0/Card2 objects;
- `docs/MAINLINE_QUICKSTART.md`;
- product policy, outcome tables, memory rules, thresholds, or UI behavior;
- V1 implementation, science experiments/scoring, push, tag, or remote anchor.

## Auto-Remote-Anchor

`Auto-Remote-Anchor: forbidden`

## Next minimal closed-loop action

After this sync is committed and post-commit validation passes, draft only
`EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A` under a separate bounded card.
Its implementation remains separately operator-authorized.
