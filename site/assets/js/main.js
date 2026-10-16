/* Signature Benefits Plus — small, dependency-free behaviour.
   Everything here degrades gracefully: the site reads fine with JS off. */
(function () {
  "use strict";
  var d = document;

  /* Mobile navigation toggle */
  var toggle = d.querySelector(".nav-toggle");
  var nav = d.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      toggle.textContent = open ? "Menu" : "Close";
      nav.classList.toggle("is-open", !open);
    });
    d.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) toggle.click();
    });
  }

  /* Close the client-login dropdown when clicking elsewhere */
  d.addEventListener("click", function (e) {
    var open = d.querySelectorAll("details.login[open]");
    for (var i = 0; i < open.length; i++) {
      if (!open[i].contains(e.target)) open[i].removeAttribute("open");
    }
  });

  /* Renewal planner: show when the review should start for a chosen month */
  var MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  var sel = d.getElementById("renew-month");
  var out = d.getElementById("planner-out");
  var cta = d.getElementById("planner-cta");
  var dial = d.getElementById("dial");
  var dialHl = d.getElementById("dial-hl");
  var dialMonth = d.getElementById("dial-month");
  var dialSub = d.getElementById("dial-sub");
  var dialDays = d.querySelectorAll(".dial__day");
  var rot = 0;            // target rotation, cumulative so the arc always takes the short way round
  var shownRot = 0;       // rotation currently drawn
  var raf = null;
  var turnTimer = null;
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function setRotation(deg) {
    shownRot = deg;
    dialHl.setAttribute("transform", "rotate(" + deg.toFixed(2) + " 260 260)");
  }
  function easeOutBack(t) { var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); }
  var settle = null;
  function animateTo(target) {
    if (raf) cancelAnimationFrame(raf);
    clearTimeout(settle);
    var from = shownRot, begin = null, dur = 900;
    function step(ts) {
      if (begin === null) begin = ts;
      var t = Math.min(1, (ts - begin) / dur);
      setRotation(from + (target - from) * easeOutBack(t));
      raf = t < 1 ? requestAnimationFrame(step) : null;
    }
    raf = requestAnimationFrame(step);
    /* If animation frames are throttled (background tab), still land on the final angle. */
    settle = setTimeout(function () {
      if (raf) { cancelAnimationFrame(raf); raf = null; }
      setRotation(target);
    }, dur + 120);
  }
  function placeDays(i) {
    for (var k = 0; k < dialDays.length; k++) {
      var rel = parseInt(dialDays[k].getAttribute("data-rel"), 10);
      var a = (i * 30 + rel) * Math.PI / 180;
      dialDays[k].setAttribute("x", (260 + 174 * Math.sin(a)).toFixed(1));
      dialDays[k].setAttribute("y", (260 - 174 * Math.cos(a)).toFixed(1));
    }
  }
  function updatePlanner(animate) {
    var i = parseInt(sel.value, 10);
    if (isNaN(i)) return;
    var start = MONTHS[(i + 9) % 12];   // ~90 days before
    var options = MONTHS[(i + 10) % 12]; // ~60 days before
    out.innerHTML = "For a <strong>" + MONTHS[i] + " 1</strong> renewal, we'd start your review in <strong>" + start +
      "</strong> and have options in front of you by <strong>" + options + "</strong>.";
    if (cta) cta.href = "/contact/?renews=" + encodeURIComponent(MONTHS[i]);
    if (dialHl) {
      var current = ((rot % 360) + 360) % 360;
      var delta = i * 30 - current;
      if (delta > 180) delta -= 360;
      if (delta < -180) delta += 360;
      rot += delta;
      if (animate && !reduceMotion) animateTo(rot); else setRotation(rot);
    }
    placeDays(i);
    if (dialMonth) dialMonth.textContent = MONTHS[i];
    if (dialSub) dialSub.textContent = "We start in " + start;
    if (animate && dial) {
      dial.classList.remove("is-turning");
      void dial.offsetWidth; // restart the swap animation
      dial.classList.add("is-turning");
      clearTimeout(turnTimer);
      turnTimer = setTimeout(function () { dial.classList.remove("is-turning"); }, 900);
    }
  }
  if (sel && out) {
    sel.addEventListener("change", function () { updatePlanner(true); });
    updatePlanner(false);
  }
  if (dial && sel) {
    /* Clicking a month on the dial selects it; the <select> stays the accessible control. */
    dial.addEventListener("click", function (e) {
      var seg = e.target.closest ? e.target.closest(".dial__seg") : null;
      if (!seg) return;
      sel.value = seg.getAttribute("data-month");
      updatePlanner(true);
    });
    /* After the load sequence, stop the intro animations from replaying on later changes. */
    setTimeout(function () { dial.classList.add("is-ready"); }, 3100);
  }

  /* Contact form: prefill from the planner, validate, submit */
  var form = d.getElementById("contact-form");
  if (form) {
    var params = new URLSearchParams(window.location.search);
    var renews = params.get("renews");
    var renewSel = d.getElementById("renew");
    var msg = d.getElementById("message");
    if (renews && MONTHS.indexOf(renews) !== -1) {
      if (renewSel) renewSel.value = renews;
      else if (msg && !msg.value) msg.value = "Our group health plan renews in " + renews + ". Please reach out 60 to 90 days before so we can review options.";
    }
    var status = d.getElementById("form-status");
    var done = d.getElementById("form-done");
    var endpoint = form.getAttribute("data-endpoint") || "";
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var trap = d.getElementById("website");
      if (trap && trap.value) return; // honeypot filled: silently ignore bots
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var data = new FormData(form);
      if (endpoint) {
        status.textContent = "Sending…";
        fetch(endpoint, { method: "POST", body: data, headers: { Accept: "application/json" } })
          .then(function (r) { if (!r.ok) throw new Error(r.status); form.hidden = true; done.hidden = false; done.focus(); })
          .catch(function () {
            status.textContent = "That didn't go through. Call 678-388-1837 or email info@sigbenplus.com and we'll pick it up from there.";
          });
      } else {
        /* No endpoint configured yet: hand off to the visitor's email app. */
        var body = "Name: " + data.get("name") + "\nCompany: " + (data.get("company") || "") +
          "\nEmail: " + data.get("email") + "\nPhone: " + (data.get("phone") || "") +
          "\nHelp with: " + (data.get("topic") || "") + "\nRenewal month: " + (data.get("renews") || "") +
          "\nEmployees: " + (data.get("headcount") || "") + "\n\n" + data.get("message");
        window.location.href = "mailto:info@sigbenplus.com?subject=" + encodeURIComponent("Website inquiry from " + data.get("name")) +
          "&body=" + encodeURIComponent(body);
        status.textContent = "Opening your email app. If nothing happens, email info@sigbenplus.com directly.";
      }
    });
  }

  /* Footer year */
  var years = d.querySelectorAll("[data-year]");
  for (var y = 0; y < years.length; y++) years[y].textContent = String(new Date().getFullYear());
})();
