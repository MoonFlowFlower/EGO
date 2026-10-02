# Shared Field implementation plan

Goal: deliver one runnable ZIP from the accepted shared-experience direction.
Architecture: independent shared-world cognitive kernel; reuse existing Provider, DirectoryLock, Service persistence/worker, and local HTTP security contracts. Keep v0.3 modules and tests. New command `shared` and launcher default. No shared remote repository exists here.
Spec: docs/shared/DESIGN.md
Tech: Python >=3.10 stdlib and plain HTML/CSS/JS; no runtime package download.

## Tasks and interfaces
1. tests/test_shared_world.py -> shared/world.py: World(seed,horizon), observe(actor), act(actor,action), perturb(kind), snapshot/restore. Tests must isolate hidden fields and non-adjacent action rollback.
2. tests/test_shared_mind.py -> shared/mind.py: Mind().observe(event,eid), plan(public_world), report(), new_expedition(); physically grounded Bayesian update, recurrent appraisal, model-based goals, bounded review. Test self/affect/freeze interventions, no evidence double count, no hidden-world access.
3. tests/test_shared_core.py -> shared/core.py: Core.apply/checkpoint/restore/view/context; event identity, exact replay, stale language output rejection, quote-grounded other state, report provenance.
4. tests/test_shared_service.py + HTTP tests -> shared/service.py/http.py/protocol.py: inherit durable service; local state-report/manual/API modes; two-phase interpretation/expression; bounded paced auto, pause/restart default-off; input concurrency no discarded paid retry; real HTTP test provider explicitly fixture.
5. shared/web and run.py: playable shared map, conversation beside current focus/affect/uncertainty, sources and ablations, provider configuration + copy/paste, help, archive. Test DOM actions/mobiles; frontend output untrusted text via textContent.
6. tools/shared_benchmark.py: preregistered paired-seed comparison with flat Bayesian, freeze, affect-off, self-off; no metric threshold tuning to force pass. Persist negatives.
7. docs/readme + verification: full tests and source grammar, browser limitation report, manifest and fresh ZIP extraction replay/test. Independent review unavailable; self-review disclosed.

## Review focus
Late network outputs after world mutation/pause; duplicate observation learning; hidden truth leaked into model context; active action on restart/new settings; API keys/directory overwrite/export secrets. Add specific regressions before fixes.

## Execution ledger
- Container copy /mnt/data/work_v04/SwitchLab; original ZIP untouched, user repo untouched.
- Baseline: 169 tests passed in 24.801s before edits.
- User explicitly requested direct implementation and final package, not another approval round.
- Tasks 1–4 implemented with RED→GREEN tests; 169 legacy tests remain intact.
- Real two-hop HTTP uncovered a tuple/list checkpoint boundary mismatch. Root cause: random.getstate() serialized to arrays then snapshot reintroduced tuples. Fixed World.snapshot to be JSON-native; same recorded-input replay now stable over transport. No benchmark policy tuning.
- Paid stale-response path uncovered implicit retry via retained message ticket. Cleared cancelled response tickets on intervening world commands; new inputs remain explicit fresh requests. Auto permission does not revive cancelled language calls.
- First 8-seed/5-method/80-step benchmark: full-minus-flat utility -0.9603; descriptive interval crosses zero. No superiority claim; no tuning to force pass. Same-history affect/self decision interventions remain separately reported.
- Native Chromium-to-loopback is blocked by administrator policy; do not bypass. UI will be checked through an explicitly labelled in-process test transport; actual HTTP independently checked.
- Tasks 5–7: current frontend 15 checks via explicit test bridge; final 225-test suite passed; 34 runtime Python files parsed under 3.10 grammar.
- Same final code reran 8x5 benchmark without any policy/metric retuning; negative result retained.
- Final edge regressions cover new-expedition provenance, third-party versus user preference, and action/permission boundaries. No independent reviewer available; SELF_REVIEW.md records actual self-review.
- Source frozen for example generation and package; original v0.3 ZIP retained for old checkpoint access. External delivery JSON is the authority for fresh ZIP extraction/tests.
