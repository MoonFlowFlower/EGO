# JOI-DEMO-HISTORY-TO-EGO-REFERENCE-ADMISSION-001A — Stage Card

Status: ACCEPTED_DOCS_ONLY / NO_CODE_YET / NOT_RUNTIME_CONNECTED.
Created: 2026-07-06. Operator-architected.

## Purpose

Admit the frozen joi-demo corpus (tag `frozen-reference-corpus-20260706`,
commit `52714ed9f7ede8dfd14da7f4c310a9e9db28c834`, path `D:\Project\AIProject\MyProject\joi-demo`,
read-only) as a REFERENCE INPUT for Ego — without porting any toy
implementation, and without connecting anything to Ego runtime.

Architecture rule (operator, 2026-07-06):

```text
joi-demo = frozen reference corpus. Ego = clean implementation surface.
What migrates is interfaces and evidence constraints only: trace schema,
replay requirement, baseline/ablation contract, artifact manifest shape,
claim-ceiling discipline. Mechanism code that ever enters Ego is rewritten
clean, default-off, harness-only, admission-gated, and regression-tested
against frozen joi-demo artifacts — never copied.
```

## Allowed first implementations (this card's entire executable scope)

1. `frozen trace reader` — parses corpus trace/artifact files read-only.
2. `artifact manifest verifier` — validates manifest shape + sha pins
   (including CreatureState v0.2 pins: card `5f1afdb3…`, schema `ddcce43f…`).
3. `baseline/result schema importer` — re-expresses the corpus result/baseline
   /ablation report shapes as Ego-side formal contracts (docs + validators).
4. `compatibility tests` — pytest-style tests proving 1-3 read the frozen
   corpus byte-faithfully (path configurable; corpus never modified).

All default-off, harness-only, no EgoOperator/EgoDesktop import, no runtime
registration, no gate/approval/transport/proactive path.

## Explicitly NOT allowed from this card

- porting `stage1/*`, `battery/*`, `skin/*`, or any toy runner into Ego;
- wiring anything to Ego runtime, EgoDesktop loop, or PSPC surfaces;
- re-running, re-scoring, or reinterpreting corpus experiments;
- upgrading any corpus claim (index ceilings are final);
- writing to the joi-demo folder.

## Acceptance

`reference_admission_readback_pass` = reader + verifier + importer +
compatibility tests green against the frozen tag, with no corpus mutation
(hash-verified before/after). Only that verdict — and a separate future
decision card — may open any mechanism-rewrite work. Expected honest failure
modes: manifest drift, EOL/hash mismatch (known FUSE history: verify
host-native), schema ambiguity → record, do not patch corpus.

## Claim ceiling

`frozen_reference_corpus_admission_only`. File-format compatibility evidence
only. Does not prove mechanism validity, transfer of any joi-demo Bar-1
result to Ego scale, runtime integration safety, durable memory, learning
headroom, user benefit, live autonomy, agency, emotion, subjectivity, or
consciousness.
