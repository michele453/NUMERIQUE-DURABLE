/* Gestion soumission quiz et affichage du score */

(function () {
  "use strict";

  const ANSWERS = { 1: 1, 2: 0, 3: 2, 4: 1, 5: 1 };
  const QUESTIONS = {
    1: "Dérivée de x²",
    2: "Dérivée de sin(x)",
    3: "Dérivée d'une constante",
    4: "Dérivée de e^x",
    5: "Dérivée de 3x³"
  };
  const OPTIONS = {
    1: ["f'(x) = x", "f'(x) = 2x", "f'(x) = x²", "f'(x) = 2"],
    2: ["f'(x) = cos(x)", "f'(x) = -sin(x)", "f'(x) = tan(x)", "f'(x) = 1"],
    3: ["1", "La constante elle-même", "0", "Indéfini"],
    4: ["x·e^(x-1)", "e^x", "ln(x)", "0"],
    5: ["3x²", "9x²", "x³", "9x³"]
  };

  const form = document.getElementById("quiz-form");
  if (!form) return;

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    // Vérifier que toutes les questions ont une réponse
    const total = Object.keys(ANSWERS).length;
    let answered = 0;
    let score = 0;
    const review = [];

    for (const qid in ANSWERS) {
      const selected = form.querySelector(`input[name="q[${qid}]"]:checked`);
      if (!selected) continue;
      answered++;
      const chosen  = parseInt(selected.value, 10);
      const correct = ANSWERS[qid];
      const isOk    = chosen === correct;
      if (isOk) score++;
      review.push({ qid, chosen, correct, isOk });
    }

    if (answered < total) {
      alert(`Répondez à toutes les questions (${answered}/${total} répondues).`);
      return;
    }

    // Afficher résultat
    document.getElementById("quiz-section").classList.add("hidden");
    const resultSection = document.getElementById("result-section");
    resultSection.classList.remove("hidden");

    document.getElementById("score-value").textContent = `${score}/${total}`;
    const pct = Math.round((score / total) * 100);
    const msgs = ["À retravailler.", "Continue tes efforts !", "Pas mal !", "Bien joué !", "Excellent !"];
    document.getElementById("score-msg").textContent =
      pct < 40 ? msgs[0] : pct < 60 ? msgs[1] : pct < 70 ? msgs[2] : pct < 90 ? msgs[3] : msgs[4];

    // Correction détaillée
    const reviewDiv = document.getElementById("answers-review");
    review.forEach(function ({ qid, chosen, correct, isOk }) {
      const div = document.createElement("div");
      div.className = "answer-item " + (isOk ? "answer-correct" : "answer-wrong");
      div.innerHTML = `
        <strong>Q${qid} — ${QUESTIONS[qid]}</strong><br>
        Votre réponse : ${OPTIONS[qid][chosen]} ${isOk ? "✓" : "✗"}
        ${!isOk ? `<br><em>Bonne réponse : ${OPTIONS[qid][correct]}</em>` : ""}`;
      reviewDiv.appendChild(div);
    });
  });
})();
