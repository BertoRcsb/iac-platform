import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { mergedEnv } from "./env.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const baseDir = path.resolve(__dirname, "../../..");
const envPath = process.argv.includes("--env")
  ? process.argv[process.argv.indexOf("--env") + 1]
  : path.join(baseDir, "config", "ai-providers.env");

const env = mergedEnv(envPath);

const providers = [
  { name: "ollama", enabled: env.AI_PROVIDER_OLLAMA_ENABLED === "true", key: null },
  { name: "openai", enabled: env.AI_PROVIDER_OPENAI_ENABLED === "true", key: "AI_PROVIDER_OPENAI_API_KEY" },
  { name: "claude", enabled: env.AI_PROVIDER_CLAUDE_ENABLED === "true", key: "AI_PROVIDER_CLAUDE_API_KEY" },
  { name: "gemini", enabled: env.AI_PROVIDER_GEMINI_ENABLED === "true", key: "AI_PROVIDER_GEMINI_API_KEY" },
  { name: "groq", enabled: env.AI_PROVIDER_GROQ_ENABLED === "true", key: "AI_PROVIDER_GROQ_API_KEY" },
  { name: "openrouter", enabled: env.AI_PROVIDER_OPENROUTER_ENABLED === "true", key: "AI_PROVIDER_OPENROUTER_API_KEY" },
  { name: "huggingface", enabled: env.AI_PROVIDER_HF_ENABLED === "true", key: "AI_PROVIDER_HF_API_KEY" }
];

console.log(`AI_HUB_ENV_PATH=${envPath}`);
for (const p of providers) {
  const hasKey = p.key ? Boolean(env[p.key]) : true;
  let status = p.enabled ? (hasKey ? "ready" : "missing_key") : "disabled";
  if (p.name === "ollama" && p.enabled) {
    const found = spawnSync("bash", ["-lc", "command -v ollama >/dev/null 2>&1"]).status === 0;
    if (!found) status = "missing_binary";
  }
  console.log(`PROVIDER_${p.name.toUpperCase()}=${status}`);
}
console.log("AI_HUB_NOTE=Use `npm run call -- --provider <name> --prompt \"...\" --dry-run false` after configuring keys.");
