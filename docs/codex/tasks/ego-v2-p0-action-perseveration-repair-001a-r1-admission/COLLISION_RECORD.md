# Collision record

Task: `EGO-V2-P0-ACTION-PERSEVERATION-REPAIR-001A-R1`

## Candidate comparison

| Candidate | Evidence | Cheapest matching baseline | Leakage / hard-coding risk | Smallest falsifier | Decision |
|---|---|---|---|---|---|
| Relabel or force variety | Different visible actions | round-robin/random | maximal | stored trace still says `forage` | reject |
| Clip or disable memory | fewer repeats | existing `memory_mode=off` | high; mechanism removal | default is equivalent to memory-off | reject as repair, keep ablation |
| Context eligibility + novel-arrival evidence + progress gate | applied/withheld memory provenance and changed canonical replay | memory-off plus generic progress heuristic | bounded if generic and trace-derived | mismatch contributes, zero-step writes, or suffix persists | select |

The selected path must preserve one canonical `compute_step` selector and must
not add action/event/seed/sequence exceptions. Action diversity alone is not an
acceptance signal.
