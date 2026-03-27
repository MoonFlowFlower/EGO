# Identity Drift Note

## Drift Summary

Real Telegram evidence shows a drift between:
- the intended closure-family contract validated by local tests
- the actual host-chain behavior seen in live Telegram samples

## Drift 1: Blocked vs Success Split Family In Reality

Local expectation:
- same action family
- same `closure_family_id`
- different `closure_signature` for different outcomes

Real Telegram result:
- blocked sample:
  - `tool:file`
  - `closure_family_id = 6824edaf39136534`
  - `closure_signature = 3e728db79c906f48`
- success sample:
  - `tool:file`
  - `closure_family_id = 7a053f9ff7c61219`
  - `closure_signature = f92efd86648b35ec`

Observed drift:
- family split happened before identity split analysis could stay within one family

Likely cause:
- in `OpenEmotion/openemotion/proto_self/cycles.py`
  - `_build_psi_bucket()` appends `risk_high` for blocked/high-risk tool results
  - `closure_family_id` is derived from `psi_bucket | action_signature`
- this means outcome-linked risk escalation can split the family itself

Impact:
- Q2 cannot be counted as a clean real-world pass
- same-action blocked/success evidence exists, but not in one stable family

## Drift 2: Real Retry Path Does Not Become Repair Closure

Real Telegram retry path existed:
1. blocked read of missing file
2. retry/follow-up read of existing file
3. repeated successful read

But in the real trace:
- `repair_closure = false`
- success path stayed in `mode_signature = exploration`

Likely cause:
- `_is_repair_closure()` requires:
  - `outcome_signature == success`
  - `mode_signature == repair`
  - previous failed tool name matching the current action family
- on the live host chain, the follow-up success did not satisfy the mode condition

Impact:
- Q3 cannot be formally accepted
- the host shows human-readable repair behavior, but not formal repair-closure consolidation

## Non-Drift: Host Root Bug Was Real And Is Now Fixed

This note is not about the already-fixed host bug.

The following host issues were real, but are now repaired:
- explicit path requests being polluted by stale uploaded-artifact context
- evidence collector mixing multiple Telegram samples into one mutable slot

Those fixes improved evidence quality.
They did not resolve the underlying closure-family / repair-closure semantic gaps above.

## Recommendation

The next task should explicitly target:
1. real-host same-action blocked/success family preservation
2. real retry path recognition as `repair_closure`

Until then:
- P3 evidence capture is valid
- P3 strict acceptance is still not complete

