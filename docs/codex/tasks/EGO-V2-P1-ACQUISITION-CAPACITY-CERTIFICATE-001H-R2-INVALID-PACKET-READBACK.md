# EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2 — invalid-packet preservation readback

- **Task ID:** `EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2-INVALID-PACKET-READBACK`
- **Layer:** engineering evidence preservation and mechanism-hypothesis boundary control; not learning-effect or subjectivity validation.
- **Problem definition:** the one authorized R2 formal execution wrote the canonical output packet bytes, then the canonical semantic verifier raised `ValueError: r2 packet semantic panel support`. Preserve the exact bytes and distinguish computed search facts from the packet's unverified saved verdict without repairing or rerunning R2.
- **Current stage:** post-run, preservation-only closeout.
- **Hypothesis:** the terminal exception is caused by a writer/verifier mismatch for a panel-not-run placeholder, not by observed corruption of the witness-search rows or cap receipts.
- **Baseline:** exact committed packet bytes plus independent row/count/rank/support recomputation and the canonical artifact-manifest verifier.
- **Ablation:** not applicable to this docs-only closeout. No code, artifact, threshold, search, panel, or runtime intervention is authorized.
- **Trace/replay requirement:** retain the exact formal packet, implementation/provenance pins, process exception, row digests, receipt summaries, and the distinction between saved self-report and verified authority.
- **Acceptance gate:** exact artifact bytes are committed unchanged; artifact hashes pass; both cap reports and row summaries independently recompute; the semantic-verifier exception is reproduced on unchanged bytes; no source/runtime/artifact byte is edited and formal is not rerun.
- **Claim ceiling:** invalid formal-packet preservation with internally coherent bounded cap-hit observations. No authoritative R2 verdict, witness impossibility, panel result, capacity result, learning effect, AGI, agency, subjectivity, consciousness, or EGO-mainline readiness.
- **Stop condition:** stop after preservation and readback. Do not patch the verifier, rerun R2, tune the search, or create an R3/R4 planner rescue under this lineage.
- **Rollback plan:** revert only this readback document if its text is wrong. Never rewrite the banked R2 packet or the earlier R1 evidence.
- **Auto-Remote-Anchor:** forbidden.

## Immutable lineage

| Boundary | Commit |
|---|---|
| Normative R2 docs | `c0f9d24c0e00d03b27e93fe35d73be1c021bb8b2` |
| Reviewed implementation/tests | `89786748dd277247d59ce4d5254e4f0292147714` |
| Pre-run provenance | `2ba4f3745d31c6994facb3babb750e0d055bd034` |
| Exact generated packet bytes | `35378630042d5ea4f07298e31883e99743c8d422` |

The implementation and tests were reviewed before the formal run. The tracked runtime receipt confirms Python `3.12.13`, NumPy `2.2.6`, and dtype `<f8`. This does not override the later formal-packet failure.

## One authorized formal execution

The formal search was invoked once through `run_formal(..., execute_search=True)` using the exact canonical output path. It was not rerun.

After both witness searches and packet writing completed, the process exited non-zero:

```text
verify_r2_formal_packet(output)
ValueError: r2 packet semantic panel support
```

The exception occurred at the semantic acceptance gate after packet bytes and `artifact_manifest.json` were written. Therefore the bytes exist, but the function did not return a verified formal result.

## Four-way evidence classification

### 1. Facts on disk

- `result.json` and `failure_manifest.json` save `WITNESS_SEARCH_INCONCLUSIVE`.
- `certificate_rows.jsonl` contains `178` rows: `89` per frozen context.
- `panel_rows.jsonl` contains `0` rows.
- Both panel placeholders have `construction_complete=false`, `panel_capacity_admitted=false`, no rollouts/checkpoints, and empty `before_dedupe` / `after_dedupe` maps.
- The exact packet has 12 files and is committed unchanged at `35378630042d5ea4f07298e31883e99743c8d422`.

### 2. Independently recomputed facts

The artifact manifest matches all 11 payload files by path, byte length, and SHA-256.

