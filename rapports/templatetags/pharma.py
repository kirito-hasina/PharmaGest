"""Filtres et balises d'affichage de PharmaGest (montants en Ariary, lots, formulaires Bootstrap)."""
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django import forms, template
from django.utils import timezone

register = template.Library()

SEUIL_PEREMPTION_PROCHE = 90  # jours, identique au tableau de bord et aux alertes


def _decimal(valeur):
    try:
        return Decimal(str(valeur))
    except (InvalidOperation, ValueError, TypeError):
        return None


@register.filter
def ar(valeur):
    """12500 -> « 12 500 Ar » ; 12500.5 -> « 12 500,50 Ar »."""
    nombre = _decimal(valeur)
    if nombre is None:
        return "—"
    texte = f"{nombre:,.0f}" if nombre == nombre.to_integral_value() else f"{nombre:,.2f}"
    texte = texte.replace(",", "\u202f").replace(".", ",")
    return f"{texte}\u00a0Ar"


@register.filter
def mul(valeur, facteur):
    a, b = _decimal(valeur), _decimal(facteur)
    return a * b if a is not None and b is not None else ""


@register.filter
def jours_restants(date_limite):
    return (date_limite - timezone.localdate()).days


@register.inclusion_tag("partials/_lot_badge.html")
def lot_badge(lot):
    """Statut d'un lot : texte + icône + couleur (la couleur seule ne porte jamais le sens)."""
    aujourdhui = timezone.localdate()
    if lot.bloque:
        code, libelle, icone = "bloque", "Bloqué", "bi-slash-circle"
    elif lot.date_peremption < aujourdhui:
        code, libelle, icone = "perime", "Périmé", "bi-x-octagon"
    elif lot.quantite_disponible == 0:
        code, libelle, icone = "rupture", "Épuisé", "bi-x-circle"
    elif lot.date_peremption <= aujourdhui + timedelta(days=SEUIL_PEREMPTION_PROCHE):
        code, libelle, icone = "proche", "Péremption proche", "bi-clock"
    else:
        code, libelle, icone = "valide", "Délivrable", "bi-check-circle"
    return {"code": code, "libelle": libelle, "icone": icone}


@register.filter
def stock_delivrable(medicament):
    aujourdhui = timezone.localdate()
    return sum(
        lot.quantite_disponible
        for lot in medicament.lots.all()
        if not lot.bloque and lot.date_peremption >= aujourdhui
    )


@register.filter
def qte_retournee(ligne_vente):
    return sum(retour.quantite_retournee for retour in ligne_vente.retours.all())


@register.filter
def qte_retournable(ligne_vente):
    return ligne_vente.quantite - qte_retournee(ligne_vente)


@register.filter
def qte_recue(ligne_achat):
    return sum(r.quantite_recue for r in ligne_achat.lignes_reception.filter(reception__validee=True))


@register.filter
def reste_a_recevoir(ligne_achat):
    return max(ligne_achat.quantite_commandee - qte_recue(ligne_achat), 0)


@register.filter
def ca_ventes(ventes):
    """Chiffre d'affaires = ventes payées uniquement (ni brouillons ni annulations)."""
    return sum((v.total for v in ventes if v.statut == "payee"), Decimal("0"))


@register.filter
def total_achats(commandes):
    return sum((c.montant_total for c in commandes if c.statut != "annulee"), Decimal("0"))


@register.simple_tag(takes_context=True)
def page_url(context, numero):
    """Lien de pagination qui conserve la recherche et les filtres en cours."""
    parametres = context["request"].GET.copy()
    parametres["page"] = numero
    return "?" + parametres.urlencode()


@register.filter
def bs(champ):
    """Rend un champ de formulaire Django avec les classes Bootstrap adaptées."""
    widget = champ.field.widget
    if getattr(widget, "input_type", "") == "checkbox":
        classe = "form-check-input"
    elif isinstance(widget, forms.Select):
        classe = "form-select"
    else:
        classe = "form-control"
    attrs = {"class": classe}
    if champ.errors:
        attrs["class"] += " is-invalid"
        attrs["aria-invalid"] = "true"
    return champ.as_widget(attrs=attrs)


@register.simple_tag(takes_context=True)
def posted(context, prefix, pk):
    """Valeur postée pour un champ dynamique « prefixe_pk » (ré-affichage après une erreur)."""
    return context["request"].POST.get(f"{prefix}_{pk}", "")


@register.filter
def absolu(valeur):
    try:
        return abs(int(valeur))
    except (TypeError, ValueError):
        return valeur
