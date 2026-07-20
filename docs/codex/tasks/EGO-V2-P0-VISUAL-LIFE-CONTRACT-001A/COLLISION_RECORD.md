# EGO-V2-P0-VISUAL-LIFE-CONTRACT-001A — collision record

## Candidate 1 — minimal surface patch

- Evidence: randomize the displayed marker locations, add a lives counter, and
  rename old macro actions.
- Strongest cheap match: the old semantic event/site/BFS policy still explains
  every decision.
- Leakage/hard-coding risk: extreme; the UI changes while policy access does not.
- Smallest falsifier: scan the actual policy projection and action scorer.
- Expected failure: visual resemblance only.
- Disposition: rejected.

## Candidate 2 — strongest cheap equal-access baseline

- Evidence: a visual lookup/count-Q/graph cache or local planner can learn token
  outcomes and survive across resampled placements.
- Strongest cheap match: the candidate itself is the shortcut explanation.
- Leakage/hard-coding risk: medium under equal access, extreme if it receives
  absolute map, mapping, seed, life ID, or semantic object names.
- Smallest falsifier: access-parity scan plus paired carry/no-carry rerun.
- Expected failure: it matches the product policy, forcing baseline-equivalence
  downgrade rather than a mechanism claim.
- Disposition: mandatory comparator; not rejected as an engineering baseline.

## Candidate 3 — selected local-visual product path

- Evidence: 5x5 ray-occluded perception, atom actions, counter-hash placement,
  visual-keyed model/memory, goal latches, and four reducer-owned lives are all
  replayable from serialized state and commands.
- Strongest cheap match: Candidate 2 with the same inputs.
- Leakage/hard-coding risk: hidden mapping or observer frame can leak; fixed
  action heuristics can also mimic exploration.
- Smallest falsifier: positive-control leakage scan, independent baseline,
  real carry/no-carry intervention, and fresh-process replay.
- Expected failure: surface behavior survives while carry ablation is inert or
  equal-access baselines match.
- Disposition: selected for product implementation because it removes known
  access leaks; it is not selected as proof of a special mechanism.

## Decision and stop rule

Candidate 3 is the smallest path that changes the actual perception-action
boundary and preserves one controller/reducer/store/replay chain. Candidate 2
remains the strongest alternative explanation. If it matches under access
parity, or if carry ablation does not damage the later paired result, record the
negative result and stop rather than tuning the product into a pass.

Claim ceiling: design collision plus local product-engineering rationale only.
Auto-Remote-Anchor: `forbidden`.
