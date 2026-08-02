# EGO-V2-PUBLIC-FEATURED-COMPOSITIONAL-CAUSAL-TRANSFER-001O

## Authority and bounded objective

- Base HEAD: `827f2ac56fb0844fb51b2b854cf8ecd7dade094c`.
- Branch: `codex/ego-v2-public-featured-compositional-transfer-001o`.
- This is a new, explicitly registered dev/research benchmark successor. It
  changes benchmark observation, action and world grammar only inside a new
  default-off task-local module. It does not overwrite or reinterpret 001N.
- Product default remains the within-world public Bayesian posterior.
- 001L product qualification and original 001J heldout remain untouched.
- No neural or dual-timescale learner is implemented by this task.
- Local commit only. Push, tag, LLM, network, autostart and background dispatch
  are forbidden.

The objective is a capacity certificate for
`PUBLIC-FEATURED-COMPOSITIONAL-CAUSAL-TRANSFER`: determine whether exact legal
hierarchical Bayes can reuse public feature/effect structure across worlds,
while still requiring current-world interaction to infer a hidden local
nuisance.

## Mechanistically distinct benchmark designs considered

1. **Discrete public linear-factor hierarchy (selected).** Five generic binary
   public factors compose energy and safety effects. A shared global coefficient
   hypothesis transfers; a hidden per-world polarity nuisance must be inferred
   from current feedback. Strongest rebuttal: a linear family may make
   composition too easy. Cheapest discriminator: unseen-combination lookup and
   feature-ablation controls must fail while exact hierarchical Bayes succeeds.
2. **Public Boolean causal program.** Effects follow a small AND/XOR rule over
   features. Strongest rebuttal: finite rule enumeration can turn the benchmark
   into program-ID selection rather than graded causal prediction. Cheapest
   discriminator would be unseen high-order parity combinations. Rejected for
   this capacity stage because it adds a second representation question.
3. **Learned public embeddings.** Transfer a learned feature encoder. Strongest
   rebuttal: learner capacity and benchmark capacity become confounded. Cheapest
   discriminator would require a reference teacher anyway. Rejected until the
   exact-reference admission gate passes.

## Successor grammar

- Public observation contains three slots. Each slot exposes only five generic
  binary fields `feature_0..feature_4`.
- Legal actions are `interact_0`, `interact_1`, `interact_2`, and `rest`.
- Slot order is re-permuted every step. Token ID, combination ID, world ID,
  split, seed, global-mechanism ID, local-mode ID and future outcomes are never
  candidate inputs.
- A public family of 40 possible shared linear mechanisms is known to both
  scratch and transfer references. The realized mechanism is evaluator-only.
- Each world has an evaluator-only local mode: `normal` or `full_reverse`, with
  frozen prior probabilities 0.75/0.25. Thus public features are predictive but
  do not determine the answer without current-world feedback.
- Candidate 1 used a public three-point noise distribution and failed because
  scratch exact Bayes acquired the shared mechanism too cheaply. The preserved
  second and final search candidate changed only feedback-support overlap: five
  public energy-noise points aligned to the energy effect lattice and five
  public safety-noise points aligned to the safety lattice. Exact references
  marginalize mechanism, local mode and feedback noise.
- The prior anonymous-permutation 001N grammar is preserved byte-for-byte as a
  negative-control benchmark and is not rerun.

## Capacity references and controls

- `UNIFORM_RANDOM`
- `PRIVATE_ORACLE`
- `PRIVATE_ALIGNED_REFERENCE`
- `SCRATCH_EXACT_BAYES`
- `TRANSFER_EXACT_HIERARCHICAL_BAYES`
- `NO_UPDATE`
- `CUE_SHUFFLE`
- `FEATURE_ABLATION`
- `HISTORY_SHUFFLE`
- `SURFACE_LOOKUP`

Transfer may use only the frozen public grammar family, prior public training
histories, current public observation and actual feedback. It may not receive
evaluator identities or truth. Surface lookup sees the same training histories
but cannot compose an effect for an unseen feature combination.

## Admission gates

Before any packet run, symbolic admission requires:

- `0 < I(public cue; effect) < H(full shared mechanism identity)`;
- every single feature level appears in training-dev;
- qualification and replication combinations are absent from all dev splits;
- oracle has positive random headroom;
- optimistic necessary local-mode probe excess cost is less than the full
  private-aligned headroom estimate, so probing does not consume all available
  headroom. This is the frozen machine-readable gate and the operator's stated
  requirement; an earlier prose-only "less than half" phrase was inconsistent
  and is preserved in the conflict-resolution artifact rather than treated as
  a post-result threshold change.

Search-dev must then show, without threshold changes:

- transfer early deficit-AUC is lower than scratch;
- recovery is at least 10% of scratch-to-private-aligned headroom;
- at least 12/16 paired worlds have positive direction;
- unseen-combination effect-sign accuracy is at least 0.80;
- each of cue shuffle, full feature ablation, history shuffle and no-update
  removes at least half the observed transfer gain;
- surface lookup does not pass the transfer gate;
- full-reverse worlds recover by the late window without material negative
  transfer.

Only a passing search-dev freezes source, grammar, packets and thresholds. New
task-local qualification and replication are then each consumed once. Both
must independently pass the same gate before a minimal dual-timescale learner
is authorized. Otherwise the learner remains unauthorized and all negative
evidence is retained.

## Claim ceiling

At most this task can establish benchmark-local, public-feature-mediated
compositional causal transfer for an exact finite hierarchical reference. It
cannot establish general transfer, a learned representation, subjectivity,
agency, consciousness, electronic life or real-world survival.
