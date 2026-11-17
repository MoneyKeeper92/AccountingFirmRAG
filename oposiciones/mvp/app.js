/*
 * Tesón MVP · app.js (v0.2: práctica adaptativa)
 *
 * Static single-page app. What it does:
 *  - Learner model per concept: recency-weighted accuracy, a spaced review interval, and a
 *    count of each typical confusion the student falls into.
 *  - Recommended practice. The adaptive arm takes 50% of questions from weak concepts, 30%
 *    from concepts due for review and 20% from new ones; no concept or area can take over a
 *    session. The standard arm gets random questions from the tema.
 *  - Experiment "adapt-v1": consenting users are randomised between the two arms. They take a
 *    10-question diagnostic (form A or B) at the start and a 10-question progress check
 *    (the other form) after enough practice. Both forms are held out of all practice.
 *  - Study and exam modes, a question timer with pause, the question ID, a numbered
 *    navigator, explanations with comparison tables (esquemas), impugnaciones, feedback.
 * Progress lives in localStorage. Pseudonymous events go to Supabase only with consent.
 */
(function () {
  "use strict";

  var CFG = window.TESON_CONFIG || {};
  var BANK = window.TESON_BANK;
  var ESQ = window.TESON_ESQUEMAS || {};
  var APP_VERSION = "mvp-0.2-private-beta";
  var EXP_ID = "adapt-v1";
  var LS_KEY = "teson.v1";
  var SESSION_KEY = "teson.session.v1";
  var DAY = 86400000;
  var LEITNER = [1, 3, 7, 21];
  var LETTERS = "ABCD";
  var ESSENTIAL_TYPES = ["question_reported", "feedback_sent"];
  var SID = sessionId();
  var WEAK = 0.7;

  var QMAP = {};
  BANK.questions.forEach(function (q) { QMAP[q.id] = q; });
  var CONTROL = BANK.controlForms.A.concat(BANK.controlForms.B);
  var AREAS = Object.keys(BANK.areas);

  // ── State ───────────────────────────────────────────────────
  function rid() {
    var a = new Uint8Array(12);
    (window.crypto || window.msCrypto).getRandomValues(a);
    return Array.prototype.map.call(a, function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
  }
  function sessionId() {
    try {
      var existing = window.sessionStorage.getItem(SESSION_KEY);
      if (existing) return existing;
      var created = rid();
      window.sessionStorage.setItem(SESSION_KEY, created);
      return created;
    } catch (e) { return rid(); }
  }
  function fresh() {
    return { v: 1, uid: rid(), consent: null, profile: null, src: null, stats: {}, history: [], days: [], queue: [],
      interest: {}, rated: {}, reported: {}, npsDone: false, created: Date.now(),
      cs: {}, mis: {}, snap: {}, exp: null, practiceSincePre: 0 };
  }
  var S = (function () {
    var s = null;
    try { s = JSON.parse(window.localStorage.getItem(LS_KEY)); } catch (e) {}
    if (!s || s.v !== 1) return fresh();
    var f = fresh();
    for (var k in f) if (!(k in s)) s[k] = f[k];
    return s;
  })();
  function persist() { try { window.localStorage.setItem(LS_KEY, JSON.stringify(S)); } catch (e) {} }
  if (!Array.isArray(S.queue) || S.queue.some(function (event) { return !event.basis || !event.bank_version; })) {
    S.queue = [];
    persist();
  }

  (function captureSource() {
    if (S.src) return;
    var src = {};
    try {
      var p = new URLSearchParams(window.location.search);
      ["utm_source", "utm_medium", "utm_campaign", "ref"].forEach(function (k) { if (p.get(k)) src[k] = p.get(k).slice(0, 80); });
      if (document.referrer) src.referrer = document.referrer.split("/").slice(0, 3).join("/");
    } catch (e) {}
    S.src = src; persist();
  })();

  // ── Experiment ──────────────────────────────────────────────
  function ensureExperiment() {
    if (S.exp && S.exp.id === EXP_ID) {
      // A user who accepts analytics later joins only if they haven't done the diagnostic yet.
      if (!S.exp.participant && S.consent === "yes" && !S.exp.pre && !S.exp.preSkipped) assign();
      return;
    }
    assign();
  }
  function assign() {
    var participant = S.consent === "yes";
    S.exp = {
      id: EXP_ID,
      participant: participant,
      arm: participant ? (Math.random() < 0.5 ? "adaptive" : "standard") : "adaptive",
      preForm: Math.random() < 0.5 ? "A" : "B",
      ts: Date.now(), pre: null, post: null, preSkipped: false, postSkipped: false
    };
    persist();
    if (participant) track("exp_assigned", { exp: EXP_ID, arm: S.exp.arm, pre_form: S.exp.preForm });
  }
  function adaptive() { return !S.exp || S.exp.arm === "adaptive"; }
  function postForm() { return S.exp.preForm === "A" ? "B" : "A"; }
  function controlHeld() {
    // Control questions stay out of practice until the progress check is done or skipped.
    return S.exp && !(S.exp.post || S.exp.postSkipped || (S.exp.preSkipped && !S.exp.pre));
  }
  function postEligible() {
    if (!S.exp || !S.exp.pre || S.exp.post || S.exp.postSkipped) return false;
    var days = (Date.now() - S.exp.pre.ts) / DAY;
    return S.practiceSincePre >= 60 || (days >= 10 && S.practiceSincePre >= 30);
  }

  // ── Events ──────────────────────────────────────────────────
  function legalReady() {
    var legal = CFG.legal || {};
    return !!(legal.updated && legal.controllerName && legal.taxId && legal.address && legal.processors && CFG.contactEmail);
  }
  function backendOn() { return !!(legalReady() && CFG.supabaseUrl && CFG.supabaseAnonKey); }
  var flushing = false, flushTimer = null, flushController = null, flushGeneration = 0;
  function track(type, payload, opts) {
    var essential = !!(opts && opts.essential);
    if (essential && ESSENTIAL_TYPES.indexOf(type) === -1) return false;
    if (!essential && S.consent !== "yes") return false;
    if (essential && !backendOn()) return false;
    payload = payload || {};
    if (!essential && S.exp && S.exp.participant) { payload.exp = EXP_ID; payload.arm = S.exp.arm; }
    S.queue.push({
      uid: essential ? null : S.uid,
      session_id: essential ? null : SID,
      type: type,
      payload: payload,
      client_ts: new Date().toISOString(),
      app_version: APP_VERSION,
      bank_version: BANK.version,
      basis: essential ? "user_request" : "consent"
    });
    if (S.queue.length > 500) S.queue = S.queue.slice(-500);
    persist();
    clearTimeout(flushTimer);
    flushTimer = setTimeout(flush, essential ? 200 : 2500);
    return true;
  }
  function flush(keepalive) {
    if (!backendOn() || flushing || !S.queue.length) return;
    var batch = S.queue.slice(0, 50);
    var generation = flushGeneration;
    flushing = true;
    var controller = window.AbortController ? new AbortController() : null;
    flushController = controller;
    try {
      fetch(CFG.supabaseUrl.replace(/\/$/, "") + "/rest/v1/events", {
        method: "POST",
        keepalive: !!keepalive,
        headers: {
          "apikey": CFG.supabaseAnonKey,
          "Authorization": "Bearer " + CFG.supabaseAnonKey,
          "Content-Type": "application/json",
          "Prefer": "return=minimal"
        },
        signal: controller ? controller.signal : undefined,
        body: JSON.stringify(batch)
      }).then(function (r) {
        if (generation !== flushGeneration) return;
        if (r.ok) {
          S.queue = S.queue.slice(batch.length);
          persist();
          if (S.queue.length) { clearTimeout(flushTimer); flushTimer = setTimeout(flush, 1000); }
        } else {
          toast("El servidor ha rechazado el envío. Tus datos siguen guardados en este navegador.");
        }
      }).catch(function () {
        if (generation !== flushGeneration) return;
        toast("No hemos podido enviar los datos. Lo reintentaremos mientras sigan guardados en este navegador.");
      }).then(function () {
        if (generation !== flushGeneration) return;
        flushing = false;
        if (flushController === controller) flushController = null;
      });
    } catch (e) {
      if (generation === flushGeneration) {
        flushing = false;
        if (flushController === controller) flushController = null;
      }
    }
  }
  document.addEventListener("visibilitychange", function () { if (document.visibilityState === "hidden") flush(true); });

  // ── Helpers ─────────────────────────────────────────────────
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      var v = attrs[k];
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "html") el.innerHTML = v; // only for static esquemas
      else if (k.slice(0, 2) === "on") el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? "" : v);
    }
    for (var i = 2; i < arguments.length; i++) add(el, arguments[i]);
    return el;
  }
  function add(el, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) { c.forEach(function (x) { add(el, x); }); return; }
    el.appendChild(c.nodeType ? c : document.createTextNode(String(c)));
  }
  function fmt(n, d) { return Number(n).toLocaleString("es-ES", { maximumFractionDigits: d == null ? 2 : d, minimumFractionDigits: 0 }); }
  function pct(a, b) { return b ? Math.round(100 * a / b) : 0; }
  function today() { var d = new Date(); d.setHours(0, 0, 0, 0); return d.getTime(); }
  function dayKey(ts) { return new Date(ts || Date.now()).toISOString().slice(0, 10); }
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function clock(ms) { var s = Math.max(0, Math.floor(ms / 1000)); var m = Math.floor(s / 60); return ("0" + Math.floor(m / 60)).slice(-2) + ":" + ("0" + (m % 60)).slice(-2) + ":" + ("0" + (s % 60)).slice(-2); }
  function wordmark() {
    var ns = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(ns, "svg");
    svg.setAttribute("class", "tick"); svg.setAttribute("viewBox", "0 0 24 16"); svg.setAttribute("aria-hidden", "true");
    var p = document.createElementNS(ns, "path"); p.setAttribute("d", "M3 9 L9 14 L21 2"); svg.appendChild(p);
    var o = h("span", { "class": "o" }, "o"); o.appendChild(svg);
    return h("div", { "class": "wm", "aria-label": "tesón" }, "tes", o, "n");
  }
  var toastTimer = null;
  function toast(msg) {
    var old = document.querySelector(".toast"); if (old) old.remove();
    var t = h("div", { "class": "toast", role: "status" }, msg);
    document.body.appendChild(t);
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.remove(); }, 3500);
  }
  function sheet(build) {
    var previouslyFocused = document.activeElement;
    var scrim = h("div", { "class": "scrim" });
    var box = h("div", { "class": "sheet", role: "dialog", "aria-modal": "true" });
    function focusable() {
      return Array.prototype.filter.call(box.querySelectorAll("button:not([disabled]), input:not([disabled]), textarea:not([disabled]), a[href]"), function (el) {
        return !el.hidden && el.offsetParent !== null;
      });
    }
    function close() {
      scrim.remove();
      document.removeEventListener("keydown", onKey);
      if (previouslyFocused && document.contains(previouslyFocused)) previouslyFocused.focus();
    }
    function onKey(e) {
      if (e.key === "Escape") return close();
      if (e.key !== "Tab") return;
      var items = focusable();
      if (!items.length) { e.preventDefault(); box.focus(); return; }
      var first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
    scrim.addEventListener("click", function (e) { if (e.target === scrim) close(); });
    document.addEventListener("keydown", onKey);
    add(box, build(close));
    var heading = box.querySelector("h2");
    if (heading) {
      heading.id = "dialog-" + rid();
      box.setAttribute("aria-labelledby", heading.id);
    } else {
      box.setAttribute("aria-label", "Diálogo");
    }
    box.setAttribute("tabindex", "-1");
    scrim.appendChild(box);
    document.body.appendChild(scrim);
    var f = focusable()[0]; if (f) f.focus(); else box.focus();
    return close;
  }
  function previewNote() { return backendOn() ? null : h("p", { "class": "small muted" }, "Vista previa: en esta versión los envíos no se guardan en ningún servidor."); }

  // ── Learner model ───────────────────────────────────────────
  function qstat(id) { return S.stats[id] || (S.stats[id] = { seen: 0, c: 0, w: 0, b: 0, box: 0, due: 0, last: 0 }); }
  function cstat(c) { return S.cs[c] || (S.cs[c] = { r: [], n: 0, c: 0, last: 0, lastOk: 0, iv: 0, due: 0 }); }

  function record(q, choice, ms, changed, ctx) {
    var res = choice == null || choice < 0 ? "blank" : choice === q.k ? "correct" : "wrong";
    var ok = res === "correct";
    var now = Date.now();
    var isCheck = ctx.session === "diagnostic" || ctx.session === "control";

    // Question level (spaced review of mistakes). Checkpoint questions never enter "Tus fallos".
    var st = qstat(q.id);
    st.seen++; st.last = now;
    if (ok) { st.c++; } else if (res === "wrong") { st.w++; } else { st.b++; }
    if (!isCheck) {
      if (ok) {
        if (st.box > 0) { st.box++; if (st.box > LEITNER.length) { st.box = 0; st.due = 0; } else st.due = today() + LEITNER[st.box - 1] * DAY; }
      } else { st.box = 1; st.due = today() + DAY; }
    }

    // Concept level: recency-weighted accuracy and an expanding review interval.
    q.concepts.forEach(function (c) {
      var x = cstat(c);
      x.r.push(ok ? 1 : 0); if (x.r.length > 12) x.r = x.r.slice(-12);
      x.n++; if (ok) { x.c++; x.lastOk = now; }
      x.last = now;
      x.iv = ok ? Math.min(45, x.iv ? x.iv * 2.5 : 2) : 1;
      x.due = today() + Math.round(x.iv) * DAY;
    });

    // Typical confusions: hits when the chosen wrong option carries one; fixes when the
    // student gets right a question that offered that confusion.
    var misHit = res === "wrong" ? q.mis[choice] || null : null;
    if (misHit) { var m = S.mis[misHit] || (S.mis[misHit] = { hits: [], fixes: [] }); m.hits.push(now); m.hits = m.hits.slice(-30); }
    if (ok) Object.keys(q.mis).forEach(function (k) {
      var id = q.mis[k]; var m2 = S.mis[id];
      if (m2) { m2.fixes.push(now); m2.fixes = m2.fixes.slice(-30); }
    });

    var d = dayKey(now); if (S.days.indexOf(d) === -1) S.days.push(d);
    if (!isCheck && S.exp && S.exp.pre) S.practiceSincePre++;
    persist();
    track("question_answered", { qid: q.id, sub: q.sub, concepts: q.concepts, diff: q.diff, result: res, choice: choice,
      mis: misHit, time_ms: ms, changed: changed || 0, mode: ctx.mode, session: ctx.session, reason: ctx.reason || null });
    return res;
  }

  function mastery(c) {
    var x = S.cs[c];
    if (!x || !x.n) return null;
    var w = 1, sw = 0, sr = 0;
    for (var i = x.r.length - 1; i >= 0; i--) { sr += w * x.r[i]; sw += w; w *= 0.75; }
    // Prior worth one answer at 50%: one correct → 75%, one wrong → 25%.
    return (sr + 0.5) / (sw + 1);
  }
  function conceptsOf(area) { return Object.keys(BANK.concepts).filter(function (c) { return !area || BANK.concepts[c].area === area; }); }
  function areaInfo(area) {
    var cs = conceptsOf(area), n = 0, sum = 0, wsum = 0;
    cs.forEach(function (c) { var x = S.cs[c]; var m = mastery(c); if (m != null) { n += x.n; sum += m * Math.min(x.n, 6); wsum += Math.min(x.n, 6); } });
    var qs = BANK.questions.filter(function (q) { return q.area === area; });
    return { n: n, pct: wsum && n >= 3 ? Math.round(100 * sum / wsum) : null, questions: qs.length };
  }
  function activeMis() {
    var cut = Date.now() - 30 * DAY, out = [];
    Object.keys(S.mis).forEach(function (id) {
      var m = S.mis[id];
      var hits = m.hits.filter(function (t) { return t > cut; }).length;
      var fixes = m.fixes.filter(function (t) { return t > cut; }).length;
      var score = hits - 0.5 * fixes;
      if (hits >= 2 && score >= 1.5 && BANK.misconceptions[id]) out.push({ id: id, hits: hits, score: score });
    });
    return out.sort(function (a, b) { return b.score - a.score; });
  }
  function snapshot() {
    var d = dayKey(), row = {};
    AREAS.forEach(function (a) { var i = areaInfo(a); if (i.pct != null) row[a] = i.pct; });
    S.snap[d] = row;
    var keys = Object.keys(S.snap).sort(); if (keys.length > 120) delete S.snap[keys[0]];
    persist();
  }
  function trend(area) {
    var now = areaInfo(area).pct; if (now == null) return null;
    var keys = Object.keys(S.snap).sort(), ref = null, cut = dayKey(Date.now() - 7 * DAY);
    for (var i = keys.length - 1; i >= 0; i--) { if (keys[i] <= cut && S.snap[keys[i]][area] != null) { ref = S.snap[keys[i]][area]; break; } }
    if (ref == null) for (var j = 0; j < keys.length; j++) { if (keys[j] < dayKey() && S.snap[keys[j]][area] != null) { ref = S.snap[keys[j]][area]; break; } }
    return ref == null ? null : now - ref;
  }
  function predicted() {
    var total = 0; for (var c in S.cs) total += S.cs[c].n;
    if (total < 30) return null;
    var all = 0, ok = 0; for (var c2 in S.cs) { all += S.cs[c2].n; ok += S.cs[c2].c; }
    var prior = all ? ok / all : 0.5, sum = 0;
    BANK.questions.forEach(function (q) {
      var ms = q.concepts.map(mastery).filter(function (m) { return m != null; });
      var p = ms.length ? ms.reduce(function (a, b) { return a + b; }, 0) / ms.length : prior;
      sum += p - (1 - p) / 3;
    });
    return Math.max(0, sum / BANK.questions.length * 10);
  }

  // ── Question selection ──────────────────────────────────────
  function practicePool(area) {
    return BANK.questions.filter(function (q) {
      if (area && q.area !== area) return false;
      if (controlHeld() && CONTROL.indexOf(q.id) !== -1) return false;
      return true;
    });
  }
  function buildStandard(n, area) {
    return shuffle(practicePool(area)).slice(0, n).map(function (q) { return { id: q.id, reason: "Práctica" }; });
  }
  function buildAdaptive(n, opts) {
    opts = opts || {};
    var pool = practicePool(opts.area);
    var now = Date.now();
    var mis = activeMis().map(function (m) { return m.id; });
    var concepts = {};
    pool.forEach(function (q) { q.concepts.forEach(function (c) { (concepts[c] = concepts[c] || []).push(q); }); });
    var cids = Object.keys(concepts);
    var weak = [], due = [], fresh = [];
    cids.forEach(function (c) {
      var m = mastery(c), x = S.cs[c];
      if (m == null) fresh.push(c);
      else if (m < WEAK) weak.push(c);
      else if (x.due <= now) due.push(c);
    });
    var misBoost = function (c) { return concepts[c].some(function (q) { return Object.keys(q.mis).some(function (k) { return mis.indexOf(q.mis[k]) !== -1; }); }) ? -0.15 : 0; };
    weak.sort(function (a, b) { return (mastery(a) + misBoost(a)) - (mastery(b) + misBoost(b)); });
    due.sort(function (a, b) { return S.cs[a].due - S.cs[b].due; });
    var order = Object.keys(BANK.concepts);
    fresh.sort(function (a, b) { return order.indexOf(a) - order.indexOf(b); });

    var picked = [], used = {}, perConcept = {}, perArea = {};
    var areaCap = opts.area ? n : Math.ceil(n * 0.4);
    function score(q) {
      var s = S.stats[q.id], sc = 0;
      if (!s || !s.seen) sc -= 2;
      else { if (now - s.last < DAY) sc += 5; sc += s.c / Math.max(1, s.seen); }
      if (opts.mis && Object.keys(q.mis).some(function (k) { return q.mis[k] === opts.mis; })) sc -= 3;
      if (Object.keys(q.mis).some(function (k) { return mis.indexOf(q.mis[k]) !== -1; })) sc -= 0.5;
      return sc + Math.random() * 0.3;
    }
    function take(cList, quota, reason) {
      var got = 0, rounds = 0;
      while (got < quota && rounds < 4) {
        var progress = false;
        for (var i = 0; i < cList.length && got < quota; i++) {
          var c = cList[i];
          if ((perConcept[c] || 0) >= 3) continue;
          var cand = concepts[c].filter(function (q) { return !used[q.id] && (perArea[q.area] || 0) < areaCap; }).sort(function (a, b) { return score(a) - score(b); })[0];
          if (!cand) continue;
          used[cand.id] = 1; perConcept[c] = (perConcept[c] || 0) + 1; perArea[cand.area] = (perArea[cand.area] || 0) + 1;
          picked.push({ id: cand.id, reason: reason }); got++; progress = true;
        }
        if (!progress) break;
        rounds++;
      }
      return got;
    }

    if (opts.mis) {
      var misQs = pool.filter(function (q) { return Object.keys(q.mis).some(function (k) { return q.mis[k] === opts.mis; }); })
        .sort(function (a, b) { return score(a) - score(b); }).slice(0, n);
      misQs.forEach(function (q) { used[q.id] = 1; picked.push({ id: q.id, reason: "Tu confusión" }); });
    } else {
      var qWeak = Math.round(n * 0.5), qDue = Math.round(n * 0.3), qNew = n - qWeak - qDue;
      take(weak, qWeak, "Refuerzo");
      take(due, qWeak + qDue - picked.length, "Repaso");
      take(fresh, n - picked.length, "Nuevo");
    }
    // Fill any shortfall with the concepts seen least recently (broad syllabus coverage).
    if (picked.length < n) {
      var rest = pool.filter(function (q) { return !used[q.id]; }).sort(function (a, b) {
        var la = Math.min.apply(null, a.concepts.map(function (c) { return S.cs[c] ? S.cs[c].last : 0; }));
        var lb = Math.min.apply(null, b.concepts.map(function (c) { return S.cs[c] ? S.cs[c].last : 0; }));
        return la - lb || score(a) - score(b);
      });
      for (var i = 0; i < rest.length && picked.length < n; i++) {
        if (!opts.area && (perArea[rest[i].area] || 0) >= areaCap && rest.length - i > n - picked.length) continue;
        perArea[rest[i].area] = (perArea[rest[i].area] || 0) + 1;
        picked.push({ id: rest[i].id, reason: "Cobertura" });
      }
    }
    return shuffle(picked);
  }
  function weakestArea() {
    var best = null;
    AREAS.forEach(function (a) { var i = areaInfo(a); if (i.pct != null && (best == null || i.pct < best.pct)) best = { area: a, pct: i.pct }; });
    return best;
  }

  // ── Views ───────────────────────────────────────────────────
  var VIEW = "home", TEST = null, timerInt = null, SETUP = null, PLAN = null;
  var root = document.getElementById("app");
  function go(v) { VIEW = v; render(); window.scrollTo(0, 0); }

  function render() {
    clearInterval(timerInt);
    root.innerHTML = "";
    if (VIEW === "quiz") { root.appendChild(viewQuiz()); return; }
    root.appendChild(topbar());
    var main = h("main", { "class": "wrap" });
    if (VIEW === "home") main.appendChild(viewHome());
    else if (VIEW === "setup") main.appendChild(viewSetup());
    else if (VIEW === "results") main.appendChild(viewResults());
    else if (VIEW === "fallos") main.appendChild(viewFallos());
    else if (VIEW === "progreso") main.appendChild(viewProgreso());
    main.appendChild(footer());
    root.appendChild(main);
    root.appendChild(h("button", { "class": "fab", type: "button", onclick: openFeedback }, "Danos tu opinión"));
  }

  function topbar() {
    var nf = fallos().length;
    function nb(v, label) { return h("button", { "class": "navbtn", type: "button", "aria-current": VIEW === v ? "page" : null, onclick: function () { go(v); } }, label); }
    return h("header", { "class": "top" }, h("div", { "class": "top-inner" },
      h("button", { "class": "brand", type: "button", onclick: function () { go("home"); } }, "tesón"),
      h("span", { "class": "beta" }, "Beta"),
      h("nav", { "aria-label": "Principal" }, nb("home", "Inicio"), nb("fallos", "Fallos" + (nf ? " (" + nf + ")" : "")), nb("progreso", "Progreso"))));
  }
  function footer() {
    var reviewCopy = BANK.status === "revisado_humano"
      ? "Banco revisado · contenido actualizado a " + BANK.contentAsOf + "."
      : "Beta privada · banco pendiente de revisión humana · contenido comprobado automáticamente a " + BANK.contentAsOf + ".";
    return h("footer", { "class": "foot" },
      h("div", null, "Tesón · Oposiciones, pregunta a pregunta. " + reviewCopy + " Si ves algo raro, impúgnalo."),
      h("div", null, "Legislación: Agencia Estatal Boletín Oficial del Estado (textos consolidados, de carácter informativo). Tesón no está vinculado al INAP ni a ninguna Administración Pública."),
      h("div", { "class": "row" },
        h("a", { href: "privacidad.html", target: "_blank", rel: "noopener" }, "Privacidad"),
        h("a", { href: "aviso-legal.html", target: "_blank", rel: "noopener" }, "Aviso legal"),
        CFG.contactEmail ? h("span", null, CFG.contactEmail) : null));
  }

  // Home: "Tu Constitución"
  function viewHome() {
    ensureExperiment();
    var s = h("section", { "class": "view stack-lg" });
    var totalAns = 0; for (var c in S.cs) totalAns += S.cs[c].n;
    var ad = adaptive();

    if (!legalReady()) {
      s.appendChild(h("div", { "class": "config-alert", role: "alert" },
        h("b", null, "Versión local no compartible."),
        h("span", null, " Faltan la identidad legal o la configuración de envíos. Los tests funcionan, pero las impugnaciones y opiniones están desactivadas.")));
    }

    if (!totalAns && !S.exp.pre) {
      s.appendChild(h("div", { "class": "hero" },
        wordmark(),
        h("h1", null, "Practica lo que más necesitas mejorar."),
        h("p", { "class": "lede" }, "Tests de Auxiliar Administrativo del Estado con cada respuesta explicada. Tesón aprende qué te cuesta y te propone las preguntas que más te ayudan."),
        h("p", { "class": "small muted" }, "Gratis durante la beta. Sin registro.")));
    }

    if (!S.exp.pre && !S.exp.preSkipped) {
      s.appendChild(h("div", { "class": "card accent stack" },
        h("span", { "class": "eyebrow" }, "Empieza aquí"),
        h("h2", null, "Diagnóstico inicial: 10 preguntas"),
        h("p", { "class": "muted", style: "margin:0" }, "Unos 5 minutos. Sirve para saber de dónde partes y personalizar tu práctica. Las explicaciones las verás al final."),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: startDiagnostic }, "Hacer el diagnóstico"),
          h("button", { "class": "btn quiet", type: "button", onclick: function () { S.exp.preSkipped = true; persist(); track("checkpoint_skipped", { kind: "pre" }); render(); } }, "Saltar"))));
    }

    if (postEligible()) {
      s.appendChild(h("div", { "class": "card accent stack" },
        h("span", { "class": "eyebrow" }, "Control de progreso"),
        h("h2", null, "¿Cuánto has mejorado?"),
        h("p", { "class": "muted", style: "margin:0" }, "10 preguntas que todavía no has visto, del mismo nivel que tu diagnóstico. Te enseñamos la comparación al terminar."),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: startControl }, "Hacer el control"),
          h("button", { "class": "btn quiet", type: "button", onclick: function () { S.exp.postSkipped = true; persist(); track("checkpoint_skipped", { kind: "post" }); render(); } }, "Ahora no"))));
    }

    // Header + areas
    s.appendChild(h("div", { "class": "stack" },
      h("span", { "class": "eyebrow" }, ad ? "Tu práctica personalizada" : "Tu práctica"),
      h("h1", null, "Tu Constitución"),
      h("p", { "class": "lede" }, ad ? (totalAns ? "Hoy vamos a reforzar tus puntos débiles. Elige un área o sigue la práctica recomendada." : "Elige un área o sigue la práctica recomendada.") : "Elige un área o haz una práctica variada del tema.")));

    var list = h("div", { "class": "areas" });
    AREAS.forEach(function (a) {
      var info = areaInfo(a), t = trend(a);
      list.appendChild(h("button", { "class": "arearow", type: "button", onclick: function () { startPractice(10, a); } },
        h("span", { "class": "an" }, BANK.areas[a]),
        h("span", { "class": "ap" }, info.pct == null ? "Sin datos" : info.pct + " %"),
        h("span", { "class": "meter", "aria-hidden": "true" }, h("i", { style: "width:" + (info.pct || 0) + "%;" + (info.pct != null && info.pct < 60 ? "background:var(--amber)" : "") })),
        h("span", { "class": "at small muted" }, t ? (t > 0 ? "▲ +" + t + " pts en 7 días" : "▼ " + t + " pts en 7 días") : info.questions + " preguntas · practicar 10")));
    });
    s.appendChild(list);

    // Recommended practice: build the real session now so the description matches it.
    var wk = weakestArea(), recText;
    PLAN = ad ? buildAdaptive(20, {}) : null;
    if (!ad) recText = "20 preguntas variadas de todo el tema.";
    else if (!totalAns) recText = "20 preguntas para conocer tu nivel en todo el tema.";
    else {
      var cnt = {}; PLAN.forEach(function (x) { cnt[x.reason] = (cnt[x.reason] || 0) + 1; });
      var parts = [];
      if (cnt["Refuerzo"]) parts.push(cnt["Refuerzo"] + " de refuerzo" + (wk && wk.pct < 70 ? " (sobre todo " + BANK.areas[wk.area] + ")" : ""));
      if (cnt["Repaso"]) parts.push(cnt["Repaso"] + " de repaso");
      if (cnt["Nuevo"]) parts.push(cnt["Nuevo"] + " de conceptos nuevos");
      if (cnt["Cobertura"]) parts.push(cnt["Cobertura"] + " para cubrir todo el tema");
      recText = PLAN.length + " preguntas adaptadas a tu progreso: " + parts.join(", ").replace(/, ([^,]*)$/, " y $1") + ".";
    }
    s.appendChild(h("div", { "class": "card rec stack" },
      h("span", { "class": "eyebrow" }, ad ? "Práctica recomendada" : "Práctica del tema"),
      h("p", { style: "margin:0;font-weight:600" }, recText),
      h("div", { "class": "row" }, h("button", { "class": "btn", type: "button", onclick: function () { startPractice(20, null, null, PLAN); } }, "Practicar ahora"))));

    // Typical confusion (adaptive arm only)
    if (ad) {
      var am = activeMis()[0];
      if (am) {
        var M = BANK.misconceptions[am.id];
        s.appendChild(h("div", { "class": "card warnc stack" },
          h("span", { "class": "eyebrow", style: "color:var(--amber-ink)" }, "Sueles confundir"),
          h("p", { style: "margin:0;font-weight:600" }, M.name),
          h("p", { "class": "small muted", style: "margin:0" }, "Has caído en esta confusión " + am.hits + " veces en los últimos 30 días."),
          h("div", { "class": "row" },
            h("button", { "class": "btn amber", type: "button", onclick: function () { startPractice(8, null, am.id); } }, "Practicar esta confusión"),
            M.esquema ? h("button", { "class": "btn quiet", type: "button", onclick: function () { openEsquema(M.esquema, "dashboard"); } }, "Ver esquema") : null)));
      }
    }

    // Stats strip
    var t2 = totals(), nf = fallos().length, pr = predicted();
    s.appendChild(h("div", { "class": "stats" + (pr != null ? " four" : "") },
      h("div", { "class": "stat" }, h("b", null, fmt(t2.seen, 0)), h("span", null, "respuestas")),
      h("div", { "class": "stat" }, h("b", null, pct(t2.c, t2.seen) + " %"), h("span", null, "aciertos")),
      h("div", { "class": "stat" }, h("b", null, String(nf)), h("span", null, "fallos por repasar")),
      pr != null ? h("div", { "class": "stat" }, h("b", null, fmt(pr, 1)), h("span", null, "nota estimada hoy (/10)")) : null));
    if (pr != null) s.appendChild(h("p", { "class": "small muted", style: "margin-top:-18px" }, "Nota estimada si hicieras hoy un examen de este tema, con la penalización oficial. Es orientativa."));

    s.appendChild(h("div", { "class": "row" },
      nf ? h("button", { "class": "btn ghost", type: "button", onclick: function () { startReview(dueFallos().length ? dueFallos() : fallos()); } }, "Repasar fallos (" + nf + ")") : null,
      h("button", { "class": "btn ghost", type: "button", onclick: function () { SETUP = { areas: AREAS.slice(), n: 20, mode: "estudio", pool: "todas" }; go("setup"); } }, "Crear test personalizado")));

    // Other temas
    var others = h("div", { "class": "temas" });
    BANK.temas.filter(function (tm) { return !tm.activo; }).forEach(function (tm) {
      var on = !!S.interest[tm.id];
      others.appendChild(h("div", { "class": "tema" },
        h("div", { "class": "t" }, tm.nombre),
        h("button", { "class": "chip", type: "button", "aria-pressed": on ? "true" : "false", onclick: function () {
          S.interest[tm.id] = !on; persist();
          track("tema_interest", { tema: tm.id, on: !on });
          if (!on) toast("Anotado. Priorizamos los temas que más pedís.");
          render();
        } }, on ? "✓ Me interesa" : "Me interesa"),
        h("div", { "class": "d" }, tm.detalle),
        h("div", { "class": "meta" }, h("span", { "class": "pill warn" }, "En preparación"))));
    });
    s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Próximos temas"), others));
    return s;
  }

  // Custom test (Maxwell-style "create test")
  function viewSetup() {
    var st = SETUP;
    var pool = practicePool().filter(function (q) {
      if (st.areas.indexOf(q.area) === -1) return false;
      var x = S.stats[q.id];
      if (st.pool === "nuevas") return !x || !x.seen;
      if (st.pool === "falladas") return x && x.box > 0;
      return true;
    });
    var n = st.n === "all" ? pool.length : Math.min(st.n, pool.length);
    var s = h("section", { "class": "view stack-lg" });
    s.appendChild(h("div", { "class": "stack" }, h("span", { "class": "eyebrow" }, "Test personalizado"), h("h1", null, "Constitución Española (I)")));

    var tbl = h("div", { "class": "areas" });
    AREAS.forEach(function (a) {
      var on = st.areas.indexOf(a) !== -1, info = areaInfo(a);
      tbl.appendChild(h("button", { "class": "arearow pick", type: "button", "aria-pressed": on ? "true" : "false", onclick: function () {
        st.areas = on ? st.areas.filter(function (x) { return x !== a; }) : st.areas.concat(a); render();
      } },
        h("span", { "class": "an" }, (on ? "☑ " : "☐ ") + BANK.areas[a]),
        h("span", { "class": "ap" }, info.pct == null ? "—" : info.pct + " %"),
        h("span", { "class": "at small muted" }, info.questions + " preguntas")));
    });
    s.appendChild(h("fieldset", null, h("legend", null, "Áreas"), tbl));

    var nChips = h("div", { "class": "chips" });
    [10, 20, 30, "all"].forEach(function (v) { nChips.appendChild(h("button", { "class": "chip", type: "button", "aria-pressed": st.n === v ? "true" : "false", onclick: function () { st.n = v; render(); } }, v === "all" ? "Todas" : String(v))); });
    s.appendChild(h("fieldset", null, h("legend", null, "Número de preguntas"), nChips));

    var pChips = h("div", { "class": "chips" });
    [["todas", "Todas"], ["nuevas", "Solo las que no he visto"], ["falladas", "Solo las que he fallado"]].forEach(function (p) {
      pChips.appendChild(h("button", { "class": "chip", type: "button", "aria-pressed": st.pool === p[0] ? "true" : "false", onclick: function () { st.pool = p[0]; render(); } }, p[1]));
    });
    s.appendChild(h("fieldset", null, h("legend", null, "Qué preguntas"), pChips));

    function modeOpt(v, t, d) { return h("label", null, h("input", { type: "radio", name: "mode", value: v, checked: st.mode === v, onchange: function () { st.mode = v; } }), h("span", null, h("b", null, t), h("small", null, d))); }
    s.appendChild(h("fieldset", null, h("legend", null, "Modo"), h("div", { "class": "choice" },
      modeOpt("estudio", "Estudio", "Corriges cada pregunta al momento y ves la explicación."),
      modeOpt("examen", "Examen", "Corrección al final, con cronómetro y penalización (−1/3 por fallo)."))));

    s.appendChild(h("div", { "class": "dock" }, h("button", { "class": "btn", type: "button", disabled: n === 0, onclick: function () {
      startTest(shuffle(pool).slice(0, n).map(function (q) { return { id: q.id, reason: null }; }), st.mode, "custom", "Test personalizado");
    } }, n === 0 ? "No hay preguntas con estos filtros" : "Crear test · " + n + " preguntas")));
    return s;
  }

  // ── Starting sessions ───────────────────────────────────────
  function needOnboarding(then) { if (!S.profile && !S.history.length) { openOnboarding(then); return true; } return false; }
  function startPractice(n, area, misId, plan) {
    if (needOnboarding(function () { startPractice(n, area, misId, plan); })) return;
    var items = plan && plan.length ? plan : adaptive() ? buildAdaptive(n, { area: area, mis: misId }) : buildStandard(n, area);
    if (!items.length) { toast("No hay preguntas disponibles ahora mismo."); return; }
    var title = misId ? "Tu confusión: " + BANK.misconceptions[misId].name : area ? BANK.areas[area] : adaptive() ? "Práctica recomendada" : "Práctica del tema";
    startTest(items, "estudio", misId ? "mis" : area ? "area" : "recommended", title);
  }
  function startDiagnostic() {
    if (needOnboarding(startDiagnostic)) return;
    startTest(shuffle(BANK.controlForms[S.exp.preForm]).map(function (id) { return { id: id, reason: null }; }), "examen", "diagnostic", "Diagnóstico inicial");
  }
  function startControl() {
    startTest(shuffle(BANK.controlForms[postForm()]).map(function (id) { return { id: id, reason: null }; }), "examen", "control", "Control de progreso");
  }
  function startReview(list) {
    if (!list.length) return;
    startTest(shuffle(list).slice(0, 30).map(function (q) { return { id: q.id, reason: "Tus fallos" }; }), "estudio", "review", "Repaso de fallos");
  }
  function startTest(items, mode, session, title) {
    TEST = { ids: items.map(function (x) { return x.id; }), reasons: {}, mode: mode, session: session, title: title, i: 0, maxI: 0,
      ans: {}, checked: {}, times: {}, changed: {}, start: Date.now(), qstart: Date.now(), paused: false, pausedAt: 0 };
    items.forEach(function (x) { TEST.reasons[x.id] = x.reason; });
    track("test_started", { mode: mode, session: session, n: TEST.ids.length, reasons: items.map(function (x) { return x.reason; }) });
    go("quiz");
  }

  // ── Quiz ────────────────────────────────────────────────────
  function isCheckpoint() { return TEST.session === "diagnostic" || TEST.session === "control"; }
  function qElapsed(q) { return (TEST.times[q.id] || 0) + (TEST.paused ? 0 : Date.now() - TEST.qstart); }
  function stamp(q) { if (!TEST.paused) TEST.times[q.id] = (TEST.times[q.id] || 0) + (Date.now() - TEST.qstart); TEST.qstart = Date.now(); }
  function jump(to) {
    var q = QMAP[TEST.ids[TEST.i]];
    stamp(q); TEST.i = to; TEST.maxI = Math.max(TEST.maxI, to); TEST.qstart = Date.now();
    render(); window.scrollTo(0, 0);
  }
  function togglePause() {
    var q = QMAP[TEST.ids[TEST.i]];
    if (!TEST.paused) { stamp(q); TEST.paused = true; TEST.pausedAt = Date.now(); }
    else { TEST.paused = false; TEST.start += Date.now() - TEST.pausedAt; TEST.qstart = Date.now(); }
    track("test_paused", { paused: TEST.paused });
    render();
  }

  function viewQuiz() {
    var T = TEST, q = QMAP[T.ids[T.i]], n = T.ids.length;
    var checked = !!T.checked[q.id], sel = T.ans[q.id];
    var wrap = h("div", null);

    // Top bar: timer + pause, report, finish (Maxwell-style)
    var timerEl = h("b", { id: "qtimer" }, clock(qElapsed(q)));
    wrap.appendChild(h("header", { "class": "qbar" }, h("div", { "class": "qbar-inner" },
      h("button", { "class": "iconbtn", type: "button", onclick: togglePause, "aria-label": T.paused ? "Reanudar" : "Pausar" }, T.paused ? "▶" : "❚❚"),
      h("div", { "class": "qtime" }, timerEl, h("span", null, "en esta pregunta")),
      h("span", { "class": "grow" }),
      h("button", { "class": "btn quiet sm", type: "button", onclick: function () { openReport(q); } }, S.reported[q.id] ? "Impugnada ✓" : "Impugnar"),
      T.mode === "examen" ? h("button", { "class": "btn sm", type: "button", onclick: function () { stamp(q); confirmFinish(); } }, "Entregar") : null,
      h("button", { "class": "btn quiet sm", type: "button", onclick: function () { confirmExit(function () { go("home"); }); } }, "Salir"))));

    var main = h("main", { "class": "wrap" });
    var s = h("section", { "class": "view stack", style: "padding-top:16px" });

    // Navigator
    var nav = h("div", { "class": "qnav", role: "navigation", "aria-label": "Preguntas" });
    T.ids.forEach(function (id, idx) {
      var cls = "qn";
      if (idx === T.i) cls += " cur";
      if (T.mode === "estudio" && T.checked[id]) cls += QMAP[id].k === T.ans[id] ? " ok" : " bad";
      else if (T.ans[id] != null && T.ans[id] >= 0) cls += " ans";
      var allowed = T.mode === "examen" || idx <= T.maxI;
      nav.appendChild(h("button", { "class": cls, type: "button", disabled: !allowed, "aria-current": idx === T.i ? "step" : null, onclick: function () { if (idx !== T.i) jump(idx); } }, String(idx + 1)));
    });
    s.appendChild(h("div", { "class": "small muted" }, T.title));
    s.appendChild(nav);
    s.appendChild(h("div", { "class": "progress", role: "progressbar", "aria-label": "Progreso del test", "aria-valuemin": "0", "aria-valuemax": String(n), "aria-valuenow": String(T.i + (checked ? 1 : 0)) }, h("i", { style: "width:" + pct(T.i + (checked ? 1 : 0), n) + "%" })));

    if (T.paused) {
      s.appendChild(h("div", { "class": "empty" }, h("b", null, "En pausa"), h("span", { "class": "small" }, "El cronómetro está parado."), h("button", { "class": "btn", type: "button", onclick: togglePause }, "Reanudar")));
      main.appendChild(s); wrap.appendChild(main); return wrap;
    }

    var reason = T.reasons[q.id];
    s.appendChild(h("div", { "class": "qmeta" },
      h("span", { "class": "qid" }, "ID " + q.id),
      h("span", null, "Pregunta " + (T.i + 1) + " de " + n),
      reason ? h("span", { "class": "pill " + (reason === "Refuerzo" || reason === "Tu confusión" ? "warn" : "on") }, reason) : null));
    s.appendChild(h("p", { "class": "stem" }, q.q));

    var opts = h("div", { "class": "opts", role: "group", "aria-label": "Opciones" });
    q.o.forEach(function (text, i) {
      var cls = "opt";
      if (checked) { if (i === q.k) cls += " right"; else if (i === sel) cls += " wrong"; }
      else if (sel === i) cls += " sel";
      opts.appendChild(h("button", { "class": cls, type: "button", disabled: checked, "aria-pressed": !checked && sel === i ? "true" : "false", onclick: function () {
        if (T.ans[q.id] != null && T.ans[q.id] >= 0 && T.ans[q.id] !== i) T.changed[q.id] = (T.changed[q.id] || 0) + 1;
        T.ans[q.id] = T.ans[q.id] === i && T.mode === "examen" ? undefined : i;
        render();
      } }, h("span", { "class": "bub" }, LETTERS[i]), h("span", null, text)));
    });
    s.appendChild(opts);

    if (checked) {
      var res = sel == null || sel < 0 ? "blank" : sel === q.k ? "correct" : "wrong";
      s.appendChild(h("div", { "class": "verdict " + (res === "correct" ? "ok" : res === "wrong" ? "bad" : "blank"), role: "status" },
        res === "correct" ? "✓ ¡Correcta!" : res === "wrong" ? "✗ Incorrecta. La correcta es la " + LETTERS[q.k] + "." : "En blanco. La correcta es la " + LETTERS[q.k] + "."));
      s.appendChild(explanation(q, sel));
    }

    var dock = h("div", { "class": "dock" });
    if (T.mode === "estudio") {
      if (!checked) {
        dock.appendChild(h("button", { "class": "btn quiet", type: "button", onclick: function () { check(q, -1); } }, "Dejar en blanco"));
        dock.appendChild(h("button", { "class": "btn", type: "button", disabled: sel == null, onclick: function () { check(q, sel); } }, "Corregir"));
      } else {
        dock.appendChild(h("button", { "class": "btn", type: "button", onclick: function () { if (T.i + 1 < n) jump(T.i + 1); else finish(); } }, T.i + 1 < n ? "Siguiente" : "Ver resultados"));
      }
    } else {
      dock.appendChild(h("button", { "class": "btn quiet", type: "button", disabled: T.i === 0, onclick: function () { jump(T.i - 1); } }, "Anterior"));
      dock.appendChild(T.i + 1 < n
        ? h("button", { "class": "btn", type: "button", onclick: function () { jump(T.i + 1); } }, sel == null ? "Siguiente (en blanco)" : "Siguiente")
        : h("button", { "class": "btn", type: "button", onclick: function () { stamp(q); confirmFinish(); } }, "Entregar"));
    }
    s.appendChild(dock);
    main.appendChild(s); wrap.appendChild(main);
    timerInt = setInterval(function () { var el = document.getElementById("qtimer"); if (el && TEST && !TEST.paused) el.textContent = clock(qElapsed(q)); }, 1000);
    return wrap;
  }
  function ctx() { return { mode: TEST.mode, session: TEST.session, reason: null }; }
  function check(q, choice) {
    stamp(q);
    TEST.ans[q.id] = choice; TEST.checked[q.id] = true;
    var c = ctx(); c.reason = TEST.reasons[q.id];
    record(q, choice, TEST.times[q.id], TEST.changed[q.id], c);
    render();
  }
  function confirmExit(then) {
    sheet(function (close) {
      return [h("h2", null, "¿Salir del test?"),
        h("p", { "class": "muted" }, TEST.mode === "examen" ? "Si sales ahora no se corregirá lo que has marcado." : "Lo que ya has corregido queda guardado en tu progreso."),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: close }, "Seguir con el test"),
          h("button", { "class": "btn quiet", type: "button", onclick: function () {
            close();
            track("test_abandoned", { mode: TEST.mode, session: TEST.session, n: TEST.ids.length, answered: Object.keys(TEST.checked).length, at: TEST.i });
            TEST = null; then();
          } }, "Salir"))];
    });
  }
  function confirmFinish() {
    var blanks = TEST.ids.filter(function (id) { return TEST.ans[id] == null; }).length;
    sheet(function (close) {
      return [h("h2", null, isCheckpoint() ? "¿Entregar?" : "¿Terminar el examen?"),
        h("p", { "class": "muted" }, blanks ? "Tienes " + blanks + " pregunta" + (blanks === 1 ? "" : "s") + " en blanco. En blanco no restan." : "Has respondido todas las preguntas."),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () { close(); finish(); } }, "Entregar y corregir"),
          h("button", { "class": "btn quiet", type: "button", onclick: close }, "Seguir"))];
    });
  }
  function finish() {
    var T = TEST;
    if (T.mode === "examen") {
      T.ids.forEach(function (id) {
        var c = T.ans[id]; T.checked[id] = true;
        record(QMAP[id], c == null ? -1 : c, T.times[id] || 0, T.changed[id], { mode: "examen", session: T.session, reason: null });
      });
    }
    var a = 0, f = 0, b = 0, byArea = {};
    T.ids.forEach(function (id) {
      var q = QMAP[id], c = T.ans[id];
      var r = c == null || c < 0 ? "b" : c === q.k ? "a" : "f";
      if (r === "a") a++; else if (r === "f") f++; else b++;
      var x = byArea[q.area] || (byArea[q.area] = { a: 0, n: 0 }); x.n++; if (r === "a") x.a++;
    });
    var n = T.ids.length, nt = Math.max(0, (a - f / 3)) / n * 10;
    T.result = { a: a, f: f, b: b, n: n, nota: nt, byArea: byArea, secs: Math.round((Date.now() - T.start) / 1000) };
    S.history.push({ ts: Date.now(), mode: T.mode, session: T.session, n: n, a: a, f: f, b: b, nota: Math.round(nt * 100) / 100 });
    if (S.history.length > 200) S.history = S.history.slice(-200);

    if (T.session === "diagnostic") {
      S.exp.pre = { ts: Date.now(), form: S.exp.preForm, a: a, f: f, b: b, score: nt };
      S.practiceSincePre = 0;
      track("checkpoint_completed", { kind: "pre", form: S.exp.preForm, a: a, f: f, b: b, score: nt });
    } else if (T.session === "control") {
      S.exp.post = { ts: Date.now(), form: postForm(), a: a, f: f, b: b, score: nt };
      track("checkpoint_completed", { kind: "post", form: postForm(), a: a, f: f, b: b, score: nt,
        practice_answers: S.practiceSincePre, days_since_pre: Math.round((Date.now() - S.exp.pre.ts) / DAY * 10) / 10, pre_score: S.exp.pre.score });
    }
    snapshot(); persist();
    track("test_completed", { mode: T.mode, session: T.session, n: n, a: a, f: f, b: b, nota: nt, secs: T.result.secs });
    go("results");
    var done = S.history.filter(function (x) { return x.session !== "review" && x.session !== "diagnostic"; }).length;
    if (done === 2 && !S.npsDone && S.consent === "yes") setTimeout(openNps, 900);
  }

  // ── Explanation (+ esquema) ─────────────────────────────────
  function esquemaFor(q) { for (var i = 0; i < q.concepts.length; i++) { var e = BANK.esquemaFor[q.concepts[i]]; if (e && ESQ[e]) return e; } return null; }
  function sourceLabel(q) {
    if (/^\d/.test(String(q.sourceRef || "")) && /^\d/.test(String(q.art || ""))) {
      return "Art. " + q.art + " de la Constitución en el BOE ↗";
    }
    if (q.sourceRef === "df") return "Disposición final de la Constitución en el BOE ↗";
    return "Texto consolidado de la Constitución en el BOE ↗";
  }
  function explanation(q, sel) {
    var wrongs = h("ul", { "class": "whynot" });
    q.o.forEach(function (_, i) { if (i !== q.k) wrongs.appendChild(h("li", null, h("span", { "class": "l" }, LETTERS[i] + ")"), h("span", null, q.w[i]))); });
    var rated = S.rated[q.id];
    function thumb(v, label) {
      return h("button", { "class": "thumb", type: "button", "aria-pressed": rated === v ? "true" : "false", onclick: function () {
        S.rated[q.id] = v; persist();
        track("explanation_rated", { qid: q.id, helpful: v === "up" });
        render();
      } }, label);
    }
    var esq = esquemaFor(q);
    var misNote = sel != null && sel >= 0 && sel !== q.k && q.mis[sel] && BANK.misconceptions[q.mis[sel]]
      ? h("div", { "class": "trap" }, h("b", null, "Confusión detectada: "), BANK.misconceptions[q.mis[sel]].name + "." + (adaptive() ? " Te propondremos más preguntas sobre esto." : "")) : null;
    return h("div", { "class": "explain" },
      h("p", null, h("b", null, "Correcta: " + LETTERS[q.k] + ") " + q.o[q.k])),
      h("p", null, q.ex),
      h("div", null, h("div", { "class": "small muted", style: "margin-bottom:6px" }, "Por qué no las demás"), wrongs),
      misNote,
      q.trap ? h("div", { "class": "trap" }, h("b", null, "Trampa típica: "), q.trap) : null,
      esq ? h("details", { "class": "esqbox", ontoggle: function (e) { if (e.target.open) track("esquema_viewed", { esquema: esq, qid: q.id, from: "explanation" }); } },
        h("summary", null, "Ver esquema: " + ESQ[esq].title), h("p", { "class": "swipehint" }, "Desliza la tabla → para ver todas las columnas"), h("div", { "class": "esqwrap", html: ESQ[esq].html })) : null,
      h("div", { "class": "src" },
        h("a", { href: q.url, target: "_blank", rel: "noopener", onclick: function () { track("boe_link_clicked", { qid: q.id }); } }, sourceLabel(q)),
        h("button", { "class": "linkbtn", type: "button", onclick: function () { openReport(q); } }, S.reported[q.id] ? "Impugnada ✓" : "Impugnar esta pregunta")),
      h("div", { "class": "helpful" }, h("span", null, "¿Te ha servido la explicación?"), thumb("up", "👍 Sí"), thumb("down", "👎 No")));
  }
  function openEsquema(id, from) {
    track("esquema_viewed", { esquema: id, from: from });
    sheet(function (close) { return [h("h2", null, ESQ[id].title), h("p", { "class": "swipehint" }, "Desliza la tabla → para ver todas las columnas"), h("div", { "class": "esqwrap", html: ESQ[id].html }), h("button", { "class": "btn", type: "button", onclick: close }, "Cerrar")]; });
  }

  // ── Results (Maxwell-style review) ──────────────────────────
  function viewResults() {
    var T = TEST, R = T && T.result;
    if (!R) { VIEW = "home"; return viewHome(); }
    var s = h("section", { "class": "view stack-lg" });
    var head = h("div", { "class": "score" },
      h("span", { "class": "eyebrow" }, T.title),
      h("div", { "class": "big" }, fmt(R.nota), h("small", null, " / 10")),
      h("span", { "class": "small muted" }, "Nota con penalización: (aciertos − fallos ÷ 3) ÷ preguntas × 10 · Tiempo: " + Math.floor(R.secs / 60) + " min " + (R.secs % 60) + " s"));
    s.appendChild(head);
    s.appendChild(h("div", { "class": "tally four" },
      h("div", { "class": "a" }, h("b", null, String(R.a)), "correctas"),
      h("div", { "class": "f" }, h("b", null, String(R.f)), "incorrectas"),
      h("div", { "class": "b" }, h("b", null, String(R.b)), "en blanco"),
      h("div", { "class": "b" }, h("b", null, String(R.n)), "total")));

    if (T.session === "control" && S.exp.pre) {
      var diff = R.nota - S.exp.pre.score;
      s.appendChild(h("div", { "class": "card accent stack" },
        h("span", { "class": "eyebrow" }, "Tu progreso"),
        h("p", { style: "margin:0;font-weight:600" }, "Diagnóstico: " + fmt(S.exp.pre.score) + " → Control: " + fmt(R.nota) + " (" + (diff >= 0 ? "+" : "") + fmt(diff) + ")"),
        h("p", { "class": "small muted", style: "margin:0" }, "Son preguntas distintas pero de nivel parecido. Gracias por ayudarnos a medir si Tesón te ayuda a aprender.")));
    }
    if (T.session === "diagnostic") {
      s.appendChild(h("div", { "class": "card accent stack" },
        h("span", { "class": "eyebrow" }, "Diagnóstico hecho"),
        h("p", { style: "margin:0" }, adaptive() ? "Ya sabemos por dónde empezar. Tu práctica recomendada se adaptará a lo que te ha costado más." : "Ya sabemos de dónde partes. Sigue practicando y en unas semanas te propondremos un control de progreso."),
        h("div", { "class": "row" }, h("button", { "class": "btn", type: "button", onclick: function () { startPractice(20, null); } }, adaptive() ? "Empezar mi práctica recomendada" : "Empezar a practicar"))));
    }

    // Two actions, like "Review Full Quiz" / "Practice Weak Areas"
    var weakAreas = Object.keys(R.byArea).filter(function (k) { var x = R.byArea[k]; return x.n >= 1 && x.a / x.n < 0.6; });
    s.appendChild(h("div", { "class": "actions2" },
      h("button", { "class": "card actcard", type: "button", onclick: function () { var r = document.getElementById("review"); Array.prototype.forEach.call(r.querySelectorAll("details"), function (d) { d.open = true; }); r.scrollIntoView(); } },
        h("b", null, "Repasar el test completo"), h("span", { "class": "small muted" }, "Recorre las preguntas y sus explicaciones")),
      h("button", { "class": "card actcard", type: "button", onclick: function () { startPractice(10, weakAreas.length === 1 ? weakAreas[0] : null); } },
        h("b", null, adaptive() ? "Practicar tus puntos débiles" : "Seguir practicando"), h("span", { "class": "small muted" }, adaptive() ? "10 preguntas sobre lo que más te ha costado" : "10 preguntas más del tema"))));

    // Performance analysis
    var strong = [], improve = [];
    Object.keys(R.byArea).forEach(function (k) { var x = R.byArea[k]; (x.a / x.n >= 0.8 ? strong : x.a / x.n < 0.6 ? improve : []).push(BANK.areas[k] + " (" + x.a + "/" + x.n + ")"); });
    s.appendChild(h("div", { "class": "perf" },
      h("div", { "class": "card stack" }, h("h3", null, "Fortalezas"), strong.length ? h("ul", { "class": "plain" }, strong.map(function (t) { return h("li", null, t); })) : h("p", { "class": "small muted", style: "margin:0" }, "Sigue practicando para consolidar tus fortalezas.")),
      h("div", { "class": "card stack" }, h("h3", null, "Áreas a mejorar"), improve.length ? h("ul", { "class": "plain" }, improve.map(function (t) { return h("li", null, t); })) : h("p", { "class": "small muted", style: "margin:0" }, "Nada por debajo del 60 % en este test."))));

    // Question table
    var rv = h("div", { "class": "review", id: "review" });
    rv.appendChild(h("div", { "class": "rvhead small muted" }, h("span", null, "Código"), h("span", null, "Pregunta"), h("span", null, "Resultado")));
    T.ids.forEach(function (id) {
      var q = QMAP[id], c = T.ans[id];
      var r = c == null || c < 0 ? "blank" : c === q.k ? "ok" : "bad";
      rv.appendChild(h("details", { "class": "rv" },
        h("summary", null, h("span", { "class": "code" }, q.id), h("span", null, q.q),
          h("span", { "class": "res " + r }, r === "ok" ? "Correcta" : r === "bad" ? "Incorrecta" : "En blanco")),
        h("div", { "class": "body" },
          h("p", { "class": "small", style: "margin:0" }, r === "blank" ? "La dejaste en blanco." : "Tu respuesta: " + LETTERS[c] + ") " + q.o[c]),
          explanation(q, c))));
    });
    s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Preguntas"), rv));

    s.appendChild(h("div", { "class": "empty" },
      h("b", null, "¿Qué te ha parecido?"),
      h("span", { "class": "small" }, "Estamos construyendo Tesón con los opositores. Dos líneas tuyas nos ayudan muchísimo."),
      h("button", { "class": "btn ghost", type: "button", onclick: openFeedback }, "Dar mi opinión")));
    return s;
  }

  // ── Fallos & Progreso ───────────────────────────────────────
  function fallos() { return BANK.questions.filter(function (q) { return S.stats[q.id] && S.stats[q.id].box > 0 && !(controlHeld() && CONTROL.indexOf(q.id) !== -1); }); }
  function dueFallos() { var now = Date.now(); return fallos().filter(function (q) { return S.stats[q.id].due <= now; }); }
  function totals() { var t = { seen: 0, c: 0 }; for (var id in S.stats) { t.seen += S.stats[id].seen; t.c += S.stats[id].c; } return t; }

  function viewFallos() {
    var all = fallos(), due = dueFallos();
    var s = h("section", { "class": "view stack-lg" });
    s.appendChild(h("div", { "class": "stack" }, h("h1", null, "Tus fallos"),
      h("p", { "class": "lede" }, "Cada pregunta que fallas vuelve al día siguiente, y luego a los 3, 7 y 21 días si la aciertas. Cuando la aciertas en todos los repasos, sale de la lista.")));
    if (!all.length) { s.appendChild(h("div", { "class": "empty" }, h("span", null, "Aún no tienes fallos guardados."), h("button", { "class": "btn", type: "button", onclick: function () { startPractice(20, null); } }, "Practicar"))); return s; }
    s.appendChild(h("div", { "class": "row" },
      h("button", { "class": "btn", type: "button", disabled: !due.length, onclick: function () { startReview(due); } }, due.length ? "Repasar los de hoy (" + due.length + ")" : "Hoy no toca ningún repaso"),
      h("button", { "class": "btn ghost", type: "button", onclick: function () { startReview(all); } }, "Repasar todos (" + all.length + ")")));
    var list = h("div", { "class": "review" });
    all.sort(function (a, b) { return S.stats[a.id].due - S.stats[b.id].due; }).forEach(function (q) {
      var st = S.stats[q.id], days = Math.round((st.due - today()) / DAY);
      list.appendChild(h("details", { "class": "rv" },
        h("summary", null, h("span", { "class": "code" }, q.id), h("span", null, q.q), h("span", { "class": "res bad" }, days <= 0 ? "Hoy" : "En " + days + " d")),
        h("div", { "class": "body" }, explanation(q, null))));
    });
    s.appendChild(list);
    return s;
  }

  function viewProgreso() {
    var t = totals();
    var s = h("section", { "class": "view stack-lg" });
    s.appendChild(h("h1", null, "Tu progreso"));
    s.appendChild(h("div", { "class": "stats" },
      h("div", { "class": "stat" }, h("b", null, fmt(t.seen, 0)), h("span", null, "respuestas")),
      h("div", { "class": "stat" }, h("b", null, pct(t.c, t.seen) + " %"), h("span", null, "aciertos")),
      h("div", { "class": "stat" }, h("b", null, String(S.days.length)), h("span", null, "días practicando"))));

    // Concept detail table
    var tbl = h("div", { "class": "ctable" });
    tbl.appendChild(h("div", { "class": "crow head" }, h("span", null, "Concepto"), h("span", null, "Dominio"), h("span", null, "Próximo repaso")));
    AREAS.forEach(function (a) {
      tbl.appendChild(h("div", { "class": "crow area" }, h("span", null, BANK.areas[a])));
      conceptsOf(a).forEach(function (c) {
        var m = mastery(c), x = S.cs[c];
        var dd = x && x.n ? Math.round((x.due - today()) / DAY) : null;
        tbl.appendChild(h("div", { "class": "crow" },
          h("span", null, BANK.concepts[c].name, h("small", { "class": "muted" }, " · art. " + BANK.concepts[c].arts)),
          h("span", null, m == null ? "—" : h("span", { "class": "pill " + (m < WEAK ? "warn" : "on") }, Math.round(m * 100) + " %")),
          h("span", { "class": "small muted" }, dd == null ? "Nuevo" : dd <= 0 ? "Hoy" : "En " + dd + " d")));
      });
    });
    s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Constitución Española (I), concepto a concepto"),
      h("p", { "class": "small muted", style: "margin:0" }, "El dominio da más peso a tus respuestas recientes. Por debajo del 70 % lo tratamos como punto débil."), tbl));

    var mis = activeMis();
    if (mis.length) {
      s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Confusiones frecuentes"),
        h("ul", { "class": "plain" }, mis.map(function (m) { return h("li", null, BANK.misconceptions[m.id].name + " · " + m.hits + " veces en 30 días"); }))));
    }

    if (S.history.length) {
      var hist = h("div", { "class": "review" });
      S.history.slice(-10).reverse().forEach(function (x) {
        var label = { recommended: "Recomendada", area: "Área", mis: "Confusión", custom: "Personalizado", review: "Repaso", diagnostic: "Diagnóstico", control: "Control" }[x.session] || "Test";
        hist.appendChild(h("div", { "class": "tema" },
          h("div", { "class": "t" }, fmt(x.nota) + " / 10"),
          h("span", { "class": "pill" + (x.mode === "examen" ? " warn" : "") }, label),
          h("div", { "class": "d" }, new Date(x.ts).toLocaleDateString("es-ES", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) + " · " + x.a + " aciertos, " + x.f + " fallos, " + x.b + " en blanco")));
      });
      s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Últimos tests"), hist));
    }

    s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Tus datos"),
      h("p", { "class": "small muted", style: "margin:0" }, "Tu progreso se guarda en este navegador. Compartir datos de uso anónimos: " + (S.consent === "yes" ? "activado." : "desactivado.")),
      h("p", { "class": "small muted", style: "margin:0" }, "Identificador para ejercer tus derechos: ", h("code", null, S.uid)),
      h("div", { "class": "row" },
        h("button", { "class": "btn quiet", type: "button", onclick: function () { openConsent(true); } }, "Cambiar preferencia"),
        h("button", { "class": "btn quiet", type: "button", onclick: confirmWipe }, "Borrar mi progreso"))));
    return s;
  }
  function confirmWipe() {
    sheet(function (close) {
      return [h("h2", null, "¿Borrar tu progreso?"), h("p", { "class": "muted" }, "Se borrarán tus respuestas, fallos e historial de este navegador. No se puede deshacer."),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () {
            track("progress_wiped", {});
            var keep = { consent: S.consent, uid: S.uid, exp: S.exp };
            S = fresh(); S.consent = keep.consent; S.uid = keep.uid; S.exp = keep.exp; persist(); close(); go("home"); toast("Progreso borrado.");
          } }, "Sí, borrar"),
          h("button", { "class": "btn quiet", type: "button", onclick: close }, "Cancelar"))];
    });
  }

  // ── Sheets ──────────────────────────────────────────────────
  function openConsent(fromSettings) {
    sheet(function (close) {
      function pick(v) {
        if (v === "no") {
          clearTimeout(flushTimer);
          flushGeneration++;
          if (flushController) flushController.abort();
          flushing = false;
          flushController = null;
          S.queue = S.queue.filter(function (event) { return event.basis === "user_request"; });
          if (S.queue.length) flushTimer = setTimeout(flush, 0);
        }
        S.consent = v; persist(); close();
        if (v === "yes") track("consent_given", { from_settings: !!fromSettings, src: S.src });
        ensureExperiment(); render();
      }
      return [h("h2", null, "Tesón está en beta"),
        h("p", { style: "margin:0" }, "Es gratis y no necesitas registrarte. Para mejorar las preguntas nos ayuda mucho saber cómo se usa la app: qué respondes, cuánto tardas y qué explicaciones te sirven."),
        h("p", { "class": "small muted", style: "margin:0" }, "Se guarda con un identificador aleatorio, sin tu nombre ni tu email, en servidores de la UE. Si aceptas, también podemos mostrarte una de dos formas de elegir las preguntas, para comprobar cuál ayuda más a aprender. Puedes cambiarlo cuando quieras en «Progreso». ",
          h("a", { href: "privacidad.html", target: "_blank", rel: "noopener" }, "Más información")),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () { pick("yes"); } }, "Sí, compartir datos de uso"),
          h("button", { "class": "btn ghost", type: "button", onclick: function () { pick("no"); } }, "No, gracias"))];
    });
  }
  function openOnboarding(then) {
    var P = { exam: null, cuando: null, academia: null, academiaNombre: "", fuente: null };
    sheet(function (close) {
      function group(key, legend, options) {
        var c = h("div", { "class": "chips" });
        options.forEach(function (o) {
          var b = h("button", { "class": "chip", type: "button", "aria-pressed": "false", onclick: function () {
            P[key] = o; Array.prototype.forEach.call(c.children, function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
            if (key === "academia") acad.hidden = o !== "Sí";
          } }, o);
          c.appendChild(b);
        });
        return h("fieldset", null, h("legend", null, legend), c);
      }
      var acad = h("input", { type: "text", id: "ob-acad", placeholder: "¿Cuál? (opcional)", "aria-label": "Nombre de la academia", oninput: function (e) { P.academiaNombre = e.target.value.slice(0, 80); } });
      acad.hidden = true;
      function done(skip) {
        S.profile = skip ? { skipped: true } : P; persist(); close();
        if (!skip) track("onboarding_completed", { exam: P.exam, cuando: P.cuando, academia: P.academia, academia_nombre: P.academiaNombre || null, fuente: P.fuente, src: S.src });
        then();
      }
      return [h("h2", null, "Cuatro preguntas rápidas"),
        h("p", { "class": "small muted", style: "margin:0" }, "Nos ayudan a priorizar qué temas preparar. Todo es opcional."),
        group("exam", "¿Qué oposición preparas?", ["Auxiliar Administrativo del Estado", "Administrativo del Estado", "Justicia", "Policía o Guardia Civil", "Otra"]),
        group("cuando", "¿Cuándo crees que te examinarás?", ["Primera mitad de 2027", "Segunda mitad de 2027", "2028 o más tarde", "No lo sé"]),
        h("div", { "class": "stack", style: "gap:8px" }, group("academia", "¿Preparas con academia o preparador?", ["No", "Sí"]), acad),
        group("fuente", "¿Cómo has conocido Tesón?", ["Telegram", "Reddit", "Instagram o TikTok", "Un foro", "Google", "Me lo recomendaron", "Otro"]),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () { done(false); } }, "Guardar y empezar"),
          h("button", { "class": "btn quiet", type: "button", onclick: function () { done(true); } }, "Saltar"))];
    });
  }
  function openReport(q) {
    sheet(function (close) {
      var reason = null;
      var c = h("div", { "class": "choice" });
      ["La respuesta correcta está mal", "La pregunta es ambigua", "La ley ha cambiado", "Errata o redacción", "Otro"].forEach(function (r, i) {
        c.appendChild(h("label", null, h("input", { type: "radio", name: "reason", id: "rr" + i, onchange: function () { reason = r; send.disabled = !backendOn(); } }), h("span", null, r)));
      });
      var txt = h("textarea", { id: "report-text", placeholder: "Cuéntanos qué está mal y, si puedes, el artículo correcto (opcional)", maxlength: "1000", "aria-label": "Detalle de la impugnación" });
      var send = h("button", { "class": "btn", type: "button", disabled: true, onclick: function () {
        if (!track("question_reported", { qid: q.id, reason: reason, text: txt.value.trim().slice(0, 1000) }, { essential: true })) {
          toast("No se ha enviado: el canal de impugnaciones no está configurado.");
          return;
        }
        S.reported[q.id] = Date.now(); persist(); close(); render();
        toast("Impugnación enviada. Objetivo de respuesta: " + (CFG.reportResponseHours || 72) + " horas.");
      } }, "Enviar impugnación");
      return [h("h2", null, "Impugnar pregunta"), h("p", { "class": "small muted", style: "margin:0" }, q.id + " · " + q.q), c, txt, previewNote(),
        h("div", { "class": "row" }, send, h("button", { "class": "btn quiet", type: "button", onclick: close }, "Cancelar"))];
    });
  }
  function openFeedback() {
    sheet(function (close) {
      var rating = null, c = h("div", { "class": "chips" });
      ["1", "2", "3", "4", "5"].forEach(function (v) {
        var b = h("button", { "class": "chip", type: "button", "aria-pressed": "false", onclick: function () { rating = Number(v); Array.prototype.forEach.call(c.children, function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); }); } }, v);
        c.appendChild(b);
      });
      var txt = h("textarea", { id: "fb-text", placeholder: "¿Qué mejorarías? ¿Qué echas en falta? ¿Qué te sobra?", maxlength: "2000", "aria-label": "Tu opinión" });
      var mail = h("input", { type: "email", id: "fb-mail", placeholder: "Tu email, si quieres que te respondamos (opcional)", "aria-label": "Email opcional" });
      return [h("h2", null, "Tu opinión"), h("fieldset", null, h("legend", null, "¿Qué te parece Tesón hasta ahora? (1 = nada, 5 = mucho)"), c), txt, mail,
        h("p", { "class": "small muted", style: "margin:0" }, "Solo usaremos tu email para responderte."), previewNote(),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", disabled: !backendOn(), onclick: function () {
            if (!rating && !txt.value.trim()) { toast("Escribe algo o elige una puntuación."); return; }
            if (!track("feedback_sent", { rating: rating, text: txt.value.trim().slice(0, 2000), email: mail.value.trim().slice(0, 120) || null, view: VIEW, tests: S.history.length }, { essential: true })) {
              toast("No se ha enviado: el canal de opiniones no está configurado.");
              return;
            }
            close(); toast("¡Gracias! Lo leemos todo.");
          } }, "Enviar"),
          h("button", { "class": "btn quiet", type: "button", onclick: close }, "Cancelar"))];
    });
  }
  function openNps() {
    sheet(function (close) {
      var score = null;
      var c = h("div", { "class": "chips" });
      var sendButton = h("button", { "class": "btn", type: "button", disabled: true, onclick: function () { done(true); } }, "Enviar");
      for (var i = 0; i <= 10; i++) (function (v) {
        var b = h("button", { "class": "chip", type: "button", "aria-pressed": "false", onclick: function () {
          score = v;
          sendButton.disabled = false;
          Array.prototype.forEach.call(c.children, function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        } }, String(v));
        c.appendChild(b);
      })(i);
      var why = h("textarea", { id: "nps-why", placeholder: "¿Por qué? (opcional)", maxlength: "1000", "aria-label": "Motivo" });
      function done(send) {
        S.npsDone = true; persist(); close();
        if (send && score != null) { track("nps_submitted", { score: score, why: why.value.trim().slice(0, 1000), tests: S.history.length }); toast("¡Gracias!"); }
      }
      return [h("h2", null, "Una pregunta rápida"), h("fieldset", null, h("legend", null, "Del 0 al 10, ¿recomendarías Tesón a otro opositor?"), c), why, previewNote(),
        h("div", { "class": "row" },
          sendButton,
          h("button", { "class": "btn quiet", type: "button", onclick: function () { done(false); } }, "Ahora no"))];
    });
  }

  // ── Boot ────────────────────────────────────────────────────
  render();
  if (S.consent === null) openConsent(false);
  else { ensureExperiment(); if (S.consent === "yes") track("session_start", { returning: S.history.length > 0, tests: S.history.length, src: S.src }); }
  flush();
})();
