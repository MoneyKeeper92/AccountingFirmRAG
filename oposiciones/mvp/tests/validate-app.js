"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const app = fs.readFileSync(path.join(root, "app.js"), "utf8");
const index = fs.readFileSync(path.join(root, "index.html"), "utf8");
const privacy = fs.readFileSync(path.join(root, "privacidad.html"), "utf8");
const legal = fs.readFileSync(path.join(root, "aviso-legal.html"), "utf8");
const schema = fs.readFileSync(path.join(root, "schema.sql"), "utf8");
const netlify = fs.readFileSync(path.resolve(root, "..", "..", "netlify.toml"), "utf8");

assert(!index.includes("fonts.googleapis.com"), "Private beta must not load Google Fonts");
assert(index.includes('content="noindex,nofollow"'), "Private beta must be noindex");
assert(!app.includes("submitted: true"), "Legacy consent bypass must not return");
assert(app.includes('ESSENTIAL_TYPES = ["question_reported", "feedback_sent"]'), "Essential event allowlist changed unexpectedly");
assert(app.includes('S.queue.filter(function (event) { return event.basis === "user_request"; })'), "Consent withdrawal must clear queued analytics");
assert(app.includes("flushController.abort()"), "Consent withdrawal must abort an in-flight flush");
assert(app.includes("flushGeneration++"), "Consent withdrawal must invalidate an in-flight flush");
assert(app.includes("if (generation !== flushGeneration) return;"), "A stale flush must not mutate the post-withdrawal queue");
assert(app.includes("if (S.queue.length) flushTimer = setTimeout(flush, 0);"), "Preserved user-request events must be retried after withdrawal");
assert(app.includes("bank_version: BANK.version"), "Events must identify the question-bank version");
assert(privacy.includes("data-legal-gate") && legal.includes("data-legal-gate"), "Legal pages must fail closed");
assert(!privacy.includes("<mark>") && !legal.includes("<mark>"), "Placeholder legal text must not be publishable");
assert(schema.includes("type in ("), "Database event types must be allowlisted");
assert(schema.includes("security_invoker = true"), "Review views must use caller permissions");
assert(schema.includes("basis = 'user_request'"), "Database must separate consent and requested submissions");
assert(netlify.includes('command = "npm run check:production"'), "Netlify deploys must run the production gate");
assert(netlify.includes("Content-Security-Policy"), "Netlify security headers are required");

console.log("App privacy and release-gate validation passed.");
