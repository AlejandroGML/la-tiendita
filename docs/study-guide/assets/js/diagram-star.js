/* immersive-doc — diagram-star.js
   The "wow factor": SVG diagrams that draw themselves as the user scrolls.

   Uses GSAP + ScrollTrigger with stroke-dasharray/stroke-dashoffset technique
   (no DrawSVG plugin needed — all free).
*/

(function () {
  "use strict";

  const DIAGRAMS = window.__DIAGRAM_STARS__ || [];
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function init() {
    if (prefersReducedMotion) {
      // Show final state, no animation
      DIAGRAMS.forEach(setupStatic);
      return;
    }

    if (typeof window.gsap === "undefined" || typeof window.ScrollTrigger === "undefined") {
      // Fallback: CSS animation via classes
      DIAGRAMS.forEach(setupStatic);
      document.querySelectorAll(".diagram-star svg path[data-section]").forEach(function (p) {
        p.classList.add("drawn");
      });
      return;
    }

    DIAGRAMS.forEach(setupAnimated);
  }

  // ----- Static (no motion) -----
  function setupStatic(diagram) {
    const container = document.getElementById("diagram-" + diagram.id);
    if (!container) return;
    // Set all paths to drawn state, all nodes to neutral
    container.querySelectorAll("svg path[data-section]").forEach(function (p) {
      p.style.strokeDasharray = "none";
      p.style.strokeDashoffset = "0";
    });
  }

  // ----- Animated -----
  function setupAnimated(diagram) {
    const container = document.getElementById("diagram-" + diagram.id);
    if (!container) return;
    const svg = container.querySelector("svg");
    if (!svg) return;

    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;

    // 1. Initialize paths: set dasharray so they're hidden initially
    const paths = container.querySelectorAll("svg path[data-section]");
    paths.forEach(function (path) {
      const len = path.getTotalLength ? path.getTotalLength() : 1000;
      path.style.strokeDasharray = len;
      path.style.strokeDashoffset = len;
      path.dataset.pathLength = String(len);
    });

    // 2. Collect section IDs in this diagram
    const sectionIds = Array.from(container.querySelectorAll("[data-section]"))
      .map(function (el) { return el.getAttribute("data-section"); })
      .filter(function (v, i, arr) { return arr.indexOf(v) === i; });

    // 3. For each section, create a ScrollTrigger
    sectionIds.forEach(function (sectionId) {
      const target = document.getElementById(sectionId) || document.querySelector('[data-section-id="' + sectionId + '"]');
      if (!target) return;

      // Path drawing animation
      const matchingPaths = container.querySelectorAll('svg path[data-section="' + sectionId + '"]');
      matchingPaths.forEach(function (path) {
        const len = parseFloat(path.dataset.pathLength);
        gsap.to(path, {
          strokeDashoffset: 0,
          duration: 1.2,
          ease: "power2.out",
          scrollTrigger: {
            trigger: target,
            start: "top 70%",
            end: "top 30%",
            scrub: 0.5,
          },
        });
      });

      // Node highlight: when target section is in viewport center
      // Offsets account for the sticky diagram occupying top ~450px of viewport.
      const nodes = container.querySelectorAll('svg [data-section="' + sectionId + '"]:not(path):not(line)');
      ScrollTrigger.create({
        trigger: target,
        start: "top 55%",
        end: "bottom 45%",
        onToggle: function (self) {
          if (self.isActive) {
            // Highlight this section's nodes
            container.querySelectorAll("[data-section]").forEach(function (el) {
              el.classList.remove("active");
              el.classList.add("dim");
            });
            container.querySelectorAll('[data-section="' + sectionId + '"]').forEach(function (el) {
              el.classList.add("active");
              el.classList.remove("dim");
            });
          }
        },
      });
    });

    // 4. Reset "dim" when leaving all triggers — keep diagram clean when scrolled away
    ScrollTrigger.create({
      trigger: container,
      start: "top 80%",
      end: "bottom 20%",
      onLeave: function () {
        container.querySelectorAll("[data-section]").forEach(function (el) {
          el.classList.remove("active", "dim");
        });
      },
      onEnterBack: function () {
        // Re-evaluate on scroll back
      },
    });

    // 5. Sticky behavior: if sticky=true, the diagram stays pinned
    // while its sibling sections scroll past. This is done via CSS position:sticky,
    // but we also pin via ScrollTrigger when the parent section is in view.
    if (diagram.sticky) {
      const parentSection = container.closest(".section");
      if (parentSection) {
        // ScrollTrigger pin could be added here if CSS sticky isn't enough
        // For now, CSS .diagram-star--sticky handles it.
      }
    }
  }

  // Run after DOM + mermaid are ready
  document.addEventListener("immersive-doc:ready", init);
})();
