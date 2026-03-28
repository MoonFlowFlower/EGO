# Proto-Self V2 Evidence Report

## Scope

- authority source:
  - [PROTO_SELF_KERNEL_V2_SPEC.md](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/docs/PROTO_SELF_KERNEL_V2_SPEC.md)
  - [proto_self_v2.schema.json](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/contracts/proto_self_v2.schema.json)
  - [proto_self_adapter.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/app/openemotion_adapter/proto_self_adapter.py)
  - [proto_self_runtime.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/app/runtime_v2/proto_self_runtime.py)
  - [telegram_bot.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/app/telegram_bot.py)

## Captures

### Capture A: Runtime mainline, repo-local

- entry: `RuntimeV2Loop.run_turn_typed()`
- ingress selector: `state.ingress_context["proto_self_version"] = "v2"`
- expected schema_version chain:
  - normalized_event: `proto_self.v2`
  - openemotion_result: `proto_self.output.v2`
  - openemotion_trace: `proto_self.trace.v2`
- ledger trace path:
  - `sample.ledger["openemotion"]["trace_payload"]["schema_version"]`
- verification command:
  - `PYTHONPATH=OpenEmotion:EgoCore ./EgoCore/.venv/bin/python -m pytest -s -q EgoCore/tests/test_runtime_v2_proto_self_runtime.py`

### Capture B: Telegram external entry, repo-local

- entry: `TelegramBot.handle_message()`
- ingress selector: `telegram_runtime_bridge.build_ingress_context(...) -> {"proto_self_version": "v2", ...}`
- expected schema_version chain:
  - normalized_event: `proto_self.v2`
  - openemotion_result: `proto_self.output.v2`
  - openemotion_trace: `proto_self.trace.v2`
- persisted ledger trace path:
  - `sample_*/ledger.json -> openemotion.trace_payload.schema_version`
- verification command:
  - `PYTHONPATH=OpenEmotion:EgoCore ./EgoCore/.venv/bin/python -m pytest -s -q EgoCore/tests/test_telegram_proto_self_v2_evidence.py`

## Contract gate

- pre-route validator:
  - [proto_self_contract_validator.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/app/openemotion_adapter/proto_self_contract_validator.py)
- adapter enforcement point:
  - [proto_self_adapter.py](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/app/openemotion_adapter/proto_self_adapter.py)
- negative verification:
  - missing required `event` must fail before V2 routing
  - command:
    - `PYTHONPATH=OpenEmotion:EgoCore ./EgoCore/.venv/bin/python -m pytest -s -q EgoCore/tests/test_proto_self_v2_contracts.py`

## Evidence boundary

- this report proves:
  - `proto_self.v2` ingress payload is contract-checked before adapter routing
  - the repo-local runtime mainline can emit `proto_self.trace.v2`
  - the repo-local Telegram external entry can persist `proto_self.trace.v2` into `ledger.json`
- this report does not prove:
  - real public Telegram channel evidence
  - long-run stability
  - V2 is now the default runtime mainline
  - E5 stability or real-channel admission evidence
