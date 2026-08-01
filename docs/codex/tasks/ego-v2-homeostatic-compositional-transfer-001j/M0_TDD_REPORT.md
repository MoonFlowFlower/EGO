# M0 TDD and capacity closeout — EGO-V2-HOMEOSTATIC-COMPOSITIONAL-TRANSFER-001J

## Scope and runtime

- Phase: `M0_DEV_ONLY_CAPACITY_CERTIFICATE`.
- Candidate source and engine integration were forbidden until M0 PASS.
- Python: `C:/Users/LEO/.codex/envs/ego-v2-numpy-2.2.6/Scripts/python.exe`.
- NumPy: `2.2.6`; pytest: `9.1.1`.
- Predecessor verification before mutation:
  `tests/test_ego_v2_causal_sprout_demo_001a.py` plus its verifier tests =
  `13 passed in 61.94s`.

## Test-first receipts

### Capacity producer RED

```text
python -m pytest -q scripts/codex/tests/test_check_ego_v2_homeostatic_compositional_transfer_001j_capacity.py
```

Observed before producer source existed: collection failed with
`ModuleNotFoundError: No module named
scripts.codex.check_ego_v2_homeostatic_compositional_transfer_001j_capacity`.

### Capacity producer GREEN

The same command after implementation returned:

```text
5 passed in 2.87s
```

### Independent verifier RED/GREEN

Before verifier source existed, its focused tests failed at collection with
`ModuleNotFoundError: No module named
scripts.codex.verify_ego_v2_homeostatic_compositional_transfer_001j`.
After implementation:

```text
3 passed in 0.81s
```

## Frozen source hashes at formal M0 execution

| Path | SHA-256 |
|---|---|
| `scripts/codex/check_ego_v2_homeostatic_compositional_transfer_001j_capacity.py` | `b5b5f72d5056118eb414d5cc47780e5294c1c79d8b096006282f3412660bbf2d` |
| `scripts/codex/tests/test_check_ego_v2_homeostatic_compositional_transfer_001j_capacity.py` | `ceb93a1edd649e003c63e49ea4e3f7bc1686b7bd260618475f90ca5d7ccfbc8f` |
| `scripts/codex/verify_ego_v2_homeostatic_compositional_transfer_001j.py` | `59f27967b034ff307686b9d5c29d7e9323ce9707187e6415519822f984e63805` |
| `scripts/codex/tests/test_verify_ego_v2_homeostatic_compositional_transfer_001j.py` | `d023b68ef2c64af69b0986dfc2a67596ec8235699613148fac89d4e18bd725ba` |

## Formal dev-only result

The producer executed all 16 dev combinations, all three registered arms, and
96 actions per trajectory.  It generated 4,608 primary rows and recomputed the
same trajectories without stored-action inputs.  No heldout combination was
executed or serialized.

```text
PRIVATE_ORACLE_NAVIGATOR mean deficit loss = 0.150569010417
PUBLIC_FACTOR_BAYES mean deficit loss      = 0.779191406250
UNIFORM_RANDOM mean deficit loss           = 0.743250000000
random-oracle headroom                     = 0.592680989583
public-reference recovered fraction        = -0.060642077073
public-reference beats random              = 5 / 16 contexts
```

Passed gates:

- complete dev population;
- real transition/outcome/metabolism invocation receipts;
- random-oracle headroom at least `0.10`;
- fresh replay exact.

Failed frozen gates:

- public reference did not recover half the headroom;
- public reference beat random in only `5/16`, below `12/16`.

Verdict: `BENCHMARK_CAPACITY_NOT_ESTABLISHED`.

This is not evidence that public acquisition is impossible.  It is evidence
that the exact frozen public reference failed to establish it.  The reference
was slightly worse than random, so the observed oracle headroom cannot be used
to authorize a neural candidate.

## Independent verification

The independent read-only verifier parsed every row, recomputed trajectory and
arm losses without importing the producer, rebuilt all gates and verdict,
checked trace chains and artifact hashes, rejected heldout aliases/tamper in
tests, and returned:

```text
passed=true
stored_verdict=BENCHMARK_CAPACITY_NOT_ESTABLISHED
recomputed_verdict=BENCHMARK_CAPACITY_NOT_ESTABLISHED
heldout_rows=0
neural_candidate_source_present=false
protected_predecessor_hashes_match=true
```

## Stop disposition

Per the committed task contract, stop before:

- `labs/ego_life_playground_v0/homeostatic_transfer.py`;
- any `engine.py` or controller integration;
- neural dev tuning, source freeze, heldout ID commitment, heldout execution,
  transfer/drive/ablation HTML, or a positive capability claim.

The cheapest honest successor is a new dev-only public-acquisition/reference
redesign with a new task ID or explicit supersession.  Reusing this observed
packet and tuning the reference until it passes would not satisfy 001J.
