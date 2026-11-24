(() => {
  "use strict";

  const form = document.getElementById("loginForm");
  const password = document.getElementById("mot-de-passe");
  const capsWarning = document.getElementById("capsWarning");

  document.querySelectorAll("[data-toggle-password]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = document.getElementById(button.dataset.togglePassword);
      if (!input) return;
      const visible = input.type === "password";
      input.type = visible ? "text" : "password";
      button.setAttribute("aria-label", visible ? "Masquer le mot de passe" : "Afficher le mot de passe");
      button.setAttribute("aria-pressed", String(visible));
      button.querySelector("i").className = visible ? "bi bi-eye-slash" : "bi bi-eye";
      input.focus();
    });
  });

  if (form && password) {
    const username = document.getElementById("identifiant");
    form.addEventListener("submit", (event) => {
      let valid = true;
      [[username, "Saisissez votre identifiant ou adresse e-mail."], [password, "Saisissez votre mot de passe."]]
        .forEach(([input, message]) => {
          if (!input.value.trim()) {
            input.classList.add("is-invalid");
            input.setCustomValidity(message);
            valid = false;
          } else {
            input.classList.remove("is-invalid");
            input.setCustomValidity("");
          }
        });
      if (!valid) {
        event.preventDefault();
        form.querySelector(".is-invalid").focus();
        return;
      }
      const button = form.querySelector("[type='submit']");
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      button.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span>Connexion…</span>';
    });

    form.querySelectorAll("input:not([type='checkbox'])").forEach((input) => {
      input.addEventListener("blur", () => {
        const valid = input.value.trim().length > 0;
        input.classList.toggle("is-invalid", !valid);
        input.setCustomValidity(valid ? "" : (input === username
          ? "Saisissez votre identifiant ou adresse e-mail."
          : "Saisissez votre mot de passe."));
      });
    });
    password.addEventListener("keyup", (event) => {
      if (capsWarning) capsWarning.hidden = !event.getModifierState("CapsLock");
    });
    password.addEventListener("blur", () => {
      if (capsWarning) capsWarning.hidden = true;
    });
  }

  const registration = document.getElementById("registerForm");
  if (registration) {
    const username = document.getElementById("regUsername");
    const passwordInput = document.getElementById("regPassword");
    const confirmation = document.getElementById("confirmPassword");
    const consent = document.getElementById("privacyConsent");
    const submit = document.getElementById("registerSubmit");
    const meter = document.getElementById("strengthMeter");
    const strengthLabel = document.getElementById("strengthLabel");
    const nameTarget = document.getElementById("nomComplet");
    const fields = [...registration.querySelectorAll("input[required]")];

    const passwordRules = () => {
      const value = passwordInput.value;
      const checks = {
        length: value.length >= 8,
        upper: /[A-Z]/.test(value),
        number: /\d/.test(value),
        special: /[^A-Za-z0-9]/.test(value),
        different: Boolean(username.value) && value.toLowerCase() !== username.value.toLowerCase(),
      };
      Object.entries(checks).forEach(([rule, ok]) => {
        const item = registration.querySelector(`[data-rule="${rule}"]`);
        if (item) item.classList.toggle("is-valid", ok);
      });
      const score = Object.values(checks).filter(Boolean).length;
      const width = score === 0 ? 0 : score <= 2 ? 30 : score <= 4 ? 65 : 100;
      meter.style.width = `${width}%`;
      meter.style.backgroundColor = score <= 2 ? "#b91c1c" : score <= 4 ? "#c2410c" : "#166534";
      strengthLabel.textContent = score <= 2 ? "Faible" : score <= 4 ? "Moyen" : "Fort";
      return Object.values(checks).every(Boolean);
    };

    const validate = (showErrors = false) => {
      const strong = passwordRules();
      const checks = [
        [document.getElementById("firstName"), Boolean(document.getElementById("firstName").value.trim())],
        [document.getElementById("lastName"), Boolean(document.getElementById("lastName").value.trim())],
        [username, username.value.trim().length >= 3],
        [document.getElementById("regEmail"), document.getElementById("regEmail").validity.valid && Boolean(document.getElementById("regEmail").value)],
        [passwordInput, strong],
        [confirmation, Boolean(confirmation.value) && confirmation.value === passwordInput.value],
        [consent, consent.checked],
      ];
      let valid = true;
      checks.forEach(([input, ok]) => {
        valid = valid && ok;
        if (showErrors && input !== consent) input.classList.toggle("is-invalid", !ok);
        if (ok) input.classList.remove("is-invalid");
      });
      submit.disabled = !valid;
      return valid;
    };

    registration.addEventListener("input", (event) => {
      if (event.target.matches("input")) validate(false);
    });
    registration.addEventListener("change", () => validate(false));
    fields.forEach((input) => input.addEventListener("blur", () => validate(true)));
    registration.addEventListener("submit", (event) => {
      if (!validate(true)) {
        event.preventDefault();
        registration.querySelector(".is-invalid")?.focus();
        return;
      }
      nameTarget.value = `${document.getElementById("firstName").value.trim()} ${document.getElementById("lastName").value.trim()}`.trim();
      submit.disabled = true;
      submit.setAttribute("aria-busy", "true");
      submit.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span><span>Envoi…</span>';
    });
    validate(false);
  }

  const forgotForm = document.getElementById("forgotForm");
  if (forgotForm) {
    forgotForm.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!forgotForm.reportValidity()) return;
      document.getElementById("forgotMessage").textContent =
        "Si cette adresse correspond à un compte, un e-mail vous a été envoyé.";
    });
  }

  const resetForm = document.getElementById("resetForm");
  if (resetForm) {
    const resetPassword = document.getElementById("resetPassword");
    const confirmation = document.getElementById("resetConfirmation");
    const rules = () => {
      const value = resetPassword.value;
      const checks = {
        length: value.length >= 8,
        upper: /[A-Z]/.test(value),
        number: /\d/.test(value),
        special: /[^A-Za-z0-9]/.test(value),
      };
      Object.entries(checks).forEach(([name, ok]) => {
        resetForm.querySelector(`[data-reset-rule="${name}"]`).classList.toggle("is-valid", ok);
      });
      const score = Object.values(checks).filter(Boolean).length;
      const meter = document.getElementById("resetStrengthMeter");
      meter.style.width = `${score * 25}%`;
      meter.style.backgroundColor = score < 2 ? "#b91c1c" : score < 4 ? "#c2410c" : "#166534";
      document.getElementById("resetStrengthLabel").textContent = score < 2 ? "Faible" : score < 4 ? "Moyen" : "Fort";
      return Object.values(checks).every(Boolean);
    };
    resetForm.addEventListener("input", () => {
      rules();
      [resetPassword, confirmation].forEach((input) => input.classList.remove("is-invalid"));
    });
    resetForm.addEventListener("submit", (event) => {
      let valid = rules();
      resetPassword.classList.toggle("is-invalid", !valid);
      const matches = Boolean(confirmation.value) && confirmation.value === resetPassword.value;
      confirmation.classList.toggle("is-invalid", !matches);
      valid = valid && matches;
      if (!valid) {
        event.preventDefault();
        resetForm.querySelector(".is-invalid")?.focus();
      }
    });
  }
})();
