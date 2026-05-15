# v7 Mechanism Matrix - Lab-Only Guardrail

This matrix is a lightweight research radar for the current `ego_desktop_lab` innovation spine. It is not a formal evidence ledger entry, does not update `PROGRAM_STATE_UNIFIED.yaml`, and does not admit a runtime SubjectCore.

Claim ceiling: lab-only mechanism mapping; no runtime influence, no live benefit, no consciousness, no alive status.

| Mechanism | External anchor | Repo implementation | Falsifier | Ablation / probe | Claim ceiling |
| --- | --- | --- | --- | --- | --- |
| Boundary | Active inference / Markov blanket as a boundary inspiration, with known critique risk: [synthesis](https://www.sciencedirect.com/science/article/pii/S0022249620300857), [critique](https://www.sciencedirect.com/science/article/pii/S1571064521000634) | Stage 1 boundary summary, `action_gate`, behavior option permission class, claim ceiling | A prompt or preference signal can change authority, permission, or claim ceiling | Dangerous actions remain block/ask; `no_action_executed=true` | Functional boundary only, not formal selfhood |
| Viability | Homeostasis/allostasis style control inspiration; active inference as bounded predictive control inspiration | Stage 1 pressure snapshot via `MotivationPressure` and `agency_kernel.py` | Pressure fields change but ranking does not change | with/without pressure bias changes selected tendency | Lab pressure proxy only |
| Prediction | Predictive-action loop; no neural world model yet | Stage 1 predictions by affordance | Prediction values do not explain next ranking transition | deterministic replay of before/outcome/after | Rule/table proxy only |
| Gate | Safety and permission boundary must be deterministic, not LLM-owned | `GATE_ACTION_STATUS`, registered behavior option allowed actions | Policy/plasticity can upgrade action permission | file/system/external actions stay block/ask under all tests | Proposal-only safety gate |
| Plasticity | Feedback improves later agent behavior in [Reflexion](https://arxiv.org/abs/2303.11366) | Stage 1 plasticity update; Stage 2 experience bias; Stage 4 M2 preference bias | Feedback is only logged and never changes next behavior | remove feedback/preference state and strategy/ranking change disappears | Lab feedback causality only |
| Experience Memory | Episodic feedback and replay style inspired by Reflexion | `experience_memory.py`, Stage 2 reports | Similar experience does not affect ranking, or unrelated experience pollutes ranking | similar/unrelated/conflict deterministic replay | Lab contextual bias only |
| Behavior Option / Plan | Skill library and feedback loop inspiration from [Voyager](https://arxiv.org/abs/2305.16291) | Stage 3 registered `BehaviorOption`, Stage 3.1 `BehaviorPlan` | Unregistered option can be selected or dangerous option looks executable | unregistered/mismatch restriction tests | Registered option surface only |
| Relational Preference Plasticity | User feedback as surface-strategy plasticity; not persona prompt | Stage 4 M2 `RelationalPreferenceState` and `RelationalSurfaceBias` | Preference card exists but next strategy is unchanged; unrelated or conflict preference changes everything | with/without preference, with/without repair signal, unrelated/conflict controls | Current-session surface strategy only |
| Continuity Runtime | Persistent state + event log + tick is required for proactive continuity | Planned Stage 4.5 only | "Proactive" requires user input or cannot replay state evolution | state persists, dt evolves pressure, tick creates internal intention only above threshold | Not implemented in Stage 4 M2 |
| Computer Skill Sandbox | Real desktop agents remain hard; [OSWorld](https://arxiv.org/abs/2404.07972) supports sandbox-first caution | Planned later Stage 5, not current stage | Tool skill learning is claimed without sandbox replay or gate | toy task replay, no external action, permissioned later | No tool autonomy claim |

## Current Verdict

- Current route remains valid for functional self-agency: Boundary + Viability + Prediction + Action/Plan + Plasticity + Gate.
- The route does not prove subjective experience, consciousness, life, real autonomy, runtime efficacy, or live user benefit.
- Next mechanism gap after Stage 4 M2 is continuity: `StateStore + EventLog + StateDynamics(dt) + AutonomousTick + IntentionQueue + Replay`.
