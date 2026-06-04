function parseArgs(argv) {
  const parsed = {};
  const args = Array.from(argv || []);
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (!arg.startsWith("--")) {
      continue;
    }
    const key = arg.slice(2);
    if (key === "smoke") {
      parsed.smoke = true;
      continue;
    }
    const next = args[index + 1];
    if (typeof next === "string" && !next.startsWith("--")) {
      parsed[key] = next;
      index += 1;
    } else {
      parsed[key] = true;
    }
  }
  return parsed;
}

module.exports = { parseArgs };
