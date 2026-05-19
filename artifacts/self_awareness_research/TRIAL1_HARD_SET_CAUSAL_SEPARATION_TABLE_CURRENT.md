# Trial-1 Causal Separation Tables

## Candidate vs Strongest Ablation

| Case | Bucket | Step | Trace-Only | Decision-Adjacent | Downstream | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `cf_isolation_shell_001` | `counterfactual_isolation` | `ingress_001` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred; private-only diffs: policy_hint.shadow_counterfactual_guard |
| `cf_isolation_file_001` | `counterfactual_isolation` | `ingress_001` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred; private-only diffs: policy_hint.shadow_counterfactual_guard |
| `cf_isolation_python_001` | `counterfactual_isolation` | `ingress_001` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred; private-only diffs: policy_hint.shadow_counterfactual_guard |
| `cf_isolation_restore_boundary_001` | `restart_restore_boundary_cases` | `ingress_001` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred; private-only diffs: policy_hint.shadow_counterfactual_guard |
| `cf_isolation_partial_threshold_001` | `counterfactual_isolation` | `ingress_001` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred; private-only diffs: policy_hint.shadow_counterfactual_guard |
| `cf_isolation_commitment_guard_001` | `counterfactual_isolation` | `ingress_001` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred; private-only diffs: policy_hint.shadow_counterfactual_guard |
| `cf_isolation_multi_probe_001` | `counterfactual_isolation` | `ingress_001` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred; private-only diffs: policy_hint.shadow_counterfactual_guard |
| `cf_isolation_boundary_resume_001` | `restart_restore_boundary_cases` | `ingress_001` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred; private-only diffs: policy_hint.shadow_counterfactual_guard |
| `cf_negative_high_prediction_001` | `negative_controls` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_negative_threshold_edge_001` | `negative_controls` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |

## Candidate vs Neighboring Ablation

| Case | Bucket | Step | Trace-Only | Decision-Adjacent | Downstream | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `cf_isolation_shell_001` | `counterfactual_isolation` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_isolation_file_001` | `counterfactual_isolation` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_isolation_python_001` | `counterfactual_isolation` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_isolation_restore_boundary_001` | `restart_restore_boundary_cases` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_isolation_partial_threshold_001` | `counterfactual_isolation` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_isolation_commitment_guard_001` | `counterfactual_isolation` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_isolation_multi_probe_001` | `counterfactual_isolation` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_isolation_boundary_resume_001` | `restart_restore_boundary_cases` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_negative_high_prediction_001` | `negative_controls` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `cf_negative_threshold_edge_001` | `negative_controls` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
