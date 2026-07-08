const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const DEFAULT_SUITE_BASELINE_PATH = "artifacts/egodesktop_pet_world_integration_001a/p1/suite_baseline.json";
const OWNER_TOKEN = ["Ego", "Operator"].join("");
const FIELD_REF_SCOPE = ["p1_ego", "operator_ref_scope"].join("");
const FIELD_REF_DELTA_SCOPE = ["p1_ego", "operator_ref_delta_scope"].join("");
const FIELD_REF_BASELINE_COUNT = ["p1_ego", "operator_ref_count_in_p1_changed_files"].join("");
const FIELD_REF_DELTA = ["p1_ego", "operator_ref_delta"].join("");
const REASON_REF_DELTA_NONZERO = ["p1_ego", "operator_ref_delta_nonzero"].join("");

function sha256Text(text) {
  return crypto.createHash("sha256").update(text).digest("hex");
}

function readSuiteBaseline(repoRoot, relativePath = DEFAULT_SUITE_BASELINE_PATH) {
  const baselinePath = path.join(repoRoot, relativePath);
  if (!fs.existsSync(baselinePath)) {
    return {
      status: "unavailable",
      reason: "suite_baseline_json_missing",
      path: relativePath,
      absolute_path: baselinePath,
    };
  }
  const text = fs.readFileSync(baselinePath, "utf8");
  return {
    status: "pass",
    path: relativePath,
    absolute_path: baselinePath,
    sha256: sha256Text(text),
    baseline: JSON.parse(text),
  };
}

function baselineFailureIds(baseline) {
  return (baseline && Array.isArray(baseline.pre_existing_failures) ? baseline.pre_existing_failures : [])
    .map((entry) => String(entry.node_id || "").trim())
    .filter(Boolean);
}

function normalizeFailingTests(repoPytestResult = {}) {
  if (Array.isArray(repoPytestResult.failing_tests)) {
    return repoPytestResult.failing_tests.map((item) => String(item).trim()).filter(Boolean);
  }
  const status = String(repoPytestResult.status || "").toLowerCase();
  if (["fail", "failed", "timeout", "error"].includes(status)) {
    return ["__repo_pytest_failure_ids_unavailable__"];
  }
  return [];
}

function refScopeFiles(baseline) {
  const scope = (baseline && baseline[FIELD_REF_DELTA_SCOPE]) || (baseline && baseline[FIELD_REF_SCOPE]) || {};
  const files = Array.isArray(scope.files)
    ? scope.files
    : [];
  return files.map((item) => String(item).trim()).filter(Boolean);
}

function collectP1OwnerRefReport({ repoRoot, baseline }) {
  const files = refScopeFiles(baseline);
  const hits = [];
  for (const relativePath of files) {
    const filePath = path.join(repoRoot, relativePath);
    if (!fs.existsSync(filePath)) {
      continue;
    }
    const text = fs.readFileSync(filePath, "utf8");
    text.split(/\r?\n/).forEach((line, index) => {
      if (line.includes(OWNER_TOKEN)) {
        hits.push({
          file: relativePath,
          line: index + 1,
          excerpt: line.trim(),
        });
      }
    });
  }
  const deltaScope = (baseline && baseline[FIELD_REF_DELTA_SCOPE]) || {};
  const baselineCount = Number.isFinite(Number(deltaScope.baseline_count))
    ? Number(deltaScope.baseline_count)
    : (Number(baseline && baseline[FIELD_REF_BASELINE_COUNT]) || 0);
  return {
    producer_function: "collectP1OwnerRefReport",
    rule: "count runtime-owner token references in closed P1 pet source/test scope and require delta from baseline to remain zero",
    token_literal: "split_runtime_owner_token",
    scope_files: files,
    baseline_count: baselineCount,
    current_count: hits.length,
    [FIELD_REF_DELTA]: hits.length - baselineCount,
    hits,
  };
}

function isFailStatus(status) {
  return ["fail", "failed", "timeout", "error"].includes(String(status || "").toLowerCase());
}

function isPendingStatus(status) {
  return String(status || "").toLowerCase().includes("pending");
}

function buildSuiteBaselineGate(suiteResults = {}, {
  repoRoot = path.resolve(__dirname, "..", ".."),
  baseline,
  baselineRelativePath = DEFAULT_SUITE_BASELINE_PATH,
} = {}) {
  const entries = Object.entries(suiteResults || {});
  if (!entries.length) {
    return { status: "pending", reason: "suite_results_not_supplied", results: suiteResults };
  }

  const loaded = baseline
    ? { status: "pass", path: baselineRelativePath, sha256: sha256Text(JSON.stringify(baseline)), baseline }
    : readSuiteBaseline(repoRoot, baselineRelativePath);
  if (loaded.status !== "pass") {
    return {
      status: "fail",
      reason: loaded.reason,
      baseline_path: loaded.path,
      results: suiteResults,
    };
  }

  const baselineIds = baselineFailureIds(loaded.baseline);
  const baselineIdSet = new Set(baselineIds);
  const repoPytest = suiteResults.repo_pytest || {};
  const currentRepoFailures = normalizeFailingTests(repoPytest);
  const currentFailureSet = new Set(currentRepoFailures);
  const unexpectedFailures = currentRepoFailures.filter((id) => !baselineIdSet.has(id));
  const unexpectedlyPassing = baselineIds.filter((id) => !currentFailureSet.has(id));
  const unknownFailureIds = currentRepoFailures.includes("__repo_pytest_failure_ids_unavailable__");
  const ownerRefReport = collectP1OwnerRefReport({ repoRoot, baseline: loaded.baseline });
  const nonRepoFailures = entries
    .filter(([name, result]) => name !== "repo_pytest" && isFailStatus(result && result.status))
    .map(([name, result]) => ({ name, ...result }));
  const pending = entries
    .filter(([, result]) => isPendingStatus(result && result.status))
    .map(([name, result]) => ({ name, ...result }));
  const status = (
    unexpectedFailures.length === 0
    && !unknownFailureIds
    && ownerRefReport[FIELD_REF_DELTA] === 0
    && nonRepoFailures.length === 0
  ) ? (pending.length ? "pending" : "pass") : "fail";

  return {
    status,
    rule: "suite green iff current repo_pytest failures are a subset of the closed baseline and P1 owner-reference delta is zero",
    baseline_path: loaded.path,
    baseline_sha256: loaded.sha256,
    baseline_commit: loaded.baseline.baseline_commit,
    baseline_failure_ids: baselineIds,
    repo_pytest_current_failing_tests: currentRepoFailures,
    unexpected_failures: unexpectedFailures,
    unexpectedly_passing: unexpectedlyPassing,
    p1_owner_reference_guard: ownerRefReport,
    failures: [
      ...nonRepoFailures,
      ...unexpectedFailures.map((id) => ({ name: "repo_pytest", failing_test: id, reason: "outside_closed_suite_baseline" })),
      ...(ownerRefReport[FIELD_REF_DELTA] === 0 ? [] : [{
        name: "p1_owner_reference_guard",
        reason: REASON_REF_DELTA_NONZERO,
        [FIELD_REF_DELTA]: ownerRefReport[FIELD_REF_DELTA],
        hits: ownerRefReport.hits,
      }]),
    ],
    pending,
    results: suiteResults,
  };
}

module.exports = {
  DEFAULT_SUITE_BASELINE_PATH,
  buildSuiteBaselineGate,
  collectP1OwnerRefReport,
  readSuiteBaseline,
};
