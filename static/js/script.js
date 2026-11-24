/* PharmaGest — interactions natives (pas de framework).
   La date de référence des lots est fixée au 15 novembre 2026
   pour que les statuts de péremption restent stables. */
(() => {
  "use strict";

  const AUJOURDHUI = new Date(2026, 10, 15);
  const ROLES = {
    administrateur: "Administrateur",
    pharmacien: "Pharmacien responsable",
    gestionnaire: "Gestionnaire de stock",
    caissier: "Caissier",
    responsable: "Responsable de gestion",
  };

  const CATALOGUE = [
    {
      code: "6191000000011",
      nom: "Paracétamol 500 mg",
      forme: "Comprimé",
      prix: 500,
      lots: [
        { numero: "L23990", peremption: "2026-10-02", qte: 20 },
        { numero: "L24140", peremption: "2026-12-20", qte: 30 },
        { numero: "L24110", peremption: "2027-06-15", qte: 80 },
      ],
    },
    {
      code: "6191000000028",
      nom: "Amoxicilline 500 mg",
      forme: "Gélule",
      prix: 2500,
      lots: [{ numero: "L24088", peremption: "2026-12-01", qte: 8 }],
    },
    {
      code: "6191000000035",
      nom: "Artéméther / Luméfantrine 20/120 mg",
      forme: "Comprimé",
      prix: 6500,
      lots: [
        { numero: "L23011", peremption: "2026-08-01", qte: 10 },
        { numero: "L24102", peremption: "2027-09-01", qte: 40 },
      ],
    },
    {
      code: "6191000000042",
      nom: "Salbutamol spray 100 µg",
      forme: "Spray",
      prix: 16500,
      lots: [
        { numero: "L24021", peremption: "2027-03-01", qte: 0 },
        { numero: "L24022", peremption: "2027-04-01", qte: 12, bloque: true },
      ],
    },
    {
      code: "6191000000059",
      nom: "Sérum physiologique 10 ml",
      forme: "Solution",
      prix: 2000,
      lots: [{ numero: "L22100", peremption: "2026-09-01", qte: 15 }],
    },
    {
      code: "6191000000066",
      nom: "Ibuprofène 400 mg",
      forme: "Comprimé",
      prix: 900,
      lots: [{ numero: "L25001", peremption: "2028-01-15", qte: 60 }],
    },
    {
      code: "6191000000073",
      nom: "Metformine 500 mg",
      forme: "Comprimé",
      prix: 700,
      lots: [{ numero: "L24155", peremption: "2027-02-01", qte: 25 }],
    },
    {
      code: "6191000000080",
      nom: "Oméprazole 20 mg",
      forme: "Gélule",
      prix: 1100,
      lots: [{ numero: "L24200", peremption: "2027-11-01", qte: 45 }],
    },
  ];

  const VENTES = [
    {
      id: "VT-2026-1841",
      date: "15/11/2026 18:05",
      client: "Rasoa Nomenjanahary",
      statut: "payee",
      paiement: "Espèces",
      lignes: [
        { produit: "Paracétamol 500 mg", lot: "L24140", qte: 2, prix: 500 },
        { produit: "Ibuprofène 400 mg", lot: "L25001", qte: 1, prix: 900 },
      ],
    },
    {
      id: "VT-2026-1836",
      date: "15/11/2026 11:40",
      client: "Comptoir",
      statut: "payee",
      paiement: "Mobile money",
      lignes: [{ produit: "Amoxicilline 500 mg", lot: "L24088", qte: 1, prix: 2500 }],
    },
    {
      id: "VT-2026-1822",
      date: "14/11/2026 16:12",
      client: "Clinique Saint Luc",
      statut: "payee",
      paiement: "Autre",
      lignes: [
        { produit: "Artéméther / Luméfantrine 20/120 mg", lot: "L24102", qte: 4, prix: 6500 },
        { produit: "Sérum physiologique 10 ml", lot: "L22100", qte: 6, prix: 2000 },
      ],
    },
    {
      id: "VT-2026-1810",
      date: "14/11/2026 09:02",
      client: "Jean Rakotomalala",
      statut: "annulee",
      paiement: "Espèces",
      lignes: [{ produit: "Oméprazole 20 mg", lot: "L24200", qte: 1, prix: 1100 }],
    },
  ];

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    initSidebar();
    initRoles();
    initConfirmForms();
    initRechercheGlobale();
    initNotifications();
    initLogin();
    document.querySelectorAll("[data-list]").forEach(initList);
    initMedicaments();
    initCategories();
    initFiches();
    initCommandes();
    initReception();
    initStock();
    initCaisse();
    initRetours();
    initRapport();
    initUtilisateurs();
    initGraphique();
    initPhoto();
  }

  function routes() {
    const node = document.getElementById("pg-routes");
    if (!node) return {};
    try { return JSON.parse(node.textContent); } catch (e) { return {}; }
  }

  function joursRestants(iso) {
    const d = new Date(iso + "T12:00:00");
    return Math.round((d - AUJOURDHUI) / 86400000);
  }

  function statutPeremption(lot) {
    if (lot.bloque) return "bloque";
    const jours = joursRestants(lot.peremption);
    if (jours < 0) return "perime";
    if (jours <= 90) return "proche";
    return "valide";
  }

  function lotVendable(lot) {
    return !lot.bloque && lot.qte > 0 && joursRestants(lot.peremption) >= 0;
  }

  function lotFefo(produit) {
    return produit.lots
      .filter(lotVendable)
      .sort((a, b) => a.peremption.localeCompare(b.peremption))[0] || null;
  }

  function formatAr(n) {
    return new Intl.NumberFormat("fr-FR").format(Math.round(Number(n) || 0)) + "\u00a0Ar";
  }

  function formatDate(iso) {
    const [y, m, d] = iso.split("-");
    return d + "/" + m + "/" + y;
  }

  function toast(opts) {
    const stack = document.getElementById("toastStack");
    if (!stack) return;
    const tone = opts.tone || "success";
    const icons = {
      success: "bi-check-circle-fill",
      danger: "bi-x-circle-fill",
      warning: "bi-exclamation-triangle-fill",
      info: "bi-info-circle-fill",
    };
    const item = document.createElement("div");
    item.className = "toast-item is-" + tone;
    item.setAttribute("role", tone === "danger" ? "alert" : "status");
    const icon = document.createElement("i");
    icon.className = "bi " + (icons[tone] || icons.info);
    icon.setAttribute("aria-hidden", "true");
    const body = document.createElement("div");
    body.className = "toast-body";
    const title = document.createElement("p");
    title.className = "toast-title";
    title.textContent = opts.title || "";
    body.appendChild(title);
    if (opts.text) {
      const text = document.createElement("p");
      text.className = "toast-text";
      text.textContent = opts.text;
      body.appendChild(text);
    }
    const close = document.createElement("button");
    close.type = "button";
    close.className = "btn-icon-quiet";
    close.setAttribute("aria-label", "Fermer la notification");
    close.innerHTML = '<i class="bi bi-x-lg" aria-hidden="true"></i>';
    item.append(icon, body, close);
    stack.appendChild(item);
    let timer = setTimeout(remove, 6000);
    item.addEventListener("mouseenter", () => clearTimeout(timer));
    item.addEventListener("mouseleave", () => { timer = setTimeout(remove, 2500); });
    close.addEventListener("click", remove);
    function remove() {
      clearTimeout(timer);
      item.remove();
    }
  }

  function openConfirm(opts) {
    const modalEl = document.getElementById("modalConfirm");
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    document.getElementById("confirmTitle").textContent = opts.title;
    document.getElementById("confirmText").textContent = opts.text;
    const ok = document.getElementById("confirmOk");
    const cancel = document.getElementById("confirmCancel");
    ok.textContent = opts.okLabel || "Confirmer";
    cancel.textContent = opts.cancelLabel || "Annuler";
    cancel.hidden = opts.tone === "alert";
    ok.className = "btn " + (opts.tone === "danger" ? "btn-danger" : "btn-primary");
    return new Promise((resolve) => {
      let settled = false;
      const finish = (value) => {
        if (settled) return;
        settled = true;
        modalEl.removeEventListener("hidden.bs.modal", onHide);
        ok.removeEventListener("click", onOk);
        resolve(value);
      };
      const onOk = () => { finish(true); modal.hide(); };
      const onHide = () => finish(false);
      ok.addEventListener("click", onOk);
      modalEl.addEventListener("hidden.bs.modal", onHide);
      modal.show();
    });
  }

  function initConfirmForms() {
    document.addEventListener("submit", async (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement) || !form.dataset.confirm || form.dataset.confirmed) return;
      event.preventDefault();
      const confirmed = await openConfirm({
        title: "Confirmer cette action",
        text: form.dataset.confirm,
        okLabel: "Continuer",
        tone: "danger",
      });
      if (!confirmed) return;
      form.dataset.confirmed = "true";
      form.requestSubmit(event.submitter || undefined);
    });
  }

  function setBusy(btn, busy, label) {
    if (!btn) return;
    if (busy) {
      if (!btn.dataset.prevLabel) btn.dataset.prevLabel = btn.innerHTML;
      btn.disabled = true;
      btn.setAttribute("aria-busy", "true");
      btn.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> ' + label;
    } else {
      btn.disabled = false;
      btn.removeAttribute("aria-busy");
      if (btn.dataset.prevLabel) btn.innerHTML = btn.dataset.prevLabel;
    }
  }

  function setFieldError(input, message) {
    if (!input) return;
    const errId = input.getAttribute("aria-describedby");
    const err = (input.parentElement && input.parentElement.querySelector(".field-error"))
      || (errId ? document.getElementById(errId) : null);
    if (!message) {
      input.removeAttribute("aria-invalid");
      if (err) { err.hidden = true; err.textContent = ""; }
      return;
    }
    input.setAttribute("aria-invalid", "true");
    if (err) { err.hidden = false; err.textContent = message; }
  }

  function readJson(id, fallback) {
    const node = document.getElementById(id);
    if (!node) return fallback;
    try { return JSON.parse(node.textContent); } catch (e) { return fallback; }
  }

  function initSidebar() {
    const sidebar = document.getElementById("appSidebar");
    const openBtn = document.getElementById("boutonMenu");
    const backdrop = document.getElementById("sidebarBackdrop");
    const collapseBtn = document.getElementById("boutonReduire");
    if (!sidebar) return;

    if (localStorage.getItem("pharmagest.sidebar") === "reduit") {
      document.body.classList.add("sidebar-collapsed");
      if (collapseBtn) {
        collapseBtn.setAttribute("aria-pressed", "true");
        const label = collapseBtn.querySelector(".side-label");
        if (label) label.textContent = "Agrandir le menu";
        collapseBtn.dataset.label = "Agrandir le menu";
      }
    }

    const close = () => {
      document.body.classList.remove("sidebar-open");
      if (backdrop) backdrop.hidden = true;
      if (openBtn) openBtn.setAttribute("aria-expanded", "false");
    };
    const open = () => {
      document.body.classList.add("sidebar-open");
      if (backdrop) backdrop.hidden = false;
      if (openBtn) openBtn.setAttribute("aria-expanded", "true");
      const first = sidebar.querySelector(".side-link:not([hidden])");
      if (first) first.focus();
    };

    if (openBtn) openBtn.addEventListener("click", () => {
      if (document.body.classList.contains("sidebar-open")) close();
      else open();
    });
    if (backdrop) backdrop.addEventListener("click", close);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && document.body.classList.contains("sidebar-open")) {
        close();
        if (openBtn) openBtn.focus();
      }
    });
    sidebar.querySelectorAll("a.side-link").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.matchMedia("(max-width: 991.98px)").matches) close();
      });
    });
    if (collapseBtn) {
      collapseBtn.addEventListener("click", () => {
        const collapsed = document.body.classList.toggle("sidebar-collapsed");
        localStorage.setItem("pharmagest.sidebar", collapsed ? "reduit" : "ouvert");
        collapseBtn.setAttribute("aria-pressed", String(collapsed));
        const label = collapsed ? "Agrandir le menu" : "Réduire le menu";
        const span = collapseBtn.querySelector(".side-label");
        if (span) span.textContent = label;
        collapseBtn.dataset.label = label;
      });
    }
    window.addEventListener("resize", () => {
      if (window.matchMedia("(min-width: 992px)").matches) close();
    });
  }

  function initRoles() {
    const select = document.getElementById("choixRole");
    const label = document.getElementById("roleCourant");
    if (!select) return;
    const role = localStorage.getItem("pharmagest.role") || "administrateur";
    applyRole(role);
    select.value = role;
    select.addEventListener("change", () => {
      localStorage.setItem("pharmagest.role", select.value);
      applyRole(select.value);
      toast({
        tone: "info",
        title: "Menu adapté",
        text: "Le menu affiche maintenant les écrans du rôle « " + ROLES[select.value] + " ».",
      });
    });

    function applyRole(value) {
      document.body.dataset.role = value;
      if (label) label.textContent = ROLES[value] || value;
      document.querySelectorAll("[data-roles]").forEach((el) => {
        const allowed = el.dataset.roles.split(/\s+/);
        el.hidden = !allowed.includes(value);
      });
      const pageRoles = (document.body.dataset.pageRoles || "").split(/\s+/).filter(Boolean);
      const denied = document.getElementById("accesRefuse");
      const content = document.getElementById("contenuPage");
      const blocked = pageRoles.length > 0 && !pageRoles.includes(value);
      if (denied && content) {
        denied.hidden = !blocked;
        content.hidden = blocked;
        if (blocked) {
          const title = denied.querySelector("h2");
          if (title) title.focus();
        }
      }
    }
  }

  function initRechercheGlobale() {
    const input = document.getElementById("rechercheGlobale");
    const list = document.getElementById("resultatsRecherche");
    if (!input || !list) return;
    const url = routes();
    const index = [
      { titre: "Tableau de bord", type: "Écran", href: url.dashboard },
      { titre: "Médicaments", type: "Écran", href: url.medicaments },
      { titre: "Catégories", type: "Écran", href: url.categories },
      { titre: "Fournisseurs", type: "Écran", href: url.fournisseurs },
      { titre: "Clients", type: "Écran", href: url.clients },
      { titre: "Achats", type: "Écran", href: url.achats },
      { titre: "Nouvelle commande", type: "Écran", href: url.commande },
      { titre: "Réception", type: "Écran", href: url.reception },
      { titre: "Stock et lots", type: "Écran", href: url.stock },
      { titre: "Caisse", type: "Écran", href: url.caisse },
      { titre: "Journal des ventes", type: "Écran", href: url.journal },
      { titre: "Retours", type: "Écran", href: url.retours },
      { titre: "Rapports", type: "Écran", href: url.rapports },
      { titre: "Utilisateurs", type: "Écran", href: url.utilisateurs },
    ];
    CATALOGUE.forEach((item) => {
      index.push({
        titre: item.nom,
        type: "Médicament · " + item.code,
        href: (url.medicaments || "") + "?q=" + encodeURIComponent(item.nom),
      });
    });
    let active = -1;

    const close = () => {
      list.hidden = true;
      list.innerHTML = "";
      input.setAttribute("aria-expanded", "false");
      active = -1;
    };

    const render = () => {
      const q = input.value.trim().toLowerCase();
      list.innerHTML = "";
      if (q.length < 2) { close(); return; }
      const hits = index.filter((item) => (item.titre + " " + item.type).toLowerCase().includes(q)).slice(0, 8);
      if (!hits.length) {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.disabled = true;
        btn.textContent = "Aucun résultat pour « " + input.value.trim() + " ».";
        li.appendChild(btn);
        list.appendChild(li);
      }
      hits.forEach((hit, i) => {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.setAttribute("role", "option");
        btn.dataset.href = hit.href || "";
        const strong = document.createElement("span");
        strong.textContent = hit.titre;
        const small = document.createElement("small");
        small.textContent = hit.type;
        btn.append(strong, small);
        btn.addEventListener("click", () => { if (hit.href) window.location.href = hit.href; });
        li.appendChild(btn);
        list.appendChild(li);
        if (i === active) btn.setAttribute("aria-selected", "true");
      });
      list.hidden = false;
      input.setAttribute("aria-expanded", "true");
    };

    input.addEventListener("input", () => { active = -1; render(); });
    input.addEventListener("keydown", (event) => {
      const buttons = [...list.querySelectorAll("button[data-href]")];
      if (event.key === "Escape") { close(); return; }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        active = Math.min(active + 1, buttons.length - 1);
        render();
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        active = Math.max(active - 1, 0);
        render();
      }
      if (event.key === "Enter" && buttons[active]) {
        event.preventDefault();
        window.location.href = buttons[active].dataset.href;
      }
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".global-search")) close();
    });
  }

  function initNotifications() {
    const btn = document.getElementById("boutonAlertes");
    const panel = document.getElementById("panneauAlertes");
    if (!btn || !panel) return;
    btn.addEventListener("click", () => {
      panel.hidden = !panel.hidden;
      btn.setAttribute("aria-expanded", String(!panel.hidden));
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".notify-wrap")) {
        panel.hidden = true;
        btn.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !panel.hidden) {
        panel.hidden = true;
        btn.setAttribute("aria-expanded", "false");
        btn.focus();
      }
    });
  }

  function initLogin() {
    const form = document.getElementById("loginForm");
    const toggle = document.getElementById("toggleMdp");
    const input = document.getElementById("mot-de-passe");
    if (toggle && input) {
      toggle.addEventListener("click", () => {
        const show = input.type === "password";
        input.type = show ? "text" : "password";
        toggle.setAttribute("aria-pressed", String(show));
        toggle.setAttribute("aria-label", show ? "Masquer le mot de passe" : "Afficher le mot de passe");
        const icon = toggle.querySelector("i");
        if (icon) icon.className = show ? "bi bi-eye-slash" : "bi bi-eye";
        input.focus();
      });
    }
    if (!form) return;
    form.addEventListener("submit", (event) => {
      const id = document.getElementById("identifiant");
      let invalid = false;
      if (!id.value.trim()) {
        setFieldError(id, "Saisissez votre identifiant.");
        invalid = true;
      } else setFieldError(id, "");
      if (!input.value) {
        setFieldError(input, "Saisissez votre mot de passe.");
        invalid = true;
      } else setFieldError(input, "");
      if (invalid) {
        event.preventDefault();
        (id.value.trim() ? input : id).focus();
        return;
      }
      setBusy(form.querySelector("[type='submit']"), true, "Connexion…");
    });
  }

  function initList(root) {
    const tbody = root.querySelector("tbody");
    if (!tbody) return;
    const search = root.querySelector("[data-filter='search']");
    const equals = [...root.querySelectorAll("[data-filter='equals']")];
    const sort = root.querySelector("[data-filter='sort']");
    const empty = root.querySelector("[data-empty]");
    const emptyText = root.querySelector("[data-empty-text]");
    const count = root.querySelector("[data-count]");
    const pager = root.querySelector("[data-pager]");
    const status = root.querySelector("[data-page-status]");
    const prev = root.querySelector("[data-page='prev']");
    const next = root.querySelector("[data-page='next']");
    const pageSize = Number(root.dataset.pageSize || 8);
    let page = 1;

    const params = new URLSearchParams(window.location.search);
    if (search && root.dataset.query && params.get(root.dataset.query)) {
      search.value = params.get(root.dataset.query);
    }

    const apply = () => {
      const rows = [...tbody.querySelectorAll("[data-row]")];
      const q = (search && search.value || "").trim().toLowerCase();
      let list = rows.filter((row) => {
        const blob = (row.dataset.search || "").toLowerCase();
        if (q && !blob.includes(q)) return false;
        return equals.every((select) => {
          if (!select.value) return true;
          return (row.dataset[select.dataset.key] || "") === select.value;
        });
      });
      if (sort && sort.value) {
        const [key, dir] = sort.value.split(":");
        list.sort((a, b) => {
          const va = a.dataset[key] || "";
          const vb = b.dataset[key] || "";
          const na = Number(va);
          const nb = Number(vb);
          const cmp = va !== "" && vb !== "" && Number.isFinite(na) && Number.isFinite(nb)
            ? na - nb
            : va.localeCompare(vb, "fr", { sensitivity: "base" });
          return dir === "desc" ? -cmp : cmp;
        });
      } else {
        list.sort((a, b) => Number(a.dataset.original || 0) - Number(b.dataset.original || 0));
      }
      list.forEach((row) => tbody.appendChild(row));
      const pages = Math.max(1, Math.ceil(list.length / pageSize));
      if (page > pages) page = pages;
      const start = (page - 1) * pageSize;
      rows.forEach((row) => { row.hidden = true; });
      list.slice(start, start + pageSize).forEach((row) => { row.hidden = false; });
      if (count) count.textContent = String(list.length);
      if (empty) empty.hidden = list.length !== 0;
      if (emptyText) {
        emptyText.textContent = q
          ? "Aucun élément ne correspond à « " + search.value.trim() + " ». Vérifiez l'orthographe ou effacez les filtres."
          : "Aucun élément ne correspond aux filtres. Élargissez la sélection ou effacez les filtres.";
      }
      const tableWrap = root.querySelector(".table-scroll");
      if (tableWrap) tableWrap.hidden = list.length === 0;
      if (pager) pager.hidden = rows.length <= pageSize && list.length <= pageSize;
      if (status) status.textContent = "Page " + page + " sur " + pages;
      if (prev) prev.disabled = page <= 1;
      if (next) next.disabled = page >= pages;
    };

    [...tbody.querySelectorAll("[data-row]")].forEach((row, index) => {
      if (!row.dataset.original) row.dataset.original = String(index);
    });

    if (search) search.addEventListener("input", debounce(() => { page = 1; apply(); }, 250));
    equals.forEach((select) => select.addEventListener("change", () => { page = 1; apply(); }));
    if (sort) sort.addEventListener("change", () => { page = 1; apply(); });
    if (prev) prev.addEventListener("click", () => { page -= 1; apply(); });
    if (next) next.addEventListener("click", () => { page += 1; apply(); });
    const clear = root.querySelector("[data-clear]");
    if (clear) clear.addEventListener("click", () => {
      if (search) search.value = "";
      equals.forEach((select) => { select.value = ""; });
      if (sort) sort.value = "";
      page = 1;
      apply();
      if (search) search.focus();
    });
    root._pgApply = apply;
    apply();
  }

  function debounce(fn, ms) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), ms);
    };
  }

  function badge(kind, icon, label) {
    const span = document.createElement("span");
    span.className = "statut statut-" + kind;
    const i = document.createElement("i");
    i.className = "bi " + icon;
    i.setAttribute("aria-hidden", "true");
    span.append(i, document.createTextNode(" " + label));
    return span;
  }

  function stockBadge(qte, seuil) {
    const q = Number(qte);
    if (q <= 0) return badge("rupture", "bi-x-circle-fill", "Rupture");
    if (q <= Number(seuil || 15)) return badge("faible", "bi-exclamation-triangle-fill", "Stock faible");
    return badge("valide", "bi-check-circle-fill", "Disponible");
  }

  function initMedicaments() {
    const modalEl = document.getElementById("modalMedicament");
    const ficheEl = document.getElementById("modalFicheMed");
    if (!modalEl || !ficheEl) return;
    const form = document.getElementById("formMedicament");
    const list = document.getElementById("listeMedicaments");

    document.addEventListener("click", async (event) => {
      const voir = event.target.closest("[data-action='voir-med']");
      const edit = event.target.closest("[data-action='modifier-med']");
      const archiver = event.target.closest("[data-action='archiver']");
      if (voir) openFiche(voir.closest("[data-row]"));
      if (edit) openForm(edit.closest("[data-row]"));
      if (archiver) {
        const row = archiver.closest("[data-row]");
        const nom = row.dataset.nom;
        const archived = row.dataset.statut === "archive";
        const ok = await openConfirm({
          title: archived ? "Réactiver ce médicament ?" : "Archiver ce médicament ?",
          text: archived
            ? "« " + nom + " » redeviendra disponible dans la liste active."
            : "« " + nom + " » ne sera plus proposé comme produit actif. Vous pourrez le réactiver ensuite.",
          okLabel: archived ? "Réactiver" : "Archiver",
          tone: archived ? "primary" : "danger",
        });
        if (!ok) return;
        row.dataset.statut = archived ? "actif" : "archive";
        paintStatut(row);
        const buttonLabel = archiver.querySelector("span");
        if (buttonLabel) buttonLabel.textContent = archived ? "Archiver" : "Réactiver";
        toast({
          title: archived ? "Médicament réactivé" : "Médicament archivé",
          text: nom + (archived ? " est de nouveau actif." : " est archivé. La ligne reste visible avec le filtre « Archivés »."),
        });
        if (list && list._pgApply) list._pgApply();
      }
    });

    document.getElementById("ajouterMedicament").addEventListener("click", () => openForm(null));
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const data = readForm();
      if (!data) return;
      const editing = form.dataset.mode === "edit" ? document.querySelector("[data-row][data-code='" + CSS.escape(form.dataset.code) + "']") : null;
      if (editing) {
        Object.assign(editing.dataset, data.dataset);
        paintRow(editing);
        toast({ title: "Médicament modifié", text: data.dataset.nom + " a été mis à jour." });
      } else {
        const row = buildRow(data.dataset);
        document.querySelector("#listeMedicaments tbody").appendChild(row);
        toast({ title: "Médicament ajouté", text: data.dataset.nom + " apparaît dans la liste." });
      }
      bootstrap.Modal.getInstance(modalEl).hide();
      if (list && list._pgApply) list._pgApply();
    });

    function openFiche(row) {
      document.getElementById("ficheNom").textContent = row.dataset.nom;
      document.getElementById("ficheCorps").innerHTML = "";
      const dl = document.createElement("dl");
      dl.className = "dl-grid";
      [
        ["Code-barres", row.dataset.code],
        ["Catégorie", row.dataset.categorieLabel],
        ["Forme", row.dataset.forme],
        ["Dosage", row.dataset.dosage],
        ["Prix d'achat", formatAr(row.dataset.achat)],
        ["Prix de vente", formatAr(row.dataset.vente)],
        ["Stock", row.dataset.stock + " unités"],
        ["Seuil d'alerte", row.dataset.seuil + " unités"],
        ["Statut", row.dataset.statut === "archive" ? "Archivé" : "Actif"],
      ].forEach(([dt, dd]) => {
        const t = document.createElement("dt");
        t.textContent = dt;
        const d = document.createElement("dd");
        d.textContent = dd;
        dl.append(t, d);
      });
      document.getElementById("ficheCorps").appendChild(dl);
      const stockHost = document.getElementById("ficheStock");
      stockHost.innerHTML = "";
      stockHost.appendChild(stockBadge(row.dataset.stock, row.dataset.seuil));
      document.getElementById("ficheModifier").onclick = () => {
        bootstrap.Modal.getInstance(ficheEl).hide();
        openForm(row);
      };
      bootstrap.Modal.getOrCreateInstance(ficheEl).show();
    }

    function openForm(row) {
      form.reset();
      clearErrors();
      resetPhoto();
      form.dataset.mode = row ? "edit" : "create";
      form.dataset.code = row ? row.dataset.code : "";
      document.getElementById("modalMedTitre").textContent = row ? "Modifier le médicament" : "Ajouter un médicament";
      if (row) {
        form.nom.value = row.dataset.nom;
        form.code.value = row.dataset.code;
        form.categorie.value = row.dataset.categorie;
        form.forme.value = row.dataset.forme;
        form.dosage.value = row.dataset.dosage;
        form.achat.value = row.dataset.achat;
        form.vente.value = row.dataset.vente;
        form.stock.value = row.dataset.stock;
        form.seuil.value = row.dataset.seuil;
        form.statut.value = row.dataset.statut;
      }
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }

    function clearErrors() {
      [...form.querySelectorAll("input, select")].forEach((input) => setFieldError(input, ""));
    }

    function readForm() {
      clearErrors();
      const nom = form.nom.value.trim();
      const code = form.code.value.trim();
      let ok = true;
      if (nom.length < 2) { setFieldError(form.nom, "Indiquez le nom commercial (au moins 2 caractères)."); ok = false; }
      if (!/^\d{8,14}$/.test(code)) { setFieldError(form.code, "Le code-barres doit contenir de 8 à 14 chiffres."); ok = false; }
      if (!form.categorie.value) { setFieldError(form.categorie, "Choisissez une catégorie."); ok = false; }
      if (!form.forme.value) { setFieldError(form.forme, "Choisissez une forme."); ok = false; }
      if (!form.dosage.value.trim()) { setFieldError(form.dosage, "Indiquez le dosage, par exemple 500 mg."); ok = false; }
      const achat = Number(form.achat.value);
      const vente = Number(form.vente.value);
      if (!(achat > 0)) { setFieldError(form.achat, "Le prix d'achat doit être supérieur à 0 Ar."); ok = false; }
      if (!(vente > 0)) { setFieldError(form.vente, "Le prix de vente doit être supérieur à 0 Ar."); ok = false; }
      else if (vente < achat) { setFieldError(form.vente, "Le prix de vente est inférieur au prix d'achat. Augmentez le prix de vente ou baissez le prix d'achat."); ok = false; }
      const stock = Number(form.stock.value);
      if (stock < 0 || Number.isNaN(stock)) { setFieldError(form.stock, "Le stock ne peut pas être négatif."); ok = false; }
      const duplicate = [...document.querySelectorAll("#listeMedicaments [data-row]")].some((row) => row.dataset.code === code && row.dataset.code !== form.dataset.code);
      if (duplicate) { setFieldError(form.code, "Ce code-barres est déjà utilisé. Ouvrez la fiche existante ou saisissez un autre code."); ok = false; }
      if (!ok) {
        const first = form.querySelector("[aria-invalid='true']");
        if (first) first.focus();
        return null;
      }
      const option = form.categorie.selectedOptions[0];
      return {
        dataset: {
          nom,
          code,
          categorie: form.categorie.value,
          categorieLabel: option.dataset.label || option.textContent,
          forme: form.forme.value,
          dosage: form.dosage.value.trim(),
          achat: String(achat),
          vente: String(vente),
          stock: String(stock),
          seuil: String(Number(form.seuil.value) || 0),
          statut: form.statut.value,
          search: (nom + " " + code).toLowerCase(),
          tone: option.dataset.tone || "soins",
          original: "999",
        },
      };
    }
  }

  function paintStatut(row) {
    const host = row.querySelector("[data-field='statut']");
    host.innerHTML = "";
    if (row.dataset.statut === "archive") host.appendChild(badge("archive", "bi-archive-fill", "Archivé"));
    else host.appendChild(badge("actif", "bi-check-circle-fill", "Actif"));
  }

  function paintRow(row) {
    row.dataset.search = (row.dataset.nom + " " + row.dataset.code).toLowerCase();
    row.querySelector("[data-field='nom']").textContent = row.dataset.nom;
    row.querySelector("[data-field='code']").textContent = row.dataset.code;
    row.querySelector("[data-field='categorie']").textContent = row.dataset.categorieLabel;
    row.querySelector("[data-field='forme']").textContent = row.dataset.forme;
    row.querySelector("[data-field='dosage']").textContent = row.dataset.dosage;
    row.querySelector("[data-field='achat']").textContent = formatAr(row.dataset.achat);
    row.querySelector("[data-field='vente']").textContent = formatAr(row.dataset.vente);
    row.querySelector("[data-field='stock']").textContent = row.dataset.stock;
    const stockHost = row.querySelector("[data-field='stock-badge']");
    stockHost.innerHTML = "";
    stockHost.appendChild(stockBadge(row.dataset.stock, row.dataset.seuil));
    const thumb = row.querySelector(".med-thumb");
    if (thumb) thumb.className = "med-thumb tone-" + (row.dataset.tone || "soins");
    paintStatut(row);
  }

  function buildRow(data) {
    const tr = document.createElement("tr");
    tr.setAttribute("data-row", "");
    Object.entries(data).forEach(([key, value]) => { tr.dataset[key] = value; });
    tr.innerHTML = document.getElementById("ligneMedicament").innerHTML;
    paintRow(tr);
    return tr;
  }

  function initCategories() {
    const form = document.getElementById("formCategorie");
    if (!form) return;
    document.getElementById("ajouterCategorie").addEventListener("click", () => openCat(null));
    document.addEventListener("click", async (event) => {
      const edit = event.target.closest("[data-action='modifier-categorie']");
      const del = event.target.closest("[data-action='supprimer-categorie']");
      if (edit) openCat(edit.closest("[data-row]"));
      if (del) {
        const row = del.closest("[data-row]");
        const n = Number(row.dataset.utilisations || 0);
        if (n > 0) {
          await openConfirm({
            title: "Suppression impossible",
            text: "La catégorie « " + row.dataset.nom + " » est utilisée par " + n + " médicament" + (n > 1 ? "s" : "") + ". Déplacez ces médicaments vers une autre catégorie, puis réessayez.",
            okLabel: "Compris",
            tone: "alert",
          });
          return;
        }
        const ok = await openConfirm({
          title: "Supprimer cette catégorie ?",
          text: "« " + row.dataset.nom + " » sera retirée de la liste.",
          okLabel: "Supprimer",
          tone: "danger",
        });
        if (!ok) return;
        row.remove();
        const list = document.getElementById("listeCategories");
        if (list && list._pgApply) list._pgApply();
        toast({ title: "Catégorie supprimée", text: row.dataset.nom + " a été retirée." });
      }
    });
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const nom = form.nom.value.trim();
      setFieldError(form.nom, nom.length < 2 ? "Indiquez un nom d'au moins 2 caractères." : "");
      if (nom.length < 2) { form.nom.focus(); return; }
      const exists = [...document.querySelectorAll("#listeCategories [data-row]")].some((row) => row.dataset.nom.toLowerCase() === nom.toLowerCase() && row.dataset.id !== form.dataset.id);
      if (exists) {
        setFieldError(form.nom, "Ce nom existe déjà. Modifiez la catégorie existante ou choisissez un autre nom.");
        return;
      }
      if (form.dataset.id) {
        const row = document.querySelector("#listeCategories [data-id='" + form.dataset.id + "']");
        row.dataset.nom = nom;
        row.dataset.description = form.description.value.trim();
        row.dataset.search = (nom + " " + row.dataset.description).toLowerCase();
        row.querySelector("[data-field='nom']").textContent = nom;
        row.querySelector("[data-field='description']").textContent = row.dataset.description || "—";
        toast({ title: "Catégorie modifiée", text: nom + " a été mise à jour." });
      } else {
        const tbody = document.querySelector("#listeCategories tbody");
        const tr = document.createElement("tr");
        const id = "cat-" + Date.now();
        tr.setAttribute("data-row", "");
        tr.dataset.id = id;
        tr.dataset.nom = nom;
        tr.dataset.description = form.description.value.trim();
        tr.dataset.utilisations = "0";
        tr.dataset.search = (nom + " " + tr.dataset.description).toLowerCase();
        tr.innerHTML = document.getElementById("ligneCategorie").innerHTML;
        tr.querySelector("[data-field='nom']").textContent = nom;
        tr.querySelector("[data-field='description']").textContent = tr.dataset.description || "—";
        tr.querySelector("[data-field='utilisations']").textContent = "0";
        tbody.appendChild(tr);
        toast({ title: "Catégorie ajoutée", text: nom + " peut maintenant être choisie sur un médicament." });
      }
      bootstrap.Modal.getInstance(document.getElementById("modalCategorie")).hide();
      const list = document.getElementById("listeCategories");
      if (list && list._pgApply) list._pgApply();
    });

    function openCat(row) {
      form.reset();
      setFieldError(form.nom, "");
      form.dataset.id = row ? row.dataset.id : "";
      document.getElementById("modalCatTitre").textContent = row ? "Modifier la catégorie" : "Ajouter une catégorie";
      if (row) {
        form.nom.value = row.dataset.nom;
        form.description.value = row.dataset.description || "";
      }
      bootstrap.Modal.getOrCreateInstance(document.getElementById("modalCategorie")).show();
    }
  }

  function initFiches() {
    document.addEventListener("click", async (event) => {
      const voir = event.target.closest("[data-action='voir-fiche']");
      const toggle = event.target.closest("[data-action='toggle-actif']");
      if (voir) {
        const sourceId = voir.getAttribute("data-source");
        const fiches = readJson(sourceId, {});
        const fiche = fiches[voir.getAttribute("data-id")];
        if (!fiche) return;
        document.getElementById("ficheTiersTitre").textContent = fiche.nom;
        const corps = document.getElementById("ficheTiersCorps");
        corps.innerHTML = "";
        const dl = document.createElement("dl");
        dl.className = "dl-grid";
        fiche.infos.forEach(([label, value]) => {
          const dt = document.createElement("dt");
          dt.textContent = label;
          const dd = document.createElement("dd");
          dd.textContent = value;
          dl.append(dt, dd);
        });
        const h = document.createElement("h3");
        h.className = "h6 mt-3";
        h.textContent = "Historique";
        const ul = document.createElement("ul");
        ul.className = "timeline";
        if (!fiche.historique.length) {
          const li = document.createElement("li");
          li.textContent = "Aucun mouvement pour le moment.";
          ul.appendChild(li);
        }
        fiche.historique.forEach((item) => {
          const li = document.createElement("li");
          const date = document.createElement("span");
          date.textContent = item.date;
          const label = document.createElement("span");
          label.textContent = item.label;
          const montant = document.createElement("strong");
          montant.textContent = item.montant;
          li.append(date, label, montant);
          ul.appendChild(li);
        });
        corps.append(dl, h, ul);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("modalFicheTiers")).show();
      }
      if (toggle) {
        const row = toggle.closest("[data-row]");
        const actif = row.dataset.statut === "actif";
        const ok = await openConfirm({
          title: actif ? "Désactiver cette fiche ?" : "Réactiver cette fiche ?",
          text: actif
            ? row.dataset.nom + " ne sera plus proposé dans les nouvelles opérations."
            : row.dataset.nom + " pourra de nouveau être sélectionné.",
          okLabel: actif ? "Désactiver" : "Réactiver",
          tone: actif ? "danger" : "primary",
        });
        if (!ok) return;
        row.dataset.statut = actif ? "inactif" : "actif";
        const host = row.querySelector("[data-field='statut']");
        host.innerHTML = "";
        host.appendChild(actif
          ? badge("inactif", "bi-pause-circle-fill", "Inactif")
          : badge("actif", "bi-check-circle-fill", "Actif"));
        const span = toggle.querySelector("span");
        if (span) span.textContent = actif ? "Réactiver" : "Désactiver";
        toast({ title: actif ? "Fiche désactivée" : "Fiche réactivée", text: row.dataset.nom });
      }
    });
  }

  function initCommandes() {
    const form = document.getElementById("commandeForm");
    if (form) {
      const tbody = document.getElementById("lignesCommande");
      const add = document.getElementById("ajouterLigne");
      const recalc = () => {
        let total = 0;
        [...tbody.querySelectorAll("tr")].forEach((row) => {
          const prix = Number(row.querySelector("[data-col='prix']").value) || 0;
          const qte = Number(row.querySelector("[data-col='qte']").value) || 0;
          const ligne = prix * qte;
          row.querySelector("[data-col='total']").textContent = formatAr(ligne);
          total += ligne;
        });
        document.getElementById("totalCommande").textContent = formatAr(total);
        refreshRemove();
      };
      const refreshRemove = () => {
        const buttons = [...tbody.querySelectorAll("[data-retirer]")];
        buttons.forEach((btn) => { btn.disabled = buttons.length === 1; });
      };
      tbody.addEventListener("change", (event) => {
        const select = event.target.closest("[data-col='produit']");
        if (select) {
          const prix = select.selectedOptions[0].dataset.prix || "";
          select.closest("tr").querySelector("[data-col='prix']").value = prix;
        }
        recalc();
      });
      tbody.addEventListener("input", recalc);
      tbody.addEventListener("click", (event) => {
        const btn = event.target.closest("[data-retirer]");
        if (!btn || btn.disabled) return;
        btn.closest("tr").remove();
        recalc();
      });
      add.addEventListener("click", () => {
        const tpl = document.getElementById("tplLigneCommande");
        tbody.appendChild(tpl.content.cloneNode(true));
        recalc();
      });
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        let ok = true;
        setFieldError(form.fournisseur, form.fournisseur.value ? "" : "Choisissez le fournisseur de cette commande.");
        if (!form.fournisseur.value) ok = false;
        [...tbody.querySelectorAll("tr")].forEach((row) => {
          const produit = row.querySelector("[data-col='produit']");
          const qte = row.querySelector("[data-col='qte']");
          setFieldError(produit, produit.value ? "" : "Choisissez un médicament.");
          setFieldError(qte, Number(qte.value) > 0 ? "" : "Indiquez une quantité supérieure à 0.");
          if (!produit.value || !(Number(qte.value) > 0)) ok = false;
        });
        if (!ok) {
          toast({
            tone: "danger",
            title: "Commande incomplète",
            text: "Complétez le fournisseur et chaque ligne avant d'enregistrer.",
          });
          return;
        }
        const confirme = await openConfirm({
          title: "Enregistrer la commande ?",
          text: "Elle sera conservée au statut Brouillon, pour un total de " + document.getElementById("totalCommande").textContent + ".",
          okLabel: "Enregistrer",
        });
        if (!confirme) return;
        const btn = document.getElementById("enregistrerCommande");
        setBusy(btn, true, "Enregistrement…");
        window.setTimeout(() => {
          setBusy(btn, false);
          const bandeau = document.getElementById("commandeOk");
          bandeau.hidden = false;
          document.getElementById("commandeOkTexte").textContent = "La commande CMD-2026-0149 est enregistrée en brouillon, total " + document.getElementById("totalCommande").textContent + ".";
          toast({ title: "Commande enregistrée", text: "CMD-2026-0149 est au statut Brouillon." });
        }, 500);
      });
      recalc();
    }

    document.addEventListener("click", async (event) => {
      const voir = event.target.closest("[data-action='voir-commande']");
      const annuler = event.target.closest("[data-action='annuler-commande']");
      if (voir) {
        const data = readJson("commandes-data", {});
        const commande = data[voir.getAttribute("data-id")];
        if (!commande) return;
        document.getElementById("commandeTitre").textContent = commande.numero + " · " + commande.fournisseur;
        const corps = document.getElementById("commandeCorps");
        corps.innerHTML = "";
        const p = document.createElement("p");
        p.textContent = "Statut : " + commande.statut;
        const table = document.createElement("table");
        table.className = "table";
        const thead = document.createElement("thead");
        thead.innerHTML = "<tr><th scope='col'>Médicament</th><th scope='col'>Quantité</th><th scope='col'>Montant</th></tr>";
        const tbody = document.createElement("tbody");
        commande.lignes.forEach((ligne) => {
          const tr = document.createElement("tr");
          [ligne.nom, String(ligne.qte), ligne.montant].forEach((value) => {
            const td = document.createElement("td");
            td.textContent = value;
            tr.appendChild(td);
          });
          tbody.appendChild(tr);
        });
        table.append(thead, tbody);
        corps.append(p, table);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("modalCommande")).show();
      }
      if (annuler) {
        const row = annuler.closest("[data-row]");
        if (row.dataset.statut === "annulee" || row.dataset.statut === "recue") {
          await openConfirm({
            title: "Annulation impossible",
            text: row.dataset.statut === "recue"
              ? "Cette commande est entièrement réceptionnée. Passez par un retour fournisseur plutôt que par une annulation."
              : "Cette commande est déjà annulée.",
            okLabel: "Compris",
            tone: "alert",
          });
          return;
        }
        const ok = await openConfirm({
          title: "Annuler la commande " + row.dataset.numero + " ?",
          text: "Les quantités non réceptionnées ne seront pas mises en stock.",
          okLabel: "Annuler la commande",
          tone: "danger",
        });
        if (!ok) return;
        row.dataset.statut = "annulee";
        const host = row.querySelector("[data-field='statut']");
        host.innerHTML = "";
        host.appendChild(badge("annulee", "bi-x-circle-fill", "Annulée"));
        const reception = row.querySelector("[data-action='receptionner']");
        if (reception) reception.remove();
        annuler.remove();
        toast({ title: "Commande annulée", text: row.dataset.numero + " est annulée." });
      }
    });
  }

  function initReception() {
    const form = document.getElementById("receptionForm");
    if (!form) return;
    document.getElementById("recevoirTout").addEventListener("click", () => {
      [...form.querySelectorAll("[data-reste]")].forEach((input) => {
        input.value = input.dataset.reste;
        input.dispatchEvent(new Event("input", { bubbles: true }));
      });
    });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      let ok = true;
      let recu = 0;
      let complet = true;
      [...form.querySelectorAll("tbody tr")].forEach((row) => {
        const qte = row.querySelector("[data-reste]");
        const lot = row.querySelector("[data-lot]");
        const date = row.querySelector("[data-date]");
        const reste = Number(qte.dataset.reste);
        const valeur = qte.value === "" ? NaN : Number(qte.value);
        setFieldError(qte, "");
        setFieldError(lot, "");
        setFieldError(date, "");
        if (Number.isNaN(valeur) || valeur < 0) {
          setFieldError(qte, "Indiquez une quantité reçue, ou 0 si la ligne n'est pas livrée.");
          ok = false;
          return;
        }
        if (valeur > reste) {
          setFieldError(qte, "Il reste " + reste + " unités à recevoir. Saisissez " + reste + " ou moins.");
          ok = false;
        }
        if (valeur > 0) {
          recu += valeur;
          if (!lot.value.trim()) {
            setFieldError(lot, "Indiquez le numéro de lot pour la quantité reçue.");
            ok = false;
          }
          if (!date.value) {
            setFieldError(date, "Indiquez la date de péremption.");
            ok = false;
          } else if (date.value < "2026-11-15") {
            setFieldError(date, "Cette date est déjà dépassée. Refusez le lot ou corrigez la date : un lot périmé ne doit pas entrer en stock.");
            ok = false;
          }
        }
        if (valeur !== reste) complet = false;
      });
      if (recu === 0) {
        ok = false;
        toast({ tone: "danger", title: "Rien à réceptionner", text: "Saisissez au moins une quantité reçue, ou annulez la commande depuis la liste." });
      }
      if (!ok) return;
      const confirme = await openConfirm({
        title: complet ? "Valider la réception complète ?" : "Valider une réception partielle ?",
        text: complet
          ? "Toutes les quantités restantes seront entrées en stock. La commande passera à « Entièrement réceptionnée »."
          : "Une partie des quantités reste à livrer. La commande passera à « Partiellement réceptionnée ».",
        okLabel: "Valider la réception",
      });
      if (!confirme) return;
      const statut = document.getElementById("statutReception");
      statut.innerHTML = "";
      statut.appendChild(complet
        ? badge("recue", "bi-check-circle-fill", "Entièrement réceptionnée")
        : badge("partielle", "bi-box-arrow-in-down", "Partiellement réceptionnée"));
      toast({
        title: "Réception enregistrée",
        text: complet ? "Le stock a été mis à jour pour toute la commande." : "Le reliquat reste à réceptionner.",
      });
    });
  }

  function initStock() {
    const root = document.getElementById("ecranStock");
    if (!root) return;
    const produit = document.getElementById("filtreProduit");
    const exp = document.getElementById("filtreExp");
    const stk = document.getElementById("filtreStk");
    const rows = [...document.querySelectorAll("#tableLots tbody [data-row]")];
    const moves = [...document.querySelectorAll("#tableMouvements tbody [data-row]")];
    const params = new URLSearchParams(window.location.search);
    if (params.get("exp")) exp.value = params.get("exp");
    if (params.get("stk")) stk.value = params.get("stk");
    if (params.get("produit")) produit.value = params.get("produit");

    const apply = () => {
      let perime = 0; let proche = 0; let valide = 0; let bloque = 0; let visible = 0;
      rows.forEach((row) => {
        const show = (!produit.value || row.dataset.produit === produit.value)
          && (!exp.value || row.dataset.exp === exp.value)
          && (!stk.value || row.dataset.stk === stk.value);
        row.hidden = !show;
        if (!show) return;
        visible += 1;
        if (row.dataset.exp === "perime") perime += 1;
        else if (row.dataset.exp === "proche") proche += 1;
        else if (row.dataset.bloque === "1") bloque += 1;
        else valide += 1;
      });
      document.querySelector("[data-card='total']").textContent = String(visible);
      document.querySelector("[data-card='perime']").textContent = String(perime);
      document.querySelector("[data-card='proche']").textContent = String(proche);
      document.querySelector("[data-card='valide']").textContent = String(valide);
      const note = document.querySelector("[data-card='bloque']");
      note.textContent = bloque
        ? bloque + " lot" + (bloque > 1 ? "s" : "") + " bloqué" + (bloque > 1 ? "s" : "") + ", exclu" + (bloque > 1 ? "s" : "") + " des valides."
        : "Aucun lot bloqué dans cette sélection.";
      const empty = document.getElementById("lotsVides");
      empty.hidden = visible !== 0;
      document.getElementById("tableLots").hidden = visible === 0;
      moves.forEach((row) => {
        row.hidden = Boolean(produit.value) && row.dataset.produit !== produit.value;
      });
    };
    [produit, exp, stk].forEach((el) => el.addEventListener("change", apply));
    document.getElementById("effacerStock").addEventListener("click", () => {
      produit.value = "";
      exp.value = "";
      stk.value = "";
      apply();
    });
    apply();
  }

  function initCaisse() {
    const root = document.getElementById("caisseApp");
    if (!root) return;
    const input = document.getElementById("saisieCaisse");
    const resultats = document.getElementById("caisseResultats");
    const erreur = document.getElementById("caisseErreur");
    const lignes = document.getElementById("panierLignes");
    const vide = document.getElementById("panierVide");
    const panier = [];
    let actif = -1;

    const showError = (message) => {
      if (!message) { erreur.hidden = true; erreur.textContent = ""; return; }
      erreur.hidden = false;
      erreur.textContent = message;
    };

    const renderResultats = () => {
      const q = input.value.trim().toLowerCase();
      resultats.innerHTML = "";
      actif = -1;
      if (q.length < 1) return;
      const hits = CATALOGUE.filter((item) => (item.nom + " " + item.code).toLowerCase().includes(q)).slice(0, 6);
      if (!hits.length) {
        const li = document.createElement("li");
        li.textContent = "Aucun produit pour cette recherche.";
        resultats.appendChild(li);
        return;
      }
      hits.forEach((item) => {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        const left = document.createElement("span");
        const name = document.createElement("span");
        name.className = "cell-title";
        name.textContent = item.nom;
        const meta = document.createElement("span");
        meta.className = "cell-sub";
        const lot = lotFefo(item);
        meta.textContent = lot
          ? "FEFO " + lot.numero + " · " + formatDate(lot.peremption) + " · " + lot.qte + " en stock"
          : "Aucun lot vendable";
        left.append(name, meta);
        const price = document.createElement("strong");
        price.textContent = formatAr(item.prix);
        btn.append(left, price);
        btn.addEventListener("click", () => ajouter(item));
        li.appendChild(btn);
        resultats.appendChild(li);
      });
    };

    const ajouter = (produit) => {
      showError("");
      const lot = lotFefo(produit);
      if (!lot) {
        showError("Aucun lot vendable pour " + produit.nom + ". Les lots périmés, bloqués ou en rupture ne peuvent pas être vendus. Choisissez un autre produit.");
        input.focus();
        return;
      }
      const key = produit.code + ":" + lot.numero;
      const existante = panier.find((ligne) => ligne.key === key);
      if (existante) {
        if (existante.qte + 1 > lot.qte) {
          showError("Stock insuffisant sur le lot " + lot.numero + " : " + lot.qte + " unité" + (lot.qte > 1 ? "s" : "") + " disponible" + (lot.qte > 1 ? "s" : "") + ". Réduisez la quantité ou attendez une réception.");
          return;
        }
        existante.qte += 1;
      } else {
        panier.push({ key, produit, lot: lot.numero, qte: 1 });
      }
      input.value = "";
      resultats.innerHTML = "";
      renderPanier();
      input.focus();
    };

    const renderPanier = () => {
      lignes.innerHTML = "";
      vide.hidden = panier.length !== 0;
      let total = 0;
      panier.forEach((ligne, index) => {
        const produit = ligne.produit;
        const sous = ligne.qte * produit.prix;
        total += sous;
        const wrap = document.createElement("div");
        wrap.className = "panier-ligne";
        const top = document.createElement("div");
        top.className = "ligne-top";
        const title = document.createElement("strong");
        title.textContent = produit.nom;
        const montant = document.createElement("span");
        montant.textContent = formatAr(sous);
        top.append(title, montant);
        const lotLabel = document.createElement("label");
        lotLabel.className = "form-label mt-2";
        lotLabel.textContent = "Lot";
        lotLabel.setAttribute("for", "lot-" + index);
        const select = document.createElement("select");
        select.className = "form-select";
        select.id = "lot-" + index;
        produit.lots.forEach((lot) => {
          const option = document.createElement("option");
          option.value = lot.numero;
          const etat = statutPeremption(lot);
          let suffix = "";
          if (etat === "perime") suffix = " — périmé, non vendable";
          else if (lot.bloque) suffix = " — bloqué, non vendable";
          else if (lot.qte <= 0) suffix = " — rupture";
          else if (etat === "proche") suffix = " — péremption proche, proposé en FEFO";
          option.textContent = lot.numero + " · " + formatDate(lot.peremption) + " · " + lot.qte + suffix;
          option.disabled = !lotVendable(lot);
          if (lot.numero === ligne.lot) option.selected = true;
          select.appendChild(option);
        });
        select.addEventListener("change", () => {
          const choisi = produit.lots.find((lot) => lot.numero === select.value);
          if (!choisi || !lotVendable(choisi)) {
            select.value = ligne.lot;
            showError("Ce lot est périmé, bloqué ou épuisé. Choisissez un lot vendable.");
            return;
          }
          if (ligne.qte > choisi.qte) {
            select.value = ligne.lot;
            showError("Ce lot ne contient que " + choisi.qte + " unités. Réduisez la quantité avant de le choisir.");
            return;
          }
          ligne.lot = choisi.numero;
          showError("");
          renderPanier();
        });
        const controls = document.createElement("div");
        controls.className = "ligne-top mt-2";
        const qty = document.createElement("div");
        qty.className = "qty";
        const minus = document.createElement("button");
        minus.type = "button";
        minus.setAttribute("aria-label", "Diminuer la quantité");
        minus.textContent = "−";
        const field = document.createElement("input");
        field.type = "number";
        field.min = "1";
        field.value = String(ligne.qte);
        field.setAttribute("aria-label", "Quantité pour " + produit.nom);
        const plus = document.createElement("button");
        plus.type = "button";
        plus.setAttribute("aria-label", "Augmenter la quantité");
        plus.textContent = "+";
        const stockLot = () => produit.lots.find((lot) => lot.numero === ligne.lot);
        const setQte = (value) => {
          const lot = stockLot();
          if (value < 1) return;
          if (value > lot.qte) {
            field.value = String(ligne.qte);
            showError("Quantité refusée : le lot " + lot.numero + " n'a que " + lot.qte + " unités. Saisissez " + lot.qte + " ou moins.");
            return;
          }
          ligne.qte = value;
          showError("");
          renderPanier();
        };
        minus.addEventListener("click", () => setQte(ligne.qte - 1));
        plus.addEventListener("click", () => setQte(ligne.qte + 1));
        field.addEventListener("change", () => setQte(Number(field.value)));
        qty.append(minus, field, plus);
        const retirer = document.createElement("button");
        retirer.type = "button";
        retirer.className = "btn btn-outline-danger";
        retirer.textContent = "Retirer";
        retirer.addEventListener("click", () => {
          panier.splice(index, 1);
          showError("");
          renderPanier();
        });
        controls.append(qty, retirer);
        const info = document.createElement("p");
        info.className = "hint";
        const lot = stockLot();
        info.textContent = "Sous-total " + formatAr(sous) + " · " + joursRestants(lot.peremption) + " jours avant péremption.";
        wrap.append(top, lotLabel, select, controls, info);
        lignes.appendChild(wrap);
      });
      document.getElementById("sousTotal").textContent = formatAr(total);
      document.getElementById("totalGeneral").textContent = formatAr(total);
      majMonnaie();
    };

    const totalPanier = () => panier.reduce((sum, ligne) => sum + ligne.qte * ligne.produit.prix, 0);

    const majMonnaie = () => {
      const bloc = document.getElementById("blocEspeces");
      const mode = document.querySelector("input[name='paiement']:checked");
      bloc.hidden = !mode || mode.value !== "especes";
      const recu = Number(document.getElementById("montantRecu").value);
      const monnaie = document.getElementById("monnaie");
      const total = totalPanier();
      if (!mode || mode.value !== "especes" || !document.getElementById("montantRecu").value) {
        monnaie.textContent = "Saisissez le montant remis par le client.";
        return;
      }
      if (recu < total) {
        monnaie.textContent = "Il manque " + formatAr(total - recu) + ". Demandez le complément ou changez de mode de paiement.";
      } else {
        monnaie.textContent = "Monnaie à rendre : " + formatAr(recu - total) + ".";
      }
    };

    document.querySelectorAll("input[name='paiement']").forEach((radio) => {
      radio.addEventListener("change", majMonnaie);
    });
    document.getElementById("montantRecu").addEventListener("input", majMonnaie);
    input.addEventListener("input", () => { showError(""); renderResultats(); });
    input.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      const q = input.value.trim().toLowerCase();
      const exact = CATALOGUE.find((item) => item.code === input.value.trim() || item.nom.toLowerCase() === q);
      const buttons = [...resultats.querySelectorAll("button")];
      if (exact) ajouter(exact);
      else if (buttons.length === 1) buttons[0].click();
      else if (!q) showError("Saisissez un nom ou un code-barres, par exemple 6191000000011.");
      else showError("Aucun produit pour ce code-barres. Vérifiez le code ou recherchez par nom.");
    });

    document.getElementById("confirmerVente").addEventListener("click", async () => {
      showError("");
      if (!panier.length) {
        showError("Le panier est vide. Ajoutez un produit avant de confirmer.");
        input.focus();
        return;
      }
      const mode = document.querySelector("input[name='paiement']:checked");
      if (!mode) {
        showError("Choisissez un mode de paiement : espèces, mobile money ou autre.");
        return;
      }
      const total = totalPanier();
      if (mode.value === "especes") {
        const recu = Number(document.getElementById("montantRecu").value);
        if (!(recu >= total)) {
          showError("Le montant reçu est inférieur au total de " + formatAr(total) + ". Demandez le complément ou changez de mode de paiement.");
          document.getElementById("montantRecu").focus();
          return;
        }
      }
      const ok = await openConfirm({
        title: "Confirmer la vente ?",
        text: "Total " + formatAr(total) + ". Le stock des lots choisis sera diminué.",
        okLabel: "Confirmer la vente",
      });
      if (!ok) return;
      const btn = document.getElementById("confirmerVente");
      setBusy(btn, true, "Enregistrement…");
      window.setTimeout(() => {
        setBusy(btn, false);
        const numero = "VT-2026-1842";
        const recu = document.getElementById("recuCorps");
        recu.innerHTML = "";
        const head = document.createElement("header");
        const h = document.createElement("h3");
        h.className = "h5";
        h.textContent = "PharmaGest";
        const sub = document.createElement("p");
        const modeLabel = document.querySelector("label[for='" + mode.id + "']");
        sub.textContent = numero + " · 15/11/2026 · " + (modeLabel ? modeLabel.textContent : "");
        head.append(h, sub);
        const table = document.createElement("table");
        panier.forEach((ligne) => {
          const tr = document.createElement("tr");
          const td1 = document.createElement("td");
          td1.textContent = ligne.produit.nom + " · lot " + ligne.lot + " × " + ligne.qte;
          const td2 = document.createElement("td");
          td2.textContent = formatAr(ligne.qte * ligne.produit.prix);
          tr.append(td1, td2);
          table.appendChild(tr);
        });
        const foot = document.createElement("p");
        foot.className = "grand";
        foot.textContent = "Total " + formatAr(total);
        recu.append(head, table, foot);
        if (mode.value === "especes") {
          const p = document.createElement("p");
          p.textContent = "Reçu " + formatAr(document.getElementById("montantRecu").value) + " · monnaie " + formatAr(Number(document.getElementById("montantRecu").value) - total);
          recu.appendChild(p);
        }
        bootstrap.Modal.getOrCreateInstance(document.getElementById("modalRecu")).show();
        panier.splice(0, panier.length);
        renderPanier();
        document.getElementById("montantRecu").value = "";
        toast({ title: "Vente confirmée", text: numero + " est enregistrée. Le reçu est affiché." });
      }, 600);
    });

    renderPanier();
  }

  function initRetours() {
    const form = document.getElementById("retourForm");
    if (!form) return;
    const vente = document.getElementById("retourVente");
    const produit = document.getElementById("retourProduit");
    const lot = document.getElementById("retourLot");
    const qte = document.getElementById("retourQte");
    const motif = document.getElementById("retourMotif");
    const detail = document.getElementById("retourDetail");
    const detailContainer = document.getElementById("retourDetailContainer");
    VENTES.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = item.id + " · " + item.date + " · " + item.client;
      vente.appendChild(option);
    });
    const params = new URLSearchParams(window.location.search);
    if (params.get("vente")) vente.value = params.get("vente");

    const remplirProduits = () => {
      produit.innerHTML = "";
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "Choisir";
      produit.appendChild(placeholder);
      const item = VENTES.find((v) => v.id === vente.value);
      if (!item) return;
      item.lignes.forEach((ligne, index) => {
        const option = document.createElement("option");
        option.value = String(index);
        option.textContent = ligne.produit + " · lot " + ligne.lot + " · " + ligne.qte + " vendue" + (ligne.qte > 1 ? "s" : "");
        produit.appendChild(option);
      });
      lot.value = "";
    };
    vente.addEventListener("change", remplirProduits);
    produit.addEventListener("change", () => {
      const item = VENTES.find((v) => v.id === vente.value);
      const ligne = item && item.lignes[Number(produit.value)];
      lot.value = ligne ? ligne.lot : "";
      if (ligne) qte.max = String(ligne.qte);
    });
    document.querySelectorAll("input[name='typeRetour']").forEach((radio) => {
      radio.addEventListener("change", () => {
        const annulation = document.getElementById("typeAnnulation").checked;
        document.getElementById("blocArticle").hidden = annulation;
      });
    });
    motif.addEventListener("change", () => {
      const autre = motif.value === "autre";
      detailContainer.hidden = !autre;
      detail.required = autre;
    });
    remplirProduits();

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const item = VENTES.find((v) => v.id === vente.value);
      setFieldError(vente, item ? "" : "Choisissez la vente d'origine.");
      if (!item) return;
      if (item.statut === "annulee") {
        setFieldError(vente, "Cette vente est déjà annulée. Choisissez une vente payée.");
        return;
      }
      const annulation = document.getElementById("typeAnnulation").checked;
      if (!motif.value) {
        setFieldError(motif, "Choisissez un motif pour expliquer le retour.");
        return;
      }
      setFieldError(motif, "");
      if (motif.value === "autre" && detail.value.trim().length < 3) {
        setFieldError(detail, "Précisez le motif en quelques mots.");
        return;
      }
      setFieldError(detail, "");
      let texte = "Annuler toute la vente " + item.id + " ?";
      if (!annulation) {
        const ligne = item.lignes[Number(produit.value)];
        if (!ligne) {
          setFieldError(produit, "Choisissez le produit retourné.");
          return;
        }
        setFieldError(produit, "");
        const valeur = Number(qte.value);
        if (!(valeur > 0)) {
          setFieldError(qte, "Indiquez la quantité à retourner.");
          return;
        }
        if (valeur > ligne.qte) {
          setFieldError(qte, "La quantité vendue sur ce lot est de " + ligne.qte + ". Saisissez " + ligne.qte + " ou moins.");
          return;
        }
        setFieldError(qte, "");
        texte = "Enregistrer le retour de " + valeur + " unité" + (valeur > 1 ? "s" : "") + " de " + ligne.produit + " (lot " + ligne.lot + ") ?";
      }
      const ok = await openConfirm({
        title: annulation ? "Annuler cette vente ?" : "Enregistrer le retour ?",
        text: texte + (form.remise.checked ? " Les unités seront remises en stock." : " Les unités ne retourneront pas en stock."),
        okLabel: annulation ? "Annuler la vente" : "Enregistrer le retour",
        tone: annulation ? "danger" : "primary",
      });
      if (!ok) return;
      const recap = document.getElementById("retourOk");
      recap.hidden = false;
      document.getElementById("retourOkTexte").textContent = annulation
        ? "La vente " + item.id + " est annulée."
        : "Le retour sur " + item.id + " est enregistré.";
      toast({ title: annulation ? "Vente annulée" : "Retour enregistré", text: item.id });
      form.reset();
      detailContainer.hidden = true;
      document.getElementById("blocArticle").hidden = false;
      remplirProduits();
    });
  }

  function initRapport() {
    const root = document.getElementById("rapportApp");
    if (!root) return;
    const type = document.getElementById("rapportType");
    const debut = document.getElementById("rapportDebut");
    const fin = document.getElementById("rapportFin");
    if (root.dataset.typeInitial) type.value = root.dataset.typeInitial;
    const data = {
      stock: {
        colonnes: ["Produit", "Lot", "Péremption", "Quantité", "Statut"],
        lignes: [
          ["Paracétamol 500 mg", "L24140", "20/12/2026", "30", "Péremption proche"],
          ["Amoxicilline 500 mg", "L24088", "01/12/2026", "8", "Stock faible"],
          ["Métronidazole 250 mg", "L24010", "01/08/2027", "0", "Rupture"],
          ["Salbutamol spray 100 µg", "L24022", "01/04/2027", "12", "Bloqué"],
        ],
      },
      ventes: {
        colonnes: ["N°", "Date", "Client", "Paiement", "Total"],
        lignes: [
          ["VT-2026-1841", "15/11/2026", "Rasoa Nomenjanahary", "Espèces", "1 900 Ar"],
          ["VT-2026-1836", "15/11/2026", "Comptoir", "Mobile money", "2 500 Ar"],
          ["VT-2026-1822", "14/11/2026", "Clinique Saint Luc", "Autre", "38 000 Ar"],
        ],
      },
      achats: {
        colonnes: ["N°", "Fournisseur", "Statut", "Total"],
        lignes: [
          ["CMD-2026-0142", "SOMAPHAR", "Commandée", "3 480 000 Ar"],
          ["CMD-2026-0139", "PHARMAGRO", "Partiellement réceptionnée", "890 000 Ar"],
          ["CMD-2026-0133", "OCEAN PHARMA", "Entièrement réceptionnée", "2 150 000 Ar"],
        ],
      },
      peremptions: {
        colonnes: ["Produit", "Lot", "Péremption", "Jours restants", "Quantité"],
        lignes: [
          ["Paracétamol 500 mg", "L23990", "02/10/2026", "Dépassé de 44 jours", "20"],
          ["Amoxicilline 500 mg", "L24088", "01/12/2026", "16 jours", "8"],
          ["Metformine 500 mg", "L24155", "01/02/2027", "78 jours", "25"],
        ],
      },
    };

    const generer = () => {
      setFieldError(type, "");
      setFieldError(debut, "");
      setFieldError(fin, "");
      if (!type.value) {
        setFieldError(type, "Choisissez un type de rapport : stock, ventes, achats ou péremptions.");
        return false;
      }
      if (!debut.value || !fin.value) {
        setFieldError(debut, "Indiquez la date de début et la date de fin.");
        return false;
      }
      if (fin.value < debut.value) {
        setFieldError(fin, "La date de fin est antérieure à la date de début. Inversez les deux dates.");
        return false;
      }
      const rapport = data[type.value];
      const preview = document.getElementById("rapportPreview");
      const table = document.getElementById("rapportTable");
      preview.hidden = false;
      document.getElementById("rapportTitre").textContent = type.selectedOptions[0].textContent;
      document.getElementById("rapportPeriode").textContent = "Du " + formatDate(debut.value) + " au " + formatDate(fin.value);
      table.innerHTML = "";
      const thead = document.createElement("thead");
      const hr = document.createElement("tr");
      rapport.colonnes.forEach((col) => {
        const th = document.createElement("th");
        th.scope = "col";
        th.textContent = col;
        hr.appendChild(th);
      });
      thead.appendChild(hr);
      const tbody = document.createElement("tbody");
      rapport.lignes.forEach((ligne) => {
        const tr = document.createElement("tr");
        ligne.forEach((value) => {
          const td = document.createElement("td");
          td.textContent = value;
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      table.append(thead, tbody);
      const hint = document.getElementById("rapportHint");
      hint.textContent = type.value === "stock"
        ? "Pour le stock, la date de fin est la date de situation."
        : "Les montants sont en ariary.";
      return true;
    };

    document.getElementById("btnPdf").addEventListener("click", () => {
      const btn = document.getElementById("btnPdf");
      if (!generer()) return;
      setBusy(btn, true, "Génération…");
      window.setTimeout(() => {
        setBusy(btn, false);
        toast({ title: "Rapport prêt", text: "La fenêtre d'impression s'ouvre pour l'enregistrer en PDF." });
        window.print();
      }, 400);
    });
    document.getElementById("btnExport").addEventListener("click", () => {
      if (!generer()) return;
      const rows = [...document.querySelectorAll("#rapportTable tr")].map((tr) =>
        [...tr.children].map((cell) => '"' + cell.textContent.replaceAll('"', '""') + '"').join(";")
      );
      const blob = new Blob(["\uFEFF" + rows.join("\n")], { type: "text/csv;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "pharmagest-" + (type.value || "rapport") + ".csv";
      a.click();
      URL.revokeObjectURL(a.href);
      toast({ title: "Export téléchargé", text: "Le fichier CSV est prêt, séparateur point-virgule." });
    });
  }

  function initUtilisateurs() {
    document.addEventListener("click", async (event) => {
      const btn = event.target.closest("[data-action='toggle-user']");
      if (!btn) return;
      const row = btn.closest("[data-row]");
      const actif = row.dataset.statut === "actif";
      const ok = await openConfirm({
        title: actif ? "Désactiver ce compte ?" : "Réactiver ce compte ?",
        text: actif
          ? row.dataset.nom + " ne pourra plus se connecter."
          : row.dataset.nom + " pourra de nouveau se connecter.",
        okLabel: actif ? "Désactiver" : "Réactiver",
        tone: actif ? "danger" : "primary",
      });
      if (!ok) return;
      row.dataset.statut = actif ? "inactif" : "actif";
      const host = row.querySelector("[data-field='statut']");
      host.innerHTML = "";
      host.appendChild(actif
        ? badge("inactif", "bi-pause-circle-fill", "Inactif")
        : badge("actif", "bi-check-circle-fill", "Actif"));
      const span = btn.querySelector("span");
      if (span) span.textContent = actif ? "Réactiver" : "Désactiver";
      toast({ title: actif ? "Compte désactivé" : "Compte réactivé", text: row.dataset.nom });
    });
  }

  function initGraphique() {
    const canvas = document.getElementById("chartVentes");
    const source = document.getElementById("donneesVentes");
    if (!canvas || !source || typeof Chart === "undefined") return;
    const data = JSON.parse(source.textContent);
    const table = document.getElementById("tableGraphique");
    let chart;
    const draw = (key) => {
      const serie = data[key];
      if (chart) chart.destroy();
      chart = new Chart(canvas, {
        type: "line",
        data: {
          labels: serie.labels,
          datasets: [{
            label: "Ventes (Ar)",
            data: serie.values,
            borderColor: "#0f766e",
            backgroundColor: "rgba(15, 118, 110, 0.15)",
            fill: true,
            tension: 0.25,
            pointBackgroundColor: "#0f766e",
            pointRadius: 3,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: (ctx) => formatAr(ctx.parsed.y) } },
          },
          scales: {
            y: { ticks: { callback: (value) => new Intl.NumberFormat("fr-FR", { notation: "compact" }).format(value) } },
            x: { ticks: { maxTicksLimit: 8 } },
          },
        },
      });
      canvas.setAttribute("aria-label", "Ventes en ariary sur " + serie.labels.length + " jours");
      table.innerHTML = "";
      const thead = document.createElement("thead");
      thead.innerHTML = "<tr><th scope='col'>Jour</th><th scope='col'>Ventes</th></tr>";
      const tbody = document.createElement("tbody");
      serie.labels.forEach((label, i) => {
        const tr = document.createElement("tr");
        const td1 = document.createElement("td");
        td1.textContent = label;
        const td2 = document.createElement("td");
        td2.textContent = formatAr(serie.values[i]);
        tr.append(td1, td2);
        tbody.appendChild(tr);
      });
      table.append(thead, tbody);
    };
    document.querySelectorAll("[data-periode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll("[data-periode]").forEach((other) => other.setAttribute("aria-pressed", "false"));
        btn.setAttribute("aria-pressed", "true");
        draw(btn.dataset.periode);
      });
    });
    draw("j14");
  }

  function initPhoto() {
    document.querySelectorAll("[data-photo-input]").forEach((input) => {
      input.addEventListener("change", () => {
        const file = input.files && input.files[0];
        const img = document.querySelector(input.dataset.preview);
        const empty = document.querySelector(input.dataset.empty);
        if (!file) {
          if (img) img.hidden = true;
          if (empty) empty.hidden = false;
          return;
        }
        const okType = ["image/jpeg", "image/png", "image/webp"].includes(file.type);
        if (!okType || file.size > 2 * 1024 * 1024) {
          input.value = "";
          setFieldError(input, !okType
            ? "Format refusé. Choisissez une image JPG, PNG ou WEBP."
            : "La photo dépasse 2 Mo. Choisissez une image plus légère.");
          return;
        }
        setFieldError(input, "");
        const reader = new FileReader();
        reader.onload = () => {
          img.src = reader.result;
          img.hidden = false;
          if (empty) empty.hidden = true;
        };
        reader.readAsDataURL(file);
      });
    });
  }

  function resetPhoto() {
    const img = document.getElementById("apercuPhoto");
    const empty = document.getElementById("apercuVide");
    const input = document.getElementById("photoMed");
    if (input) input.value = "";
    if (img) { img.hidden = true; img.removeAttribute("src"); }
    if (empty) empty.hidden = false;
  }
})();
