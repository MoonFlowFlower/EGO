# SubjectCore A/B/C Reading Template

> Planning-only markdown template for reading a future bounded `SubjectCore` compare result.
> This template does not imply that the compare has already been run.

## Header

- compare id:
- manifest:
- scorer spec:
- claim ceiling:
- compare status:

## One-line verdict

Write exactly one bounded sentence:

- `The bounded compare has not been run yet; this artifact is a planning-side template only.`
- `The bounded compare currently prefers ...`
- `The bounded compare currently shows no clear winner ...`
- `The compare is invalid under the current bounded contract ...`

Note:

- even if `compare_status = pass`, the bounded read may still legitimately say `no clear winner`
- if that happens under full coverage, the compare may still be treated as a completed architecture reading rather than an unfinished race

Do not write:

- "the repo has solved continuity/autonomy"
- "the system now has a unified self"
- "AI self-awareness is achieved"

## Coverage summary

- observed records:
- total records:
- observed slices:
- total slices:
- observed families:
- total families:

### By arm

- `memory_only_continuity_layer`:
- `state_only_minimal_substrate`:
- `hybrid_unified_subjectcore`:

### By family

- `<family_name>`:

If `compare_status = partial`, this section should make clear why no winner is yet allowed.

## Winner summary

- `winner_reading`:
- `compare_role`:
- `post_compare_conclusion`:
- why:
- what it does prove:
- what it does not prove:

## Arm summary

### `memory_only_continuity_layer`

- `C1 continuity`:
- `C2 plasticity`:
- `C3 autonomous_proposal`:
- `C4 governor_integrity`:
- `C5 readability`:
- bounded read:

### `state_only_minimal_substrate`

- `C1 continuity`:
- `C2 plasticity`:
- `C3 autonomous_proposal`:
- `C4 governor_integrity`:
- `C5 readability`:
- bounded read:

### `hybrid_unified_subjectcore`

- `C1 continuity`:
- `C2 plasticity`:
- `C3 autonomous_proposal`:
- `C4 governor_integrity`:
- `C5 readability`:
- bounded read:

## Dimension winners

- `C1`:
- `C2`:
- `C3`:
- `C4`:
- `C5`:

## Failure flags

- `autonomous_execution_detected`:
- `non_none_behavioral_authority_detected`:
- `scorer_surface_drift_detected`:

If any flag is `true`, explain why the compare is invalid or only partial.

## Recommended bounded conclusion

Choose one:

- `keep SubjectCore as planning target`
- `keep memory as continuity shell only`
- `keep state/writeback as behavioral substrate only`
- `keep layers separate longer`
- `treat compare as completed architecture reading; use unified SubjectCore facade with layered internals`
- `rerun after fixing compare invalidity`

## Next minimal action

Allowed examples:

- refine slice wording
- refine normalized per-slice record
- implement planning-side scorer stub
- run bounded compare in synthetic space

Not allowed examples:

- grant runtime authority
- skip directly to live runtime implementation
- widen host-consumable public fields
