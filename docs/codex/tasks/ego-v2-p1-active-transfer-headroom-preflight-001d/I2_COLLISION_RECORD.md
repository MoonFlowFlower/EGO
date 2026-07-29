# 001D-I2 collision-before-collapse record

## Real unknown

Can the already-frozen 001D active-information reference be executed and independently recomputed without turning a 7,168,356-case exact contract into an unauditable in-memory object, a stored-answer replay, or a resource-unbounded governance exercise?

The scientific unknown remains the frozen 001D headroom hypothesis. This record chooses only the evidence-execution architecture; it does not choose or tune a scientific answer.

## Candidate 1 — monolithic materialized JSON packet

- **Grade:** rejected shortcut.
- **Evidence produced:** one canonical JSON object containing every ledger and prerequisite record, then one reducer call.
- **Strongest cheap baseline that can match it:** a stored precomputed packet or self-hashed result dictionary can look identical without fresh computation.
- **Leakage/hard-coding risk:** high. Expected verdicts, aggregate booleans, or cached actions can enter the packet before validation; peak memory grows with all 7,168,356 records.
- **Smallest falsifier:** enforce a low memory limit or mutate one early record after the object is built. The design either exhausts memory or cannot prove pre-read ordering.
- **Expected failure mode:** tens of gigabytes of duplicated Python objects, process death, partial files, and replay that reads stored answers before recomputing.
- **Strongest objection to rejection:** a monolith is simplest to reason about and could be compressed. Response: simplicity is outweighed by the measured 10.76-GB lower bound before wrappers/recompute duplication, and compression does not solve pre-read or peak-memory provenance.

## Candidate 2 — stored primary rows plus reducer-only independent check

- **Grade:** transitional but scientifically insufficient.
- **Evidence produced:** the primary runner emits rows once; a separate reducer recomputes aggregates and verdicts from those rows.
- **Strongest cheap baseline that can match it:** the same buggy or leaked row producer. Independent aggregate arithmetic cannot detect a wrong prediction, query, posterior, or action embedded identically in every row.
- **Leakage/hard-coding risk:** medium-high. The row producer remains a single point of scientific failure; a result literal can be distributed across apparently valid rows.
- **Smallest falsifier:** inject a common-bug canary into primary prediction bytes while keeping row schemas and aggregate formulas correct. Reducer-only checking accepts it.
- **Expected failure mode:** exact replay and row-level aggregation pass while the actual learner computation is wrong.
- **Strongest objection to rejection:** full independent row reproduction duplicates a large implementation. Response: duplication is expensive, but the frozen parent explicitly requires an independent implementation path; downgrading it after I1 would overstate evidence.

## Candidate 3 — selected: length-prefixed streaming plus separate row producer

- **Grade:** formal bounded solution if resource admission and TDD pass.
- **Evidence produced:** exact ordered, length-prefixed, hash-chained stream shards; primary, fresh-process, and separate independent row/aggregate recomputation; strict incremental consumer; computed reduction and standard artifact bundle.
- **Strongest cheap baseline that can match it:** `CANDIDATE_RULE_AMORTIZED_LOOKUP` can still match the finite behavior. It is retained and caps claims; the architecture does not pretend to prove non-memorization.
- **Leakage/hard-coding risk:** lower but nonzero. Same human/model lineage may encode the same misunderstanding in two paths. Frozen design bytes, divergent algorithms, common-bug canaries, source-import prohibition, and pre-read receipts reduce but do not eliminate this risk.
- **Smallest falsifier:** reverse two adjacent frames, splice a shard, mutate a target-independent public input, sabotage one independent posterior/median/query operation, or force stored-primary read before recompute completion. Each must fail closed.
- **Expected failure mode:** resource admission blocks before formal run; otherwise the first primary/independent disagreement stops reduction and produces only an engineering failure packet.
- **Strongest objection:** the stream may consume tens of gigabytes and hours while remaining a static lookup-saturated preflight. This objection is valid. Therefore the 120-GiB/24-h/150-GiB resource gates, one-bank measurement, and amortization claim ceiling are mandatory. If they fail, do not optimize the packet post-result; reframe to a smaller preregistered bank design under a successor task.

## Selection

Select Candidate 3 because it is the only option that satisfies the frozen replay, exact-order, independent-row, and bounded-memory requirements without silently weakening the evidence claim.

This is not globally optimal if the objective is immediate visible product behavior. It is locally necessary only because the current route asks a prerequisite question: whether any active-transfer reference has headroom beyond equal-access controls before neural/product implementation. If I2 is resource-blocked or the static reference is lookup-saturated, the next better global action is not more evidence plumbing; it is to freeze that negative boundary and design a smaller prospective learned-candidate benchmark with genuinely unconsumed environments.

## Decision boundary

- Proceed only after the Phase-C provenance lock binds actual source/test/runtime bytes and resource measurements.
- Stop before formal execution on any hash drift, insufficient disk, full-packet materialization, or missing separate row producer.
- Stop before neural/product work unless the final frozen 001D verdict is `ACTIVE_TRANSFER_STATIC_REFERENCE_FEASIBLE` and no structural equal-access control matches.

## Independence boundary

Primary and independent implementations are separate code paths but are authored within the same Codex/model lineage. This is internal algorithmic separation, not external independent audit or replication.
