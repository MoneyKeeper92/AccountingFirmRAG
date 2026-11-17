// Post-build checks for the Tesón website. Fails the Netlify build on any problem.
import { readFileSync, readdirSync, statSync, existsSync } from "node:fs";
import { join, relative } from "node:path";

const dist = new URL("../dist/", import.meta.url).pathname;
const errors = [];
const html = [];
(function walk(dir) {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (p.endsWith(".html")) html.push(p);
  }
})(dist);

const robots = readFileSync(join(dist, "robots.txt"), "utf8");
const indexable = !robots.includes("Disallow: /\n");

for (const file of html) {
  const rel = "/" + relative(dist, file);
  const s = readFileSync(file, "utf8");
  if (!/<html lang="es">/.test(s)) errors.push(`${rel}: missing lang="es"`);
  const title = s.match(/<title>([^<]*)<\/title>/)?.[1] ?? "";
  if (title.length < 5 || title.length > 90) errors.push(`${rel}: title length ${title.length}`);
  if (!/<meta name="description" content="[^"]{50,}"/.test(s)) errors.push(`${rel}: description missing or short`);
  if (/fonts\.googleapis|fonts\.gstatic|googletagmanager|google-analytics/.test(s)) errors.push(`${rel}: third-party request (privacy: no cookies/analytics promised)`);
  if (!indexable && !s.includes('content="noindex,nofollow"')) errors.push(`${rel}: pre-launch page is indexable`);
  for (const [, href] of s.matchAll(/href="(\/[^"#?]*)/g)) {
    if (href.startsWith("//")) continue;
    const target = join(dist, href);
    const ok = existsSync(target) && (statSync(target).isFile() || existsSync(join(target, "index.html")));
    if (!ok) errors.push(`${rel}: broken internal link ${href}`);
  }
}

if (errors.length) {
  console.error("Site check FAILED:\n- " + errors.join("\n- "));
  process.exit(1);
}
console.log(`Site check passed: ${html.length} pages. ${indexable ? "PUBLIC (indexable)" : "PRE-LAUNCH: noindex + robots Disallow until legal details are filled in src/site.ts"}`);
