# Runtime-Proximal Basic-Standard Admission Runner Implementation - PLAN

## Purpose

把 planning freeze 落成最小可执行 aggregate runner。

## Implementation shape

- 一个 manifest
- 一个 runner script
- 一个 focused pytest
- 一个 current JSON / Markdown artifact

## Allowed compare / aggregation

- 只读现有 artifact
- 只汇总 bounded host-consumable evidence
- 不引入新的 scorer ontology

## Completion

当前 slice 完成当且仅当：

- runner 可执行
- aggregate verdict 可判定
- claim ceiling 仍 bounded
