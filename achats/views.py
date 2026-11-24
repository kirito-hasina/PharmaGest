from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from fournisseurs.models import Fournisseur
from medicaments.models import Medicament
from stock.models import LotStock, MouvementStock
from utilisateurs.permissions import roles_required
from utilisateurs.models import JournalAudit

from .models import CommandeAchat, LigneAchat, LigneReception, ReceptionAchat


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def ecran_reception(request):
    return render(request, "achats/reception.html", {"commandes": CommandeAchat.objects.exclude(statut__in=[CommandeAchat.Statut.RECUE, CommandeAchat.Statut.ANNULEE])})


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def liste_commandes(request):
    qs = CommandeAchat.objects.select_related("fournisseur", "utilisateur").order_by("-pk")
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "achats/liste.html", {"commandes": page, "page_obj": page})


def _lire_lignes_commande(request):
    """Valide les lignes postées (médicament, quantité, prix) ; renvoie (lignes, total) ou lève ValueError."""
    ids, qtes, prix = request.POST.getlist("medicament"), request.POST.getlist("quantite"), request.POST.getlist("prix")
    if not ids or len(ids) != len(qtes) or len(ids) != len(prix):
        raise ValueError
    lignes, total = [], Decimal("0")
    for med_id, qte, prix_unitaire in zip(ids, qtes, prix):
        try:
            med = Medicament.objects.get(pk=med_id, statut=Medicament.Statut.ACTIF)
            qte = int(qte)
            prix_unitaire = Decimal(prix_unitaire.replace(",", "."))
        except (Medicament.DoesNotExist, InvalidOperation):
            raise ValueError
        if qte <= 0 or prix_unitaire <= 0:
            raise ValueError
        lignes.append((med, qte, prix_unitaire))
        total += qte * prix_unitaire
    return lignes, total


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def creer_commande(request):
    fournisseurs = Fournisseur.objects.filter(actif=True)
    medicaments = Medicament.objects.filter(statut=Medicament.Statut.ACTIF)
    if request.method == "POST":
        fournisseur = get_object_or_404(Fournisseur, pk=request.POST.get("fournisseur"), actif=True)
        try:
            lignes, total = _lire_lignes_commande(request)
        except ValueError:
            messages.error(request, "Vérifiez les médicaments, quantités et prix saisis.")
        else:
            with transaction.atomic():
                commande = CommandeAchat.objects.create(
                    numero=f"ACH-{timezone.localdate():%Y%m%d}-{timezone.now():%H%M%S%f}",
                    statut=CommandeAchat.Statut.BROUILLON if request.POST.get("statut") == "brouillon" else CommandeAchat.Statut.ENVOYEE,
                    fournisseur=fournisseur, utilisateur=request.user, montant_total=total,
                )
                LigneAchat.objects.bulk_create([LigneAchat(commande=commande, medicament=m, quantite_commandee=q, prix_achat=p) for m, q, p in lignes])
                JournalAudit.objects.create(action="Commande créée", objet_type=f"Commande {commande.numero}", utilisateur=request.user)
            messages.success(request, f"Commande {commande.numero} enregistrée.")
            return redirect("achats:detail", pk=commande.pk)
    return render(request, "achats/creer.html", {"fournisseurs": fournisseurs, "medicaments": medicaments})

