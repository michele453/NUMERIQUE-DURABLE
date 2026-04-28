(function () {
  "use strict";

  window.filterQuiz = function (value) {
    document.querySelectorAll("#quiz-list tr").forEach(function (row) {
      const statut = row.dataset.statut || "";
      row.style.display = (value === "all" || statut === value) ? "" : "none";
    });
  };

  window.archiver = function (id) {
    if (!confirm("Archiver ce quiz ? Il ne sera plus visible par les étudiants.")) return;
    const row = document.querySelector(`#quiz-list tr button[onclick="archiver(${id})"]`);
    if (row) {
      const tr = row.closest("tr");
      tr.dataset.statut = "archive";
      tr.querySelector(".badge").className = "badge badge-gray";
      tr.querySelector(".badge").textContent = "Archivé";
    }
  };

  window.reactiver = function (id) {
    // Production : fetch(`/quiz/${id}/activate`, { method: "POST" })
    if (row) {
      const tr = row.closest("tr");
      tr.dataset.statut = "actif";
      tr.querySelector(".badge").className = "badge badge-green";
      tr.querySelector(".badge").textContent = "Actif";
    }
  };

  window.supprimer = function (id) {
    if (!confirm("Supprimer définitivement ce quiz ? Cette action est irréversible.")) return;
    // Production : fetch(`/quiz/${id}`, { method: "DELETE" })
    if (row) row.closest("tr").remove();
  };
})();
