---
name: "codex-project-autopilot"
description: "Use for cross-project Codex task-board automation, GitHub Project backlog scanning, unattended/bounded devloop planning, sweeping Todo issues, or deciding what Codex should do next from a Project board. This generic skill reads a project contract first and uses the Codex autopilot scripts for report, plan-next, classification, and dry-run loops. It does not replace project-specific skills such as ego-operator-devloop."
---

# Codex Project Autopilot

Use this skill when the user asks Codex to work from a task board, run semi-autonomously, sweep Todo/In Progress issues, or build/operate a cross-project devloop.

## Workflow

1. Read the project contract:
   `python3 scripts/codex_project_autopilot.py doctor`
2. Inspect the current board:
   `python3 scripts/codex_project_autopilot.py report`
3. Select a candidate without mutation:
   `python3 scripts/codex_project_autopilot.py plan-next`
4. In dirty repositories, record a local operational baseline before L2 dry-run planning:
   `python3 scripts/codex_project_autopilot.py baseline`
5. Inspect scoped changes against that baseline:
   `python3 scripts/codex_project_autopilot.py diff-scope`
6. For unattended/batch requests, run bounded dry-run planning:
   `python3 scripts/codex_project_autopilot.py run-loop --dry-run --max-issues 3 --max-minutes 10`
7. For closeout automation, inspect eligibility before mutation:
   `python3 scripts/codex_project_autopilot.py closeout-check --issue <n>`
8. For scheduled patrols, use L3 dry-run mode only:
   `python3 scripts/codex_project_autopilot.py run-loop --mode l3-closeout --dry-run --write-report`
9. Only move from dry-run to implementation or closeout when the selected issue is ready, local authority is clear, and the current project contract permits that autonomy level.

## Stop Conditions

Stop instead of acting when:

- No project contract exists.
- The issue is classified as `human_required`, `aggregate`, `parked`, `supporting`, `high_impact`, `blocked`, or `unknown`.
- The worktree has unsafe dirty changes outside the contract's allowed mutation paths.
- A dirty-baseline run shows new or changed out-of-scope paths.
- The action would modify program state, evidence ledger, protected runtime paths, credentials, or external service settings.
- The required verification profile is missing.
- The issue requires human smoke, a Stage Card, permissions expansion, memory promotion, mainline/demotion, or scheduled observation before closeout.
- An LLM reviewer says closeout is allowed but any hard-stop gate is active; hard-stop gates win.

## Pairing

- Pair with project-specific skills after selection. In EGO, EgoOperator human-trial logs, GitHub comments, file/web_fetch/approval/memory regressions, and closeout still use `ego-operator-devloop`.
- Pair with `ego-reflective-quality-gate` for high-risk agent/autopilot architecture or repeated failure.
- Pair with `ego-review-against-acceptance` before claiming done.

## Claim Boundary

This skill can coordinate a bounded task-board devloop. It cannot prove full unattended autonomous development, stable productivity gains, product runtime efficacy, durable memory efficacy, live autonomy, or consciousness.