@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def detail_commande(request, pk):
    return render(request, "achats/detail.html", {"commande": get_object_or_404(CommandeAchat.objects.select_related("fournisseur"), pk=pk)})


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def modifier_commande(request, pk):
    commande = get_object_or_404(CommandeAchat.objects.select_related("fournisseur").prefetch_related("lignes__medicament"), pk=pk)
    if commande.statut != CommandeAchat.Statut.BROUILLON:
        messages.error(request, "Seules les commandes en brouillon peuvent être modifiées.")
        return redirect("achats:detail", pk=pk)
    if request.method == "POST":
        fournisseur = get_object_or_404(Fournisseur, pk=request.POST.get("fournisseur"), actif=True)
        try:
            lignes, total = _lire_lignes_commande(request)
        except ValueError:
            messages.error(request, "Vérifiez les médicaments, quantités et prix saisis.")
        else:
            with transaction.atomic():
                verrouillee = CommandeAchat.objects.select_for_update().get(pk=pk)
                if verrouillee.statut != CommandeAchat.Statut.BROUILLON:
                    messages.error(request, "Cette commande n’est plus modifiable.")
                    return redirect("achats:detail", pk=pk)
                verrouillee.fournisseur = fournisseur
                verrouillee.montant_total = total
                if request.POST.get("statut") != "brouillon":
                    verrouillee.statut = CommandeAchat.Statut.ENVOYEE
                verrouillee.save(update_fields=["fournisseur", "montant_total", "statut"])
                verrouillee.lignes.all().delete()
                LigneAchat.objects.bulk_create([LigneAchat(commande=verrouillee, medicament=m, quantite_commandee=q, prix_achat=p) for m, q, p in lignes])
                JournalAudit.objects.create(action="Commande modifiée", objet_type=f"Commande {verrouillee.numero}", utilisateur=request.user)
            messages.success(request, "Commande mise à jour.")
            return redirect("achats:detail", pk=pk)
    return render(request, "achats/creer.html", {
        "commande": commande,
        "fournisseurs": Fournisseur.objects.filter(actif=True),
        "medicaments": Medicament.objects.filter(statut=Medicament.Statut.ACTIF),
    })


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def valider_commande(request, pk):
    """Brouillon -> Commandée (étape 7 du module F). Le stock ne bouge pas : seule la réception l'augmente (RG04)."""
    get_object_or_404(CommandeAchat, pk=pk)
    if request.method == "POST":
        with transaction.atomic():
            commande = CommandeAchat.objects.select_for_update().get(pk=pk)
            if commande.statut != CommandeAchat.Statut.BROUILLON:
                messages.error(request, "Seule une commande en brouillon peut être validée.")
            elif not commande.lignes.exists():
                messages.error(request, "Une commande sans ligne ne peut pas être validée.")
            else:
                commande.statut = CommandeAchat.Statut.ENVOYEE
                commande.save(update_fields=["statut"])
                JournalAudit.objects.create(action="Commande validée", objet_type=f"Commande {commande.numero}", utilisateur=request.user)
                messages.success(request, f"Commande {commande.numero} validée : elle peut maintenant être réceptionnée.")
    return redirect("achats:detail", pk=pk)

