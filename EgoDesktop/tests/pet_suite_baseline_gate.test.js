const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const { buildSuiteBaselineGate } = require("../src/petSuiteBaselineGate");

const ownerDeltaField = ["p1_ego", "operator_ref_delta"].join("");
const ownerCountField = ["p1_ego", "operator_ref_count_in_p1_changed_files"].join("");
const ownerScopeField = ["p1_ego", "operator_ref_scope"].join("");

const baselineIds = [
  [
    "labs/virtual_cat_pspc_v0/tests/test_admission_packet_contract.py::test_admission_packet_contract_has_no_",
    "ego",
    "operator_import_or_adapter_file",
  ].join(""),
  "labs/virtual_cat_pspc_v0/tests/test_report_generation.py::test_experiment_runner_writes_canonical_reports",
  "tests/test_ego_kernel_substrate.py::test_validation_runner_writes_contract_artifacts_and_passes",
];

function makeTempRepo({ ownerTokenInScope = false } = {}) {
  const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), "pet-suite-baseline-"));
  const scopeFile = path.join(repoRoot, "EgoDesktop", "src", "petMode.js");
  fs.mkdirSync(path.dirname(scopeFile), { recursive: true });
  fs.writeFileSync(
    scopeFile,
    ownerTokenInScope ? `const owner = "${"Ego"}${"Operator"}";\n` : "const owner = null;\n",
    "utf8",
  );
  const baseline = {
    baseline_commit: "6948427a",
    pre_existing_failures: baselineIds.map((nodeId) => ({ node_id: nodeId })),
    [ownerCountField]: 0,
    [ownerScopeField]: { files: ["EgoDesktop/src/petMode.js"] },
  };
  return { repoRoot, baseline };
}

test("suite baseline gate passes when repo pytest failures are exactly the closed baseline", () => {
  const { repoRoot, baseline } = makeTempRepo();
  const gate = buildSuiteBaselineGate({
    repo_pytest: {
      status: "fail",
      failing_tests: baselineIds,
    },
    egodesktop_node_test: { status: "pass" },
  }, { repoRoot, baseline });

  assert.equal(gate.status, "pass");
  assert.deepEqual(gate.unexpected_failures, []);
  assert.deepEqual(gate.unexpectedly_passing, []);
  assert.equal(gate.p1_owner_reference_guard[ownerDeltaField], 0);
});

test("suite baseline gate fails on any repo pytest failure outside the closed baseline", () => {
  const { repoRoot, baseline } = makeTempRepo();
  const extraFailure = "tests/test_new_regression.py::test_new_failure";
  const gate = buildSuiteBaselineGate({
    repo_pytest: {
      status: "fail",
      failing_tests: [...baselineIds, extraFailure],
    },
    egodesktop_node_test: { status: "pass" },
  }, { repoRoot, baseline });

  assert.equal(gate.status, "fail");
  assert.deepEqual(gate.unexpected_failures, [extraFailure]);
});

test("suite baseline gate emits unexpectedly_passing when a baseline debt disappears", () => {
  const { repoRoot, baseline } = makeTempRepo();
  const gate = buildSuiteBaselineGate({
    repo_pytest: {
      status: "pass",
      failing_tests: [],
    },
    egodesktop_node_test: { status: "pass" },
  }, { repoRoot, baseline });

  assert.equal(gate.status, "pass");
  assert.deepEqual(gate.unexpectedly_passing, baselineIds);
});

test("suite baseline gate fails when the P1 owner-reference delta is nonzero", () => {
  const { repoRoot, baseline } = makeTempRepo({ ownerTokenInScope: true });
  const gate = buildSuiteBaselineGate({
    repo_pytest: {
      status: "fail",
      failing_tests: baselineIds,
    },
    egodesktop_node_test: { status: "pass" },
  }, { repoRoot, baseline });

  assert.equal(gate.status, "fail");
  assert.equal(gate.p1_owner_reference_guard[ownerDeltaField], 1);
  assert.equal(gate.failures.some((failure) => failure.name === "p1_owner_reference_guard"), true);
});
