// Tesón · delete-account Edge Function (Supabase, Deno)
// POST /functions/v1/delete-account (Authorization: Bearer <student's session JWT>)
// Deletes the student's login (email), their synced progress (profiles cascades), their plans
// (cascade) and their analytics events. Used by "Borrar mi cuenta" in the app (RGPD art. 17).

import { createClient } from "npm:@supabase/supabase-js@2.119.0";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false, autoRefreshToken: false },
});
const headers = {
  "Access-Control-Allow-Origin": Deno.env.get("TESON_ALLOWED_ORIGINS")?.split(",")[0]?.trim() || "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers });
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "method_not_allowed" }), { status: 405, headers });
  const jwt = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  const { data } = await admin.auth.getUser(jwt);
  const user = data?.user;
  if (!user) return new Response(JSON.stringify({ error: "unauthorized" }), { status: 401, headers });

  await admin.from("events").delete().eq("uid", user.id);
  const { error } = await admin.auth.admin.deleteUser(user.id);
  if (error) return new Response(JSON.stringify({ error: "delete_failed" }), { status: 500, headers });
  return new Response(JSON.stringify({ deleted: true }), { status: 200, headers: { ...headers, "Content-Type": "application/json" } });
});
