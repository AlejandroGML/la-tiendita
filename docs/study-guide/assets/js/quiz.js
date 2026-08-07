/* immersive-doc — quiz.js
   Score tracking and quiz navigation.
   Base rendering is in components.js; this adds cross-quiz tracking.
*/

(function () {
  "use strict";

  const state = {
    answered: 0,
    correct: 0,
    total: 0,
  };

  function init() {
    const quizzes = window.__QUIZZES__ || [];
    state.total = quizzes.length;
    if (state.total === 0) return;

    injectScoreBadge();
    trackAnswers();
  }

  function injectScoreBadge() {
    const sidebar = document.getElementById("sidebar");
    if (!sidebar) return;
    const badge = document.createElement("div");
    badge.className = "quiz-score-badge";
    badge.innerHTML =
      '<p class="quiz-score-badge__title">Progress</p>' +
      '<p class="quiz-score-badge__value"><span id="quiz-correct">0</span> / <span id="quiz-total">' +
      state.total + '</span></p>' +
      '<div class="quiz-score-badge__bar"><div class="quiz-score-badge__fill" id="quiz-fill"></div></div>';
    sidebar.insertBefore(badge, sidebar.firstChild);
  }

  function trackAnswers() {
    document.addEventListener("click", function (e) {
      const opt = e.target.closest(".quiz__option");
      if (!opt) return;
      const form = opt.closest(".quiz");
      if (!form || form.dataset.tracked) return;
      form.dataset.tracked = "true";
      state.answered++;
      if (opt.getAttribute("data-correct") === "true") {
        state.correct++;
      }
      updateBadge();
      if (state.answered === state.total) {
        showFinalSummary();
      }
    });
  }

  function updateBadge() {
    const correct = document.getElementById("quiz-correct");
    const fill = document.getElementById("quiz-fill");
    if (correct) correct.textContent = String(state.correct);
    if (fill) {
      const pct = state.total > 0 ? (state.answered / state.total) * 100 : 0;
      fill.style.width = pct + "%";
    }
  }

  function showFinalSummary() {
    const pct = state.total > 0 ? Math.round((state.correct / state.total) * 100) : 0;
    let message;
    if (pct === 100) message = "Perfect score! You mastered this. 🏆";
    else if (pct >= 70) message = "Great job! You got " + pct + "% correct.";
    else if (pct >= 40) message = "Decent. Review the weak spots and try again.";
    else message = "Worth re-reading this section. You got " + pct + "%.";

    const banner = document.createElement("div");
    banner.className = "quiz-summary quiz-summary--" + (
      pct >= 70 ? "good" : pct >= 40 ? "ok" : "bad"
    );
    banner.innerHTML =
      '<p class="quiz-summary__title">Quiz complete</p>' +
      '<p class="quiz-summary__score">' + state.correct + ' / ' + state.total + ' (' + pct + '%)</p>' +
      '<p class="quiz-summary__msg">' + message + '</p>';

    const main = document.getElementById("main-content");
    if (main) {
      main.appendChild(banner);
      setTimeout(function () {
        banner.scrollIntoView({ behavior: "smooth" });
      }, 300);
    }
  }

  document.addEventListener("immersive-doc:ready", init);
})();
