# SwitchLab Implementation Plan

Goal: a usable offline Python package with an actual observe/infer/plan/act/update loop,
visible traces and reproducible checks. Architecture: finite Bayesian state estimator,
budgeted POMDP planner, goal/commitment bookkeeping, independent world and evidence runner.
Tech stack: Python >=3.10 standard library; vanilla local HTML/CSS/JavaScript.
Spec: DESIGN.md. Native execution in a newly created isolated local artifact workspace.

## Constraints and review focus
No network dependencies or real external actions; no modification of user repositories.
Check invisible-state leakage, duplicated replay evidence, checkpoint continuity,
informative-vs-random signals, loopback request forgery, and negative comparison reporting.

## Tasks
- [x] 1. Write and run failing world/filter tests. Implement separate physical kernels,
      seeded world, finite likelihood model and Bayesian updates. Run full tests.
- [x] 2. Write and run failing planner tests. Implement contingent lookahead, generated
      outcome goals, persistent commitments, baselines, and scoped ablations. Run tests.
- [x] 3. Write and run failing persistence/replay tests. Implement deterministic Session,
      hash-chained event trace, snapshots, semantic replay and tamper detection.
- [x] 4. Write and run failing HTTP/CLI tests. Implement local dashboard, bounded commands,
      safe launchers, validation and export. Check a real browser where available.
- [x] 5. Freeze numerical experiment configuration; execute independent-life baseline and
      ablation comparisons. Save raw rows and summarize without changing the gate.
- [x] 6. Run tests from an extracted archive, verify source/manifest/replay, document
      failures, limits, and run instructions. Deliver the archive and observed evidence.
