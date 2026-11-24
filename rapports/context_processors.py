from datetime import timedelta

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone

from medicaments.models import Medicament
from stock.models import LotStock


def stock_alertes(request):
    if not request.user.is_authenticated:
        return {"alertes_stock": [], "nombre_alertes_stock": 0}
    today = timezone.localdate()
    alerts = []
    for lot in LotStock.objects.filter(quantite_disponible=0).select_related("medicament")[:3]:
        alerts.append(("bi-x-circle-fill", "#991b1b", "Rupture", f"{lot.medicament} · lot {lot.numero_lot}", reverse("stock:liste") + "?stk=rupture"))
    faibles = Medicament.objects.filter(statut=Medicament.Statut.ACTIF).annotate(stock_total=Coalesce(Sum("lots__quantite_disponible"), 0)).filter(stock_total__lte=F("seuil_alerte"))[:3]
    for medicament in faibles:
        alerts.append(("bi-exclamation-triangle-fill", "#9a3412", "Stock faible", f"{medicament} · {medicament.stock_total} unité(s)", reverse("stock:liste") + "?stk=faible"))
    for lot in LotStock.objects.filter(quantite_disponible__gt=0, date_peremption__gte=today, date_peremption__lte=today + timedelta(days=90)).select_related("medicament").order_by("date_peremption")[:3]:
        alerts.append(("bi-clock-fill", "#854d0e", "Péremption proche", f"{lot.medicament} · lot {lot.numero_lot}", reverse("stock:liste") + "?exp=proche"))
    return {"alertes_stock": alerts, "nombre_alertes_stock": len(alerts)}
