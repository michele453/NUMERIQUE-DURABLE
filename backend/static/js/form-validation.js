/* Validation côté client légère */

(function () {
  "use strict";

  function show(id, msg) {
    const el = document.getElementById(id);
    if (el) { el.textContent = msg || el.textContent; el.classList.remove("hidden"); }
  }
  function hide(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add("hidden");
  }

  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", function (e) {
      let ok = true;
      const email = document.getElementById("email");
      const pass  = document.getElementById("password");
      if (!email.value || !/\S+@\S+\.\S+/.test(email.value)) {
        show("email-error"); ok = false;
      } else hide("email-error");
      if (!pass.value) {
        show("pass-error"); ok = false;
      } else hide("pass-error");
      if (!ok) e.preventDefault();
    });
  }

  const regForm = document.getElementById("register-form");
  if (regForm) {
    regForm.addEventListener("submit", function (e) {
      let ok = true;
      const nom    = document.getElementById("nom");
      const prenom = document.getElementById("prenom");
      const email  = document.getElementById("email");
      const pass   = document.getElementById("password");
      const pass2  = document.getElementById("password2");

      if (!nom.value.trim())    { show("nom-error");    ok = false; } else hide("nom-error");
      if (!prenom.value.trim()) { show("prenom-error"); ok = false; } else hide("prenom-error");
      if (!email.value || !/\S+@\S+\.\S+/.test(email.value)) { show("email-error"); ok = false; } else hide("email-error");
      if (pass.value.length < 8) { show("pass-error"); ok = false; } else hide("pass-error");
      if (pass.value !== pass2.value) { show("pass2-error"); ok = false; } else hide("pass2-error");
      if (!ok) e.preventDefault();
    });
  }
})();
