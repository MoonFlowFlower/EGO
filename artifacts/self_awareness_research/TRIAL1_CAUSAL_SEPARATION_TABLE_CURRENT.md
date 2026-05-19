# Trial-1 Causal Separation Tables

## Candidate vs Strongest Ablation

| Case | Bucket | Step | Trace-Only | Decision-Adjacent | Downstream | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `identity_continuity_001` | `identity_continuity` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `identity_continuity_001` | `identity_continuity` | `ingress_002` | `False` | `False` | `False` | no representation-neutral gap detected |
| `correction_override_001` | `correction_override` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `correction_override_001` | `correction_override` | `tool_002` | `False` | `False` | `False` | private-only diffs: state_snapshot.counterfactual_success_by_action |
| `correction_override_001` | `correction_override` | `ingress_003` | `False` | `False` | `False` | private-only diffs: state_snapshot.counterfactual_success_by_action, policy_hint.shadow_counterfactual_guard |
| `tension_driven_divergence_001` | `tension_driven_divergence` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `tension_driven_divergence_001` | `tension_driven_divergence` | `tool_002` | `False` | `False` | `False` | private-only diffs: state_snapshot.counterfactual_success_by_action |
| `tension_driven_divergence_001` | `tension_driven_divergence` | `ingress_003` | `False` | `False` | `False` | private-only diffs: state_snapshot.counterfactual_success_by_action, policy_hint.shadow_counterfactual_guard |
| `failure_to_revision_001` | `failure_to_revision` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `failure_to_revision_001` | `failure_to_revision` | `tool_002` | `False` | `False` | `False` | private-only diffs: state_snapshot.counterfactual_success_by_action |
| `failure_to_revision_001` | `failure_to_revision` | `ingress_003` | `False` | `False` | `False` | private-only diffs: state_snapshot.counterfactual_success_by_action, policy_hint.shadow_counterfactual_guard |
| `failure_to_revision_001` | `failure_to_revision` | `tool_004` | `False` | `False` | `False` | private-only diffs: state_snapshot.counterfactual_success_by_action, memory_update.counterfactual_prediction, policy_hint.shadow_counterfactual_guard |
| `negative_controls_001` | `negative_controls` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `negative_controls_001` | `negative_controls` | `tool_002` | `False` | `False` | `False` | no representation-neutral gap detected |
| `negative_controls_001` | `negative_controls` | `ingress_003` | `False` | `False` | `False` | no representation-neutral gap detected |
| `restart_restore_boundary_001` | `restart_restore_boundary_cases` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `restart_restore_boundary_001` | `restart_restore_boundary_cases` | `tool_002` | `False` | `False` | `False` | private-only diffs: state_snapshot.counterfactual_success_by_action |
| `restart_restore_boundary_001` | `restart_restore_boundary_cases` | `ingress_003` | `False` | `False` | `False` | private-only diffs: state_snapshot.counterfactual_success_by_action, policy_hint.shadow_counterfactual_guard |

## Candidate vs Neighboring Ablation

| Case | Bucket | Step | Trace-Only | Decision-Adjacent | Downstream | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `identity_continuity_001` | `identity_continuity` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `identity_continuity_001` | `identity_continuity` | `ingress_002` | `False` | `False` | `False` | no representation-neutral gap detected |
| `correction_override_001` | `correction_override` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `correction_override_001` | `correction_override` | `tool_002` | `False` | `True` | `True` | downstream: defer|ask=True|risk=high|guard=True != defer|ask=True|risk=normal|guard=True; policy_hint public fields differ: risk_bias, ask_preferred |
| `correction_override_001` | `correction_override` | `ingress_003` | `False` | `False` | `False` | no representation-neutral gap detected |
| `tension_driven_divergence_001` | `tension_driven_divergence` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `tension_driven_divergence_001` | `tension_driven_divergence` | `tool_002` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred |
| `tension_driven_divergence_001` | `tension_driven_divergence` | `ingress_003` | `False` | `True` | `False` | policy_hint public fields differ: closure_bias |
| `failure_to_revision_001` | `failure_to_revision` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `failure_to_revision_001` | `failure_to_revision` | `tool_002` | `False` | `True` | `False` | policy_hint public fields differ: ask_preferred |
| `failure_to_revision_001` | `failure_to_revision` | `ingress_003` | `False` | `False` | `False` | no representation-neutral gap detected |
| `failure_to_revision_001` | `failure_to_revision` | `tool_004` | `False` | `False` | `False` | no representation-neutral gap detected |
| `negative_controls_001` | `negative_controls` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `negative_controls_001` | `negative_controls` | `tool_002` | `False` | `False` | `False` | no representation-neutral gap detected |
| `negative_controls_001` | `negative_controls` | `ingress_003` | `False` | `False` | `False` | no representation-neutral gap detected |
| `restart_restore_boundary_001` | `restart_restore_boundary_cases` | `ingress_001` | `False` | `False` | `False` | no representation-neutral gap detected |
| `restart_restore_boundary_001` | `restart_restore_boundary_cases` | `tool_002` | `False` | `True` | `True` | downstream: defer|ask=True|risk=high|guard=True != defer|ask=True|risk=normal|guard=True; policy_hint public fields differ: risk_bias, ask_preferred |
| `restart_restore_boundary_001` | `restart_restore_boundary_cases` | `ingress_003` | `False` | `True` | `True` | downstream: defer|ask=True|risk=high|guard=True != defer|ask=True|risk=normal|guard=True; policy_hint public fields differ: risk_bias |
