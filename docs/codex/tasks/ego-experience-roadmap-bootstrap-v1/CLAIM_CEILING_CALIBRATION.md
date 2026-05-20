# EgoOperator Experience-First Claim Ceiling Calibration v1

## Purpose

This file defines the allowed wording for experience-first roadmap milestones. It prevents local tests, scripted samples, or human comments from being upgraded into claims about durable user benefit, runtime efficacy, live autonomy, consciousness, or independent awareness.

## Global Rule

Every experience-first closeout must name its evidence class and must keep the claim at or below the row that matches the strongest evidence actually collected.

## Allowed Claim States

| claim_state | Minimum evidence | Allowed wording | Must not imply |
| --- | --- | --- | --- |
| `local_candidate` | deterministic local tests or static contract checks pass | `<capability> local candidate pass` | real-user benefit, production reliability, real-provider quality |
| `scripted_real_entry` | a script uses the same user-facing entrypoint and produces deterministic pass/fail output | `<capability> scripted real-entry observation pass` | human preference, stable benefit, broad naturalness |
| `scripted_with_llm_judge` | local/scripted evidence plus bounded reviewer verdict | `<capability> reviewer-assisted scripted observation pass` | objective truth, human preference, stable benefit |
| `real_provider_smoke` | one or more real provider CLI/user-entry samples are attached | `<capability> real-provider smoke pass` | provider stability, long-term quality, durable memory efficacy |
| `human_smoke` | explicit operator comment/log says the tested case felt acceptable | `<capability> human-observable smoke pass` | general user benefit, stable user benefit, complete milestone success |
| `milestone_candidate` | relevant mechanism tests and required scripted/human samples pass for the milestone scope | `<milestone> operational proxy milestone candidate pass` | consciousness, independent awareness, live autonomy, runtime efficacy |
| `stable_benefit_pending` | repeated longitudinal samples are not yet available | `stable benefit pending longitudinal evidence` | any completed stable-benefit claim |

## Observation Class Mapping

| observation_class | Max closeout wording without extra evidence |
| --- | --- |
| `deterministic_local` | `local_candidate` |
| `scripted_real_entry` | `scripted_real_entry` |
| `scripted_with_llm_judge` | `scripted_with_llm_judge` |
| `human_required` | no automatic closeout; wait for `human_smoke` evidence |
| `human_comment_observation` | planning packet only; not closeout proof |

## Closeout Comment Template

```text
Claim: `<capability> <allowed claim state wording>`.

Evidence:
- observation_class: `<class>`
- verification: `<commands or linked report>`
- human/source log: `<link or not applicable>`

Not claimed: real consciousness, independent awareness, stable user benefit, runtime efficacy, live autonomy, durable memory efficacy, or provider/model stability.
```

## Disallowed Escalations

- Do not say an experience milestone proves real consciousness or independent awareness.
- Do not say a single human smoke proves stable user benefit.
- Do not say a provider smoke proves provider/model stability.
- Do not say local tests prove runtime efficacy.
- Do not say candidate-local memory proves durable memory efficacy.
- Do not say bounded initiative proves live autonomy.

## Upgrade Gate

To move beyond `milestone_candidate`, create a separate Stage Card that defines:

- longitudinal sample count and time window;
- real user-entry path;
- failure taxonomy;
- reviewer or human observation contract;
- rollback condition;
- exact wording that remains forbidden.
