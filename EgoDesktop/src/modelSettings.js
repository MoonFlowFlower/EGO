const fs = require("node:fs");
const path = require("node:path");

function listExpressionFiles(modelDir) {
  if (!modelDir) {
    return [];
  }
  const expDir = path.join(modelDir, "exp");
  if (!fs.existsSync(expDir) || !fs.statSync(expDir).isDirectory()) {
    return [];
  }
  return fs.readdirSync(expDir)
    .filter((name) => name.toLowerCase().endsWith(".exp3.json"))
    .sort((left, right) => left.localeCompare(right, "zh-Hans-CN"))
    .map((name) => ({
      Name: name.replace(/\.exp3\.json$/i, ""),
      File: `exp/${name}`,
    }));
}

function mergeExpressionDefinitions(existing, discovered) {
  const merged = [];
  const seen = new Set();
  for (const item of Array.isArray(existing) ? existing : []) {
    if (!item || typeof item !== "object" || !item.Name || !item.File) {
      continue;
    }
    merged.push(item);
    seen.add(String(item.Name));
  }
  for (const item of discovered) {
    if (!seen.has(String(item.Name))) {
      merged.push(item);
      seen.add(String(item.Name));
    }
  }
  return merged;
}

function normalizeModelSettingsJson(rawJson, options = {}) {
  const settings = JSON.parse(rawJson);
  if (!settings || typeof settings !== "object" || Array.isArray(settings)) {
    throw new Error("model settings json must be an object");
  }
  if (!settings.FileReferences || typeof settings.FileReferences !== "object") {
    settings.FileReferences = {};
  }
  if (!Array.isArray(settings.HitAreas)) {
    settings.HitAreas = [];
  }
  if (!Array.isArray(settings.Groups)) {
    settings.Groups = [];
  }
  const discoveredExpressions = listExpressionFiles(options.modelDir);
  const expressions = mergeExpressionDefinitions(settings.FileReferences.Expressions, discoveredExpressions);
  if (expressions.length > 0) {
    settings.FileReferences.Expressions = expressions;
  }
  return settings;
}

module.exports = {
  listExpressionFiles,
  normalizeModelSettingsJson,
};
