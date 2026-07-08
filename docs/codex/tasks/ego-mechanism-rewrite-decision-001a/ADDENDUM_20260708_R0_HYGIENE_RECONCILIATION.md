## Addendum 2026-07-08 — R0 hygiene sub-gate reconciled with R3-adoption mandate
Authorizes: EGO-R0-HYGIENE-ADOPTION-DISPOSITION-001A. Authorized by operator (Zhouyu), 2026-07-08.

Finding: the R0 child card `ego-r0-kernel-state-substrate-001a` added a local hygiene sub-gate
requiring `EgoDesktop/`+`EgoOperator/` → kernel references == 0. This over-constrains relative to
THIS card's frozen R0 acceptance contract (§R0: replay / state-causality / LLM-swap harness /
"No mutation of EgoOperator runtime; EgoDesktop only" — no zero-reference clause) and contradicts
THIS card's R3 obligation (§R3: "adopt R0 serialized-state/replay substrate when R0 lands").
Adoption necessarily creates EgoDesktop→kernel references; the zero-reference sub-gate fails a
re-run of R0 validation the moment the mandated R3-adoption lands.

Authorization: the R0 child card MAY relax its hygiene sub-gate from "0 references" to
"0 UNDECLARED references", gated by a sanctioned-adopter allowlist in which every entry cites an
authorizing card. This does NOT alter this card's frozen R0 acceptance contract (replay /
state-causality / LLM-swap / no EgoOperator runtime mutation remain exactly as frozen) and is
therefore not a widening of the parent contract; it reconciles a child over-constraint with the
parent's own R3-adoption mandate. The strict half — no `EgoOperator` import inside
`scripts/ego_kernel` — remains unchanged (== 0).

Binding conditions on the implementation: (1) each allowlist entry names an existing authorizing
card; (2) a negative control proves the gate still fails on an UNDECLARED kernel reference; (3) an
allowlist-ablation proves entries are load-bearing; (4) authorization + allowlist + gate change are
committed as ancestors of the gated re-run (commit-order ex-ante); (5) claim ceiling unchanged
(`kernel_substrate_engineering_only`). Claude Red pre-check required before landing.
