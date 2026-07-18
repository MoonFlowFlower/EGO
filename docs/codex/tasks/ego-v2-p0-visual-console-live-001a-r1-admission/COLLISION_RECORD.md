# R1 visual-console admission collision record

Task: `EGO-V2-P0-VISUAL-CONSOLE-LIVE-001A-R1-ROUTE-ADMISSION-001A-R2`

Layer: engineering control plane. Mainline target: none / forbidden. Enabled:
false. Real visual trigger: absent until Phase A.

## Candidate 1 — docs-only permission

- Evidence: readable intent only.
- Cheapest matching baseline: any unvalidated note.
- Leakage/hard-coding risk: high; no action-to-path enforcement.
- Smallest falsifier: guard still exposes the old action or old 25 paths.
- Expected failure: apparent permission without callable admission.

Rejected.

## Candidate 2 — union old 25 paths with UI paths

- Evidence: broad mutation succeeds.
- Cheapest matching baseline: route-label change with unchanged bypass surface.
- Leakage/hard-coding risk: high; engine/store/launcher remain mutable.
- Smallest falsifier: substitute `engine.py` or `store.py` and still pass.
- Expected failure: second logic path or accidental mechanism rewrite.

Rejected.

## Candidate 3 — consume old action and transcribe exact 12-path action

- Evidence: one committed ITL authority, four exact Git-object pins, one
  field-by-field V2 projection, exact action/path mutation guard, hostile
  source/action/switch/path controls.
- Cheapest matching baseline: static copied JSON; rejected by committed-object
  recomputation and canonical-byte comparison.
- Leakage/hard-coding risk: bounded to explicit operator-authorized route
  literals; no product evidence is claimed.
- Smallest falsifier: any object pin, action, order, switch, or target drift
  passes callable validation.
- Expected failure: precommit/postcommit admission stops closed.

Selected.

## Collision decision

Candidate 3 is the only approach that narrows authority while preserving the
existing engine boundary. This record does not authorize Phase A by itself and
does not prove a GUI or product mechanism.
