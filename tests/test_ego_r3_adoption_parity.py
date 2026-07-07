import json
import subprocess
import sys
from pathlib import Path

from scripts.ego_kernel.state import KernelState, canonical_json_dumps, canonical_sha256


REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = REPO_ROOT / "EgoDesktop" / "src" / "joiRealLoopGAblationKernelStateAdapter.js"


def _node_payload() -> dict:
    script = f"""
const adapter = require({json.dumps(str(ADAPTER_PATH))});
const envelope = adapter.createKernelStateEnvelope({{
  taskId: "ego-r3-adoption-slice-001a",
  runId: "python-parity-run",
  episodeId: "python-parity-episode",
  stepId: 3,
  substate: {{
    cjk_label: "椰果",
    decimal_control: 0.125,
    nested: {{ z: -3, a: ["β", true, null] }},
  }},
  seedRegistry: {{ step_3: {{ seed: 777, draw_index: 3 }} }},
  ablations: {{ llm_mode: "replay_locked" }},
}});
process.stdout.write(JSON.stringify({{
  vectors: adapter.PARITY_VECTORS.map((vector) => ({{
    id: vector.id,
    value: vector.value,
    canonical: adapter.canonicalJsonStringify(vector.value),
    hash: adapter.canonicalSha256(vector.value),
  }})),
  parity_vector_sha256: adapter.PARITY_VECTOR_SHA256,
  envelope,
  envelope_hash: adapter.canonicalSha256(envelope),
}}));
"""
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_js_canonical_hashes_match_python_kernel_state_hashes_for_all_parity_vectors():
    payload = _node_payload()

    assert len(payload["vectors"]) == 16
    for vector in payload["vectors"]:
        assert canonical_json_dumps(vector["value"]) == vector["canonical"], vector["id"]
        assert canonical_sha256(vector["value"]) == vector["hash"], vector["id"]

    expected_vector_sha = canonical_sha256([
        {"id": vector["id"], "value": vector["value"]} for vector in payload["vectors"]
    ])
    assert payload["parity_vector_sha256"] == expected_vector_sha


def test_js_kernel_state_envelope_is_r0_compatible_and_hashes_with_python_kernel_state():
    payload = _node_payload()
    envelope = payload["envelope"]

    assert envelope["schema_version"] == "kernel_state_v0"
    assert set(envelope) == {
        "schema_version",
        "task_id",
        "run_id",
        "episode_id",
        "step_id",
        "substates",
        "seed_registry",
        "ablations",
    }
    assert set(envelope["substates"]) == {"joi_loop_state_v0"}
    assert envelope["substates"]["joi_loop_state_v0"]["decimal_control"] == "0.125000"

    state = KernelState.from_dict(envelope)
    assert state.to_dict() == envelope
    assert canonical_sha256(envelope) == payload["envelope_hash"]
    assert state.state_hash() == payload["envelope_hash"]
