# Ego_handmade Algorithm Inventory

Status: `replacement candidate / operator cut`

Claim ceiling: `Ego_handmade replacement candidate with extracted primitives`.

This inventory records what is worth extracting from `EgoCore`, `OpenEmotion`,
and `ego_desktop_lab` without importing their runtime architecture. The
operator path remains:

`user text -> LLM understanding -> candidate response/plan -> gate`

No item below authorizes demoting, archiving, or modifying the old projects.

## Structure Risk Check

- Real target: improve operator experience and preserve natural-language
  understanding, not merely reorganize folders.
- Main risk: copying old route/template/schema layers would reintroduce the
  same semantic flattening that made paraphrases fail.
- Contract first: primitives must be readonly or gate-owned; LLM proposes,
  outer gate admits side effects, and trace records what happened.
- Counterexample gate: if adding primitives makes "你觉得黑暗之魂怎么样" and
  "你认为黑暗之魂如何" diverge, the extraction is wrong.
- Current validation: local tests can only prove candidate-local primitive
  wiring and paraphrase harness behavior, not formal replacement.

## EgoCore Extraction

### Keep

- Safety gate as final admission for tools, files, commands, network, memory
  writes, and claim ceiling.
- Workspace path containment before file read/write.
- UTF-8 JSONL trace and replay-readable audit records.
- Tool execution boundary: model proposes tool calls; runtime decides and
  executes.
- Output claim checker concept: visible claims must not exceed evidence.

### Rewrite

- Transport ideas such as Telegram/CLI profiles, but only after the operator
  candidate passes local gates.
- Trace/replay formatting can be simplified into Ego_handmade-local JSONL.
- Team/subagent dispatch can remain isolated worker reports, not shared state.

### Discard

- Chat keyword routing before LLM understanding.
- Template fallback answers for open-ended user meaning.
- Complex proactive main-chain behavior in this operator cut.
- Any path where a tool or subagent mutates lead memory/todo directly.

### Reference-Only

- Formal EGO program-state and evidence governance.
- Existing Telegram production launcher details.
- Mainline acceptance ledger and old live evidence.

## OpenEmotion Extraction

### Keep

- Self-model snapshot as readonly context.
- Appraisal signal as candidate context, never as reply owner.
- Memory salience as bounded prompt context, not canonical memory mutation.
- Reflection proposal as optional reasoning support.
- Initiative candidate as a proposal only.

### Rewrite

- Subject signals are represented in `primitives/subject_context.py` as a
  small readonly snapshot.
- Any core-memory proposal must be written to candidate updates or surfaced to
  the operator, not auto-promoted.

### Discard

- Direct state mutation from subject context.
- Visible reply ownership by a lower-level subject signal.
- Any rule that compresses the latest user message into a keyword route before
  the LLM reads it.

### Reference-Only

- Proto-self internals and developmental memory details.
- Formal `subject_system_v1_governed_proactivity` live evidence chain.

## ego_desktop_lab Extraction

### Keep

- Paraphrase suite design for checking stable understanding.
- Deterministic replay idea.
- Operator report format for scenario comparison.
- Corpus/eval harness concepts for natural Q&A, tool refusal recovery, and
  long-task breakdown.

### Rewrite

- Eval harnesses become local primitive tests under `Ego_handmade/tests/`.
- Lab reports should compare candidate behavior; they must not become runtime
  routing tables.

### Discard

- Lab shell as production runtime.
- Semantic router as the first step of user-message handling.
- Template matching as a substitute for natural-language response generation.

### Reference-Only

- Existing lab scenario notes and previous acceptance docs.

## Current Primitive Layout

- `primitives/subject_context.py`: readonly self/appraisal/reflection context.
- `primitives/runtime_gate.py`: local gate and claim-ceiling contract.
- `primitives/evals.py`: paraphrase and operator-behavior eval primitives.

## Next Gate

Run the 20-case Dark Souls paraphrase gate and the five-scenario operator
comparison. Only if `Ego_handmade` stays better on experience, explainability,
side-effect control, and trace readability should a separate
`ego-mainline-demotion-v1` task be opened.
