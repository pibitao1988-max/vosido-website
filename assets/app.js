/* LUMIVA B2B site - interaction layer
   1. Language preference memory + optional auto-switch banner (never forced)
   2. Language switcher dropdown
   3. Mobile navigation
   4. Product filtering
   5. Enquiry form validation

   Note on switching: content itself is generated per language into separate
   URLs (/en/, /es/ ...). JavaScript only decides whether to *suggest* a
   switch, so crawlers can still reach every language version. */

(function () {
  "use strict";

  var COOKIE_LANG = "lumiva_lang";
  var COOKIE_DISMISS = "lumiva_lang_dismiss";

  function setCookie(name, value, days) {
    var d = new Date();
    d.setTime(d.getTime() + days * 86400000);
    document.cookie = name + "=" + encodeURIComponent(value) +
      ";expires=" + d.toUTCString() + ";path=/;SameSite=Lax";
  }

  function getCookie(name) {
    var parts = document.cookie ? document.cookie.split("; ") : [];
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i].split("=");
      if (p[0] === name) return decodeURIComponent(p.slice(1).join("="));
    }
    return null;
  }

  function currentLang() {
    return (document.documentElement.lang || "en").slice(0, 2);
  }

  /* Available languages are read from the switcher links in the header,
     so the list stays in sync with what is actually published. */
  function availableLangs() {
    var map = {};
    var links = document.querySelectorAll(".lang-switch a[data-lang]");
    for (var i = 0; i < links.length; i++) {
      map[links[i].getAttribute("data-lang")] = links[i].getAttribute("href");
    }
    return map;
  }

  /* ---- auto-switch suggestion banner ---- */
  function initLangBanner() {
    var banner = document.getElementById("lang-banner");
    if (!banner) return;

    if (getCookie(COOKIE_LANG) || getCookie(COOKIE_DISMISS)) return;

    var langs = availableLangs();
    var cur = currentLang();
    var prefs = navigator.languages || [navigator.language || "en"];
    var match = null;

    for (var i = 0; i < prefs.length && !match; i++) {
      var code = (prefs[i] || "").slice(0, 2).toLowerCase();
      if (langs[code] && code !== cur) match = code;
    }
    if (!match) return;

    var target = null;
    var links = document.querySelectorAll(".lang-switch a[data-lang]");
    for (var j = 0; j < links.length; j++) {
      if (links[j].getAttribute("data-lang") === match) {
        target = links[j];
        break;
      }
    }
    if (!target) return;

    var tpl = banner.getAttribute("data-template") || "Switch to {lang}?";
    var msg = banner.querySelector(".msg");
    if (msg) msg.textContent = tpl.replace("{lang}", target.textContent.trim());

    var accept = banner.querySelector(".accept");
    var dismiss = banner.querySelector(".dismiss");
    if (accept) accept.textContent = banner.getAttribute("data-accept") || "Switch";
    if (dismiss) dismiss.textContent = banner.getAttribute("data-dismiss") || "Stay here";

    banner.classList.add("is-open");

    if (accept) {
      accept.addEventListener("click", function () {
        setCookie(COOKIE_LANG, match, 180);
        window.location.href = target.getAttribute("href");
      });
    }
    if (dismiss) {
      dismiss.addEventListener("click", function () {
        setCookie(COOKIE_DISMISS, "1", 30);
        banner.classList.remove("is-open");
      });
    }
  }

  /* ---- language switcher dropdown ---- */
  function initLangSwitch() {
    var sw = document.querySelector(".lang-switch");
    if (!sw) return;
    var btn = sw.querySelector("button");
    var list = sw.querySelector("ul");
    if (!btn || !list) return;

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      list.classList.toggle("open");
    });
    document.addEventListener("click", function () {
      list.classList.remove("open");
    });
    list.addEventListener("click", function (e) {
      var a = e.target.closest("a[data-lang]");
      if (a) setCookie(COOKIE_LANG, a.getAttribute("data-lang"), 180);
    });
  }

  /* ---- mobile navigation ---- */
  function initNavToggle() {
    var btn = document.querySelector(".nav-toggle");
    var nav = document.querySelector(".nav");
    if (!btn || !nav) return;
    btn.addEventListener("click", function () {
      nav.classList.toggle("open");
    });
  }

  /* ---- product filtering ---- */
  function initFilters() {
    var bar = document.querySelector(".filter-bar");
    if (!bar) return;
    var cards = document.querySelectorAll("[data-cat]");
    bar.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-filter]");
      if (!btn) return;
      var want = btn.getAttribute("data-filter");
      var btns = bar.querySelectorAll("button");
      for (var i = 0; i < btns.length; i++) btns[i].classList.remove("active");
      btn.classList.add("active");
      for (var j = 0; j < cards.length; j++) {
        var show = want === "all" || cards[j].getAttribute("data-cat") === want;
        cards[j].style.display = show ? "" : "none";
      }
    });
  }

  /* ---- enquiry form ---- */
  function fallbackMailto(form) {
    var to = form.getAttribute("data-mailto") || "";
    var subject = form.getAttribute("data-subject") || "Enquiry";
    var lines = [];
    var fields = form.querySelectorAll("input, select, textarea");
    for (var i = 0; i < fields.length; i++) {
      if (!fields[i].name) continue;
      lines.push(fields[i].name + ": " + fields[i].value);
    }
    window.location.href = "mailto:" + to +
      "?subject=" + encodeURIComponent(subject) +
      "&body=" + encodeURIComponent(lines.join("\n"));
  }

  function initForm() {
    var form = document.getElementById("enquiry-form");
    if (!form) return;

    var success = document.getElementById("form-success");

    function fail(field, show) {
      var err = field.parentNode.querySelector(".field-error");
      if (err) err.style.display = show ? "block" : "none";
      field.style.borderColor = show ? "#b3261e" : "";
      return !show;
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();

      var ok = true;
      var name = form.querySelector("#f-name");
      var email = form.querySelector("#f-email");
      var product = form.querySelector("#f-product");

      if (name) ok = fail(name, name.value.trim() === "") && ok;
      if (product) ok = fail(product, product.value.trim() === "") && ok;
      if (email) {
        var bad = !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim());
        ok = fail(email, bad) && ok;
      }

      if (!ok) return;

      var endpoint = form.getAttribute("data-endpoint");

      if (endpoint) {
        /* Real endpoint configured in build.py (FORM_ENDPOINT):
           formspree, a self-hosted handler, or the CMS form action. */
        var btn = form.querySelector("button[type=submit]");
        if (btn) btn.disabled = true;
        fetch(endpoint, {
          method: "POST",
          body: new FormData(form),
          headers: { Accept: "application/json" }
        }).then(function (r) {
          if (!r.ok) throw new Error(r.status);
          if (success) success.style.display = "block";
          form.reset();
        }).catch(function () {
          fallbackMailto(form);
        }).then(function () {
          if (btn) btn.disabled = false;
        });
        return;
      }

      /* No endpoint configured: hand the enquiry to the visitor's mail client
         so nothing is silently lost. Set FORM_ENDPOINT in build.py to replace. */
      console.warn("[VOSIDO] no form endpoint configured - using mailto fallback");
      fallbackMailto(form);
      if (success) {
        success.style.display = "block";
        success.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      form.reset();
    });
  }

  /* ---- floating whatsapp picker (multiple sales lines) ---- */
  function initWaFloat() {
    var box = document.getElementById("wa-float");
    if (!box) return;
    var btn = box.querySelector(".wa-toggle");
    if (!btn) return; /* single contact: plain link, nothing to toggle */

    function close() {
      box.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
    }

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = box.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", close);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initLangBanner();
    initLangSwitch();
    initNavToggle();
    initFilters();
    initForm();
    initWaFloat();
  });
})();
