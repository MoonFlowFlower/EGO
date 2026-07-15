# Collision Record — V1 READY authority Phase C

## Candidate A — local READY prose

- **Evidence produced:** a card or status page says V1 is authorized.
- **Strongest cheap baseline:** any hand-edited README or YAML boolean.
- **Leakage / hard-coding risk:** maximal; the desired verdict is the input.
- **Smallest falsifying test:** compare committed ITL currently executable
  actions with Ego's action surface.
- **Expected failure mode:** a second route authority and false READY wording.

## Candidate B — copy the commit and 20 targets

- **Evidence produced:** Ego names ITL `81f19613...`, sets implementation true,
  and copies a nonempty allowlist.
- **Strongest cheap baseline:** a partial transcription that omits nested
  permissions, conditional-action state, triggers, or source receipt fields.
- **Leakage / hard-coding risk:** high; schema split and stale reader pointers
  can survive while headline fields look correct.
- **Smallest falsifying test:** remove one nested source leaf or reorder one
  target and require fail-closed rejection.
- **Expected failure mode:** hidden permission drift or unreviewed scope growth.

## Candidate C — committed-object pins, exhaustive crosswalk, fail-closed sync

- **Evidence produced:** seven committed-object pins; a callable 213-leaf
  product-axis/V1-state crosswalk; exact ordered target validation; distinct
  trigger fields; runtime/science/remote firewall; stale-pointer scan;
  deterministic route fingerprint; staged/committed receipt binding.
- **Strongest cheap baseline:** Candidates A/B cannot match omission, source-pin,
  target-drift, trigger, pointer, and receipt controls under equal access.
- **Leakage / hard-coding risk:** bounded but nonzero. Frozen semantic constants
  can become stale, so the validator must first bind the committed source bytes
  and then require exact transcription rather than infer missing fields.
- **Smallest falsifying test:** omit one source leaf, mutate one blob pin, reorder
  one implementation target, claim a V1 trigger, reopen one runtime/science
  flag, restore a stale M1/EgoDesktop pointer, or tamper one reviewed blob.
- **Expected failure mode:** the Ego schema cannot represent the complete source
  without a second logic path. If so, STOP rather than weaken the crosswalk.

## Selection

Select Candidate C. It is the only approach that increases authority-integrity
evidence beyond a copied READY label. The endpoint is a local implementation
authorization boundary, not product behavior or mechanism evidence.

## Downgrade condition

If a Candidate A/B shortcut survives the same callable mutations, downgrade
this task to invalid governance work and do not authorize V1 implementation.