@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def annuler_commande(request, pk):
    commande = get_object_or_404(CommandeAchat, pk=pk)
    if request.method == "POST":
        if commande.statut not in (CommandeAchat.Statut.BROUILLON, CommandeAchat.Statut.ENVOYEE, CommandeAchat.Statut.PARTIELLE):
            messages.error(request, "Cette commande ne peut plus être annulée.")
        else:
            with transaction.atomic():
                commande = CommandeAchat.objects.select_for_update().get(pk=pk)
                commande.statut = CommandeAchat.Statut.ANNULEE
                commande.save(update_fields=["statut"])
                JournalAudit.objects.create(action="Commande annulée", objet_type=f"Commande {commande.numero}", utilisateur=request.user)
            messages.success(request, "Commande annulée ; les réceptions déjà faites restent dans l’historique.")
    return redirect("achats:detail", pk=pk)


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def reception_commande(request, pk):
    commande = get_object_or_404(CommandeAchat.objects.prefetch_related("lignes__lignes_reception"), pk=pk)
    if request.method == "POST":
        if commande.statut not in (CommandeAchat.Statut.ENVOYEE, CommandeAchat.Statut.PARTIELLE):
            messages.error(request, "Seules les commandes envoyées ou partiellement réceptionnées peuvent être réceptionnées.")
            return redirect("achats:detail", pk=pk)
        try:
            entries = []
            for ligne in commande.lignes.all():
                qte = int(request.POST.get(f"q_{ligne.pk}", "0"))
                reste = ligne.quantite_commandee - sum(r.quantite_recue for r in ligne.lignes_reception.filter(reception__validee=True))
                if qte < 0 or qte > reste:
                    raise ValueError
                if qte:
                    lotno = request.POST.get(f"lot_{ligne.pk}", "").strip()
                    exp = request.POST.get(f"exp_{ligne.pk}", "")
                    if not lotno or not exp or date.fromisoformat(exp) <= timezone.localdate():
                        raise ValueError
                    entries.append((ligne, qte, lotno, exp))
            if not entries:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "La réception contient une quantité, un lot ou une péremption invalide.")
        else:
            try:
                with transaction.atomic():
                    commande = CommandeAchat.objects.select_for_update().get(pk=pk)
                    if commande.statut in (CommandeAchat.Statut.RECUE, CommandeAchat.Statut.ANNULEE):
                        raise ValueError("Cette commande ne peut plus être réceptionnée.")
                    for ligne, qte, _, _ in entries:
                        ligne_verrouillee = LigneAchat.objects.select_for_update().get(pk=ligne.pk)
                        deja_recu = sum(r.quantite_recue for r in LigneReception.objects.filter(ligne_achat=ligne_verrouillee, reception__validee=True))
                        if qte > ligne_verrouillee.quantite_commandee - deja_recu:
                            raise ValueError("La quantité dépasse le reliquat à recevoir.")
                    reception = ReceptionAchat.objects.create(commande=commande, utilisateur=request.user, validee=True)
                    for ligne, qte, lotno, exp in entries:
                        expiration = date.fromisoformat(exp)
                        stocklot, _ = LotStock.objects.get_or_create(medicament=ligne.medicament, numero_lot=lotno, defaults={"date_peremption": expiration})
                        if stocklot.date_peremption != expiration:
                            raise ValueError("Numéro de lot déjà associé à une autre péremption.")
                        stocklot.quantite_disponible += qte
                        stocklot.quantite_recue += qte
                        stocklot.save(update_fields=["quantite_disponible", "quantite_recue"])
                        LigneReception.objects.create(reception=reception, ligne_achat=ligne, quantite_recue=qte, numero_lot=lotno, date_peremption=exp)
                        MouvementStock.objects.create(type=MouvementStock.Type.ENTREE, quantite=qte, motif=f"Réception {commande.numero}", medicament=ligne.medicament, lot=stocklot, utilisateur=request.user)
                    complets = all(l.quantite_commandee <= sum(r.quantite_recue for r in l.lignes_reception.filter(reception__validee=True)) for l in commande.lignes.all())
                    commande.statut = CommandeAchat.Statut.RECUE if complets else CommandeAchat.Statut.PARTIELLE
                    commande.save(update_fields=["statut"])
                    JournalAudit.objects.create(action="Réception de commande", objet_type=f"Commande {commande.numero}", utilisateur=request.user)
                messages.success(request, "Réception validée et stock mis à jour.")
                return redirect("achats:detail", pk=pk)
            except ValueError as exc:
                messages.error(request, str(exc))
    return render(request, "achats/reception.html", {"commande": commande})


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def bon_commande(request, pk):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    commande = get_object_or_404(CommandeAchat.objects.prefetch_related("lignes__medicament"), pk=pk)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="commande-{commande.numero}.pdf"'
    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setTitle(f"Bon de commande {commande.numero}")
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(45, 795, "PharmaGest — Bon de commande")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(45, 775, f"N° {commande.numero} · Fournisseur : {commande.fournisseur}")
    pdf.drawString(45, 758, f"Créé par {commande.utilisateur} · {commande.get_statut_display()}")
    y = 720
    for ligne in commande.lignes.all():
        pdf.drawString(45, y, str(ligne.medicament)[:50])
        pdf.drawRightString(390, y, str(ligne.quantite_commandee))
        pdf.drawRightString(485, y, f"{ligne.prix_achat:,.2f} Ar")
        pdf.drawRightString(565, y, f"{ligne.quantite_commandee * ligne.prix_achat:,.2f} Ar")
        y -= 18
        if y < 55:
            pdf.showPage(); y = 800; pdf.setFont("Helvetica", 10)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawRightString(565, y - 12, f"Total : {commande.montant_total:,.2f} Ar")
    pdf.save()
    return response


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def bon_reception(request, pk, reception_pk):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    reception = get_object_or_404(ReceptionAchat.objects.select_related("commande__fournisseur", "utilisateur").prefetch_related("lignes__ligne_achat__medicament"), pk=reception_pk, commande_id=pk, validee=True)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="reception-{reception.pk}.pdf"'
    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setTitle(f"Bon de réception {reception.pk}")
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(45, 795, "PharmaGest — Bon de réception")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(45, 775, f"Commande {reception.commande.numero} · {reception.commande.fournisseur}")
    pdf.drawString(45, 758, f"Réception {reception.pk} · {reception.date_reception:%d/%m/%Y %H:%M} · {reception.utilisateur}")
    y = 720
    for ligne in reception.lignes.all():
        pdf.drawString(45, y, f"{ligne.ligne_achat.medicament} · lot {ligne.numero_lot}"[:60])
        pdf.drawRightString(400, y, str(ligne.quantite_recue))
        pdf.drawRightString(565, y, ligne.date_peremption.strftime("%d/%m/%Y"))
        y -= 18
        if y < 55:
            pdf.showPage(); y = 800; pdf.setFont("Helvetica", 10)
    pdf.save()
    return response
