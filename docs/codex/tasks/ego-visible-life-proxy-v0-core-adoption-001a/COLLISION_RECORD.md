# Collision Record — EGO V0 product-core authority sync

## Candidate A — local prose/self-adoption

- **Evidence:** Ego says V0 is the sole core.
- **Cheap match:** any README or stale route view.
- **Leakage/hard-coding risk:** maximum; the conclusion is supplied locally.
- **Smallest falsifier:** the committed ITL product axis still reports sync pending.
- **Expected failure:** two authorities and route drift.

## Candidate B — commit pin only

- **Evidence:** Ego names ITL `619bff5f...` and V0 `546e363...`.
- **Cheap match:** a copied hash string with no object/payload validation.
- **Leakage/hard-coding risk:** high; wrong or partial packet fields can survive.
- **Smallest falsifier:** mutate one ITL blob while preserving the commit string.
- **Expected failure:** silent schema split or trigger-claim conflation.

## Candidate C — committed ITL authority, exhaustive transcription, callable sync

- **Evidence:** seven committed product-axis object pins; verbatim leaf crosswalk
  for product axis/state/closure; event/report/receipt semantic checks; preserved
  Card2 closure; separate ITL-vs-Ego trigger fields; V0 Git-object/SQLite replay;
  exact route/action and Red-review binding.
- **Cheap match:** none of A/B under the same mutation controls.
- **Leakage/hard-coding risk:** bounded; the sync validator reads committed Git
  objects and product evidence cannot grant route authority.
- **Smallest falsifier:** omit one crosswalk leaf, swap one object, conflate the
  trigger fields, or expose V1 implementation and require fail-closed rejection.
- **Expected failure:** cross-repo schema cannot represent conditional V1 draft
  without inventing new authority. If that occurs, STOP rather than self-grant.

## Selection

Select Candidate C. It is a product-axis synchronization and engineering
evidence task, not a mechanism comparison or electronic-life result.
