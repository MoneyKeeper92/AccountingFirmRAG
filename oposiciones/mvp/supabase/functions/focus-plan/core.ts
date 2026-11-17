// Tesón · focus planner core (pure logic, no I/O). Imported by index.ts and by the tests.
// The AI chooses WHICH concepts a student should focus on today and explains why; the app's
// selection rules still decide the actual questions and enforce the safeguards (caps per
// concept and area, coverage). The AI can only name concepts that exist in the catalog.

export interface CatalogConcept {
  id: string; area: string; name: string; arts: string; importance: number; questions: number;
}
export interface Catalog {
  version: string; tema: string; exam: string;
  areas: Record<string, string>;
  concepts: CatalogConcept[];
  misconceptions: { id: string; name: string }[];
}

// The learner state the app syncs to profiles.state (only the fields the planner reads).
export interface ConceptStat { r: number[]; n: number; c: number; last: number; due: number }
export interface LearnerState {
  cs?: Record<string, ConceptStat>;
  mis?: Record<string, { hits: number[]; fixes: number[] }>;
  history?: { ts: number; session?: string; n: number; a: number; f: number; b: number; nota: number }[];
  days?: string[];
  profile?: { exam?: string | null; cuando?: string | null; horas?: string | null } | null;
  studied?: string[] | null;
  exp?: { pre?: { score: number } | null } | null;
}

export interface Summary {
  exam: string | null;
  exam_when: string | null;
  hours_per_week: string | null;
  days_active: number;
  total_answers: number;
  diagnostic_score_10: number | null;
  studied_areas: string[];
  concepts: { id: string; answers: number; recent_answers: number; recent_wrong: number; mastery_pct: number; days_since_last: number; review_due_in_days: number }[];
  unseen_concepts: string[];
  confusions: { id: string; hits_30d: number; fixes_30d: number }[];
  recent_sessions: { days_ago: number; questions: number; mark_10: number }[];
}

export interface PlanFocus { concept: string; weight: 1 | 2 | 3; reason_es: string }
export interface Plan {
  focus: PlanFocus[];
  review: string[];
  session_size: 10 | 15 | 20;
  coach_message_es: string;
}

const DAY = 86400000;

export function mastery(st: ConceptStat | undefined): number | null {
  if (!st || !st.n) return null;
  let w = 1, sw = 0, sr = 0;
  for (let i = st.r.length - 1; i >= 0; i--) { sr += w * st.r[i]; sw += w; w *= 0.75; }
  return (sr + 0.5) / (sw + 1);
}

export function summarize(state: LearnerState, catalog: Catalog, now = Date.now()): Summary {
  const cs = state.cs || {};
  const known = new Set(catalog.concepts.map((c) => c.id));
  const allAreas = Object.keys(catalog.areas);
  const studied = (state.studied && state.studied.length ? state.studied : allAreas).filter((a) => allAreas.includes(a));
  const concepts: Summary["concepts"] = [];
  const unseen: string[] = [];
  let total = 0;
  for (const c of catalog.concepts) {
    const st = cs[c.id];
    const m = mastery(st);
    if (m == null || !st) { unseen.push(c.id); continue; }
    total += st.n;
    concepts.push({
      id: c.id, answers: st.n, mastery_pct: Math.round(m * 100),
      recent_answers: Math.min(5, st.r.length), recent_wrong: st.r.slice(-5).filter((x) => !x).length,
      days_since_last: Math.max(0, Math.round((now - st.last) / DAY)),
      review_due_in_days: Math.round((st.due - now) / DAY),
    });
  }
  const cut = now - 30 * DAY;
  const confusions = Object.entries(state.mis || {})
    .map(([id, m]) => ({ id, hits_30d: (m.hits || []).filter((t) => t > cut).length, fixes_30d: (m.fixes || []).filter((t) => t > cut).length }))
    .filter((x) => x.hits_30d > 0 && catalog.misconceptions.some((m) => m.id === x.id))
    .sort((a, b) => b.hits_30d - a.hits_30d).slice(0, 6);
  const recent = (state.history || []).slice(-5).map((h) => ({
    days_ago: Math.max(0, Math.round((now - h.ts) / DAY)), questions: h.n, mark_10: Math.round(h.nota * 10) / 10,
  }));
  const p = state.profile || {};
  return {
    exam: p.exam ?? null, exam_when: p.cuando ?? null, hours_per_week: p.horas ?? null,
    days_active: (state.days || []).length, total_answers: total,
    diagnostic_score_10: state.exp && state.exp.pre ? Math.round(state.exp.pre.score * 10) / 10 : null,
    studied_areas: studied,
    concepts, unseen_concepts: unseen.filter((id) => known.has(id)), confusions, recent_sessions: recent,
  };
}

