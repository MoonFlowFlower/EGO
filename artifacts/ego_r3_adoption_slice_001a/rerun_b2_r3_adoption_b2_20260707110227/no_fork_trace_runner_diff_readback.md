# EGO-R3-ADOPTION-SLICE-001A — TraceRunner no-fork diff readback

Evidence role: B-1 post-check readback for the A5 hook-only condition.

- execution_date_local: 2026-07-07
- repo: `D:\Project\AIProject\MyProject\Ego`
- HEAD: `fd9924e036d433069b59389d59b0cc07878f40ef`
- base_commit: `be2de377eda80f513d82173ea363282f8d1f1a37`
- target_file: `EgoDesktop/src/joiRealLoopGAblationTraceRunner.js`
- claim_ceiling: `r3_adoption_engineering_only`

This readback records the host-side diff evidence only. It does not by
itself prove runtime integration safety, mechanism validity, learning,
stable user benefit, live autonomy, agency, consciousness, subjective
experience, or real emotion.

## Command 1

```powershell
git diff --numstat be2de377..fd9924e0 -- EgoDesktop/src/joiRealLoopGAblationTraceRunner.js
```

### Output

```text
11	0	EgoDesktop/src/joiRealLoopGAblationTraceRunner.js
```

## Command 2

```powershell
git diff be2de377..fd9924e0 -- EgoDesktop/src/joiRealLoopGAblationTraceRunner.js
```

### Full unified diff output

```diff
diff --git a/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js b/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js
index 86a7c4e0..ec64d973 100644
--- a/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js
+++ b/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js
@@ -7,6 +7,7 @@ const {
   buildJoiRealLoopGAblationContract,
   buildJoiRealLoopTraceRow,
   hashValue,
+  validateNoAuthorityFields,
} = require("./joiRealLoopGAblationHarness");

 const CLAIM_CEILING = "egodesktop_real_loop_g_ablation_trace_runner_contract_only";
@@ -204,6 +205,7 @@ function createJoiRealLoopTraceRunner(env, options = {}) {
   const traceDir = contract.trace_dir ? path.resolve(contract.trace_dir) : "";
   const blockedStatus = contractBlockStatus(contract);
   const sourceHashes = sourceHashesFor(options.repoRoot, options.sourceHashes);
+  const kernelAdoptionHook = typeof options.kernelAdoptionHook === "function" ? options.kernelAdoptionHook : null;
   let traceRowCount = 0;
  let eventCounter = 0;

@@ -329,6 +331,15 @@ function createJoiRealLoopTraceRunner(env, options = {}) {
       },
       replayInputs,
     });
+    if (kernelAdoptionHook) {
+      const kernelAdoptionBlock = kernelAdoptionHook({ contract, eventCounter, payload, row });
+      if (kernelAdoptionBlock && typeof kernelAdoptionBlock === "object") {
+        row.kernel_adoption_v0 = validateNoAuthorityFields(
+          kernelAdoptionBlock,
+          "kernel_adoption_v0",
+        );
+      }
+    }
     appendJsonLine(path.join(traceDir, "trace_rows.jsonl"), row);
     traceRowCount += 1;
     const hasIpcEntrypoint = entrypointProvenance.status === "ipc_event_observed";
```
