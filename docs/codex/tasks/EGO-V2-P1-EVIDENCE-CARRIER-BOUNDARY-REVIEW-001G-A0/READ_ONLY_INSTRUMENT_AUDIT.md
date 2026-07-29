# EGO-V2-P1-EVIDENCE-CARRIER-BOUNDARY-REVIEW-001G-A0

## Verdict

`RAW_JSON_BOUNDARY_INSTRUMENT_INVALID_FOR_MECHANISM_ADMISSION`

The `32768B` mean raw-canonical-JSON threshold remains an immutable failed
check in `EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F`.  This review does
not waive, raise, rerun, or retroactively pass that check.  It finds that the
threshold was a useful preregistered P0 product-engineering target, but no
repository evidence derives the exact `32768B` discontinuity from a current
UI, SQLite, export, memory, recovery, or other consumer limit.  It therefore
must not remain a universal prerequisite for adjudicating a learning mechanism.

Future work must keep semantic evidence and carrier engineering as two
separately frozen axes.  This review selects neither a replacement byte limit
nor a production compression format.

## Scope and method

This was a docs-only, read-only instrument audit.  It:

- inspected tracked history, task cards, runtime source, verifiers, tests, and
  banked 001F artifacts;
- opened the two banked optimized 001F SQLite files with
  `mode=ro&immutable=1`;
- used one-off, non-checked-in Codex processes to recompute byte counts,
  lossless compression round trips, JSON decode timing, authenticated receipt
  expansion timing, and positive-control corruptions;
- did not modify source, tests, route state, 001F artifacts, worlds, actions,
  metabolism, policies, priors, or thresholds;
- did not rerun the 001F formal gate or any held-out/development world.

The timing observations below were collected on this host with Python
`3.12.13` through:

```text
uv run --with-requirements requirements-ego-v2.txt python -
```

They are diagnostic medians, not a portable latency SLA.  The reviewer and
measurement processes are same-model internal work, not external independent
audits.

## Fact / inference / unknown boundary

### Facts

1. The threshold first entered the repository in commit
   `c94192a0822c2b6dc34cd96d88e9bb691c86844f` as a frozen P0 runtime-scaling
   acceptance target.  It predated 001F and was not chosen to rescue 001F.
2. P0's diagnosed problem was real: a 355-command live run had a
   `57,581,568B` SQLite file, `160,110B` mean trace, `303,011B` maximum trace,
   and 66--80 second recovery.  The banked P0 result later recorded
   `24,500.1549B` mean, `30,156B` maximum, `9,424,896B` SQLite, and
   `4.031797s` recovery.
3. Neither the P0 task card nor its collision record states a consumer-derived
   calculation for exactly `32KiB` mean or `64KiB` maximum.  The values occur
   as acceptance constants.
4. A tracked-source scan found no `32768`, `32KiB`, or equivalent threshold in
   `labs/` or application runtime files.  Relevant occurrences are in task
   cards, verifier scripts, and verifier tests.  Unrelated `32768`/`65536`
   buffer constants in the life-kernel continuity checker are not trace-size
   consumers.
5. `SQLiteEventStore.append_step` stores canonical trace JSON as unbounded
   SQLite `TEXT` and verifies exact row readback.  `recover_run` first
   recomputes behavior from initial state plus ordered commands and then parses,
   hashes, and compares the stored trace.  `export_run` writes recomputed
   traces.  None has a 32KiB allocation, truncation, rejection, or behavioral
   branch.
6. The Tk UI consumes decoded mappings and renders selected projections.  It
   has no 32KiB cutoff.  UI observability therefore depends on retaining and
   reconstructing the required fields, not on one raw-JSON mean boundary.
7. Banked 001F's optimized and scalar SQLite files are byte-identical within
   each context.  Every one of the six fresh-process recoveries was exact and
   below 10 seconds; full tamper controls failed closed.  The only failed 001F
   check was world 54's mean raw JSON size.
8. World 54's failure remains exactly `32847.16949152543B`, which is
   `79.16949152543B` above the frozen limit.  This numerical closeness is not
   used as the reason to change the instrument.

### Inferences

1. The P0 threshold was a reasonable coarse anti-bloat engineering target for
   the original 160KiB-per-row failure, but its exact boundary is not evidence
   of a mechanism-validity discontinuity.
2. Raw JSON size affects storage, parsing, hashing, export, and recovery
   continuously.  The banked exact recovery results and the measurements below
   provide no evidence of a discontinuity at byte 32768.
3. At the observed four-life bytes-per-command, a purely linear 569-command
   projection is about `19.21--19.35MiB`, below the separately frozen `20MiB`
   P0 SQLite cap.  This is only an extrapolation: later-life state growth could
   invalidate it, so a future product carrier gate must measure the actual
   full lifecycle rather than use this projection as authority.
4. Lossless compression demonstrates that raw canonical JSON bytes are a
   representation-dependent quantity.  It does not by itself establish that
   compression should be adopted or that a compressed carrier is fast enough
   in the full product path.

### Unknowns

1. The original author's undocumented reason, if any, for selecting exactly
   `32KiB` and `64KiB` is unknown.
2. The correct product storage/latency envelope for future full-lifecycle
   predictive traces is unknown until it is derived from a stated consumer and
   measured on that consumer before seeing a new gate result.
3. The current measurements do not establish held-out learning, prediction
   headroom, survival benefit, or neural self-discovery.

## Banked carrier measurements

