/* immersive-doc — components.js
   Renders deferred components (quizzes, glossary, tabs).
   Listens for the immersive-doc:ready event to coordinate with mermaid/gsap.
*/

(function () {
  "use strict";

  const META = window.__DOC_META__ || {};

  // ----- Render quizzes -----
  function renderQuizzes() {
    const data = window.__QUIZZES__ || [];
    data.forEach(function (quiz) {
      const placeholder = document.querySelector('[data-quiz-id="' + quiz.id + '"]');
      if (!placeholder) return;
      const form = document.createElement("form");
      form.className = "quiz";
      form.setAttribute("data-quiz-id", quiz.id);

      const q = document.createElement("p");
      q.className = "quiz__question";
      q.textContent = quiz.question;
      form.appendChild(q);

      const ul = document.createElement("ul");
      ul.className = "quiz__options";
      quiz.options.forEach(function (opt, i) {
        const li = document.createElement("li");
        li.className = "quiz__option";
        li.setAttribute("data-correct", opt.correct ? "true" : "false");
        li.setAttribute("data-idx", String(i));
        li.textContent = opt.text;
        li.addEventListener("click", function () {
          if (form.classList.contains("answered")) return;
          form.classList.add("answered");
          ul.querySelectorAll(".quiz__option").forEach(function (o) {
            o.classList.remove("selected");
            if (o.getAttribute("data-correct") === "true") {
              o.classList.add("correct");
            }
          });
          li.classList.add("selected");
          const isCorrect = li.getAttribute("data-correct") === "true";
          const feedback = form.querySelector(".quiz__feedback");
          feedback.classList.add("show", isCorrect ? "correct" : "incorrect");
          feedback.querySelector(".quiz__feedback-text").textContent = isCorrect
            ? "✓ Correct!"
            : "✗ Not quite. Try again later.";
        });
        ul.appendChild(li);
      });
      form.appendChild(ul);

      const feedback = document.createElement("div");
      feedback.className = "quiz__feedback";
      const fbText = document.createElement("p");
      fbText.className = "quiz__feedback-text";
      feedback.appendChild(fbText);
      if (quiz.explanation) {
        const exp = document.createElement("p");
        exp.className = "quiz__explanation";
        exp.textContent = quiz.explanation;
        feedback.appendChild(exp);
      }
      form.appendChild(feedback);

      placeholder.replaceWith(form);
    });
  }

  // ----- Render glossary at end of main -----
  function renderGlossary() {
    // glossary directives currently rendered inline by parser; this hook is for
    // auto-tooltipping: find glossary terms in body and wrap them in <abbr>.
    const dl = document.querySelector(".glossary");
    if (!dl) return;
    const terms = Array.from(dl.querySelectorAll("dt")).map(function (dt) {
      const dd = dt.nextElementSibling;
      return { term: dt.textContent.trim(), definition: dd ? dd.textContent.trim() : "" };
    });
    terms.forEach(function (t) {
      const re = new RegExp("\\b" + escapeRegExp(t.term) + "\\b", "gi");
      document.querySelectorAll("main p, main li, main td").forEach(function (el) {
        if (el.querySelector(".glossary")) return;
        walkAndReplace(el, re, t);
      });
    });
  }

  function escapeRegExp(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function walkAndReplace(node, regex, term) {
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    const matches = [];
    let current;
    while ((current = walker.nextNode())) {
      if (current.parentElement && current.parentElement.tagName === "ABBR") continue;
      if (regex.test(current.nodeValue)) {
        matches.push(current);
      }
      regex.lastIndex = 0;
    }
    matches.forEach(function (textNode) {
      const span = document.createElement("span");
      span.innerHTML = textNode.nodeValue.replace(regex, function (m) {
        return '<abbr title="' + escapeHtml(term.definition) + '">' + m + "</abbr>";
      });
      textNode.replaceWith(...span.childNodes);
    });
  }

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  // ----- View Transitions -----
  function initViewTransitions() {
    if (prefersReducedMotion() || !document.startViewTransition) return;
    // Wrap TOC clicks in a view transition
    document.querySelectorAll('.toc__list a, .breadcrumbs a').forEach(function (a) {
      a.addEventListener("click", function (e) {
        const href = a.getAttribute("href");
        if (!href || !href.startsWith("#")) return;
        e.preventDefault();
        document.startViewTransition(function () {
          const target = document.getElementById(href.slice(1));
          if (target) target.scrollIntoView({ behavior: "auto" });
        });
      });
    });
  }

  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  document.addEventListener("immersive-doc:ready", function () {
    renderQuizzes();
    renderGlossary();
    initViewTransitions();
  });
})();
