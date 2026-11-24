/* PharmaGest — interactions de l'interface (JavaScript natif, sans framework).
   Les données viennent du serveur ; le serveur revalide tout (RG03). */
(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const nombre = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 });
  const ar = (valeur) => `${nombre.format(Number(valeur) || 0)}\u00a0Ar`;
  const dateFr = (iso) => iso.split("-").reverse().join("/");

  function el(tag, attrs = {}, enfants = []) {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => {
      if (v === false || v == null) return;
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else node.setAttribute(k, v === true ? "" : v);
    });
    [].concat(enfants).forEach((e) => e != null && node.append(e));
    return node;
  }
  const icone = (classe) => el("i", { class: `bi ${classe}`, "aria-hidden": "true" });

  const stockage = {
    lire(cle) { try { return localStorage.getItem(cle); } catch { return null; } },
    ecrire(cle, valeur) { try { localStorage.setItem(cle, valeur); } catch { /* navigation privée : on ignore */ } },
  };

  function initMenu() {
    const corps = document.body;
    const ouvrir = $("#sidebarOpen");
    const fond = $("#sidebarBackdrop");
    const reduire = $("#sidebarCollapse");

    const basculerMobile = (ouvert) => {
      corps.classList.toggle("sidebar-open", ouvert);
      if (fond) fond.hidden = !ouvert;
      if (ouvrir) ouvrir.setAttribute("aria-expanded", String(ouvert));
    };
    ouvrir?.addEventListener("click", () => basculerMobile(!corps.classList.contains("sidebar-open")));
    fond?.addEventListener("click", () => basculerMobile(false));

    if (stockage.lire("pg-menu-reduit") === "1") {
      corps.classList.add("sidebar-collapsed");
      reduire?.setAttribute("aria-pressed", "true");
    }
    reduire?.addEventListener("click", () => {
      const reduit = corps.classList.toggle("sidebar-collapsed");
      reduire.setAttribute("aria-pressed", String(reduit));
      stockage.ecrire("pg-menu-reduit", reduit ? "1" : "0");
    });

    const bouton = $("#notifyButton");
    const panneau = $("#notifyPanel");
    const fermerAlertes = () => {
      if (!panneau || panneau.hidden) return;
      panneau.hidden = true;
      bouton.setAttribute("aria-expanded", "false");
    };
    bouton?.addEventListener("click", (e) => {
      e.stopPropagation();
      panneau.hidden = !panneau.hidden;
      bouton.setAttribute("aria-expanded", String(!panneau.hidden));
    });
    document.addEventListener("click", (e) => { if (panneau && !panneau.contains(e.target)) fermerAlertes(); });
    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      fermerAlertes();
      basculerMobile(false);
    });
  }

  function initFormulaires() {
    const modalEl = $("#modalConfirm");
    let attente = null;

    document.addEventListener("submit", (e) => {
      const form = e.target;
      if (!(form instanceof HTMLFormElement)) return;
      const message = form.dataset.confirm;
      if (!message || form.dataset.confirmed || !modalEl || !window.bootstrap) return;
      e.preventDefault();
      attente = { form, submitter: e.submitter };
      $("#confirmText").textContent = message;
      window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }, true);

    $("#confirmOk")?.addEventListener("click", () => {
      if (!attente) return;
      const { form, submitter } = attente;
      attente = null;
      form.dataset.confirmed = "1";
      window.bootstrap.Modal.getOrCreateInstance(modalEl).hide();
      try { form.requestSubmit(submitter || undefined); } finally { delete form.dataset.confirmed; }
    });

    document.addEventListener("submit", (e) => {
      const form = e.target;
      if (e.defaultPrevented || !(form instanceof HTMLFormElement) || form.method.toLowerCase() !== "post") return;
      if (form.dataset.envoye) { e.preventDefault(); return; }
      form.dataset.envoye = "1";
      setTimeout(() => $$("button[type='submit']", form).forEach((b) => {
        b.disabled = true;
        b.setAttribute("aria-busy", "true");
      }), 0);
    });
    window.addEventListener("pageshow", (e) => {
      if (!e.persisted) return;
      $$("form[data-envoye]").forEach((form) => {
        delete form.dataset.envoye;
        $$("button[type='submit']", form).forEach((b) => { b.disabled = false; b.removeAttribute("aria-busy"); });
      });
      window.dispatchEvent(new Event("pg:retour-page"));
    });

    $$("[data-imprimer]").forEach((b) => b.addEventListener("click", () => window.print()));
  }

  function initPhoto() {
    const champ = $("[data-photo-input]");
    if (!champ) return;
    const apercu = $("#apercuPhoto");
    const vide = $("#apercuVide");
    const erreur = $("#erreurPhoto");
    champ.addEventListener("change", () => {
      const fichier = champ.files[0];
      erreur.hidden = true;
      if (!fichier) return;
      if (!["image/jpeg", "image/png", "image/webp"].includes(fichier.type) || fichier.size > 2 * 1024 * 1024) {
        erreur.textContent = "La photo doit être au format JPG, PNG ou WEBP et ne pas dépasser 2 Mo.";
        erreur.hidden = false;
        champ.value = "";
        return;
      }
      apercu.src = URL.createObjectURL(fichier);
      apercu.alt = "Aperçu de la photo choisie";
      apercu.hidden = false;
      if (vide) vide.hidden = true;
    });
  }

  function initCommande() {
    const corps = $("#lignesCommande");
    const modele = $("#modeleLigne");
    if (!corps || !modele) return;
    const total = $("#totalCommande");

    const recalculer = () => {
      let somme = 0;
      $$("tr[data-ligne]", corps).forEach((tr) => {
        const q = Number($("[name='quantite']", tr).value) || 0;
        const p = Number($("[name='prix']", tr).value) || 0;
        somme += q * p;
        $("[data-soustotal]", tr).textContent = q * p ? ar(q * p) : "—";
      });
      total.textContent = ar(somme);
    };
    const ajouter = () => {
      const ligne = modele.content.firstElementChild.cloneNode(true);
      corps.append(ligne);
      recalculer();
      return ligne;
    };

    corps.addEventListener("input", (e) => {
      if (e.target.name === "prix") delete e.target.dataset.auto;
      recalculer();
    });
    corps.addEventListener("change", (e) => {
      if (e.target.name !== "medicament") return;
      const prix = $("[name='prix']", e.target.closest("tr"));
      const defaut = e.target.selectedOptions[0]?.dataset.prix;
      if (defaut && (!prix.value || prix.dataset.auto)) { prix.value = defaut; prix.dataset.auto = "1"; }
      recalculer();
    });
    corps.addEventListener("click", (e) => {
      const retirer = e.target.closest("[data-retirer]");
      if (!retirer) return;
      retirer.closest("tr").remove();
      if (!$("tr[data-ligne]", corps)) ajouter();
      recalculer();
    });
    $("#ajouterLigne").addEventListener("click", () => $("select", ajouter()).focus());
    if (!$("tr[data-ligne]", corps)) ajouter(); else recalculer();
  }

  function initStock() {
    const demain = new Date();
    demain.setDate(demain.getDate() + 1);
    const iso = `${demain.getFullYear()}-${String(demain.getMonth() + 1).padStart(2, "0")}-${String(demain.getDate()).padStart(2, "0")}`;
    $$("[data-date-future]").forEach((champ) => { champ.min = iso; });

    const reception = $("#receptionForm");
    if (reception) {
      reception.addEventListener("submit", (e) => {
        const lignes = $$("[data-qte-reception]", reception).filter((c) => Number(c.value) > 0);
        const manque = lignes.some((c) => {
          const id = c.name.slice(2);
          return !reception.elements[`lot_${id}`].value.trim() || !reception.elements[`exp_${id}`].value;
        });
        if (!lignes.length || manque) {
          e.preventDefault();
          e.stopImmediatePropagation();
          alert(!lignes.length
            ? "Saisissez une quantité reçue sur au moins une ligne."
            : "Indiquez le numéro de lot et la date de péremption de chaque ligne reçue.");
        }
      }, true);
    }

    const lot = $("#inventaireForm #lot");
    const quantite = $("#inventaireForm #quantite");
    const ecart = $("#ecartInventaire");
    if (lot && quantite && ecart) {
      const maj = () => {
        const dispo = Number(lot.selectedOptions[0]?.dataset.dispo);
        if (!lot.value || quantite.value === "") { ecart.textContent = "Saisissez la quantité réellement présente."; return; }
        const diff = Number(quantite.value) - dispo;
        ecart.textContent = diff === 0
          ? "Aucun écart : le stock est exact."
          : `Écart de ${diff > 0 ? "+" : "−"}${Math.abs(diff)} par rapport au stock enregistré (${dispo}).`;
      };
      lot.addEventListener("change", maj);
      quantite.addEventListener("input", maj);
    }
  }

  function initCaisse() {
    const form = $("#caisseForm");
    if (!form) return;
    const entree = $("#caisseRecherche");
    const resultats = $("#caisseResultats");
    const erreur = $("#caisseErreur");
    const zone = $("#panierLignes");
    const vide = $("#panierVide");
    const compte = $("#panierCompte");
    const totalEl = $("#panierTotal");
    const valider = $("#caisseValider");
    const recu = $("#montantRecu");
    const monnaie = $("#monnaie");
    const blocEspeces = $("#blocEspeces");

    let panier = [];       
    let trouves = [];
    let requete = null;
    let minuteur = null;

    const afficherErreur = (texte) => { erreur.textContent = texte; erreur.hidden = !texte; };
    const lotDe = (ligne) => ligne.med.lots.find((l) => l.id === ligne.lotId);
    const totalPanier = () => panier.reduce((s, l) => s + Number(l.med.prix) * l.qte, 0);

    function majTotaux() {
      const articles = panier.reduce((s, l) => s + l.qte, 0);
      compte.textContent = `${articles} article${articles > 1 ? "s" : ""}`;
      totalEl.textContent = ar(totalPanier());
      vide.hidden = panier.length > 0;
      valider.disabled = panier.length === 0;
      $$(".panier-ligne", zone).forEach((node, i) => {
        const l = panier[i];
        $("[data-soustotal]", node).textContent = ar(Number(l.med.prix) * l.qte);
      });
      const especes = form.elements.mode.value === "especes";
      blocEspeces.hidden = !especes;
      if (especes && recu.value !== "") {
        const reste = Number(recu.value) - totalPanier();
        monnaie.textContent = reste >= 0 ? `Monnaie à rendre : ${ar(reste)}` : `Montant insuffisant : il manque ${ar(-reste)}.`;
      } else {
        monnaie.textContent = "";
      }
    }

    function dessinerPanier() {
      zone.replaceChildren(...panier.map((ligne, index) => {
        const lot = lotDe(ligne);
        const select = el("select", { class: "form-select", name: "lot", "aria-label": `Lot de ${ligne.med.nom}` },
          ligne.med.lots.map((l) => el("option", {
            value: l.id,
            selected: l.id === ligne.lotId,
            text: `Lot ${l.numero} · exp. ${dateFr(l.date)} · ${l.stock} dispo`,
          })));
        const quantite = el("input", { type: "number", name: "quantite", min: "1", max: lot.stock, step: "1", value: ligne.qte, inputmode: "numeric", "aria-label": `Quantité de ${ligne.med.nom}` });
        const message = el("p", { class: "field-error", role: "alert", hidden: true });
        const regler = (valeur) => {
          const borne = lotDe(ligne).stock;
          let v = Math.floor(Number(valeur));
          message.hidden = true;
          if (!Number.isFinite(v) || v < 1) v = 1;
          if (v > borne) { v = borne; message.textContent = `Stock disponible sur ce lot : ${borne}.`; message.hidden = false; }
          ligne.qte = v;
          quantite.value = v;
          quantite.max = borne;
          majTotaux();
        };
        quantite.addEventListener("input", () => { if (quantite.value !== "") { ligne.qte = Math.max(1, Math.floor(Number(quantite.value)) || 1); majTotaux(); } });
        quantite.addEventListener("change", () => regler(quantite.value));
        select.addEventListener("change", () => { ligne.lotId = Number(select.value); regler(ligne.qte); });

        const moins = el("button", { type: "button", "aria-label": "Diminuer la quantité" }, "−");
        const plus = el("button", { type: "button", "aria-label": "Augmenter la quantité" }, "+");
        moins.addEventListener("click", () => regler(ligne.qte - 1));
        plus.addEventListener("click", () => regler(ligne.qte + 1));
        const retirer = el("button", { type: "button", class: "btn btn-icon-quiet", "aria-label": `Retirer ${ligne.med.nom}` }, icone("bi-trash"));
        retirer.addEventListener("click", () => { panier.splice(index, 1); dessinerPanier(); entree.focus(); });

        return el("div", { class: "panier-ligne" }, [
          el("div", { class: "ligne-top" }, [
            el("div", {}, [el("span", { class: "cell-title", text: ligne.med.nom }), el("span", { class: "cell-sub", text: `${ar(ligne.med.prix)} l’unité` })]),
            retirer,
          ]),
          el("div", { class: "mt-2" }, select),
          el("div", { class: "ligne-top mt-2" }, [el("div", { class: "qty" }, [moins, quantite, plus]), el("strong", { class: "num", "data-soustotal": "" })]),
          message,
        ]);
      }));
      majTotaux();
    }

    function ajouter(med) {
      const lot = med.lots[0]; 
      if (!lot) return;
      afficherErreur("");
      const existante = panier.find((l) => l.med.id === med.id && l.lotId === lot.id);
      if (existante) {
        if (existante.qte < lot.stock) existante.qte += 1;
        else afficherErreur(`Stock maximum atteint pour ${med.nom} (${lot.stock}).`);
      } else {
        panier.push({ med, lotId: lot.id, qte: 1 });
      }
      resultats.replaceChildren();
      entree.value = "";
      dessinerPanier();
      entree.focus();
    }

    function dessinerResultats(q) {
      if (!trouves.length) {
        resultats.replaceChildren(el("li", { class: "empty-inline" }, [icone("bi-search"), `Aucun médicament actif trouvé pour « ${q} ».`]));
        return;
      }
      resultats.replaceChildren(...trouves.map((m) => {
        const stock = m.lots.reduce((s, l) => s + l.stock, 0);
        const premier = m.lots[0];
        const bouton = el("button", { type: "button", disabled: !premier }, [
          el("span", {}, [
            el("strong", { text: m.nom }),
            el("small", { text: premier ? `${m.code ? m.code + " · " : ""}lot ${premier.numero} · exp. ${dateFr(premier.date)}` : "Aucun lot délivrable (périmé, bloqué ou épuisé)" }),
          ]),
          el("span", { class: "num" }, [ar(m.prix), el("small", { text: premier ? `${stock} en stock` : "Indisponible" })]),
        ]);
        bouton.addEventListener("click", () => ajouter(m));
        return el("li", {}, bouton);
      }));
    }

    async function chercher(q) {
      if (q.length < 2) { trouves = []; resultats.replaceChildren(); return trouves; }
      requete?.abort();
      requete = new AbortController();
      try {
        const reponse = await fetch(`${form.dataset.searchUrl}?q=${encodeURIComponent(q)}`, {
          headers: { Accept: "application/json" }, credentials: "same-origin", signal: requete.signal,
        });
        if (!reponse.ok) throw new Error(String(reponse.status));
        trouves = (await reponse.json()).results;
        afficherErreur("");
        dessinerResultats(q);
      } catch (err) {
        if (err.name !== "AbortError") afficherErreur("La recherche a échoué. Vérifiez la connexion puis réessayez.");
      }
      return trouves;
    }

    entree.addEventListener("input", () => {
      clearTimeout(minuteur);
      minuteur = setTimeout(() => chercher(entree.value.trim()), 250);
    });
    entree.addEventListener("keydown", async (e) => {
      if (e.key !== "Enter") return;
      e.preventDefault(); 
      clearTimeout(minuteur);
      const q = entree.value.trim();
      const liste = await chercher(q);
      const choisi = liste.find((m) => m.code === q && m.lots.length) || (liste.length === 1 && liste[0].lots.length ? liste[0] : null);
      if (choisi) ajouter(choisi);
      else if (liste.length) $("button:not([disabled])", resultats)?.focus();
    });

    form.addEventListener("change", (e) => { if (e.target.name === "mode") majTotaux(); });
    recu.addEventListener("input", majTotaux);
    form.addEventListener("submit", (e) => {
      const invalide = panier.some((l) => l.qte < 1 || l.qte > lotDe(l).stock);
      if (!panier.length || invalide) {
        e.preventDefault();
        e.stopImmediatePropagation();
        afficherErreur(panier.length ? "Une quantité dépasse le stock du lot choisi." : "Ajoutez au moins un produit.");
      }
    }, true);
    window.addEventListener("pg:retour-page", majTotaux);
    majTotaux();
  }

  function initGraphique() {
    const boite = $("#chartVentes");
    const source = $("#donneesVentes");
    if (!boite || !source) return;
    const donnees = JSON.parse(source.textContent);
    const NS = "http://www.w3.org/2000/svg";
    const svg = (tag, attrs = {}) => {
      const node = document.createElementNS(NS, tag);
      Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
      return node;
    };
    let periode = "j30";

    function dessiner() {
      const { labels, values } = donnees[periode];
      const L = boite.clientWidth || 600;
      const H = boite.clientHeight || 280;
      const marge = { haut: 12, droite: 12, bas: 28, gauche: 64 };
      const max = Math.max(...values, 0);
      const total = values.reduce((s, v) => s + v, 0);
      boite.setAttribute("aria-label", `Ventes sur ${values.length} jours : ${ar(total)} au total.`);
      if (max === 0) {
        boite.replaceChildren(el("div", { class: "chart-vide" }, [el("span", {}, [icone("bi-graph-up"), " Aucune vente sur cette période."])]));
        return;
      }
      const echelle = Math.ceil(max / 4 / 1000) * 1000 || 1;
      const haut = echelle * 4;
      const x = (i) => marge.gauche + (values.length === 1 ? 0 : (i * (L - marge.gauche - marge.droite)) / (values.length - 1));
      const y = (v) => marge.haut + (H - marge.haut - marge.bas) * (1 - v / haut);

      const s = svg("svg", { viewBox: `0 0 ${L} ${H}`, "aria-hidden": "true" });
      for (let i = 0; i <= 4; i += 1) {
        const v = echelle * i;
        s.append(svg("line", { class: "grid-line", x1: marge.gauche, x2: L - marge.droite, y1: y(v), y2: y(v) }));
        const t = svg("text", { class: "axis-label", x: marge.gauche - 8, y: y(v) + 4, "text-anchor": "end" });
        t.textContent = nombre.format(v);
        s.append(t);
      }
      const pas = Math.ceil(values.length / 7);
      labels.forEach((nom, i) => {
        if (i % pas !== 0 && i !== values.length - 1) return;
        const t = svg("text", { class: "axis-label", x: x(i), y: H - 8, "text-anchor": i === 0 ? "start" : i === values.length - 1 ? "end" : "middle" });
        t.textContent = nom;
        s.append(t);
      });
      const chemin = values.map((v, i) => `${i ? "L" : "M"}${x(i)},${y(v)}`).join(" ");
      s.append(svg("path", { class: "aire", d: `${chemin} L${x(values.length - 1)},${y(0)} L${x(0)},${y(0)} Z` }));
      s.append(svg("path", { class: "serie", d: chemin }));
      values.forEach((v, i) => {
        const point = svg("circle", { class: "point", cx: x(i), cy: y(v), r: 4, tabindex: "0" });
        const info = svg("title");
        info.textContent = `${labels[i]} : ${ar(v)}`;
        point.append(info);
        s.append(point);
      });
      boite.replaceChildren(s);
    }

    $$("[data-periode]").forEach((bouton) => bouton.addEventListener("click", () => {
      periode = bouton.dataset.periode;
      $$("[data-periode]").forEach((b) => {
        const actif = b === bouton;
        b.classList.toggle("btn-primary", actif);
        b.classList.toggle("btn-outline-secondary", !actif);
        b.setAttribute("aria-pressed", String(actif));
      });
      dessiner();
    }));
    let attente;
    window.addEventListener("resize", () => { clearTimeout(attente); attente = setTimeout(dessiner, 150); });
    dessiner();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initMenu();
    initFormulaires();
    initPhoto();
    initCommande();
    initStock();
    initCaisse();
    initGraphique();
  });
})();
