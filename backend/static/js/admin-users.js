/* Filtre côté client + modale de confirmation */

(function () {
  "use strict";

  let pendingDeleteId = null;

  window.filterUsers = function () {
    const search = (document.getElementById("search-input").value || "").toLowerCase();
    const role   = (document.getElementById("role-filter").value || "").toLowerCase();
    document.querySelectorAll("#users-table tr").forEach(function (row) {
      const name  = (row.dataset.name  || "").toLowerCase();
      const email = (row.dataset.email || "").toLowerCase();
      const r     = (row.dataset.role  || "").toLowerCase();
      const matchSearch = !search || name.includes(search) || email.includes(search);
      const matchRole   = !role   || r === role;
      row.style.display = (matchSearch && matchRole) ? "" : "none";
    });
  };

  window.askDelete = function (id, name) {
    pendingDeleteId = id;
    document.getElementById("modal-title").textContent = "Supprimer " + name + " ?";
    document.getElementById("confirm-modal").style.display = "flex";
    document.getElementById("confirm-modal").classList.remove("hidden");
  };

  window.closeModal = function () {
    pendingDeleteId = null;
    document.getElementById("confirm-modal").style.display = "none";
  };

  document.getElementById("confirm-delete-btn").addEventListener("click", function () {
    if (!pendingDeleteId) return;
    const row = document.querySelector(`#users-table tr button[onclick*="askDelete(${pendingDeleteId}"]`);
    if (row) row.closest("tr").remove();
    closeModal();
    const flash = document.getElementById("flash-msg");
    flash.textContent = "Utilisateur supprimé avec succès.";
    flash.classList.remove("hidden");
    setTimeout(() => flash.classList.add("hidden"), 4000);
  });

  // Fermer la modale en cliquant en dehors
  document.getElementById("confirm-modal").addEventListener("click", function (e) {
    if (e.target === this) closeModal();
  });
})();
