// Tesón · focus-plan Edge Function (Supabase, Deno)
//
// POST /functions/v1/focus-plan   (Authorization: Bearer <student's session JWT>)
// Reads the signed-in student's synced learning state from public.profiles, summarises it
// (no email, no free text), asks Claude which concepts to focus on today, validates the answer
// against the catalog, stores it, and returns it. Falls back to deterministic rules when the AI
// is unavailable, refuses, returns something unusable, or a cost cap is reached.
//
// Secrets: ANTHROPIC_API_KEY (supabase secrets set ...). SUPABASE_URL and
// SUPABASE_SERVICE_ROLE_KEY are provided by Supabase automatically.
// Optional env: TESON_PLAN_MODEL (default claude-opus-5-5), TESON_PLAN_EFFORT (default medium),
// TESON_PLANS_PER_USER_DAY (default 3), TESON_PLANS_PER_DAY (default 300),
// TESON_ALLOWED_ORIGINS (comma-separated; default *).

import Anthropic from "npm:@anthropic-ai/sdk@1.9.0";
import { createClient } from "npm:@supabase/supabase-js@2.119.0";
import catalogJson from "./catalog.json" with { type: "json" };
import { type Catalog, type LearnerState, type Plan, planSchema, rulesPlan, summarize, systemPrompt, validatePlan } from "./core.ts";

const catalog = catalogJson as Catalog;
const MODEL = Deno.env.get("TESON_PLAN_MODEL") || "claude-opus-5-5";
const EFFORT = (Deno.env.get("TESON_PLAN_EFFORT") || "medium") as "low" | "medium" | "high";
const PER_USER_DAY = Number(Deno.env.get("TESON_PLANS_PER_USER_DAY") || 3);
const PER_DAY = Number(Deno.env.get("TESON_PLANS_PER_DAY") || 300);
const ORIGINS = (Deno.env.get("TESON_ALLOWED_ORIGINS") || "*").split(",").map((s) => s.trim());
const SYSTEM = systemPrompt(catalog);
const SCHEMA = planSchema(catalog);

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false, autoRefreshToken: false },
});
const anthropic = Deno.env.get("ANTHROPIC_API_KEY") ? new Anthropic() : null;

function cors(req: Request): Record<string, string> {
  const origin = req.headers.get("origin") || "";
  const allow = ORIGINS.includes("*") ? "*" : ORIGINS.includes(origin) ? origin : ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}
function json(req: Request, body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { ...cors(req), "Content-Type": "application/json" } });
}

async function askClaude(summary: ReturnType<typeof summarize>): Promise<{ plan: Plan | null; usage?: { input_tokens: number; output_tokens: number }; error?: string }> {
  if (!anthropic) return { plan: null, error: "no_api_key" };
  try {
    const response = await anthropic.beta.messages.create({
      model: MODEL,
      max_tokens: 16000,
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      system: [{ type: "text", text: SYSTEM, cache_control: { type: "ephemeral" } }],
      output_config: { effort: EFFORT, format: { type: "json_schema", schema: SCHEMA } },
      messages: [{ role: "user", content: "Student summary (JSON):\n" + JSON.stringify(summary) }],
    });
    const usage = { input_tokens: response.usage.input_tokens, output_tokens: response.usage.output_tokens };
    if (response.stop_reason === "refusal") return { plan: null, usage, error: "refusal" };
    if (response.stop_reason === "max_tokens") return { plan: null, usage, error: "max_tokens" };
    let text = "";
    for (const block of response.content) if (block.type === "text") text += block.text;
    let parsed: unknown;
    try { parsed = JSON.parse(text); } catch { return { plan: null, usage, error: "invalid_json" }; }
    const plan = validatePlan(parsed, catalog, summary);
    return plan ? { plan, usage } : { plan: null, usage, error: "invalid_plan" };
  } catch (e) {
    if (e instanceof Anthropic.RateLimitError) return { plan: null, error: "rate_limited" };
    if (e instanceof Anthropic.APIError) return { plan: null, error: "api_" + e.status };
    return { plan: null, error: "network" };
  }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors(req) });
  if (req.method !== "POST") return json(req, { error: "method_not_allowed" }, 405);

  const jwt = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  const { data: auth } = await admin.auth.getUser(jwt);
  const user = auth?.user;
  if (!user) return json(req, { error: "unauthorized" }, 401);

  const { data: profile } = await admin.from("profiles").select("state, plan, plan_at").eq("id", user.id).maybeSingle();
  const state = (profile?.state || {}) as LearnerState;
  const summary = summarize(state, catalog);

  // Cost guards: per student per day, and a global daily cap.
  const since = new Date(Date.now() - 86400000).toISOString();
  const { count: mine } = await admin.from("plans").select("id", { count: "exact", head: true }).eq("user_id", user.id).gte("created_at", since);
  if ((mine || 0) >= PER_USER_DAY && profile?.plan) return json(req, { plan: profile.plan, cached: true });
  const { count: all } = await admin.from("plans").select("id", { count: "exact", head: true }).eq("source", "ai").gte("created_at", since);

  const started = Date.now();
  let plan: Plan, source: "ai" | "rules", error: string | null = null, usage: { input_tokens: number; output_tokens: number } | undefined;
  if (summary.total_answers < 10) {
    plan = rulesPlan(summary, catalog); source = "rules"; error = "too_little_data";
  } else if ((all || 0) >= PER_DAY) {
    plan = rulesPlan(summary, catalog); source = "rules"; error = "daily_cap";
  } else {
    const r = await askClaude(summary);
    usage = r.usage;
    if (r.plan) { plan = r.plan; source = "ai"; } else { plan = rulesPlan(summary, catalog); source = "rules"; error = r.error || "unknown"; }
  }
  const stored = { ...plan, source, model: source === "ai" ? MODEL : null, created_at: new Date().toISOString(), catalog_version: catalog.version };

  await admin.from("plans").insert({
    user_id: user.id, source, model: source === "ai" ? MODEL : null, plan: stored, summary,
    input_tokens: usage?.input_tokens ?? null, output_tokens: usage?.output_tokens ?? null,
    latency_ms: Date.now() - started, error,
  });
  await admin.from("profiles").update({ plan: stored, plan_at: stored.created_at }).eq("id", user.id);
  return json(req, { plan: stored, cached: false });
});
