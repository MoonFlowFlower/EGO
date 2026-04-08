# Repo Authority Cleanup - FILE FATE LEDGER

| path | current_role | formal_caller | tests_tools_docs_caller | classification | why | delete_precondition | rollback_path |
|---|---|---|---|---|---|---|---|
| `EgoCore/app/openemotion_hooks/*` | current host hook chain | yes | yes | `authority` | formal mainline depends on it | none | keep current hook chain |
| `EgoCore/app/runtime_v2/proto_self_runtime.py` | formal runtime bridge | yes | yes | `authority` | mainline bridge and governed writeback live here | none | keep current runtime bridge |
| `EgoCore/app/openemotion_adapter/proto_self_adapter.py` | formal adapter | yes | yes | `authority` | mainline adapter boundary | none | keep current adapter |
| `OpenEmotion/openemotion/proto_self_v2/*` | formal surface/orchestrator | yes | yes | `authority` | current formal subject mainline surface | none | keep v2 surface |
| `OpenEmotion/openemotion/proto_self/*` reachable by v2 | active substrate | yes | yes | `active_substrate` | current runtime semantics still depend on v1 substrate | dedicated later wave must prove retirement | keep substrate |
| `OpenEmotion/openemotion/self_model/*` | formal self-model owner | yes | yes | `authority` | formal owner already wired into runtime injection/writeback and now self-describes its authority role in code | none | keep owner package |
| `OpenEmotion/emotiond/self_model_adapter.py` | legacy compat bridge | no | yes | `delete_candidate` | no formal caller; still has legacy daemon/tool/docs callers and confuses authority | migrate/archive remaining tools/docs and verify no formal caller regression | restore module and referenced tools/docs |
| `OpenEmotion/emotiond/self_model_mirror.py` | legacy read-only mirror | no | yes | `delete_candidate` | no formal caller; retained only for reference-only mirror/report tooling | migrate/archive remaining mirror tooling | restore mirror module and tooling |
| `EgoCore/app/openemotion_adapter/proto_self_restore.py` | restore shim | no | yes | `delete_candidate` | no formal caller; current role is legacy restore/helper only | remove package re-export and prove restore path callers are non-formal | restore shim and package export |
| `OpenEmotion/openemotion/identity/identity_invariants.py` | identity reference surface | no | yes | `reference_only` | already code-demoted; keep until or unless formal owner cutover is real | future mainline cutover task | restore reference-only status |
| `OpenEmotion/openemotion/identity/long_term_self_summary.py` | long-term summary support | no | yes | `reference_only` | not consumed on formal mainline | future formal consumer task | restore reference-only status |
| `OpenEmotion/emotiond/reflection_*` and `self_counterfactual.py` | reflection legacy residue | no | yes | `reference_only` | current wave does not touch reflection semantics; keep as non-authoritative residue | later reflection wave + caller proof | restore reference-only classification |
| `OpenEmotion/emotiond/memory_legacy.py` | historical memory residue | no | yes | `reference_only` | not on formal mainline, but current archive/delete admission not yet done | later memory/deletion wave | restore reference-only classification |
| `OpenEmotion/openemotion/cycle_core/*` | historical cycle reference | no | yes | `reference_only` | current mainline uses proto_self/proto_self_v2, not cycle_core | later archive/delete admission | restore reference-only classification |
| `artifacts/P0`–`artifacts/P7` | historical cleanup artifacts | no | yes | `archive` | useful as history, not current formal evidence | canonical current evidence index must be complete first | keep in-place or restore from archive |
| `OpenEmotion/artifacts/mvp10` / `mvp11*` / `memory_loop_v*` / old eval dirs | historical research/eval artifacts | no | yes | `archive` | not current mainline proof; high storage/noise cost | current evidence inventory and archive layout must exist first | keep in-place or restore from archive |
