"use strict";

const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(root, "config.js"), "utf8"), context);
vm.runInNewContext(fs.readFileSync(path.join(root, "questions.js"), "utf8"), context);
vm.runInNewContext(fs.readFileSync(path.join(root, "oficiales.js"), "utf8"), context);

const cfg = context.window.TESON_CONFIG;
const bank = context.window.TESON_BANK;
const review = JSON.parse(fs.readFileSync(path.join(root, "review.json"), "utf8"));
const requiredLegal = ["updated", "controllerName", "taxId", "address", "processors"];
const errors = [];
function requireGate(condition, message) {
  if (!condition) errors.push(message);
}

requireGate(/^https:\/\/[a-z0-9-]+\.supabase\.co$/i.test(cfg.supabaseUrl || ""), "Set the production Supabase URL");
requireGate(String(cfg.supabaseAnonKey || "").length > 20, "Set the public Supabase anon/publishable key");
requireGate(!String(cfg.supabaseAnonKey).toLowerCase().includes("service_role"), "Never expose a service-role key");
requireGate(/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(cfg.contactEmail || ""), "Set the controller contact email");
requiredLegal.forEach((field) => requireGate(String(cfg.legal && cfg.legal[field] || "").trim(), `Set legal.${field}`));

requireGate(bank.status === "revisado_humano", "Bank must remain blocked until human review is complete");
requireGate(review.reviewer, "Name the human reviewer in review.json");
requireGate(/^\d{4}-\d{2}-\d{2}$/.test(review.completedAt || ""), "Set review completion date");
const pendingQuestions = bank.questions.filter((q) => q.reviewStatus !== "approved");
const pendingLedger = bank.questions.filter((q) => review.items[q.id] !== "approved");
requireGate(!pendingQuestions.length, `${pendingQuestions.length} question(s) are not approved in questions.js`);
requireGate(!pendingLedger.length, `${pendingLedger.length} question(s) are not approved in review.json`);
requireGate(bank.humanReview.reviewer === review.reviewer, "Bank and ledger reviewer must match");
requireGate(bank.humanReview.completedAt === review.completedAt, "Bank and ledger review date must match");

if (errors.length) {
  console.error(`Production release blocked by ${errors.length} gate(s):`);
  errors.forEach((error) => console.error(`- ${error}`));
  process.exit(1);
}

console.log("Production configuration and human-review gates passed.");
