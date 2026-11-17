"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(root, "questions.js"), "utf8"), context);

const bank = context.window.TESON_BANK;
const review = JSON.parse(fs.readFileSync(path.join(root, "review.json"), "utf8"));
assert(bank, "TESON_BANK must be defined");
assert.equal(bank.questions.length, 82, "Expected the reviewed beta scope of 82 questions");
assert.match(bank.version, /^\d{4}-\d{2}-\d{2}\.\d+$/);
assert.match(bank.contentAsOf, /^\d{4}-\d{2}-\d{2}$/);
assert.equal(review.bankVersion, bank.version, "review.json must target the current bank version");

const ids = new Set();
const stems = new Set();
bank.questions.forEach((q, index) => {
  const expectedId = `CE-${String(index + 1).padStart(3, "0")}`;
  assert.equal(q.id, expectedId, `Question ${index + 1} must keep a contiguous ID`);
  assert(!ids.has(q.id), `Duplicate ID: ${q.id}`);
  assert(!stems.has(q.q), `Duplicate stem: ${q.id}`);
  ids.add(q.id);
  stems.add(q.q);

  assert.equal(q.tema, "CE1", `${q.id}: unexpected tema`);
  assert(bank.subs[q.sub], `${q.id}: unknown subtopic`);
  assert.equal(q.o.length, 4, `${q.id}: exactly four options required`);
  assert(Number.isInteger(q.k) && q.k >= 0 && q.k < 4, `${q.id}: invalid key`);
  assert.equal(q.w.length, 4, `${q.id}: four option explanations required`);
  q.w.forEach((reason, optionIndex) => {
    if (optionIndex === q.k) assert.equal(reason, null, `${q.id}: correct option reason must be null`);
    else assert.equal(typeof reason, "string", `${q.id}: missing wrong-option explanation`);
  });
  ["q", "ex", "art", "sourceType", "sourceId", "sourceUrl", "sourceRef", "contentAsOf", "reviewStatus", "url"].forEach((field) => {
    assert(String(q[field] || "").trim(), `${q.id}: missing ${field}`);
  });
  assert.equal(q.sourceType, "teson_original_from_legislation", `${q.id}: source type`);
  assert.equal(q.sourceId, "BOE-A-1978-31229", `${q.id}: source id`);
  assert.equal(q.contentAsOf, bank.contentAsOf, `${q.id}: stale content date`);
  assert.match(q.url, /^https:\/\/www\.boe\.es\/buscar\/act\.php\?id=BOE-A-1978-31229(?:#(?:a\d+|df))?$/, `${q.id}: invalid BOE URL`);
  assert(["pending_human", "approved"].includes(q.reviewStatus), `${q.id}: invalid review status`);
  assert(["pending", "approved"].includes(review.items[q.id]), `${q.id}: missing review ledger entry`);
});

assert.deepEqual(Object.keys(review.items).sort(), [...ids].sort(), "Review ledger IDs must exactly match the bank");
console.log(`Bank validation passed: ${bank.questions.length} questions, ${ids.size} unique IDs.`);
