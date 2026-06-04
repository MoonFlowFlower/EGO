const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  resolveModelInput,
  resolveModelRequestPath,
} = require("../src/modelResolver");
const { normalizeModelSettingsJson } = require("../src/modelSettings");

function createModelFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "ego-live2d-悠小喵-"));
  const modelDir = path.join(root, "悠小喵");
  fs.mkdirSync(modelDir, { recursive: true });
  fs.mkdirSync(path.join(modelDir, "exp"), { recursive: true });
  const modelFile = path.join(modelDir, "悠小喵.model3.json");
  fs.writeFileSync(modelFile, JSON.stringify({ Version: 3, FileReferences: {} }), "utf8");
  fs.writeFileSync(path.join(modelDir, "exp", "水印开关.exp3.json"), JSON.stringify({
    Type: "Live2D Expression",
    Parameters: [{ Id: "Param85", Value: 1, Blend: "Add" }],
  }), "utf8");
  fs.writeFileSync(path.join(modelDir, "exp", "哭哭.exp3.json"), JSON.stringify({
    Type: "Live2D Expression",
    Parameters: [{ Id: "Param113", Value: 1, Blend: "Add" }],
  }), "utf8");
  fs.writeFileSync(path.join(modelDir, "texture_00.png"), "png");
  return { root, modelDir, modelFile };
}

test("resolves either a model3 json file or its containing directory", () => {
  const fixture = createModelFixture();

  const fromFile = resolveModelInput(fixture.modelFile);
  const fromDir = resolveModelInput(fixture.modelDir);

  assert.equal(fromFile.modelFile, fixture.modelFile);
  assert.equal(fromFile.modelDir, fixture.modelDir);
  assert.equal(fromFile.modelFileName, "悠小喵.model3.json");
  assert.deepEqual(fromDir, fromFile);
});

test("decodes Chinese model URLs while staying inside the selected model directory", () => {
  const fixture = createModelFixture();
  const resolved = resolveModelInput(fixture.modelFile);

  const target = resolveModelRequestPath(resolved, "/model/" + encodeURIComponent("悠小喵.model3.json"));

  assert.equal(target, fixture.modelFile);
});

test("rejects model request traversal outside the selected directory", () => {
  const fixture = createModelFixture();
  const resolved = resolveModelInput(fixture.modelFile);

  assert.throws(
    () => resolveModelRequestPath(resolved, "/model/../secret.txt"),
    /outside selected model directory/
  );
});

test("normalizes model3 settings that omit HitAreas", () => {
  const normalized = normalizeModelSettingsJson(JSON.stringify({
    Version: 3,
    FileReferences: {},
  }));

  assert.deepEqual(normalized.HitAreas, []);
});

test("injects exp directory expressions into model3 settings without editing model assets", () => {
  const fixture = createModelFixture();

  const normalized = normalizeModelSettingsJson(
    fs.readFileSync(fixture.modelFile, "utf8"),
    { modelDir: fixture.modelDir }
  );

  assert.deepEqual(normalized.FileReferences.Expressions, [
    { Name: "哭哭", File: "exp/哭哭.exp3.json" },
    { Name: "水印开关", File: "exp/水印开关.exp3.json" },
  ]);
});
