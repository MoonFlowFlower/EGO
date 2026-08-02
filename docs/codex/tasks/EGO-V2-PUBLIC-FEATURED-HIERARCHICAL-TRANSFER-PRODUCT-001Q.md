# EGO-V2-PUBLIC-FEATURED-HIERARCHICAL-TRANSFER-PRODUCT-001Q

## Authority and objective

- Base HEAD: `c5df39522c5649ad1cbee1d1a7097f33b6abcfa1`.
- Branch: `codex/ego-v2-public-featured-transfer-product-001q`.
- Authorized predecessor decision:
  `ROUTE_A_LEARNER_PRODUCT_SEMANTICS_AUTHORIZATION_REQUIRED`.
- Operator authorization: create a default-off product successor using frozen
  001O public feature slots, positional interactions, and energy/safety
  transition contract, then wire a clean learner extraction through the sole
  controller/reducer/store/replay chain.

The real goal is a runnable product vertical slice. It must use the existing
`PlaygroundController -> engine.compute_step -> SQLiteEventStore` path. New
modules may provide pure learner and environment primitives, but may not own a
second controller, reducer, store, replay implementation, or evaluator wrapper.

## Frozen product contract

- Product profile: `public_featured_hierarchical_transfer`, default off.
- Public observation:
  - `organism`: energy, safety, target;
  - three positional `slots`;
  - each slot exposes exactly five binary public features;
  - `previous` contains only prior public action/result or null.
- Actions: `interact_0`, `interact_1`, `interact_2`, `rest`.
- Terminal: energy <= 0 or safety <= 0, plus the existing bounded-life censor.
- Learner state:
  - slow shared marginal over the public 40-hypothesis family;
  - fast current-world nuisance posterior;
  - both update only from public observation, selected action, and realized
    energy/safety feedback.
- Planner: fixed homeostatic expected-deficit + terminal-risk + information-gain
  planner. There is no independent learned policy reward.
- World switch: existing respawn boundary. Shared posterior persists; current
  nuisance posterior and public short history reset.

## Leakage and truth-source boundary

- The clean learner module must not contain packet splits, evaluator arms,
  private constructors, realized mechanism index, world/seed/layout identifiers,
  oracle actions, or future values.
- Private environment truth belongs only to the pure product-world module and
  is never passed into learner plan/update functions or public trace fields.
- The product must not import `public_featured_transfer.py` or the 001O runner.
- Stored traces are comparison-only during recovery; recomputation precedes
  trace reads exactly as in the existing store.

## TDD milestones and acceptance

1. Clean learner/world primitives fail first, then pass public-input, exact
   prediction/update, reset, determinism, and leakage tests.
2. Engine profile fails first, then passes default-off, selector exclusivity,
   energy/safety metabolism, terminal, slow/fast persistence, component hashing,
   replay, and trace tests.
3. CLI/terminal/HTML fails first, then exposes energy, safety, deficits, slot
   features, per-action predictions, selected reason, actual result, uncertainty,
   slow/fast hashes, update count, and world switches.
4. Freeze one new product qualification packet. It must verify fresh SQLite
   execution/recovery, product-vs-frozen-reference public API equivalence,
   no-update damage, drive intervention, private-field rejection, trace tamper
   fail-closed, and default-off regression. It must not rerun 001O packets or
   touch 001J heldout.

## Stop and rollback

- Stop rather than adapt token identity/private assignment into public features.
- Stop if the implementation needs LLM, network, autostart, background dispatch,
  old heldout, push, or tag.
- Rollback is deletion of the new profile/modules and restoration of the prior
  engine/controller/view bytes; the default normal product remains unchanged.

## Claim ceiling

Passing proves only that the previously admitted exact public model-based learner
can run, learn, persist, and replay inside this bounded product successor under
the frozen featured grammar. It does not prove learning outside the finite
hypothesis family, general transfer, consciousness, agency, or real-world
survival ability.
