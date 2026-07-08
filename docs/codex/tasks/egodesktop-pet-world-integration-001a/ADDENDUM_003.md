# ADDENDUM 003 — rng_audit self-match repair and probe positive-claim guard

Status: PRE-RUN INSTRUMENT REPAIR PINS / NO CODE / NO SCORED RUN.

This addendum is an ex-ante repair contract for the P0 instrument failure banked
at commit `8884b57349e4c7c1f37220cb0a603acf832cb978`. It must be committed
before the repair implementation and before any re-run probe. Every re-run probe
and every later scored run must be a descendant of this addendum commit.

## Defect A — `rng_audit` self-match

The STEP3 probe STOP on `UNSEEDED-RNG-AUDIT` is recorded as a confirmed false
positive: scanner self-match, not real unseeded RNG. The audit scanned
`scripts/ego_pet/*.py`, including `battery.py` itself, and used bare substring
matching against its own forbidden-token tuple:

`("secrets.", "random.", "np.random", "torch.rand")`

The reported hits trace to that detector literal, not to executable RNG usage.
The run-1 STOP artifacts remain valid evidence of the catch and must be
preserved.

## Defect B — phase-blind probe positive claim

`choose_verdict` was phase-blind. A fully passing one-seed probe could emit
`pet_integration_p0_pass` and set `positive_claim_flag=true`, which would mint a
positive product-gate claim from STEP3. Positive product-gate language is
reserved for STEP4 scored evidence plus Claude hostile audit.

## Repair invariants

1. Fix the instrument, not the mechanism: no edits to `world.py`, `creature.py`,
   `standin.py`, `memory_wiring.py`, `static_gate.py`, configs,
   `DERIVATION_NOTES.md`, or freeze files.
2. No weakening: `rng_audit` must not unconditionally pass, must not exclude
   `battery.py` or any other pet file from the default scan set, and must keep
   forbidden RNG import/call coverage.
3. Mandatory positive-control falsifier: tests must prove the audit fails on
   real unseeded RNG usage and passes the clean pet package without self-match.

## Acceptance tests, pre-registered

- `test_rng_audit_catches_unseeded_calls`: temp fixtures containing real
  unseeded calls for numpy default_rng, Python random, torch rand, and numpy
  random.rand each fail the audit with a hit.
- `test_rng_audit_passes_clean_pet_package`: default `rng_audit()` over
  `scripts/ego_pet` passes with `forbidden_hits == []`.
- `test_rng_audit_scans_battery_and_no_self_match`: `battery.py` is in the
  default scan set and yields zero hits.
- `test_probe_never_emits_positive_claim`: a fully passing probe emits a
  probe-scoped verdict, not `pet_integration_p0_pass`, and
  `positive_claim_flag is False`.

## Claim ceiling

`instrument_repair_only`: this addendum earns no mechanism, gate, product,
runtime, or user-benefit evidence. It only restores a correct evidence
instrument and closes a phase-scoped claim-ceiling leak before re-running STEP3.
