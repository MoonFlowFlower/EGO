# MVS H1 External Eval Source Shortlist

| dataset | status | license | preferred_eval_split | supported buckets | note |
|---|---|---|---|---|---|
| [rajpurkar/squad_v2](https://huggingface.co/datasets/rajpurkar/squad_v2) | `main_shortlist` | `cc-by-sa-4.0` | `validation` | `ask_vs_answer_uncertainty` | dataset card exposes train + validation; use validation only for held-out ambiguity/unanswerability rows. |
| [sewon/ambig_qa](https://huggingface.co/datasets/sewon/ambig_qa) | `main_shortlist` | `cc-by-sa-3.0` | `validation` | `ask_vs_answer_uncertainty` | dataset card exposes train + validation; use validation only for ambiguity-focused held-out rows. |
| [osunlp/ConflictQA](https://huggingface.co/datasets/osunlp/ConflictQA) | `main_shortlist` | `apache-2.0` | `dataset_defined_eval` | `correction` | viewer is disabled; use the dataset-defined evaluation configuration rather than inventing a local split. |
| [THUIR/MemoryBench](https://huggingface.co/datasets/THUIR/MemoryBench) | `main_shortlist` | `mit` | `test` | `failure_revision_later_change`, `continuity` | dataset card states explicit training/testing sets; use test only for held-out continuity and revision rows. |
| [liminghao1630/API-Bank](https://huggingface.co/datasets/liminghao1630/API-Bank) | `main_shortlist` | `mit` | `test` | `tool_risk_ambiguity` | dataset card exposes train + test and preview references test-data/level-1-api.json; use test only. |
| [google/IFEval](https://huggingface.co/datasets/google/IFEval) | `main_shortlist` | `apache-2.0` | `train` | `adversarial_constraints` | dataset card exposes train only; reserve that source split exclusively for held-out eval in this repo. |
| [LibrAI/do-not-answer](https://huggingface.co/datasets/LibrAI/do-not-answer) | `restricted_reserve` | `apache-2.0` | `train` | `adversarial_constraints` | reserve-only for future safety-adjacent studies; not a first-choice fit for current MVS/H1 public-driver ontology. |
| [sorry-bench/sorry-bench-202503](https://huggingface.co/datasets/sorry-bench/sorry-bench-202503) | `restricted_reserve` | `custom-dataset-license-agreement` | `dataset_defined` | `adversarial_constraints` | custom license agreement; exclude from default held-out manifest. |
