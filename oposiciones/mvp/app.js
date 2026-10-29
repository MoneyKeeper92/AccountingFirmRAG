/*
 * Tesón MVP · app.js
 * Static single-page app: tests by block, study/exam modes, explanations,
 * spaced review of mistakes, progress, impugnaciones and feedback.
 * Progress lives in localStorage. Pseudonymous usage events go to Supabase
 * (config.js) only if the user accepts; reports and feedback are sent when the
 * user submits them.
 */
(function () {
  "use strict";

  var CFG = window.TESON_CONFIG || {};
  var BANK = window.TESON_BANK;
  var APP_VERSION = "mvp-0.1";
  var LS_KEY = "teson.v1";
  var DAY = 86400000;
  var INTERVALS = [1, 3, 7, 21];
  var LETTERS = "ABCD";
  var SID = rid();

  var QMAP = {};
  BANK.questions.forEach(function (q) { QMAP[q.id] = q; });

  // ── State ───────────────────────────────────────────────────
  function rid() {
    var a = new Uint8Array(12);
    (window.crypto || window.msCrypto).getRandomValues(a);
    return Array.prototype.map.call(a, function (b) { return ("0" + b.toString(16)).slice(-2); }).join("");
  }
  function fresh() {
    return { v: 1, uid: rid(), consent: null, profile: null, src: null, stats: {}, history: [], days: [], queue: [], interest: {}, rated: {}, reported: {}, npsDone: false, created: Date.now() };
  }
  var S = (function () {
    try {
      var s = JSON.parse(window.localStorage.getItem(LS_KEY));
      if (s && s.v === 1) return s;
    } catch (e) {}
    return fresh();
  })();
  function persist() {
    try { window.localStorage.setItem(LS_KEY, JSON.stringify(S)); } catch (e) {}
  }

  // Acquisition source (UTM / referrer), stored once.
  (function () {
    if (S.src) return;
    var src = {};
    try {
      var p = new URLSearchParams(window.location.search);
      ["utm_source", "utm_medium", "utm_campaign", "ref"].forEach(function (k) { if (p.get(k)) src[k] = p.get(k).slice(0, 80); });
      if (document.referrer) src.referrer = document.referrer.split("/").slice(0, 3).join("/");
    } catch (e) {}
    S.src = src;
    persist();
  })();

  // ── Events ──────────────────────────────────────────────────
  function backendOn() { return !!(CFG.supabaseUrl && CFG.supabaseAnonKey); }
  var flushing = false, flushTimer = null;
  function track(type, payload, opts) {
    var submitted = !!(opts && opts.submitted);
    if (!submitted && S.consent !== "yes") return;
    S.queue.push({
      uid: S.consent === "yes" ? S.uid : null,
      session_id: S.consent === "yes" ? SID : null,
      type: type,
      payload: payload || {},
      client_ts: new Date().toISOString(),
      app_version: APP_VERSION
    });
    if (S.queue.length > 500) S.queue = S.queue.slice(-500);
    persist();
    clearTimeout(flushTimer);
    flushTimer = setTimeout(flush, submitted ? 200 : 2500);
  }
  function flush(keepalive) {
    if (!backendOn() || flushing || !S.queue.length) return;
    var batch = S.queue.slice(0, 50);
    flushing = true;
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
        body: JSON.stringify(batch)
      }).then(function (r) {
        if (r.ok) {
          S.queue = S.queue.slice(batch.length);
          persist();
          if (S.queue.length) { clearTimeout(flushTimer); flushTimer = setTimeout(flush, 1000); }
        }
      }).catch(function () {}).then(function () { flushing = false; });
    } catch (e) { flushing = false; }
  }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") flush(true);
  });

  // ── DOM helpers ─────────────────────────────────────────────
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      var v = attrs[k];
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
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
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
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
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.remove(); }, 3500);
  }

  function sheet(build) {
    var scrim = h("div", { "class": "scrim" });
    var box = h("div", { "class": "sheet", role: "dialog", "aria-modal": "true" });
    function close() { scrim.remove(); document.removeEventListener("keydown", onKey); }
    function onKey(e) { if (e.key === "Escape") close(); }
    scrim.addEventListener("click", function (e) { if (e.target === scrim) close(); });
    document.addEventListener("keydown", onKey);
    add(box, build(close));
    scrim.appendChild(box);
    document.body.appendChild(scrim);
    var f = box.querySelector("button, input, textarea"); if (f) f.focus();
    return close;
  }
  function previewNote() {
    return backendOn() ? null : h("p", { "class": "small muted" }, "Vista previa: en esta versión los envíos no se guardan en ningún servidor.");
  }

  // ── Stats & spaced review ───────────────────────────────────
  function stat(id) { return S.stats[id] || (S.stats[id] = { seen: 0, c: 0, w: 0, b: 0, box: 0, due: 0, last: 0 }); }
  function record(q, choice, ms, changed, mode) {
    var res = choice == null || choice < 0 ? "blank" : choice === q.k ? "correct" : "wrong";
    var st = stat(q.id);
    st.seen++; st.last = Date.now();
    if (res === "correct") {
      st.c++;
      if (st.box > 0) {
        st.box++;
        if (st.box > INTERVALS.length) { st.box = 0; st.due = 0; }
        else st.due = today() + INTERVALS[st.box - 1] * DAY;
      }
    } else {
      if (res === "wrong") st.w++; else st.b++;
      st.box = 1; st.due = today() + DAY;
    }
    var d = new Date().toISOString().slice(0, 10);
    if (S.days.indexOf(d) === -1) S.days.push(d);
    persist();
    track("question_answered", { qid: q.id, sub: q.sub, result: res, choice: choice, time_ms: ms, changed: changed || 0, mode: mode });
    return res;
  }
  function fallos() { return BANK.questions.filter(function (q) { return S.stats[q.id] && S.stats[q.id].box > 0; }); }
  function dueFallos() { var now = Date.now(); return fallos().filter(function (q) { return S.stats[q.id].due <= now; }); }
  function totals() {
    var t = { seen: 0, c: 0, w: 0, b: 0, uniq: 0 };
    for (var id in S.stats) { var s = S.stats[id]; t.seen += s.seen; t.c += s.c; t.w += s.w; t.b += s.b; if (s.seen) t.uniq++; }
    return t;
  }
  function nota(a, f, n) { return n ? Math.max(0, (a - f / 3)) / n * 10 : 0; }

  // ── Views ───────────────────────────────────────────────────
  var VIEW = "home";
  var TEST = null;
  var timerInt = null;
  var root = document.getElementById("app");

  function go(v) { VIEW = v; render(); window.scrollTo(0, 0); }

  function render() {
    clearInterval(timerInt);
    root.innerHTML = "";
    root.appendChild(topbar());
    var main = h("main", { "class": "wrap" });
    if (VIEW === "home") main.appendChild(viewHome());
    else if (VIEW === "setup") main.appendChild(viewSetup());
    else if (VIEW === "quiz") main.appendChild(viewQuiz());
    else if (VIEW === "results") main.appendChild(viewResults());
    else if (VIEW === "fallos") main.appendChild(viewFallos());
    else if (VIEW === "progreso") main.appendChild(viewProgreso());
    if (VIEW !== "quiz") main.appendChild(footer());
    root.appendChild(main);
    if (VIEW !== "quiz") root.appendChild(h("button", { "class": "fab", type: "button", onclick: openFeedback }, "Danos tu opinión"));
  }

  function topbar() {
    var nf = fallos().length;
    function nb(v, label) {
      return h("button", { "class": "navbtn", type: "button", "aria-current": VIEW === v ? "page" : null, onclick: function () { if (VIEW === "quiz") return confirmExit(function () { go(v); }); go(v); } }, label);
    }
    return h("header", { "class": "top" }, h("div", { "class": "top-inner" },
      h("button", { "class": "brand", type: "button", onclick: function () { if (VIEW === "quiz") return confirmExit(function () { go("home"); }); go("home"); } }, "tesón"),
      h("span", { "class": "beta" }, "Beta"),
      h("nav", { "aria-label": "Principal" }, nb("home", "Inicio"), nb("fallos", "Fallos" + (nf ? " (" + nf + ")" : "")), nb("progreso", "Progreso"))
    ));
  }

  function footer() {
    return h("footer", { "class": "foot" },
      h("div", null, "Tesón · Oposiciones, pregunta a pregunta. Beta gratuita: preguntas en revisión. Si ves algo raro, impúgnalo."),
      h("div", null, "Legislación: Agencia Estatal Boletín Oficial del Estado (textos consolidados, de carácter informativo). Tesón no está vinculado al INAP ni a ninguna Administración Pública."),
      h("div", { "class": "row" },
        h("a", { href: "privacidad.html", target: "_blank", rel: "noopener" }, "Privacidad"),
        h("a", { href: "aviso-legal.html", target: "_blank", rel: "noopener" }, "Aviso legal"),
        CFG.contactEmail ? h("span", null, CFG.contactEmail) : null)
    );
  }

  // Home
  function viewHome() {
    var t = totals();
    var returning = S.history.length > 0;
    var due = dueFallos().length, nf = fallos().length;
    var s = h("section", { "class": "view stack-lg" });

    if (!returning) {
      s.appendChild(h("div", { "class": "hero" },
        wordmark(),
        h("h1", null, "Tests de oposiciones que te explican la ley."),
        h("p", { "class": "lede" }, "Auxiliar Administrativo del Estado. En cada pregunta te explicamos por qué la correcta lo es, por qué las otras tres no, y te enlazamos el artículo del BOE."),
        h("div", { "class": "row" }, h("button", { "class": "btn", type: "button", onclick: function () { startSetup("CE1"); } }, "Empezar un test")),
        h("p", { "class": "small muted" }, "Gratis durante la beta. Sin registro.")
      ));
    } else {
      s.appendChild(h("div", { "class": "stack" },
        h("h1", null, "Hola de nuevo."),
        h("div", { "class": "stats" },
          h("div", { "class": "stat" }, h("b", null, fmt(t.seen, 0)), h("span", null, "respuestas")),
          h("div", { "class": "stat" }, h("b", null, pct(t.c, t.seen) + " %"), h("span", null, "aciertos")),
          h("div", { "class": "stat" }, h("b", null, String(nf)), h("span", null, "fallos por repasar"))),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () { startSetup("CE1"); } }, "Nuevo test"),
          nf ? h("button", { "class": "btn ghost", type: "button", onclick: function () { startReview(due ? dueFallos() : fallos()); } }, due ? "Repasar fallos de hoy (" + due + ")" : "Repasar fallos (" + nf + ")") : null)
      ));
    }

    var list = h("div", { "class": "temas" });
    BANK.temas.forEach(function (tm) {
      if (tm.activo) {
        var qs = BANK.questions.filter(function (q) { return q.tema === tm.id; });
        var seen = qs.filter(function (q) { return S.stats[q.id] && S.stats[q.id].seen; }).length;
        list.appendChild(h("div", { "class": "tema on" },
          h("div", { "class": "t" }, tm.nombre),
          h("button", { "class": "btn", type: "button", onclick: function () { startSetup(tm.id); } }, "Practicar"),
          h("div", { "class": "d" }, tm.detalle),
          h("div", { "class": "meta" }, h("span", { "class": "pill on" }, qs.length + " preguntas"), h("span", null, "Vistas " + seen + "/" + qs.length), h("span", { "class": "meter", "aria-hidden": "true" }, h("i", { style: "width:" + pct(seen, qs.length) + "%" })))
        ));
      } else {
        var on = !!S.interest[tm.id];
        list.appendChild(h("div", { "class": "tema" },
          h("div", { "class": "t" }, tm.nombre),
          h("button", { "class": "chip", type: "button", "aria-pressed": on ? "true" : "false", onclick: function () {
            S.interest[tm.id] = !on; persist();
            track("tema_interest", { tema: tm.id, on: !on }, { submitted: true });
            if (!on) toast("Anotado. Priorizamos los temas que más pedís.");
            render();
          } }, on ? "✓ Me interesa" : "Me interesa"),
          h("div", { "class": "d" }, tm.detalle),
          h("div", { "class": "meta" }, h("span", { "class": "pill warn" }, "En preparación"))
        ));
      }
    });
    s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Temas"), list));

    s.appendChild(h("div", { "class": "stack" },
      h("h2", null, "Cómo funciona"),
      h("div", { "class": "choice" },
        info("Practica por bloques", "Elige las partes del tema y el número de preguntas. En modo examen se aplica la penalización oficial: cada fallo resta un tercio de acierto."),
        info("Entiende cada fallo", "La explicación cubre las cuatro opciones y enlaza el artículo exacto en el BOE."),
        info("Repasa antes de olvidar", "Tus fallos vuelven a los 1, 3, 7 y 21 días hasta que los dominas.")
      )));
    return s;
  }
  function info(t, d) { return h("label", { "class": "info", style: "grid-template-columns:1fr;cursor:default" }, h("span", null, h("b", null, t), h("small", null, d))); }

  // Setup
  var SETUP = null;
  function startSetup(tema) {
    SETUP = { tema: tema, subs: Object.keys(BANK.subs), n: 20, mode: "estudio", pool: "todas" };
    if (!S.profile && !S.history.length) return openOnboarding(function () { go("setup"); });
    go("setup");
  }
  function poolFor(st) {
    return BANK.questions.filter(function (q) {
      if (q.tema !== st.tema || st.subs.indexOf(q.sub) === -1) return false;
      var s = S.stats[q.id];
      if (st.pool === "nuevas") return !s || !s.seen;
      if (st.pool === "falladas") return s && s.box > 0;
      return true;
    });
  }
  function viewSetup() {
    var st = SETUP;
    var tm = BANK.temas.filter(function (t) { return t.id === st.tema; })[0];
    var pool = poolFor(st);
    var n = st.n === "all" ? pool.length : Math.min(st.n, pool.length);
    var s = h("section", { "class": "view stack-lg" });
    s.appendChild(h("div", { "class": "stack" }, h("span", { "class": "eyebrow" }, "Nuevo test"), h("h1", null, tm.nombre)));

    var allOn = st.subs.length === Object.keys(BANK.subs).length;
    var chips = h("div", { "class": "chips" },
      h("button", { "class": "chip", type: "button", "aria-pressed": allOn ? "true" : "false", onclick: function () { st.subs = allOn ? [] : Object.keys(BANK.subs); render(); } }, "Todo el tema"));
    Object.keys(BANK.subs).forEach(function (k) {
      var on = st.subs.indexOf(k) !== -1;
      chips.appendChild(h("button", { "class": "chip", type: "button", "aria-pressed": on ? "true" : "false", onclick: function () {
        if (on) st.subs = st.subs.filter(function (x) { return x !== k; }); else st.subs = st.subs.concat(k);
        render();
      } }, BANK.subs[k]));
    });
    s.appendChild(h("fieldset", null, h("legend", null, "Partes del tema"), chips));

    var nChips = h("div", { "class": "chips" });
    [10, 20, 30, "all"].forEach(function (v) {
      nChips.appendChild(h("button", { "class": "chip", type: "button", "aria-pressed": st.n === v ? "true" : "false", onclick: function () { st.n = v; render(); } }, v === "all" ? "Todas" : String(v)));
    });
    s.appendChild(h("fieldset", null, h("legend", null, "Número de preguntas"), nChips));

    var pChips = h("div", { "class": "chips" });
    [["todas", "Todas"], ["nuevas", "Solo las que no he visto"], ["falladas", "Solo las que he fallado"]].forEach(function (p) {
      pChips.appendChild(h("button", { "class": "chip", type: "button", "aria-pressed": st.pool === p[0] ? "true" : "false", onclick: function () { st.pool = p[0]; render(); } }, p[1]));
    });
    s.appendChild(h("fieldset", null, h("legend", null, "Qué preguntas"), pChips));

    function modeOpt(v, t, d) {
      return h("label", null,
        h("input", { type: "radio", name: "mode", value: v, checked: st.mode === v, onchange: function () { st.mode = v; } }),
        h("span", null, h("b", null, t), h("small", null, d)));
    }
    s.appendChild(h("fieldset", null, h("legend", null, "Modo"), h("div", { "class": "choice" },
      modeOpt("estudio", "Estudio", "Corriges cada pregunta al momento y ves la explicación."),
      modeOpt("examen", "Examen", "Corrección al final, con cronómetro y penalización (−1/3 por fallo).")
    )));

    s.appendChild(h("div", { "class": "dock" },
      h("button", { "class": "btn", type: "button", disabled: n === 0, onclick: function () {
        var ids = shuffle(pool).slice(0, n).map(function (q) { return q.id; });
        startTest(ids, st.mode, false);
      } }, n === 0 ? "No hay preguntas con estos filtros" : "Empezar · " + n + " preguntas")));
    return s;
  }

  // Quiz
  function startTest(ids, mode, review) {
    TEST = { ids: ids, mode: mode, review: review, i: 0, ans: {}, checked: {}, times: {}, changed: {}, start: Date.now(), qstart: Date.now() };
    track("test_started", { mode: mode, review: review, n: ids.length, subs: SETUP && !review ? SETUP.subs : null, pool: SETUP && !review ? SETUP.pool : null });
    go("quiz");
  }
  function startReview(list) {
    if (!list.length) return;
    startTest(shuffle(list).slice(0, 30).map(function (q) { return q.id; }), "estudio", true);
  }
  function confirmExit(then) {
    sheet(function (close) {
      var answered = Object.keys(TEST.checked).length + (TEST.mode === "examen" ? Object.keys(TEST.ans).length : 0);
      return [
        h("h2", null, "¿Salir del test?"),
        h("p", { "class": "muted" }, TEST.mode === "examen" ? "En modo examen, si sales ahora no se corregirá lo que has marcado." : "Lo que ya has corregido queda guardado en tu progreso."),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () { close(); } }, "Seguir con el test"),
          h("button", { "class": "btn quiet", type: "button", onclick: function () {
            close();
            track("test_abandoned", { mode: TEST.mode, review: TEST.review, n: TEST.ids.length, answered: answered, at: TEST.i });
            TEST = null; then();
          } }, "Salir"))
      ];
    });
  }
  function elapsed() {
    var s = Math.floor((Date.now() - TEST.start) / 1000);
    return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2);
  }

  function viewQuiz() {
    var T = TEST, q = QMAP[T.ids[T.i]], n = T.ids.length;
    var checked = !!T.checked[q.id];
    var sel = T.ans[q.id];
    var s = h("section", { "class": "view stack" });

    var timer = T.mode === "examen" ? h("span", { id: "timer" }, elapsed()) : null;
    s.appendChild(h("div", { "class": "qhead" },
      h("span", null, (T.review ? "Repaso · " : T.mode === "examen" ? "Examen · " : "") + "Pregunta " + (T.i + 1) + " de " + n),
      h("span", { "class": "grow" }),
      timer,
      T.mode === "examen" ? h("button", { "class": "linkbtn", type: "button", onclick: confirmFinish }, "Terminar") : null));
    s.appendChild(h("div", { "class": "progress", "aria-hidden": "true" }, h("i", { style: "width:" + pct(T.i + (checked ? 1 : 0), n) + "%" })));
    s.appendChild(h("div", { "class": "small muted" }, BANK.subs[q.sub]));
    s.appendChild(h("p", { "class": "stem" }, q.q));

    var opts = h("div", { "class": "opts", role: "group", "aria-label": "Opciones" });
    q.o.forEach(function (text, i) {
      var cls = "opt";
      if (checked) { if (i === q.k) cls += " right"; else if (i === sel) cls += " wrong"; }
      else if (sel === i) cls += " sel";
      opts.appendChild(h("button", { "class": cls, type: "button", disabled: checked, "aria-pressed": !checked && sel === i ? "true" : "false", onclick: function () {
        if (T.ans[q.id] != null && T.ans[q.id] !== i && T.ans[q.id] >= 0) T.changed[q.id] = (T.changed[q.id] || 0) + 1;
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
        dock.appendChild(h("button", { "class": "btn", type: "button", onclick: next }, T.i + 1 < n ? "Siguiente" : "Ver resultados"));
      }
    } else {
      dock.appendChild(h("button", { "class": "btn quiet", type: "button", disabled: T.i === 0, onclick: function () { stamp(q); T.i--; T.qstart = Date.now(); render(); } }, "Anterior"));
      dock.appendChild(T.i + 1 < n
        ? h("button", { "class": "btn", type: "button", onclick: function () { stamp(q); T.i++; T.qstart = Date.now(); render(); window.scrollTo(0, 0); } }, sel == null ? "Siguiente (en blanco)" : "Siguiente")
        : h("button", { "class": "btn", type: "button", onclick: function () { stamp(q); confirmFinish(); } }, "Terminar test"));
    }
    s.appendChild(dock);

    if (timer) timerInt = setInterval(function () { var el = document.getElementById("timer"); if (el) el.textContent = elapsed(); }, 1000);
    return s;
  }
  function stamp(q) { TEST.times[q.id] = (TEST.times[q.id] || 0) + (Date.now() - TEST.qstart); }
  function check(q, choice) {
    stamp(q);
    TEST.ans[q.id] = choice;
    TEST.checked[q.id] = true;
    record(q, choice, TEST.times[q.id], TEST.changed[q.id], TEST.review ? "repaso" : "estudio");
    render();
  }
  function next() {
    if (TEST.i + 1 < TEST.ids.length) { TEST.i++; TEST.qstart = Date.now(); render(); window.scrollTo(0, 0); }
    else finish();
  }
  function confirmFinish() {
    var blanks = TEST.ids.filter(function (id) { return TEST.ans[id] == null; }).length;
    sheet(function (close) {
      return [
        h("h2", null, "¿Terminar el examen?"),
        h("p", { "class": "muted" }, blanks ? "Tienes " + blanks + " pregunta" + (blanks === 1 ? "" : "s") + " en blanco. En blanco no restan." : "Has respondido todas las preguntas."),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () { close(); finish(); } }, "Terminar y corregir"),
          h("button", { "class": "btn quiet", type: "button", onclick: close }, "Seguir"))
      ];
    });
  }
  function finish() {
    var T = TEST;
    if (T.mode === "examen") {
      T.ids.forEach(function (id) {
        var c = T.ans[id];
        T.checked[id] = true;
        record(QMAP[id], c == null ? -1 : c, T.times[id] || 0, T.changed[id], "examen");
      });
    }
    var a = 0, f = 0, b = 0, bySub = {};
    T.ids.forEach(function (id) {
      var q = QMAP[id], c = T.ans[id];
      var r = c == null || c < 0 ? "b" : c === q.k ? "a" : "f";
      if (r === "a") a++; else if (r === "f") f++; else b++;
      var x = bySub[q.sub] || (bySub[q.sub] = { a: 0, n: 0 }); x.n++; if (r === "a") x.a++;
    });
    var n = T.ids.length;
    T.result = { a: a, f: f, b: b, n: n, nota: nota(a, f, n), bySub: bySub, secs: Math.round((Date.now() - T.start) / 1000) };
    S.history.push({ ts: Date.now(), mode: T.mode, review: T.review, n: n, a: a, f: f, b: b, nota: Math.round(T.result.nota * 100) / 100 });
    if (S.history.length > 200) S.history = S.history.slice(-200);
    persist();
    track("test_completed", { mode: T.mode, review: T.review, n: n, a: a, f: f, b: b, nota: T.result.nota, secs: T.result.secs });
    go("results");
    var done = S.history.filter(function (x) { return !x.review; }).length;
    if (done === 2 && !S.npsDone) setTimeout(openNps, 900);
  }

  // Explanation block
  function explanation(q, sel) {
    var wrongs = h("ul", { "class": "whynot" });
    q.o.forEach(function (_, i) {
      if (i === q.k) return;
      wrongs.appendChild(h("li", null, h("span", { "class": "l" }, LETTERS[i] + ")"), h("span", null, q.w[i])));
    });
    var rated = S.rated[q.id];
    function thumb(v, label) {
      return h("button", { "class": "thumb", type: "button", "aria-pressed": rated === v ? "true" : "false", onclick: function () {
        S.rated[q.id] = v; persist();
        track("explanation_rated", { qid: q.id, helpful: v === "up" }, { submitted: true });
        render();
      } }, label);
    }
    return h("div", { "class": "explain" },
      h("p", null, h("b", null, "Correcta: " + LETTERS[q.k] + ") " + q.o[q.k])),
      h("p", null, q.ex),
      h("div", null, h("div", { "class": "small muted", style: "margin-bottom:6px" }, "Por qué no las demás"), wrongs),
      q.trap ? h("div", { "class": "trap" }, h("b", null, "Trampa típica: "), q.trap) : null,
      h("div", { "class": "src" },
        h("a", { href: q.url, target: "_blank", rel: "noopener", onclick: function () { track("boe_link_clicked", { qid: q.id }); } }, "Art. " + q.art + " de la Constitución en el BOE ↗"),
        h("button", { "class": "linkbtn", type: "button", onclick: function () { openReport(q); } }, S.reported[q.id] ? "Impugnada ✓" : "Impugnar esta pregunta")),
      h("div", { "class": "helpful" }, h("span", null, "¿Te ha servido la explicación?"), thumb("up", "👍 Sí"), thumb("down", "👎 No"))
    );
  }

  // Results
  function viewResults() {
    var T = TEST, R = T && T.result;
    if (!R) { VIEW = "home"; return viewHome(); }
    var s = h("section", { "class": "view stack-lg" });
    s.appendChild(h("div", { "class": "score" },
      h("span", { "class": "eyebrow" }, T.review ? "Repaso terminado" : "Resultado"),
      h("div", { "class": "big" }, fmt(R.nota), h("small", null, " / 10")),
      h("span", { "class": "small muted" }, "Nota con penalización: (aciertos − fallos ÷ 3) ÷ preguntas × 10. Tiempo: " + Math.floor(R.secs / 60) + " min " + (R.secs % 60) + " s.")));
    s.appendChild(h("div", { "class": "tally" },
      h("div", { "class": "a" }, h("b", null, String(R.a)), "aciertos"),
      h("div", { "class": "f" }, h("b", null, String(R.f)), "fallos"),
      h("div", { "class": "b" }, h("b", null, String(R.b)), "en blanco")));

    var bars = h("div", { "class": "bars" });
    Object.keys(R.bySub).forEach(function (k) {
      var x = R.bySub[k];
      bars.appendChild(h("div", { "class": "bar" }, h("span", null, BANK.subs[k]), h("span", null, x.a + "/" + x.n),
        h("span", { "class": "meter", "aria-hidden": "true" }, h("i", { style: "width:" + pct(x.a, x.n) + "%" }))));
    });
    s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Por partes del tema"), bars));

    var nf = fallos().length;
    s.appendChild(h("div", { "class": "row" },
      h("button", { "class": "btn", type: "button", onclick: function () { startSetup(SETUP ? SETUP.tema : "CE1"); } }, "Otro test"),
      nf ? h("button", { "class": "btn ghost", type: "button", onclick: function () { startReview(fallos()); } }, "Repasar mis fallos (" + nf + ")") : null));

    var rv = h("div", { "class": "review" });
    T.ids.forEach(function (id, idx) {
      var q = QMAP[id], c = T.ans[id];
      var r = c == null || c < 0 ? "blank" : c === q.k ? "ok" : "bad";
      var color = r === "ok" ? "var(--ok)" : r === "bad" ? "var(--bad)" : "var(--blank)";
      rv.appendChild(h("details", { "class": "rv" },
        h("summary", null, h("span", { "class": "dot", style: "background:" + color }), h("span", null, (idx + 1) + ". " + q.q)),
        h("div", { "class": "body" },
          h("p", { "class": "small", style: "margin:0" }, r === "blank" ? "La dejaste en blanco." : "Tu respuesta: " + LETTERS[c] + ") " + q.o[c]),
          explanation(q, c))));
    });
    s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Revisa las preguntas"), rv));

    s.appendChild(h("div", { "class": "empty" },
      h("b", null, "¿Qué te ha parecido?"),
      h("span", { "class": "small" }, "Estamos construyendo Tesón con los opositores. Dos líneas tuyas nos ayudan muchísimo."),
      h("button", { "class": "btn ghost", type: "button", onclick: openFeedback }, "Dar mi opinión")));
    return s;
  }

  // Fallos
  function viewFallos() {
    var all = fallos(), due = dueFallos();
    var s = h("section", { "class": "view stack-lg" });
    s.appendChild(h("div", { "class": "stack" },
      h("h1", null, "Tus fallos"),
      h("p", { "class": "lede" }, "Cada pregunta que fallas o dejas en blanco vuelve a ti al día siguiente, y luego a los 3, 7 y 21 días si la aciertas. Cuando la aciertas en todos los repasos, sale de la lista.")));
    if (!all.length) {
      s.appendChild(h("div", { "class": "empty" }, h("span", null, "Aún no tienes fallos guardados."), h("button", { "class": "btn", type: "button", onclick: function () { startSetup("CE1"); } }, "Hacer un test")));
      return s;
    }
    s.appendChild(h("div", { "class": "row" },
      h("button", { "class": "btn", type: "button", disabled: !due.length, onclick: function () { startReview(due); } }, due.length ? "Repasar los de hoy (" + due.length + ")" : "Hoy no toca ningún repaso"),
      h("button", { "class": "btn ghost", type: "button", onclick: function () { startReview(all); } }, "Repasar todos (" + all.length + ")")));
    var list = h("div", { "class": "review" });
    all.sort(function (a, b) { return S.stats[a.id].due - S.stats[b.id].due; }).forEach(function (q) {
      var st = S.stats[q.id];
      var days = Math.round((st.due - today()) / DAY);
      list.appendChild(h("details", { "class": "rv" },
        h("summary", null, h("span", { "class": "dot", style: "background:var(--bad)" }), h("span", null, q.q,
          h("span", { "class": "small muted", style: "display:block" }, (days <= 0 ? "Toca hoy" : "En " + days + " día" + (days === 1 ? "" : "s")) + " · fallada " + (st.w + st.b) + " vez" + (st.w + st.b === 1 ? "" : "es")))),
        h("div", { "class": "body" }, explanation(q, null))));
    });
    s.appendChild(list);
    return s;
  }

  // Progreso
  function viewProgreso() {
    var t = totals();
    var s = h("section", { "class": "view stack-lg" });
    s.appendChild(h("h1", null, "Tu progreso"));
    s.appendChild(h("div", { "class": "stats" },
      h("div", { "class": "stat" }, h("b", null, fmt(t.seen, 0)), h("span", null, "respuestas")),
      h("div", { "class": "stat" }, h("b", null, pct(t.c, t.seen) + " %"), h("span", null, "aciertos")),
      h("div", { "class": "stat" }, h("b", null, String(S.days.length)), h("span", null, "días practicando"))));

    var bars = h("div", { "class": "bars" });
    Object.keys(BANK.subs).forEach(function (k) {
      var qs = BANK.questions.filter(function (q) { return q.sub === k; });
      var c = 0, n = 0, seen = 0;
      qs.forEach(function (q) { var x = S.stats[q.id]; if (x && x.seen) { seen++; c += x.c; n += x.seen; } });
      bars.appendChild(h("div", { "class": "bar" }, h("span", null, BANK.subs[k]),
        h("span", null, n ? pct(c, n) + " % aciertos · " + seen + "/" + qs.length + " vistas" : "Sin empezar"),
        h("span", { "class": "meter", "aria-hidden": "true" }, h("i", { style: "width:" + (n ? pct(c, n) : 0) + "%" }))));
    });
    s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Constitución Española (I)"), bars,
      h("p", { "class": "small muted" }, "Pronto: tu percentil frente al resto de opositores de Tesón.")));

    if (S.history.length) {
      var hist = h("div", { "class": "review" });
      S.history.slice(-10).reverse().forEach(function (x) {
        hist.appendChild(h("div", { "class": "tema" },
          h("div", { "class": "t" }, fmt(x.nota) + " / 10"),
          h("span", { "class": "pill" + (x.mode === "examen" ? " warn" : "") }, x.review ? "Repaso" : x.mode === "examen" ? "Examen" : "Estudio"),
          h("div", { "class": "d" }, new Date(x.ts).toLocaleDateString("es-ES", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) + " · " + x.a + " aciertos, " + x.f + " fallos, " + x.b + " en blanco")));
      });
      s.appendChild(h("div", { "class": "stack" }, h("h2", null, "Últimos tests"), hist));
    }

    s.appendChild(h("div", { "class": "stack" },
      h("h2", null, "Tus datos"),
      h("p", { "class": "small muted", style: "margin:0" }, "Tu progreso se guarda en este navegador. Compartir datos de uso anónimos: " + (S.consent === "yes" ? "activado." : "desactivado.")),
      h("div", { "class": "row" },
        h("button", { "class": "btn quiet", type: "button", onclick: function () { openConsent(true); } }, "Cambiar preferencia"),
        h("button", { "class": "btn quiet", type: "button", onclick: confirmWipe }, "Borrar mi progreso"))));
    return s;
  }
  function confirmWipe() {
    sheet(function (close) {
      return [h("h2", null, "¿Borrar tu progreso?"),
        h("p", { "class": "muted" }, "Se borrarán tus respuestas, fallos e historial de este navegador. No se puede deshacer."),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () {
            track("progress_wiped", {});
            var keep = { consent: S.consent, uid: S.uid };
            S = fresh(); S.consent = keep.consent; S.uid = keep.uid; persist(); close(); go("home"); toast("Progreso borrado.");
          } }, "Sí, borrar"),
          h("button", { "class": "btn quiet", type: "button", onclick: close }, "Cancelar"))];
    });
  }

  // ── Sheets: consent, onboarding, report, feedback, NPS ─────
  function openConsent(fromSettings) {
    sheet(function (close) {
      function pick(v) {
        S.consent = v; persist(); close();
        if (v === "yes") track("consent_given", { from_settings: !!fromSettings, src: S.src });
        if (fromSettings) render();
      }
      return [
        h("h2", null, "Tesón está en beta"),
        h("p", { style: "margin:0" }, "Es gratis y no necesitas registrarte. Para mejorar las preguntas nos ayuda mucho saber cómo se usa la app: qué respondes, cuánto tardas y qué explicaciones te sirven."),
        h("p", { "class": "small muted", style: "margin:0" }, "Se guarda con un identificador aleatorio, sin tu nombre ni tu email, en servidores de la UE. Puedes cambiarlo cuando quieras en «Progreso». ", h("a", { href: "privacidad.html", target: "_blank", rel: "noopener" }, "Más información")),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () { pick("yes"); } }, "Sí, compartir datos de uso"),
          h("button", { "class": "btn ghost", type: "button", onclick: function () { pick("no"); } }, "No, gracias"))
      ];
    });
  }

  function openOnboarding(then) {
    var P = { exam: null, cuando: null, academia: null, academiaNombre: "", fuente: null };
    sheet(function (close) {
      function group(key, legend, options) {
        var c = h("div", { "class": "chips" });
        options.forEach(function (o) {
          var b = h("button", { "class": "chip", type: "button", "aria-pressed": "false", onclick: function () {
            P[key] = o;
            Array.prototype.forEach.call(c.children, function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
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
        if (!skip) track("onboarding_completed", { exam: P.exam, cuando: P.cuando, academia: P.academia, academia_nombre: P.academiaNombre || null, fuente: P.fuente, src: S.src }, { submitted: true });
        then();
      }
      return [
        h("h2", null, "Cuatro preguntas rápidas"),
        h("p", { "class": "small muted", style: "margin:0" }, "Nos ayudan a priorizar qué temas preparar. Todo es opcional."),
        group("exam", "¿Qué oposición preparas?", ["Auxiliar Administrativo del Estado", "Administrativo del Estado", "Justicia", "Policía o Guardia Civil", "Otra"]),
        group("cuando", "¿Cuándo crees que te examinarás?", ["Primera mitad de 2027", "Segunda mitad de 2027", "2028 o más tarde", "No lo sé"]),
        h("div", { "class": "stack", style: "gap:8px" }, group("academia", "¿Preparas con academia o preparador?", ["No", "Sí"]), acad),
        group("fuente", "¿Cómo has conocido Tesón?", ["Telegram", "Reddit", "Instagram o TikTok", "Un foro", "Google", "Me lo recomendaron", "Otro"]),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () { done(false); } }, "Guardar y empezar"),
          h("button", { "class": "btn quiet", type: "button", onclick: function () { done(true); } }, "Saltar"))
      ];
    });
  }

  function openReport(q) {
    sheet(function (close) {
      var reason = null;
      var reasons = ["La respuesta correcta está mal", "La pregunta es ambigua", "La ley ha cambiado", "Errata o redacción", "Otro"];
      var c = h("div", { "class": "choice" });
      reasons.forEach(function (r, i) {
        c.appendChild(h("label", null, h("input", { type: "radio", name: "reason", id: "rr" + i, onchange: function () { reason = r; send.disabled = false; } }), h("span", null, r)));
      });
      var txt = h("textarea", { id: "report-text", placeholder: "Cuéntanos qué está mal y, si puedes, el artículo correcto (opcional)", maxlength: "1000", "aria-label": "Detalle de la impugnación" });
      var send = h("button", { "class": "btn", type: "button", disabled: true, onclick: function () {
        track("question_reported", { qid: q.id, reason: reason, text: txt.value.trim().slice(0, 1000) }, { submitted: true });
        S.reported[q.id] = Date.now(); persist(); close(); render();
        toast("Gracias. La revisaremos en menos de 72 horas.");
      } }, "Enviar impugnación");
      return [h("h2", null, "Impugnar pregunta"), h("p", { "class": "small muted", style: "margin:0" }, q.id + " · " + q.q), c, txt, previewNote(),
        h("div", { "class": "row" }, send, h("button", { "class": "btn quiet", type: "button", onclick: close }, "Cancelar"))];
    });
  }

  function openFeedback() {
    sheet(function (close) {
      var rating = null;
      var c = h("div", { "class": "chips" });
      ["1", "2", "3", "4", "5"].forEach(function (v) {
        var b = h("button", { "class": "chip", type: "button", "aria-pressed": "false", onclick: function () {
          rating = Number(v);
          Array.prototype.forEach.call(c.children, function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        } }, v);
        c.appendChild(b);
      });
      var txt = h("textarea", { id: "fb-text", placeholder: "¿Qué mejorarías? ¿Qué echas en falta? ¿Qué te sobra?", maxlength: "2000", "aria-label": "Tu opinión" });
      var mail = h("input", { type: "email", id: "fb-mail", placeholder: "Tu email, si quieres que te respondamos (opcional)", "aria-label": "Email opcional" });
      return [
        h("h2", null, "Tu opinión"),
        h("fieldset", null, h("legend", null, "¿Qué te parece Tesón hasta ahora? (1 = nada, 5 = mucho)"), c),
        txt, mail,
        h("p", { "class": "small muted", style: "margin:0" }, "Solo usaremos tu email para responderte."),
        previewNote(),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () {
            if (!rating && !txt.value.trim()) { toast("Escribe algo o elige una puntuación."); return; }
            track("feedback_sent", { rating: rating, text: txt.value.trim().slice(0, 2000), email: mail.value.trim().slice(0, 120) || null, view: VIEW, tests: S.history.length }, { submitted: true });
            close(); toast("¡Gracias! Lo leemos todo.");
          } }, "Enviar"),
          h("button", { "class": "btn quiet", type: "button", onclick: close }, "Cancelar"))
      ];
    });
  }

  function openNps() {
    sheet(function (close) {
      var score = null;
      var c = h("div", { "class": "chips" });
      for (var i = 0; i <= 10; i++) (function (v) {
        var b = h("button", { "class": "chip", type: "button", "aria-pressed": "false", onclick: function () {
          score = v;
          Array.prototype.forEach.call(c.children, function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        } }, String(v));
        c.appendChild(b);
      })(i);
      var why = h("textarea", { id: "nps-why", placeholder: "¿Por qué? (opcional)", maxlength: "1000", "aria-label": "Motivo" });
      function done(send) {
        S.npsDone = true; persist(); close();
        if (send && score != null) { track("nps_submitted", { score: score, why: why.value.trim().slice(0, 1000), tests: S.history.length }, { submitted: true }); toast("¡Gracias!"); }
      }
      return [h("h2", null, "Una pregunta rápida"),
        h("fieldset", null, h("legend", null, "Del 0 al 10, ¿recomendarías Tesón a otro opositor?"), c), why, previewNote(),
        h("div", { "class": "row" },
          h("button", { "class": "btn", type: "button", onclick: function () { done(true); } }, "Enviar"),
          h("button", { "class": "btn quiet", type: "button", onclick: function () { done(false); } }, "Ahora no"))];
    });
  }

  // ── Boot ────────────────────────────────────────────────────
  render();
  if (S.consent === null) openConsent(false);
  else if (S.consent === "yes") track("session_start", { returning: S.history.length > 0, tests: S.history.length, src: S.src });
  flush();
})();
