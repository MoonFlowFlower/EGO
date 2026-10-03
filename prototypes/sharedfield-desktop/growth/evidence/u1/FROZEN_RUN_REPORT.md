# U1 result

**Status: STOP_UB**

All cloud inputs/outputs, transport errors, reservations and state stores remain under ignored `growth/runs/u1/`.
This report supports only the frozen synthetic protocol; it is not evidence that the companion understands its owner.

- Ua_main: {"status": "completed", "pass": true, "decisions": 180, "expected": 180}
- Ua_same_reasoning: {"status": "stopped", "pass": false, "stop": "http_404", "decisions": 67, "expected": 90}
- Ua_stronger: {"status": "stopped", "pass": false, "stop": "http_429", "decisions": 24, "expected": 90}
- Ub: {"status": "stopped", "pass": false, "stop": "route_preflight_rejected"}

The full frozen criteria and pre-run ambiguity resolutions are in `frozen_v1.json` (or the explicitly recorded model-switch v2).

Reported successful U1 cost: $0.033759; shared ledger occupancy: $0.804510 / $5.
Unknown/failed-request reservations remain occupied; no U1-only charge is inferred from a shared ledger delta.
