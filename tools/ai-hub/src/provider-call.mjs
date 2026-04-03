import path from "node:path";
import { fileURLToPath } from "node:url";
import OpenAI from "openai";
import Anthropic from "@anthropic-ai/sdk";
import { GoogleGenerativeAI } from "@google/generative-ai";
import Groq from "groq-sdk";
import { InferenceClient } from "@huggingface/inference";
import { mergedEnv } from "./env.mjs";

function getArg(name, fallback = "") {
  const idx = process.argv.indexOf(name);
  if (idx >= 0 && idx + 1 < process.argv.length) return process.argv[idx + 1];
  return fallback;
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const baseDir = path.resolve(__dirname, "../../..");
const envPath = getArg("--env", path.join(baseDir, "config", "ai-providers.env"));
const provider = getArg("--provider", "").toLowerCase();
const prompt = getArg("--prompt", "Hello from iac-platform");
const dryRunArg = getArg("--dry-run", "true").toLowerCase();
const dryRun = dryRunArg !== "false";

if (!provider) {
  console.error("Usage: npm run call -- --provider <openai|claude|gemini|groq|openrouter|huggingface> --prompt \"...\" [--dry-run true|false]");
  process.exit(1);
}

const env = mergedEnv(envPath);

const out = (k, v) => console.log(`${k}=${v}`);
out("AI_HUB_PROVIDER", provider);
out("AI_HUB_DRY_RUN", String(dryRun));
out("AI_HUB_ENV_PATH", envPath);

if (dryRun) {
  out("AI_HUB_STATUS", "SIMULATED");
  out("AI_HUB_PROMPT_PREVIEW", prompt.slice(0, 240));
  process.exit(0);
}

async function callProvider() {
  if (provider === "openai") {
    const key = env.AI_PROVIDER_OPENAI_API_KEY;
    if (!key) throw new Error("Missing AI_PROVIDER_OPENAI_API_KEY");
    const model = env.AI_PROVIDER_OPENAI_MODEL_FAST || "gpt-4o-mini";
    const client = new OpenAI({ apiKey: key });
    const res = await client.responses.create({ model, input: prompt });
    return { model, text: res.output_text ?? "" };
  }

  if (provider === "claude") {
    const key = env.AI_PROVIDER_CLAUDE_API_KEY;
    if (!key) throw new Error("Missing AI_PROVIDER_CLAUDE_API_KEY");
    const model = env.AI_PROVIDER_CLAUDE_MODEL_FAST || "claude-3-5-haiku-latest";
    const client = new Anthropic({ apiKey: key });
    const res = await client.messages.create({
      model,
      max_tokens: 512,
      messages: [{ role: "user", content: prompt }]
    });
    const text = (res.content || []).map((c) => (c.type === "text" ? c.text : "")).join("\n");
    return { model, text };
  }

  if (provider === "gemini") {
    const key = env.AI_PROVIDER_GEMINI_API_KEY;
    if (!key) throw new Error("Missing AI_PROVIDER_GEMINI_API_KEY");
    const model = env.AI_PROVIDER_GEMINI_MODEL_FAST || "gemini-2.0-flash";
    const client = new GoogleGenerativeAI(key);
    const genModel = client.getGenerativeModel({ model });
    const res = await genModel.generateContent(prompt);
    const text = res.response.text();
    return { model, text: text ?? "" };
  }

  if (provider === "groq") {
    const key = env.AI_PROVIDER_GROQ_API_KEY;
    if (!key) throw new Error("Missing AI_PROVIDER_GROQ_API_KEY");
    const model = env.AI_PROVIDER_GROQ_MODEL_FAST || "llama-3.1-8b-instant";
    const client = new Groq({ apiKey: key });
    const res = await client.chat.completions.create({
      model,
      messages: [{ role: "user", content: prompt }]
    });
    const text = res.choices?.[0]?.message?.content ?? "";
    return { model, text };
  }

  if (provider === "openrouter") {
    const key = env.AI_PROVIDER_OPENROUTER_API_KEY;
    if (!key) throw new Error("Missing AI_PROVIDER_OPENROUTER_API_KEY");
    const model = env.AI_PROVIDER_OPENROUTER_MODEL_FAST || "meta-llama/llama-3.1-8b-instruct:free";
    const client = new OpenAI({
      apiKey: key,
      baseURL: "https://openrouter.ai/api/v1"
    });
    const res = await client.chat.completions.create({
      model,
      messages: [{ role: "user", content: prompt }]
    });
    const text = res.choices?.[0]?.message?.content ?? "";
    return { model, text };
  }

  if (provider === "huggingface") {
    const key = env.AI_PROVIDER_HF_API_KEY;
    if (!key) throw new Error("Missing AI_PROVIDER_HF_API_KEY");
    const model = env.AI_PROVIDER_HF_MODEL_FAST || "Qwen/Qwen2.5-7B-Instruct";
    const client = new InferenceClient(key);
    const res = await client.chatCompletion({
      model,
      messages: [{ role: "user", content: prompt }],
      max_tokens: 512
    });
    const text = res.choices?.[0]?.message?.content ?? "";
    return { model, text };
  }

  throw new Error(`Unsupported provider: ${provider}`);
}

try {
  const result = await callProvider();
  out("AI_HUB_STATUS", "OK");
  out("AI_HUB_MODEL", result.model);
  out("AI_HUB_RESPONSE", (result.text || "").replace(/\s+/g, " ").trim().slice(0, 1000));
} catch (err) {
  out("AI_HUB_STATUS", "ERROR");
  out("AI_HUB_ERROR", err instanceof Error ? err.message : String(err));
  process.exit(2);
}