// Deterministic plan: importance × weakness, used when the AI is unavailable or data is thin.
export function rulesPlan(sum: Summary, catalog: Catalog): Plan {
  const byId = new Map(catalog.concepts.map((c) => [c.id, c]));
  const studied = new Set(sum.studied_areas);
  const scored = sum.concepts
    .filter((c) => studied.has(byId.get(c.id)!.area) && c.mastery_pct < 70)
    // importance × weakness × evidence (1–2 answers are weak evidence)
    .map((c) => ({ c, score: byId.get(c.id)!.importance * (1 - c.mastery_pct / 100) * Math.min(1, c.answers / 3) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 4);
  const focus: PlanFocus[] = scored.map(({ c }, i) => ({
    concept: c.id,
    weight: (i === 0 ? 3 : i === 1 ? 2 : 1) as 1 | 2 | 3,
    reason_es: reasonFor(c.recent_wrong, c.recent_answers),
  }));
  if (!focus.length) {
    const fresh = sum.unseen_concepts.filter((id) => studied.has(byId.get(id)!.area))
      .sort((a, b) => byId.get(b)!.importance - byId.get(a)!.importance).slice(0, 3);
    fresh.forEach((id, i) => focus.push({ concept: id, weight: (i === 0 ? 2 : 1) as 1 | 2, reason_es: "Aún no lo has practicado y suele ser importante en el examen." }));
  }
  const review = sum.concepts.filter((c) => c.mastery_pct >= 70 && c.review_due_in_days <= 0).map((c) => c.id).slice(0, 6);
  const size: 10 | 15 | 20 = sum.hours_per_week === "Menos de 5" ? 10 : 20;
  return { focus, review, session_size: size, coach_message_es: focus.length ? "Hoy toca reforzar lo que más te está costando." : "Sigue practicando para que podamos afinar tu plan." };
}

export function reasonFor(wrong: number, n: number): string {
  if (n === 1) return wrong ? "Fallaste la única pregunta que has hecho sobre esto." : "Solo has hecho una pregunta sobre esto.";
  return `Has fallado ${wrong} de tus últimas ${n} respuestas sobre esto.`;
}

export function planSchema(catalog: Catalog) {
  const ids = catalog.concepts.map((c) => c.id);
  return {
    type: "object",
    additionalProperties: false,
    required: ["focus", "review", "session_size", "coach_message_es"],
    properties: {
      focus: {
        type: "array",
        description: "2 to 5 concepts to focus on today, most important first.",
        items: {
          type: "object",
          additionalProperties: false,
          required: ["concept", "weight", "reason_es"],
          properties: {
            concept: { type: "string", enum: ids },
            weight: { type: "integer", enum: [1, 2, 3] },
            reason_es: { type: "string", description: "One short sentence in Spanish (tú) citing the student's own numbers." },
          },
        },
      },
      review: { type: "array", description: "0 to 6 concepts to review.", items: { type: "string", enum: ids } },
      session_size: { type: "integer", enum: [10, 15, 20] },
      coach_message_es: { type: "string", description: "At most two short sentences in Spanish (tú)." },
    },
  };
}

export function systemPrompt(catalog: Catalog): string {
  return [
    "You plan today's practice for a student preparing the Spanish civil-service exam " + catalog.exam +
      ", topic " + catalog.tema + ", in a multiple-choice practice app called Tesón.",
    "You receive the concept catalog (with an estimated exam importance from 1 to 3 and how many practice questions exist) and a summary of the student's results. You choose which concepts the student should focus on and which to review. The app then picks the actual questions and enforces its own limits, so you only choose concepts.",
    "How to choose:",
    "- focus: 2 to 5 concepts. Prioritise importance × weakness: low mastery on important concepts first, then recent mistakes and active confusions (a confusion is a typical mix-up, e.g. alarma vs excepción). A mastery figure based on 1-2 answers is weak evidence; prefer concepts with more answers when the choice is close. Give weight 3 to the single most urgent concept, 2 to the next, 1 to the rest.",
    "- Only choose concepts in the student's studied areas. If the student has fewer than 15 answers, include important unseen concepts from studied areas so the app learns their level.",
    "- Do not put every focus concept in one area unless all the weaknesses really are there.",
    "- Skip concepts with 0 practice questions.",
    "- review: up to 6 concepts with mastery of 70% or more whose review is due (review_due_in_days <= 0) or that are important and were not seen for a long time.",
    "- session_size: 10 if the student studies fewer than 5 hours a week or their recent sessions were short, otherwise 15 or 20.",
    "Writing, in Spanish from Spain, addressing the student as tú:",
    "- reason_es: one short sentence per focus concept, with the student's real numbers taken from recent_wrong / recent_answers (e.g. «Has fallado 3 de tus últimas 4 sobre el estado de excepción»). Never invent numbers and never quote mastery_pct, which is an internal estimate.",
    "- coach_message_es: at most two short sentences, warm and concrete, about today's plan. Never promise passing the exam, never compare with other students, no emojis.",
    "",
    "Concept catalog (JSON):",
    JSON.stringify({ areas: catalog.areas, concepts: catalog.concepts, misconceptions: catalog.misconceptions }),
  ].join("\n");
}

function clean(s: unknown, max: number): string {
  return String(s ?? "").replace(/[\u0000-\u001f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
}

// Validates and clamps model output. Returns null when it is unusable.
export function validatePlan(raw: unknown, catalog: Catalog, sum: Summary): Plan | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;
  const byId = new Map(catalog.concepts.map((c) => [c.id, c]));
  const studied = new Set(sum.studied_areas);
  const seen = new Set<string>();
  const focus: PlanFocus[] = [];
  for (const f of Array.isArray(r.focus) ? r.focus : []) {
    const fo = f as Record<string, unknown>;
    const id = String(fo.concept);
    const c = byId.get(id);
    if (!c || seen.has(id) || !c.questions || !studied.has(c.area)) continue;
    const w = Number(fo.weight);
    seen.add(id);
    focus.push({ concept: id, weight: (w === 3 || w === 2 ? w : 1) as 1 | 2 | 3, reason_es: clean(fo.reason_es, 200) });
    if (focus.length === 5) break;
  }
  if (!focus.length) return null;
  const review = (Array.isArray(r.review) ? r.review : []).map(String)
    .filter((id) => byId.has(id) && !seen.has(id)).filter((id, i, a) => a.indexOf(id) === i).slice(0, 6);
  const size = Number(r.session_size);
  return {
    focus, review,
    session_size: (size === 10 || size === 15 ? size : 20) as 10 | 15 | 20,
    coach_message_es: clean(r.coach_message_es, 300),
  };
}
