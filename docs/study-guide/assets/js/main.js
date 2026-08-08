/* immersive-doc — main.js
   Initializes all vendor libs with feature detection and graceful degradation.
   This file is the bootstrap; specific components live in their own files.
*/

(function () {
  "use strict";

  const META = window.__DOC_META__ || {};
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ----- Theme toggle -----
  function initTheme() {
    const root = document.documentElement;
    const stored = localStorage.getItem("immersive-doc-color-scheme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const scheme = stored || (prefersDark ? "dark" : "light");
    root.setAttribute("data-color-scheme", scheme);

    const toggle = document.querySelector('[data-action="theme-toggle"]');
    if (toggle) {
      toggle.addEventListener("click", function () {
        const current = root.getAttribute("data-color-scheme");
        const next = current === "dark" ? "light" : "dark";
        root.setAttribute("data-color-scheme", next);
        localStorage.setItem("immersive-doc-color-scheme", next);
      });
    }
  }

  // ----- Lenis smooth scroll -----
  function initLenis() {
    if (prefersReducedMotion || typeof window.Lenis === "undefined") return null;
    const lenis = new window.Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });
    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
    return lenis;
  }

  // ----- GSAP + ScrollTrigger -----
  function initGSAP() {
    if (typeof window.gsap === "undefined" || typeof window.ScrollTrigger === "undefined") return null;
    window.gsap.registerPlugin(window.ScrollTrigger);
    return { gsap: window.gsap, ScrollTrigger: window.ScrollTrigger };
  }

  // ----- Mermaid -----
  function initMermaid() {
    if (typeof window.mermaid === "undefined") return Promise.resolve();
    window.mermaid.initialize({
      startOnLoad: false,
      theme: META.theme || "default",
      securityLevel: "loose",
      fontFamily: "inherit",
    });
    const blocks = document.querySelectorAll(".mermaid");
    if (!blocks.length) return Promise.resolve();
    return Promise.all(Array.from(blocks).map(function (el) {
      const id = "mermaid-" + Math.random().toString(36).slice(2, 9);
      const code = el.textContent;
      return window.mermaid.render(id, code).then(function (result) {
        el.innerHTML = result.svg;
        if (typeof window.ScrollTrigger !== "undefined") {
          window.ScrollTrigger.refresh();
        }
      }).catch(function (err) {
        el.classList.add("mermaid-fallback");
        el.classList.remove("mermaid");
        el.textContent = "Mermaid render error: " + err.message + "\n\nSource:\n" + code;
      });
    }));
  }

  // ----- highlight.js -----
  function initHighlight() {
    if (typeof window.hljs === "undefined") return;
    document.querySelectorAll('pre code[class*="language-"]').forEach(function (block) {
      try { window.hljs.highlightElement(block); } catch (e) { /* ignore */ }
    });
  }

  // ----- KaTeX -----
  function initKatex() {
    if (typeof window.renderMathInElement === "undefined") return;
    renderMathInElement(document.body, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "$", right: "$", display: false },
      ],
      throwOnError: false,
    });
  }

  // ----- TOC builder + scroll spy -----
  function initTOC() {
    const tocList = document.querySelector(".toc__list");
    if (!tocList) return;
    const sections = document.querySelectorAll("main .section");
    const headings = [];
    sections.forEach(function (section) {
      const id = section.getAttribute("data-section-id");
      const title = section.querySelector("h2, h3");
      if (!id || !title) return;
      const li = document.createElement("li");
      const level = title.tagName.toLowerCase();
      if (level === "h3") li.classList.add("toc__sub");
      const a = document.createElement("a");
      a.href = "#" + id;
      a.textContent = title.textContent;
      a.setAttribute("data-target", id);
      li.appendChild(a);
      tocList.appendChild(li);
      headings.push({ id: id, link: a, section: section });
    });

    // Scroll spy
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            const id = entry.target.getAttribute("data-section-id");
            document.querySelectorAll(".toc__list a").forEach(function (a) {
              a.classList.toggle("active", a.getAttribute("data-target") === id);
            });
            updateBreadcrumbs(entry.target);
          }
        });
      }, { rootMargin: "-20% 0px -60% 0px", threshold: 0 });
      sections.forEach(function (s) { observer.observe(s); });
    }
  }

  // ----- Breadcrumbs -----
  function updateBreadcrumbs(section) {
    const bc = document.getElementById("breadcrumbs");
    if (!bc) return;
    const id = section.getAttribute("data-section-id");
    const title = section.querySelector("h2, h3");
    if (!title) return;
    bc.innerHTML = '<a href="#hero">Home</a> <span>›</span> <span>' + title.textContent + "</span>";
  }

  // ----- Progress bar -----
  function initProgress(lenis) {
    const bar = document.getElementById("progress-bar");
    if (!bar) return;
    function update() {
      const scrollTop = window.scrollY;
      const height = document.documentElement.scrollHeight - window.innerHeight;
      const pct = height > 0 ? (scrollTop / height) * 100 : 0;
      bar.style.width = pct + "%";
    }
    if (lenis) {
      lenis.on("scroll", update);
    } else {
      window.addEventListener("scroll", update, { passive: true });
    }
    update();
  }

  // ----- Search (Ctrl+K) -----
  function initSearch() {
    const modal = document.getElementById("search-modal");
    const input = document.getElementById("search-input");
    const resultsList = document.getElementById("search-results");
    if (!modal || !input || !resultsList) return;

    const sections = Array.from(document.querySelectorAll("main .section")).map(function (s) {
      const title = s.querySelector("h2, h3");
      const ps = Array.from(s.querySelectorAll("p, li, td")).map(function (el) { return el.textContent; }).join(" ");
      return {
        id: s.getAttribute("data-section-id") || s.id,
        title: title ? title.textContent : "",
        text: ps,
      };
    });

    let index = null;
    if (typeof window.FlexSearch !== "undefined") {
      index = new FlexSearch.Index({ tokenize: "forward" });
      sections.forEach(function (s, i) {
        index.add(i, s.title + " " + s.text);
      });
    }

    function open() {
      modal.hidden = false;
      input.value = "";
      resultsList.innerHTML = "";
      setTimeout(function () { input.focus(); }, 50);
    }
    function close() { modal.hidden = true; }

    document.addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        modal.hidden ? open() : close();
      }
      if (e.key === "Escape") close();
    });

    document.querySelector('[data-action="search"]')?.addEventListener("click", open);
    document.querySelector('[data-action="close-search"]')?.addEventListener("click", close);

    input.addEventListener("input", function () {
      const q = input.value.trim();
      if (!q) { resultsList.innerHTML = ""; return; }
      let matches = [];
      if (index) {
        const ids = index.search(q, 10);
        matches = ids.map(function (i) { return sections[i]; });
      } else {
        const ql = q.toLowerCase();
        matches = sections.filter(function (s) {
          return s.title.toLowerCase().includes(ql) || s.text.toLowerCase().includes(ql);
        }).slice(0, 10);
      }
      resultsList.innerHTML = matches.length === 0
        ? '<li>No results</li>'
        : matches.map(function (m) {
            const lower = m.title.toLowerCase();
            const pos = lower.indexOf(q.toLowerCase());
            const highlighted = pos >= 0
              ? m.title.slice(0, pos) + "<mark>" + m.title.slice(pos, pos + q.length) + "</mark>" + m.title.slice(pos + q.length)
              : m.title;
            return '<li data-target="' + m.id + '">' + highlighted + "</li>";
          }).join("");
      resultsList.querySelectorAll("li[data-target]").forEach(function (li) {
        li.addEventListener("click", function () {
          const target = document.getElementById(li.getAttribute("data-target"));
          if (target) {
            target.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth" });
            close();
          }
        });
      });
    });
  }

  // ----- Copy buttons -----
  function initCopy() {
    document.querySelectorAll(".copy-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const code = btn.parentElement.querySelector("code");
        if (!code) return;
        const text = code.textContent;
        const fallback = function () {
          const ta = document.createElement("textarea");
          ta.value = text;
          document.body.appendChild(ta);
          ta.select();
          try { document.execCommand("copy"); } catch (e) {}
          document.body.removeChild(ta);
        };
        if (navigator.clipboard) {
          navigator.clipboard.writeText(text).catch(fallback);
        } else { fallback(); }
        const original = btn.textContent;
        btn.textContent = "Copied!";
        setTimeout(function () { btn.textContent = original; }, 1500);
      });
    });
  }

  // ----- Lightbox for images -----
  function initLightbox() {
    const dialog = document.getElementById("lightbox");
    const img = document.getElementById("lightbox-img");
    if (!dialog || !img) return;
    document.querySelectorAll(".figure img, .gallery img").forEach(function (image) {
      image.addEventListener("click", function () {
        img.src = image.src;
        img.alt = image.alt;
        if (dialog.showModal) {
          dialog.showModal();
        } else {
          dialog.hidden = false;
        }
      });
    });
    document.querySelector('[data-action="close-lightbox"]')?.addEventListener("click", function () {
      if (dialog.close) dialog.close(); else dialog.hidden = true;
    });
  }

  // ----- Bootstrap -----
  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    const lenis = initLenis();
    const gsapCtx = initGSAP();
    initHighlight();
    initTOC();
    initProgress(lenis);
    initSearch();
    initCopy();
    initLightbox();

    initMermaid().then(function () {
      initKatex();
      // Notify other components that mermaid is ready
      document.dispatchEvent(new CustomEvent("immersive-doc:ready", { detail: { gsap: !!gsapCtx } }));
    }).catch(function () {
      initKatex();
      document.dispatchEvent(new CustomEvent("immersive-doc:ready", { detail: { gsap: !!gsapCtx } }));
    });

    // Expose for debugging
    window.__IMMERSIVE_DOC__ = { lenis: lenis, gsap: gsapCtx, meta: META };
  });
})();
