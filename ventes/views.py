import json
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models import F
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from clients.models import Client
from medicaments.models import Medicament
from stock.models import LotStock, MouvementStock
from utilisateurs.models import JournalAudit
from utilisateurs.permissions import roles_required

from .models import LigneVente, Paiement, Vente


@roles_required('administrateur', 'caissier', 'pharmacien responsable')
def recherche_caisse(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"results": []})
    today = timezone.localdate()
    meds = Medicament.objects.filter(statut=Medicament.Statut.ACTIF).filter(Q(nom_commercial__icontains=q) | Q(code_barres__icontains=q))[:10]
    results = []
    for med in meds:
        lots = LotStock.objects.filter(medicament=med, quantite_disponible__gt=0, bloque=False, date_peremption__gte=today).order_by("date_peremption")
        results.append({"id": med.pk, "nom": med.nom_commercial, "code": med.code_barres or "", "prix": str(med.prix_vente), "lots": [{"id": l.pk, "numero": l.numero_lot, "date": l.date_peremption.isoformat(), "stock": l.quantite_disponible} for l in lots]})
    return JsonResponse({"results": results})


@roles_required('administrateur', 'caissier', 'pharmacien responsable')
def retours(request):
    from .models import RetourVente
    return render(request, "ventes/retours.html", {"retours": RetourVente.objects.select_related("utilisateur", "ligne_vente__vente")})


@roles_required('administrateur', 'caissier', 'pharmacien responsable')
def liste_ventes(request):
    qs = Vente.objects.select_related("client", "utilisateur").order_by("-date_vente")
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "ventes/liste.html", {"ventes": page, "page_obj": page})


def _sortir_stock_vente(vente, utilisateur):
    for ligne in vente.lignes.select_related("lot__medicament"):
        lot = ligne.lot
        updated = LotStock.objects.filter(
            pk=lot.pk,
            quantite_disponible__gte=ligne.quantite,
            bloque=False,
            date_peremption__gte=timezone.localdate(),
            medicament__statut=Medicament.Statut.ACTIF,
        ).update(quantite_disponible=F("quantite_disponible") - ligne.quantite)
        if not updated:
            raise ValueError(f"Stock modifié ou lot non délivrable : {lot}.")
        MouvementStock.objects.create(
            type=MouvementStock.Type.SORTIE,
            quantite=ligne.quantite,
            motif=f"Vente {vente.numero}",
            medicament=lot.medicament,
            lot=lot,
            utilisateur=utilisateur,
        )


