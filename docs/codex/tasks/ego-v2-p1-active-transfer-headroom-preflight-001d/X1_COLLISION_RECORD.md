# 001D-X1 collision-before-collapse record

## Candidate approaches

### 1. Continue the full 7,168,356-case I2 formal packet immediately

- **Evidence:** complete frozen 001D verdict, all ablations, sensitivity branches, replay, and independent recomputation.
- **Strongest cheap baseline:** a single mandatory-variant counterexample can already rule out the only positive branch.
- **Leakage/hard-coding risk:** low if completed, but large implementation surface creates more opportunities for common bugs and stored-output shortcuts.
- **Smallest falsifier:** one exact member or nonmember failing the conservative universal gate.
- **Expected failure:** spend hours and tens of gigabytes proving a positive branch that was already impossible.
- **Strongest objection:** only the full packet can assign the exact negative branch. Correct; X1 therefore does not claim a full 001D verdict.

### 2. Trust the exploratory I1 call

- **Evidence:** immediate exact-looking numbers from the committed evaluator.
- **Strongest cheap baseline:** a common bug in I1 can reproduce every number; no artifact/replay/independent path exists.
- **Leakage/hard-coding risk:** high claim risk because the observation occurred before the X1 card and used one implementation.
- **Smallest falsifier:** separately implement the same bank and target metrics and compare every row.
- **Expected failure:** promote a diagnostic into evidence.
- **Strongest objection:** deterministic arithmetic does not need repetition. Response: the route's evidence contract does; the independent path tests the real possibility of an implementation defect.

### 3. Selected: exact first-bank counterexample confirmation

- **Evidence:** all 120 HASH_00 targets, primary/fresh/independent recomputation, exact member and bounded-safety gates, raw-versus-conservative diagnostic, machine-readable artifacts.
- **Strongest cheap baseline:** PUBLIC L1 risk-DP is already the equal-access comparator inside every metric.
- **Leakage/hard-coding risk:** witness cherry-picking or copied logic. Mitigation: derive HASH_00 as the first frozen bank, enumerate all targets, never accept a witness input, independently implement the formulas, and disclose the exploratory origin.
- **Smallest falsifier:** primary/independent disagreement on any of 360 rows or any aggregate; then the instrument blocks.
- **Expected failure:** candidate positive gate is falsified, but the result cannot identify the exact full 001D negative branch.
- **Strongest objection:** a single bank may be unrepresentative. Irrelevant to the narrow universal claim: representativeness matters for average-performance claims, not for one-counterexample falsification.

## Selection

Choose approach 3. It answers the current decision question at much lower cost: whether implementing the large formal packet or a neural/product candidate can still lead to the frozen positive 001D branch. If X1 falsifies that branch, freeze the candidate and redesign the decision rule/benchmark rather than optimizing evidence plumbing.

## Independence boundary

The primary and independent code paths remain same-model internal work. They are not external independent audit. Exact agreement increases confidence in deterministic computation but does not eliminate shared specification error.
