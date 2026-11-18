"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { spawn } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const chromePath = process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const profile = path.join("/tmp", `teson-e2e-${process.pid}`);

function mime(file) {
  return ({ ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".webmanifest": "application/manifest+json", ".svg": "image/svg+xml" })[path.extname(file)] || "application/octet-stream";
}

function wait(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function getJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`${response.status} ${url}`);
  return response.json();
}

async function main() {
  assert(fs.existsSync(chromePath), `Chrome not found at ${chromePath}; set CHROME_PATH`);
  const server = http.createServer((req, res) => {
    const pathname = new URL(req.url, "http://localhost").pathname;
    const relative = pathname === "/" ? "index.html" : decodeURIComponent(pathname.slice(1));
    const file = path.resolve(root, relative);
    if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404).end("Not found");
      return;
    }
    res.setHeader("Content-Type", mime(file));
    fs.createReadStream(file).pipe(res);
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const appPort = server.address().port;
  const debugPort = 9230 + (process.pid % 300);
  const chrome = spawn(chromePath, [
    "--headless=new", "--disable-gpu", "--no-sandbox",
    `--remote-debugging-port=${debugPort}`, `--user-data-dir=${profile}`, "about:blank"
  ], { stdio: "ignore" });

  let socket;
  try {
    let version;
    for (let attempt = 0; attempt < 50; attempt++) {
      try { version = await getJson(`http://127.0.0.1:${debugPort}/json/version`); break; } catch (_) { await wait(100); }
    }
    assert(version, "Chrome DevTools endpoint did not start");
    const target = await getJson(`http://127.0.0.1:${debugPort}/json/new?http://127.0.0.1:${appPort}/`, { method: "PUT" });
    socket = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      socket.addEventListener("open", resolve, { once: true });
      socket.addEventListener("error", reject, { once: true });
    });

    let nextId = 0;
    const pending = new Map();
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (!message.id || !pending.has(message.id)) return;
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(message.error.message));
      else resolve(message.result);
    });
    function send(method, params = {}) {
      const id = ++nextId;
      socket.send(JSON.stringify({ id, method, params }));
      return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
    }

    await send("Page.enable");
    await send("Runtime.enable");
    await send("Page.navigate", { url: `http://127.0.0.1:${appPort}/` });
    await wait(600);

    const expression = `(async function () {
      const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
      const byText = (selector, text) => {
        const found = Array.from(document.querySelectorAll(selector)).find((el) => el.textContent.trim().includes(text));
        if (!found) throw new Error("Missing " + selector + " containing " + JSON.stringify(text) + ". Visible text: " + document.body.innerText.slice(0, 800));
        return found;
      };
      const result = {};
      result.dialogLabelled = !!document.querySelector('[role="dialog"][aria-labelledby]');
      byText("button", "No, gracias").click();
      await wait(20);
      let state = JSON.parse(localStorage.getItem("teson.v1"));
      result.consentRefused = state.consent === "no" && state.queue.length === 0;
      byText("button", "Practicar ahora").click();
      await wait(20);
      byText('[role="dialog"] button', "Saltar").click();
      await wait(20);
      document.querySelector(".opt").click();
      byText("button", "Corregir").click();
      await wait(20);
      result.quizWorked = !!document.querySelector(".verdict") && !!document.querySelector(".explain a[href*='boe.es']");
      byText("button", "Impugnar esta pregunta").click();
      await wait(20);
      document.querySelector('input[name="reason"]').click();
      const sendReport = byText("button", "Enviar impugnación");
      result.offlineReportDisabled = !!sendReport && sendReport.disabled;
      result.reportExplained = !!byText(".sheet", "no se guardan en ningún servidor");
      return result;
    })()`;
    const evaluated = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (evaluated.exceptionDetails) {
      throw new Error(evaluated.exceptionDetails.text + "\n" + JSON.stringify(evaluated.exceptionDetails.exception, null, 2));
    }
    const result = evaluated.result.value;
    assert.deepEqual(result, {
      dialogLabelled: true,
      consentRefused: true,
      quizWorked: true,
      offlineReportDisabled: true,
      reportExplained: true
    });
    console.log("Headless end-to-end flow passed:", result);
  } finally {
    if (socket) socket.close();
    chrome.kill("SIGTERM");
    await Promise.race([
      new Promise((resolve) => chrome.once("exit", resolve)),
      wait(1500)
    ]);
    server.close();
    for (let attempt = 0; attempt < 5; attempt++) {
      try { fs.rmSync(profile, { recursive: true, force: true }); break; }
      catch (error) {
        if (attempt === 4) throw error;
        await wait(100);
      }
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