@roles_required('administrateur', 'caissier', 'pharmacien responsable')
def creer_vente(request):
    lots = LotStock.objects.filter(quantite_disponible__gt=0, bloque=False, date_peremption__gte=timezone.localdate(), medicament__statut=Medicament.Statut.ACTIF).select_related("medicament").order_by("date_peremption")
    if request.method == "POST":
        try:
            lot_ids, quantities = request.POST.getlist("lot"), request.POST.getlist("quantite")
            if not lot_ids or len(lot_ids) != len(quantities):
                raise ValueError("Ajoutez au moins un produit.")
            requested = {}
            for lot_id, qty in zip(lot_ids, quantities):
                qty = int(qty)
                if qty <= 0: raise ValueError("Les quantités doivent être positives.")
                lot_id = int(lot_id)
                requested[lot_id] = requested.get(lot_id, 0) + qty
            items = list(requested.items())
            mode = request.POST.get("mode")
            modes = {"especes": Paiement.Mode.ESPECES, "mobile_money": Paiement.Mode.MOBILE_MONEY, "carte": Paiement.Mode.CARTE, "cheque": Paiement.Mode.CHEQUE}
            if mode not in modes: raise ValueError("Choisissez un mode de paiement valide.")
            client_id = request.POST.get("client") or None
        except (ValueError, TypeError) as exc:
            messages.error(request, str(exc))
        else:
            try:
                with transaction.atomic():
                    lignes, total = [], Decimal("0.00")
                    for lot_id, qty in items:
                        lot = LotStock.objects.select_for_update().select_related("medicament").get(pk=lot_id)
                        if lot.bloque or lot.date_peremption < timezone.localdate() or lot.medicament.statut != Medicament.Statut.ACTIF or qty > lot.quantite_disponible:
                            raise ValueError(f"Stock insuffisant ou lot non délivrable : {lot}.")
                        lignes.append((lot, qty, lot.medicament.prix_vente))
                        total += qty * lot.medicament.prix_vente
                    client = get_object_or_404(Client, pk=client_id, actif=True) if client_id else None
                    sale = Vente.objects.create(numero=f"VT-{timezone.localdate():%Y%m%d}-{timezone.now():%H%M%S%f}", utilisateur=request.user, client=client, total=total)
                    for lot, qty, price in lignes:
                        LigneVente.objects.create(vente=sale, lot=lot, quantite=qty, prix_applique=price)
                    simulation = mode != Paiement.Mode.ESPECES
                    Paiement.objects.create(
                        vente=sale,
                        mode=modes[mode],
                        montant=total,
                        statut=Paiement.Statut.VALIDE,
                        utilisateur=request.user,
                    )
                    sale.statut = Vente.Statut.PAYEE
                    sale.save(update_fields=["statut"])
                    _sortir_stock_vente(sale, request.user)
                    JournalAudit.objects.create(
                        action="Paiement électronique simulé" if simulation else "Vente enregistrée",
                        objet_type=f"Vente {sale.numero}",
                        utilisateur=request.user,
                    )
                if simulation:
                    messages.success(request, f"Paiement électronique simulé avec succès. Vente {sale.numero} validée et stock mis à jour.")
                else:
                    messages.success(request, f"Vente {sale.numero} validée. Reçu disponible.")
                return redirect("ventes:detail", pk=sale.pk)
            except (ValueError, LotStock.DoesNotExist) as exc:
                messages.error(request, str(exc))
    return render(request, "ventes/creer.html", {"lots": lots, "clients": Client.objects.filter(actif=True)})


@roles_required('administrateur', 'caissier', 'pharmacien responsable')
def detail_vente(request, pk):
    return render(request, "ventes/detail.html", {"vente": get_object_or_404(Vente.objects.prefetch_related("lignes__lot__medicament", "paiements"), pk=pk)})


@roles_required('administrateur', 'caissier', 'pharmacien responsable')
def recu_vente(request, pk):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    vente = get_object_or_404(Vente.objects.prefetch_related("lignes__lot__medicament", "paiements"), pk=pk)
    if vente.statut != Vente.Statut.PAYEE:
        messages.error(request, "Un reçu ne peut être produit qu’après confirmation du paiement.")
        return redirect("ventes:detail", pk=pk)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="recu-{vente.numero}.pdf"'
    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setTitle(f"Reçu {vente.numero}")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(48, 790, "PharmaGest — Reçu de vente")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(48, 768, f"N° {vente.numero} · {timezone.localtime(vente.date_vente):%d/%m/%Y %H:%M}")
    pdf.drawString(48, 748, f"Caissier : {vente.utilisateur}")
    paiement = vente.paiements.first()
    if paiement:
        detail_paiement = paiement.get_mode_display()
        if paiement.mode != Paiement.Mode.ESPECES:
            detail_paiement += " (simulation academique)"
        pdf.drawString(48, 728, f"Paiement : {detail_paiement}")
    y = 710
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(48, y, "Médicament / lot")
    pdf.drawString(330, y, "Qté")
    pdf.drawString(390, y, "Prix unitaire")
    pdf.drawString(490, y, "Sous-total")
    y -= 18
    pdf.setFont("Helvetica", 9)
    for ligne in vente.lignes.all():
        pdf.drawString(48, y, f"{ligne.lot.medicament} · {ligne.lot.numero_lot}"[:48])
        pdf.drawRightString(355, y, str(ligne.quantite))
        pdf.drawRightString(455, y, f"{ligne.prix_applique:,.2f} Ar")
        pdf.drawRightString(550, y, f"{ligne.prix_applique * ligne.quantite:,.2f} Ar")
        y -= 16
        if y < 90:
            pdf.showPage()
            y = 790
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawRightString(550, y - 10, f"Total payé : {vente.total:,.2f} Ar")
    pdf.setFont("Helvetica", 8)
    pdf.drawString(48, 45, "Document de gestion interne. Les mentions fiscales applicables doivent être validées par la pharmacie.")
    pdf.save()
    return response


