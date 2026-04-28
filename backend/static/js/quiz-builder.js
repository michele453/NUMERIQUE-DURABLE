/* Ajout dynamique de questions au formulaire */

(function () {
  "use strict";

  let questionCount = 1; // La question 1 est déjà dans le HTML

  function updateCount() {
    const el = document.getElementById("question-count");
    if (el) el.textContent = questionCount + " question(s)";
  }

  updateCount();

  window.addQuestion = function () {
    questionCount++;
    const i = questionCount;
    const container = document.getElementById("questions-container");

    const fieldset = document.createElement("fieldset");
    fieldset.className = "question-block";
    fieldset.id = "q-" + i;
    fieldset.innerHTML = `
      <legend>Question ${i}</legend>
      <div class="form-group mt-1">
        <label for="q${i}-texte">Énoncé</label>
        <input type="text" id="q${i}-texte" name="questions[${i-1}][texte]"
               required placeholder="Votre question..." aria-required="true">
      </div>
      <div class="options-grid">
        ${["A","B","C","D"].map((l, idx) => `
        <div class="form-group">
          <label for="q${i}-opt${idx}">Option ${l}</label>
          <input type="text" id="q${i}-opt${idx}" name="questions[${i-1}][options][${idx}]"
                 required placeholder="Option ${l}">
        </div>`).join("")}
      </div>
      <div class="form-group">
        <label for="q${i}-reponse">Bonne réponse</label>
        <select id="q${i}-reponse" name="questions[${i-1}][index_bonne_rep]" required aria-required="true">
          <option value="">-- Choisir --</option>
          ${["Option A","Option B","Option C","Option D"].map((l,idx) =>
            `<option value="${idx}">${l}</option>`).join("")}
        </select>
      </div>
      <button type="button" class="btn btn-danger btn-sm" onclick="removeQuestion(${i})">
        Supprimer cette question
      </button>`;

    container.appendChild(fieldset);
    updateCount();
    fieldset.querySelector("input").focus();
  };

  window.removeQuestion = function (id) {
    if (questionCount <= 1) {
      alert("Un quiz doit contenir au moins une question.");
      return;
    }
    const el = document.getElementById("q-" + id);
    if (el) { el.remove(); questionCount--; updateCount(); }
  };

  // Validation avant soumission
  const form = document.getElementById("quiz-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      if (questionCount < 2) {
        e.preventDefault();
        alert("Ajoutez au moins 2 questions avant d'enregistrer le quiz.");
      }
    });
  }
})();
