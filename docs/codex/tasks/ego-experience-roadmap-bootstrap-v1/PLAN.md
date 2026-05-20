# EGO Experience-First Roadmap Bootstrap v1 PLAN

## Milestone 1: Classification Support

- Extend project contract and autopilot classifier for `Epic` and `Research` roadmap cards.
- Keep epic overview cards non-executable.
- Allow structured research cards to be selected when they are scoped and have acceptance gates.

## Milestone 2: Roadmap Issue Bootstrap

- Create 9 epic overview issues.
- Create executable issues under each epic with canonical source, acceptance gate, rollback, claim ceiling, and observation class.
- Mark Epic 0 `In Progress`; executable cards start `Todo` until an implementation run explicitly takes ownership.

## Milestone 3: Verification

- Run autopilot report and plan-next.
- Confirm no new roadmap issue is `unknown`.
- Run L3 dry-run patrol and verify it does not auto-close human/high-impact work.
- Run script tests and scoped diff check.

## Rollback

Close incorrectly created issues as not planned / superseded, then revert contract/test/task-doc changes.
