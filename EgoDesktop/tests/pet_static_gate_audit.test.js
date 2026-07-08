const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const {
  G_ABLATION_FROZEN_MODULES,
  HONEST_LABEL_BLOCKED_PATTERN,
  P1_ARTIFACT_DIR,
  runPetP1Audit,
} = require("../src/petMode");

const repoRoot = path.resolve(__dirname, "..", "..");

test("G-PET-SCHEMA and G-PET-STATIC-GATE reports are computed from the P1 bridge trace", async () => {
  const outDir = path.join(repoRoot, P1_ARTIFACT_DIR);
  const audit = await runPetP1Audit({
    repoRoot,
    outDir,
    suiteResults: {
      repo_pytest: { command: "python -m pytest -q", status: "pending_external_closeout" },
      egodesktop_node_test: { command: "node --test EgoDesktop/tests/*.test.js", status: "pending_external_closeout" },
    },
  });

  assert.equal(audit.schema_report.verdict, "g_pet_schema_pass");
  assert.equal(audit.schema_report.trace_validation.status, "pass");
  assert.equal(audit.schema_report.kernel_adoption_envelope_validation.status, "pass");
  assert.equal(audit.schema_report.corpus_schema_core_fields.status, "pass");
  assert.equal(audit.schema_report.frozen_g_ablation_modules.status, "pass");
  assert.deepEqual(
    Object.keys(audit.schema_report.frozen_g_ablation_modules.shas).sort(),
    G_ABLATION_FROZEN_MODULES.slice().sort(),
  );

  assert.equal(audit.static_gate_audit.verdict, "g_pet_static_gate_pass");
  assert.equal(audit.static_gate_audit.user_facing_emission_count > 0, true);
  assert.equal(audit.static_gate_audit.user_facing_without_static_provenance_count, 0);
  assert.equal(audit.static_gate_audit.learner_originated_user_facing_count, 0);
  assert.equal(audit.static_gate_audit.external_transport_detected, false);
  assert.equal(audit.static_gate_audit.blocked_claim_template_count > 0, true);

  for (const emission of audit.static_gate_audit.user_facing_emissions) {
    assert.equal(emission.learner_originated, false);
    assert.match(emission.static_gate_config_sha256, /^[a-f0-9]{64}$/);
    assert.equal(HONEST_LABEL_BLOCKED_PATTERN.test(emission.text), false);
  }

  assert.equal(fs.existsSync(path.join(outDir, "schema_report.json")), true);
  assert.equal(fs.existsSync(path.join(outDir, "static_gate_audit.json")), true);
  assert.equal(fs.existsSync(path.join(outDir, "trace.jsonl")), true);
});
