# EGO-FS-093: Functional Subject Repair-Dependence Audit v0

## Goal

Turn the Loop 120 GPT-5.5 follow-up risk, "reduce runtime-repair dependence",
into a replayable repair-dependence audit with owners, priority, and the next
behavior-changing slice.

## Positive Mechanism Target

Make Functional Subject first-pass behavior more observable by separating:

- clean LLM / native gate / outcome-prediction paths;
- runtime repair and terminal guard paths;
- mechanism-critical repair causes;
- observation-only repair causes;
- the next minimal behavior-changing slice.

## Acceptance

- Read the Loop 120 #94 report.
- Classify every runtime-repair case.
- Select priority cases by mechanism-criticality, not by cosmetic wording.
- Output JSON and Markdown reports.
- Do not change runtime behavior, memory authority, program state, evidence
  ledger, GitHub truth source, or legacy code.

## Rollback

Remove this task directory, remove `EGO-FS-093` from `Tasks/TASK_BOARD.yaml`,
and delete `scripts/analyze_functional_subject_repair_dependence.py` plus its
test.

## Claim Ceiling

`Functional Subject repair-dependence audit local workflow candidate pass`

Does not claim runtime-repair dependence is solved, runtime efficacy, stable user
benefit, durable memory efficacy, live autonomy, consciousness, real subjective
experience, or independent personhood.
