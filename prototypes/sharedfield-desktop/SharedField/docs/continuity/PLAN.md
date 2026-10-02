# v0.5 implementation ledger

Goal: based on the supplied test trace, ship a usable update in the existing shared-experience direction.
User explicitly requested continuing development and packaging; previous design and scope retained. Isolated extracted directory /mnt/data/work_v05/SharedField, original ZIP unchanged.

- [x] Baseline 225 tests passed, 37.657s. Original user strict replay FAILED at E000005; first difference integral float JSON representation. Exact Python equality shows all 108 regenerated events match including hash strings; production migration must verify strict typed numeric-normalized equivalence instead of ignoring hashes.
- [x] Task1: tests v04 numeric export migration, portable v5 digest, fresh state replay & no overwrite. Frozen full fingerprint runtime in compatibility archive, isolate verification process.
- [x] Task2: tests goal ownership and stable plan identity, joint commitment/wait/partner difficulty, meaningful memory; extend Mind and Core only bounded actions.
- [x] Task3: tests action-grounded speech, stale physical observation vs dialogue cancellation, pause/new-message still cancel; integrate protocols and service.
- [x] Task4: UI collaboration/concern/memory/intent receipt, import file via same-origin validated API, real HTTP tests and browser probe.
- [ ] Task5: unchanged offline metric, targeted probes, full tests, self-review, docs, manifest, ZIP extraction and full suite/replay/continue. No independent reviewer tool available.

Risk classes: cross-person goal completion; stale paid response; paraphrase guard false positives; numeric bool confusion; unverified imported state; privacy of real user dialogue; automatic looping while waiting; hidden-world leakage; permission expansion.

Review finding: v4 UI-number serialization changed integral floats; keep all old hash strings and typed numeric-equivalent re-execution. Do not claim the original strict reader passed.
Intentional contract replacement: tests expecting physical player input to discard paid answers are replaced by tests expecting exactly one interpret+express, pinned temporal scope. Pause/new-message cancellation is unchanged. Version/schema assertions updated, not experiment thresholds.
TDD review found partner success closed unrelated route concerns, rejoin goal never completed, and non-object import crashed HTTP. Target ownership and validation now tested before fixes. Duplicate inherited HTTP executions removed.

Additional end-to-end finding: import HTTP body budget was 16MiB, but inherited JSON parser imposed a 50k character model-output limit. A real-size checkpoint test failed; explicit bounded import parse limit added, default model limit unchanged. Browser test initially used nonexistent CSS selectors; corrected test selectors to actual DOM without changing product behavior.

Speech guard self-review: broad undecided pattern incorrectly rewrote a question about the user. RED-GREEN regression narrowed it to explicit first-person non-question statements. Remaining paraphrase/false-positive uncertainty is disclosed, not labeled semantic certification.

Final use-chain review: the recorded user also clicked invite during an in-flight question; preserving only movement still lost the answer on invitation. RED-GREEN test now covers invitation/wait as well. Those changes preserve the question but mark revision-stale expressions as earlier snapshots; pause/new question still cancel, with no late action execution.

Current final source suite: 266 PASS; UI 25 PASS. Fixed original utility remains negative full-minus-flat. Next remaining execution is release ZIP extraction, manifest check, fresh entire suite and state continuation. No additional implementation planned.