All compression rows below compress each full canonical trace independently,
preserving random row access.  Every decompressed byte string and SHA-256
matched the stored raw trace exactly.

| context | commands | raw mean / max | SQLite + sidecars | bytes / command | gzip-9 mean / max | zlib-9 mean / max | LZMA-6 mean / max |
|---|---:|---:|---:|---:|---:|---:|---:|
| `p0_cross_v1:world=52:policy=711` | 92 | `32742.587 / 35359B` | `3,280,896B` | `35,661.91B` | `8106.315 / 8892B` | `8094.315 / 8880B` | `7474.957 / 8164B` |
| `p2_vertical_v1:world=54:policy=711` | 118 | `32847.169 / 36327B` | `4,177,920B` | `35,406.10B` | `8136.542 / 9062B` | `8124.542 / 9050B` | `7503.458 / 8288B` |

The total per-row compression ratios were:

- gzip-9: `0.24758` and `0.24771` of raw bytes;
- zlib-9: `0.24721` and `0.24734`;
- LZMA-6: `0.22829` and `0.22844`.

No SQLite `-wal`, `-shm`, or `-journal` sidecar was present.  Both files had
zero freelist pages.

### Decode and authenticated reconstruction diagnostics

| context | raw JSON decode median | authenticated receipts | receipt expansion median | raw decode + expansion | gzip decode + JSON + expansion |
|---|---:|---:|---:|---:|---:|
| world 52 | `265.950us/trace` | 89 plan + 89 update | `124.810us/receipt` | `510.901us/trace` | `616.937us/trace` |
| world 54 | `245.170us/trace` | 115 plan + 115 update | `116.853us/receipt` | `492.468us/trace` | `614.947us/trace` |

The gzip diagnostic added approximately `106.036us/trace` and
`122.480us/trace` to the measured raw decode-plus-expansion path on this host.
These figures compare representation costs only; they do not include planner
recomputation and must not replace the banked full-recovery measurements.

### Positive-control corruptions

For both contexts, all five in-memory corruption controls failed closed:

1. mutate a candidate-value breakdown item;
2. delete the candidate receipt source-hash field;
3. mutate a projection dictionary value;
4. replace a projection dictionary index with an out-of-range index;
5. flip one bit in the middle of a gzip payload.

The authenticated expansion functions raised `EngineInvariantError` for the
first four controls; gzip raised `BadGzipFile` on CRC mismatch.  These checks
show that the existing banked representations can be authenticated and that a
lossless alternative is feasible.  They do not constitute a production
carrier implementation or full store/recovery ablation.

## Hostile alternative explanations

### Candidate 1: retain 32768B as universal admission authority

Strongest case: a strict inherited number prevents silent evidence growth and
post-hoc exceptions.  Rejection: strictness is valuable only when the measured
quantity is tied to the target decision.  The repository has independent
exactness, recovery-time, DB-size, export, row-readback, and tamper gates, while
no runtime consumer branches at 32768B.  Keeping it as an engineering SLA is
defensible; using it to decide whether a predictor can be statistically
adjudicated is not.

### Candidate 2: waive or raise the number because 001F nearly passed

Rejected.  That would be post-hoc threshold tuning.  001F remains failed and
its result/artifacts remain immutable.

### Candidate 3: separate semantic evidence from carrier engineering

Selected.  The semantic axis remains non-negotiable:

- initial-state-plus-ordered-command full recomputation is the only replay
  authority;
- selected action, state, trace, model, and ordered rows remain exact;
- compact fields required by analysis/UI must be losslessly reconstructed and
  authenticated;
- source/model/receipt/command corruption and recomputation bypass must fail
  closed;
- export and UI observability must remain available.

The engineering axis must be independently preregistered against a real
consumer, for example actual full-lifecycle SQLite-plus-sidecar growth,
recovery latency, export latency, and UI responsiveness.  A future carrier card
may compare raw JSON and lossless codecs, but must select limits before its
formal run and without using the observed 001F miss to set them.

## Decision and successor boundary

1. Keep `EGO-V2-P1-PREDICTIVE-REPLAY-KERNEL-REPAIR-001F` permanently at
   `BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION`.
2. Freeze further byte shaving under the current additive/performance framing.
3. Remove `mean raw canonical JSON <=32768B` from future **mechanism-admission**
   logic.  Do not remove exact replay, row-readback, tamper, export, UI, or
   separately derived storage/latency requirements.
4. Author a separate old-context task card for Bayesian active outcome
   identification versus `PUBLIC_COUNT_DEFICIT_COVERAGE`.  This report does not
   authorize that implementation or a formal cycle.
5. Worlds `30--150` remain contaminated.  Any future fresh effect adjudication
   must use externally selected, commitment-hashed, opaque worlds wholly above
   150 after implementation, priors, thresholds, baselines, and development
   verdict are frozen.

## Stop conditions and claim ceiling

- **Triggered:** the exact raw-JSON threshold lacks documented external
  consumer justification as a universal mechanism prerequisite.
- **Not triggered:** no replay, reconstruction, tamper, UI, export, or row
  evidence was weakened.
- **Claim ceiling:** measurement-instrument governance and read-only banked
  carrier diagnostics only.
- **This does not prove:** that 001F passed; that compression should ship; that
  the additive predictor learns; that Bayesian active identification will beat
  a cheap coverage baseline; any held-out or survival effect; neural emergence;
  agency; AGI; consciousness; or electronic life.
