from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from medicaments.models import Medicament
from utilisateurs.models import JournalAudit
from utilisateurs.permissions import roles_required

from .models import LotStock, MouvementStock


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def liste_stock(request):
    lots = LotStock.objects.select_related("medicament").order_by("date_peremption")
    statut = request.GET.get("stk")
    today = timezone.localdate()
    if statut == "rupture":
        lots = lots.filter(quantite_disponible=0)
    elif statut == "faible":
        faibles = Medicament.objects.filter(statut=Medicament.Statut.ACTIF).annotate(stock_total=Coalesce(Sum("lots__quantite_disponible"), 0)).filter(stock_total__lte=F("seuil_alerte")).values("pk")
        lots = lots.filter(medicament_id__in=faibles)
    exp = request.GET.get("exp")
    if exp == "proche":
        lots = lots.filter(date_peremption__gte=today, date_peremption__lte=today + timezone.timedelta(days=90), quantite_disponible__gt=0)
    elif exp == "perime":
        lots = lots.filter(date_peremption__lt=today)
    return render(request, "stock/liste.html", {"lots": lots})


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def lots(request):
    page = Paginator(LotStock.objects.select_related("medicament").order_by("date_peremption"), 20).get_page(request.GET.get("page"))
    return render(request, "stock/lots.html", {"lots": page, "page_obj": page})


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def mouvements(request):
    qs = MouvementStock.objects.select_related("medicament", "lot", "utilisateur")
    kind = request.GET.get("type")
    if kind in MouvementStock.Type.values:
        qs = qs.filter(type=kind)
    q = request.GET.get("q", "").strip()
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(medicament__nom_commercial__icontains=q) | Q(lot__numero_lot__icontains=q) | Q(utilisateur__username__icontains=q))
    return render(request, "stock/mouvements.html", {"mouvements": qs[:200], "types": MouvementStock.Type.choices})


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def detail_lot(request, pk):
    lot = get_object_or_404(LotStock, pk=pk)
    return render(request, "stock/detail.html", {"lot": lot})


@roles_required('administrateur', 'gestionnaire de stock', 'pharmacien responsable')
def inventaire(request):
    if request.method == "POST":
        try:
            lot_id = int(request.POST.get("lot", ""))
            count = int(request.POST.get("quantite", ""))
            if count < 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Saisissez un lot et un décompte nul ou positif.")
        else:
            with transaction.atomic():
                lot = get_object_or_404(LotStock.objects.select_for_update(), pk=lot_id)
                diff = count - lot.quantite_disponible
                if diff:
                    lot.quantite_disponible = count
                    lot.save(update_fields=["quantite_disponible"])
                    MouvementStock.objects.create(type=MouvementStock.Type.AJUSTEMENT, quantite=diff, motif="Inventaire physique", medicament=lot.medicament, lot=lot, utilisateur=request.user)
                    JournalAudit.objects.create(action="Inventaire physique", objet_type=f"Lot {lot.numero_lot} · variation {diff}", utilisateur=request.user)
            messages.success(request, "Inventaire physique enregistré avec son mouvement de correction.")
            return redirect("stock:mouvements")
    return render(request, "stock/inventaire.html", {"lots": LotStock.objects.select_related("medicament").order_by("date_peremption")})