@roles_required('administrateur', 'caissier', 'pharmacien responsable')
def payer_vente(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    if request.method == "POST" and vente.statut == Vente.Statut.EN_COURS:
        mode = request.POST.get("mode")
        modes = {choice for choice, _ in Paiement.Mode.choices}
        if mode not in modes:
            messages.error(request, "Choisissez un mode de paiement valide.")
        else:
            try:
                with transaction.atomic():
                    vente = Vente.objects.select_for_update().get(pk=pk)
                    if vente.statut != Vente.Statut.EN_COURS:
                        raise ValueError("Cette vente est déjà réglée.")
                    _sortir_stock_vente(vente, request.user)
                    paiement = vente.paiements.select_for_update().filter(
                        statut=Paiement.Statut.EN_ATTENTE
                    ).first()
                    if paiement:
                        paiement.mode = mode
                        paiement.statut = Paiement.Statut.VALIDE
                        paiement.utilisateur = request.user
                        paiement.save(update_fields=["mode", "statut", "utilisateur"])
                    else:
                        Paiement.objects.create(
                            vente=vente,
                            mode=mode,
                            montant=vente.total,
                            statut=Paiement.Statut.VALIDE,
                            utilisateur=request.user,
                        )
                    vente.statut = Vente.Statut.PAYEE
                    vente.save(update_fields=["statut"])
                    JournalAudit.objects.create(
                        action="Paiement simulé" if mode != Paiement.Mode.ESPECES else "Paiement validé",
                        objet_type=f"Vente {vente.numero}",
                        utilisateur=request.user,
                    )
            except (ValueError, Vente.DoesNotExist) as exc:
                messages.error(request, str(exc))
            else:
                label = "Paiement électronique simulé avec succès" if mode != Paiement.Mode.ESPECES else "Paiement enregistré"
                messages.success(request, f"{label}. La vente est validée et le stock a été mis à jour.")
                return redirect("ventes:detail", pk=vente.pk)
    return render(request, "ventes/paiement.html", {"vente": vente})


@roles_required('administrateur', 'caissier', 'pharmacien responsable')
def retour_vente(request, pk):
    from .models import RetourVente
    vente = get_object_or_404(Vente.objects.prefetch_related("lignes__retours"), pk=pk)
    if request.method == "POST" and vente.statut == Vente.Statut.PAYEE:
        try:
            with transaction.atomic():
                ligne = LigneVente.objects.select_for_update().get(pk=request.POST.get("ligne"), vente=vente)
                qte = int(request.POST.get("quantite", "0"))
                deja_retourne = sum(RetourVente.objects.filter(ligne_vente=ligne).values_list("quantite_retournee", flat=True))
                motif = request.POST.get("motif", "").strip()
                if qte <= 0 or qte + deja_retourne > ligne.quantite or not motif:
                    raise ValueError
                RetourVente.objects.create(ligne_vente=ligne, quantite_retournee=qte, motif=motif, remise_en_stock=False, utilisateur=request.user)
                JournalAudit.objects.create(action="Retour de vente", objet_type=f"Vente {vente.numero}", utilisateur=request.user)
        except (ValueError, Vente.DoesNotExist, LigneVente.DoesNotExist):
            messages.error(request, "Vérifiez la ligne, la quantité retournée et le motif.")
        else:
            messages.success(request, "Retour enregistré. Le produit reste exclu du stock délivrable en attente de contrôle.")
            return redirect("ventes:detail", pk=pk)
    return render(request, "ventes/retour.html", {"vente": vente})
