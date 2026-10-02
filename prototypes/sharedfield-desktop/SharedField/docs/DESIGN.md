# SwitchLab v0.1 — bounded offline engineering experiment

Authorized scope: implement the preceding persistent-belief/goal-controller design as an
independent, locally runnable Python package. No existing repository, EGO/ITL route,
real software action authority, external service, persona, or model API is used.

## Concrete slice
A partially observed two-resource workshop has four extraction stations, a fallible
actuator, delayed observable fault costs, and intermittent delivery commitments.
Unknown source modes and actuator condition are inferred from actual outcomes with
an eight-state Bayesian filter. This is finite-family online latent-state learning,
NOT neural training, learned model-class discovery, or learned ultimate values.

A bounded 10-step / 8-particle observation-conditioned rollout planner evaluates action consequences.
The original two-step planner is retained as a comparator; the amendment and negative
development result are recorded in BUILD_LOG.md. Goals are
resource/commitment/information outcome schemas instantiated by this planner, with
small explicit switching cost and persistent records. Schema, likelihood family,
utility and switching cost are engineered priors. The direct Bayes planner is a
strong same-access baseline; equality is retained, never promoted to mechanism PASS.
Noisy observations carry zero likelihood information. Replaying exact sufficient
statistics must be idempotent: no additional evidence or unsupported replay gain.

## Separation
World private state is owned by World; agent receives only immutable copies of public
observations and transitions. World and agent predictive physical kernels are separate
implementations tested against a published contract. Both use the same specified model
family, a deliberately disclosed well-specified-model advantage. The evaluation oracle
may access private state but is an informed finite-horizon reference, not an upper bound.
Keyed exogenous randomness avoids action-dependent RNG consumption across comparisons.

## User path
Python 3.10+ standard library only. Windows launcher or `python run.py serve` opens a
loopback-only Chinese dashboard: step, run/pause, interventions, internal computation,
state export and restore through CLI. CLI also supports deterministic run, benchmark,
trace verification, and tests. No installation, API key, GPU or internet is required.
Browser autoplay advances a simulated world clock; motivation is not a timer reward.
Closing the page stops autoplay. Internal computation cannot create observations.

## Evidence limits / STOP
Engineering tests and policy results are reported separately. All baseline/ablation
results, including negative ones, remain in the report. Missing RNN/history-transformer/
meta-learner comparison prevents a claim of superior mechanism. No social ToM, neural
consolidation, skill discovery, open-ended values or real-world integration is claimed.
Claim ceiling: bounded offline observations under this source/trace/replay contract.

## Numerical contract frozen before benchmark
Energy/coolant drains .60/.35 per tick. Matched source success .92 (healthy), .14
(damaged); unmatched .18/.04. Yield +5; diagnostic accuracy .90. Passive alternatives
+1.8 energy/+1.5 coolant. Work costs 2 energy/1 coolant, 3 work units per contract,
completion +10 and missed deadline -6. Extraction failure schedules .8 energy loss
2 ticks later. Ordinary action cost .05, diagnostic/noise .20, repair .40. Shortage
penalty is 5 per missing resource unit. Preferred terminal stocks 7/5. Hidden
mode flip probability .015 per tick and tool failure probability .008. Environment
also provides unannounced disturbances and explicit test interventions. No parameters
may be tuned on the shipped evaluation seeds to turn negative evidence positive.
