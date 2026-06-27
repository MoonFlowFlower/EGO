# EgoDesktop Joi Real-Loop G-ABLATION Preregistration Manifest v0 Review

## Claude Review 1

- reviewer: `desktop Claude / source-limited`
- submitted manifest SHA256:
  `ff719a09aa3ea34293f0f23c9aad444120cfe11c1017e2878e11d04a8b5237dd`
- submitted prompt-pack SHA256:
  `0efa84cc27e9ab7fee74c28b5b5fb615633c92c5ba7a1a2902372c187ee82404`
- verdict: `BLOCKING_FINDINGS`

Blocking findings preserved for the task record:

- B-011-1: heldout prompts were too close to calibration templates/positions. The reviewer measured high cross-split
  surface overlap in the submitted pack and treated the split as insufficient for a meaningful generalization check.
- B-011-2: the near-duplicate gate was internally inconsistent because the scanner used surface Jaccard while the claim
  sounded semantic; the original thresholds also failed the intended positive-control behavior.
- B-011-3: the binomial design used 160 rows as if iid, but the submitted packs were structured as 20 families x 8
  intents, so the effective independent unit could be much smaller.

Advisories preserved for the task record:

- A-011-1: predeclare expression-name base rate, entropy, and CREATURE_ON vs CREATURE_FROZEN movement rate; block
  degenerate near-constant expression channels.
- A-011-2: clarify that `chat_turn.expression_name` and `adapter_output.expression_name` are a row-level consistency
  relation, not two independent scored channels.
- A-011-3: narrow any future saturation claim to this single expression-name channel and distribution.

## Repaired v2 Pending Review

- repaired manifest SHA256:
  `25af2cf6644a0c1d4beb37cd3d9dfaae5d9b87d16b90fed0df70d86f4d343b63`
- repaired prompt-pack SHA256:
  `cafe9a2336e251c4cd3d4bc0397dde207e3a6ad1d7decb372219dd5f1e9d0199`
- status: `awaiting_claude_re_review`

Repair readback:

- B-011-1 repair: prompt packs now contain 160 calibration prompts and 160 heldout prompts, with 160 independent prompt
  families per split and one prompt per family.
- B-011-2 repair: the scanner is explicitly a surface-template overlap gate, not a semantic-equivalence gate. Thresholds
  are token `0.45` and char-5gram `0.25`; the positive control triggers and the negative control passes.
- B-011-3 repair: the equivalence gate uses `independent_prompt_family` as the unit. Repeated rows per family require
  family-level collapse or block as `blocked_clustered_or_underpowered_equivalence_design`.
- Advisory repair: anti-degeneracy reporting and block status are predeclared; D-field relation is clarified; future
  saturation wording is limited to the single `adapter_output.expression_name` channel and this distribution.

## Review Scope

Claude should review only the repaired preregistration boundary:

- `PREREGISTRATION_MANIFEST.json`
- `PROMPT_PACKS.json`
- SHA sidecars
- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `MUTATION_SCOPE.yaml`
- `Tasks/TASK_BOARD.yaml` entry

Claude should not treat this as permission to capture `CREATURE_ON`, run same-access baselines, score, compare, emit a
verdict, update program state/evidence ledger, push, tag, or remote-anchor.

## Requested Verdict Format

- `NO_BLOCKING_FINDINGS`, with next minimal action; or
- `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and next minimal action.

## Claude Review 2

- reviewer: `desktop Claude / source-limited`
- submitted manifest SHA256:
  `25af2cf6644a0c1d4beb37cd3d9dfaae5d9b87d16b90fed0df70d86f4d343b63`
- submitted prompt-pack SHA256:
  `cafe9a2336e251c4cd3d4bc0397dde207e3a6ad1d7decb372219dd5f1e9d0199`
- verdict: `BLOCKING_FINDINGS`

Accepted repairs:

- B-011-2/B-011-3 statistical repairs were accepted at the framework layer: `independent_prompt_family` unit,
  `cluster_guard`, calibrated surface-template overlap gate, positive/negative controls, anti-degeneracy gate, single
  scored `adapter_output.expression_name` channel, and narrowed claim ceiling.
- Claude noted its shell/FUSE view served stale/truncated bytes, but used host-authoritative ripgrep/Grep for prompt
  structure. This was treated as a Claude environment issue, not a local hash failure.

New blocking findings:

- B-011-4: prompt text leaks split/meta identity. Calibration prompts contain `Calibration` wording and heldout prompts
  contain `Heldout`, `Evaluation`, or `Review split` wording, so the future user text would expose split membership and
  would not resemble credible desktop-chat user text.
- B-011-5: nominal 160 independent prompt families per split collapse to a small set of repeated sentence templates.
  Unique `independence_unit_id` values alone do not prove effective independence if expression output is template driven.
- B-011-6: all prompts remain in one low-intensity calm affect band. The manifest does not decide whether it tests
  prompt-affect generalization or internal-state trajectory behavior; each interpretation needs a different design.

Claude recommended not attempting a third synthetic prompt-pack repair. The next decision is between:

- A: replace the synthetic packs with a separate design based on real captured desktop chat turns, requiring a new task
  card and no 011 capture/scoring authority; or
- B: close or downgrade the synthetic-pack attribution path without claiming saturation or route success.

Codex local routing response: choose a conservative docs-only B-like route decision for the synthetic-pack path only.
This does not claim baseline saturation, `CREATURE_ON` redundancy, route advancement, or mechanism evidence.
