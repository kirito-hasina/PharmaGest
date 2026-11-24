from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from achats.models import CommandeAchat
from .forms import FournisseurForm
from utilisateurs.models import JournalAudit
from utilisateurs.permissions import roles_required

from .models import Fournisseur


@roles_required('administrateur', 'gestionnaire de stock')
def liste_fournisseurs(request):
    qs = Fournisseur.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(raison_sociale__icontains=q) | Q(telephone__icontains=q))
    page = Paginator(qs.order_by("raison_sociale"), 20).get_page(request.GET.get("page"))
    return render(request, "fournisseurs/liste.html", {"fournisseurs": page, "page_obj": page})


@roles_required('administrateur', 'gestionnaire de stock')
def creer_fournisseur(request):
    form = FournisseurForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        fournisseur = form.save()
        JournalAudit.objects.create(action="Fournisseur créé", objet_type=f"Fournisseur {fournisseur.pk}", utilisateur=request.user)
        messages.success(request, "Fournisseur enregistré.")
        return redirect("fournisseurs:detail", pk=fournisseur.pk)
    return render(request, "fournisseurs/creer.html", {"form": form})


@roles_required('administrateur', 'gestionnaire de stock')
def detail_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    commandes = CommandeAchat.objects.filter(fournisseur=fournisseur).prefetch_related("lignes", "receptions__lignes__ligne_achat")
    total = commandes.aggregate(total=Sum("montant_total"))["total"] or 0
    total_recu = sum(ligne.quantite_recue * ligne.ligne_achat.prix_achat for commande in commandes for reception in commande.receptions.filter(validee=True) for ligne in reception.lignes.all())
    return render(request, "fournisseurs/detail.html", {"fournisseur": fournisseur, "commandes": commandes, "total_commandes": total, "total_receptions": total_recu})


@roles_required('administrateur', 'gestionnaire de stock')
def modifier_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    form = FournisseurForm(request.POST or None, instance=fournisseur)
    if request.method == "POST" and form.is_valid():
        form.save()
        JournalAudit.objects.create(action="Fournisseur modifié", objet_type=f"Fournisseur {pk}", utilisateur=request.user)
        messages.success(request, "Fournisseur modifié.")
        return redirect("fournisseurs:detail", pk=pk)
    return render(request, "fournisseurs/modifier.html", {"fournisseur": fournisseur, "form": form})


@roles_required('administrateur', 'gestionnaire de stock')
def desactiver_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    if request.method == "POST":
        fournisseur.actif = not fournisseur.actif
        fournisseur.save(update_fields=["actif"])
        JournalAudit.objects.create(action="Fournisseur activé" if fournisseur.actif else "Fournisseur désactivé", objet_type=f"Fournisseur {pk}", utilisateur=request.user)
        messages.success(request, "Statut du fournisseur mis à jour.")
    return redirect("fournisseurs:detail", pk=pk)
