# Frozen report aggregation defect

During the first live Ua lane, static review found that the frozen report's
`per_decision_results.json` exclusion checks for a directory literally named
`engineering`, while the offline engineering suite creates `engineering_*`.
That aggregate therefore includes clearly marked `offline_fixture` rows.

The source, prompts, scripts, thresholds and live request order remain frozen.
The Ua and chain gate functions read exact `v1`/`v2` worker paths and do not
consume this aggregate. Resource accounting already excludes `engineering_*`.

The root reviewer authorized a read-only corrected export,
`live_per_decision_results.json`, selecting only worker paths under `v1` and
`v2`, plus an independent recount from those same live files. This export is
the table to use for real model results. The original aggregate remains as
produced, and final export metadata records its real/offline row counts.

No failed output is retried, no selected answer is altered, and no outcome is
reclassified because of this report-only defect.
