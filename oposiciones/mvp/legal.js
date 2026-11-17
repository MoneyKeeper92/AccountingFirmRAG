(function () {
  "use strict";

  var cfg = window.TESON_CONFIG || {};
  var legal = cfg.legal || {};
  var required = ["updated", "controllerName", "taxId", "address", "processors"];
  var missing = required.filter(function (key) { return !String(legal[key] || "").trim(); });
  if (!String(cfg.contactEmail || "").trim()) missing.push("contactEmail");

  document.querySelectorAll("[data-legal]").forEach(function (el) {
    var key = el.getAttribute("data-legal");
    el.textContent = legal[key] || "NO CONFIGURADO";
  });
  document.querySelectorAll("[data-contact-email]").forEach(function (el) {
    var email = cfg.contactEmail || "NO CONFIGURADO";
    el.textContent = email;
    if (cfg.contactEmail) el.setAttribute("href", "mailto:" + cfg.contactEmail);
  });

  if (legal.registryDetails) {
    document.querySelectorAll("[data-registry-row]").forEach(function (el) { el.hidden = false; });
  }

  if (missing.length) {
    document.querySelectorAll("[data-legal-gate]").forEach(function (el) {
      el.hidden = false;
      el.textContent = "Despliegue bloqueado: faltan datos legales obligatorios en config.js (" + missing.join(", ") + "). No compartas esta versión.";
    });
    document.documentElement.setAttribute("data-config-incomplete", "true");
  }
})();