| Context | Rows | Search status saved in search report | Processed nodes | Complete | Unprocessed legal child | Duplicate skips | Receipt digest |
|---|---:|---|---:|---|---|---:|---|
| `p0_cross_v1:world=52:policy=711` | 89 | `WITNESS_SEARCH_INCONCLUSIVE` | 2,000,000 | false | true | 0 | `3285d267ab19d50c13ec5331150282be6225178b6fa9a8166d43b90e805fc706` |
| `p2_vertical_v1:world=54:policy=711` | 89 | `WITNESS_SEARCH_INCONCLUSIVE` | 2,000,000 | false | true | 0 | `29f63b038520f53c4570ce18f07a9484177a66cf57a47db8ac7740b899b019c6` |

Receipt counters are internally consistent:

- p0: `expanded=400030`, `bound_pruned=1599970`, `child=2000150`;
- p2: `expanded=400028`, `bound_pruned=1599972`, `child=2000140`;
- for both contexts, `expanded + bound_pruned = 2,000,000` and `child = 5 * expanded`.

The serialized warm-start attempts are not witness certificates:

- p0 ranks: turn-left `11`, turn-right `10`, move-forward `8`, interact `13`, rest `4`; several support strata are below 4;
- p2 ranks: turn-left `11`, turn-right `9`, move-forward `10`, interact `13`, rest `8`; several support strata are below 4.

Independent row digests:

- p0: `d924953b054ab900806ba946f10005d7dffeb245057fa1377367b18868f3ae4d`;
- p2: `e2ce9c679917a28419a1004388b5fcbf467852df84ab8634cdb73a4ac3d53f9c`;
- combined canonical list: `b054d6c3c01b64873d62fef87ab7123cfee8737a1c52f6a09a8d760956a66f1a`.

The row-level leakage recomputation is clean and detects all three positive controls. This does not repair packet semantics.

### 3. Delivery-file self-report

`result.json` reports all validity fields true and saves `WITNESS_SEARCH_INCONCLUSIVE`. Those statements are delivery-file self-report, not the final formal authority, because the same canonical implementation subsequently rejected the unchanged packet.

### 4. Unknown

- Whether an acceptable witness exists beyond the two-million-node cap: **unknown**.
- Whether panel capacity would pass: **unknown**; panel search never ran.
- Independent reconstruction of every receipt in the two-million-node digest chains: **unknown**; the final packet stores bounded samples and summaries, not every receipt.
- Any learning/generalization effect: **unknown and not tested by R2**.

## Exact verifier mismatch

For a panel-not-run context, `_panel_not_run` serialized:

```json
{"before_dedupe": {}, "after_dedupe": {}}
```

The verifier recomputed zero-filled token maps:

```json
{
  "before_dedupe": {"v0": 0, "v1": 0, "v2": 0, "v3": 0, "v4": 0, "empty": 0, "wall": 0},
  "after_dedupe": {"v0": 0, "v1": 0, "v2": 0, "v3": 0, "v4": 0, "empty": 0, "wall": 0}
}
```

`required_floors` and `passed=false` agree. The mismatch is therefore a post-search panel-not-run serialization/verification contract defect. No observed evidence ties it to witness-row corruption, but this does not permit bypassing the failed acceptance gate.

## Closeout verdict and route

### Preservation verdict

`INVALID_FORMAL_PACKET_SELF_VERIFICATION_FAILED`

### Saved inner verdict

`WITNESS_SEARCH_INCONCLUSIVE` — preserved as an unverified packet self-report, not promoted to authoritative formal status.

### Route consequence

- Capacity remains unresolved.
- This does not close the benchmark scientifically.
- No R3/R4 same-framing planner rescue is authorized.
- No verifier patch or formal rerun is authorized under R2.
- Any future action requires a separately bounded preservation/tooling authority and must not retroactively upgrade this packet.

## Independence boundary

The recomputation and hostile review used same-model internal agents plus controller-side pinned commands. They are role-separated but not external independent replication.

## What this does not prove

This readback does not prove witness impossibility, panel failure, structural capacity, causal-schema transfer, neural self-learned transfer control, learning, generalization, AGI, electronic life, agency, subjective experience, consciousness, or mainline readiness.
