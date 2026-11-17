// Exports the concept catalog the AI planner needs (from mvp/questions.js + mvp/tags.js)
// to mvp/supabase/functions/focus-plan/catalog.json. Run after editing tags or questions:
//   node tools/export_catalog.cjs
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const mvp = path.join(__dirname, "..", "mvp");
const ctx = { window: {} };
vm.createContext(ctx);
for (const f of ["questions.js", "tags.js"]) vm.runInContext(fs.readFileSync(path.join(mvp, f), "utf8"), ctx);
const B = ctx.window.TESON_BANK;
const counts = {};
B.questions.forEach((q) => q.concepts.forEach((c) => { counts[c] = (counts[c] || 0) + 1; }));
const catalog = {
  version: B.version,
  tema: "Constitución Española (I)",
  exam: "Auxiliar Administrativo del Estado (C2)",
  areas: B.areas,
  concepts: Object.keys(B.concepts).map((id) => ({
    id, area: B.concepts[id].area, name: B.concepts[id].name, arts: B.concepts[id].arts,
    importance: B.concepts[id].imp, questions: counts[id] || 0,
  })),
  misconceptions: Object.keys(B.misconceptions).map((id) => ({ id, name: B.misconceptions[id].name })),
};
const out = path.join(mvp, "supabase", "functions", "focus-plan", "catalog.json");
fs.writeFileSync(out, JSON.stringify(catalog, null, 2) + "\n");
console.log("wrote", out, catalog.concepts.length, "concepts");
