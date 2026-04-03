import fs from "node:fs";

export function loadEnvFile(path) {
  const env = {};
  if (!path || !fs.existsSync(path)) {
    return env;
  }

  const content = fs.readFileSync(path, "utf8");
  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const idx = line.indexOf("=");
    if (idx <= 0) continue;
    const key = line.slice(0, idx).trim();
    let val = line.slice(idx + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    env[key] = val;
  }

  return env;
}

export function mergedEnv(filePath) {
  const fileEnv = loadEnvFile(filePath);
  return { ...fileEnv, ...process.env };
}
