from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.db.models.functions import TruncDate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.utils import timezone
from utilisateurs.permissions import acces_modules, page_accueil, roles_required

from achats.models import CommandeAchat
from clients.models import Client
from fournisseurs.models import Fournisseur
from medicaments.models import Medicament
from stock.models import LotStock
from ventes.models import LigneVente, Vente


@login_required
def dashboard(request):
    if not acces_modules(request.user)["dashboard"]:
        cible = page_accueil(request.user)
        if cible:
            return redirect(cible)
        raise PermissionDenied
    return _tableau_de_bord(request)


def _tableau_de_bord(request):
    aujourd_hui = timezone.localdate()
    fin_periode = aujourd_hui + timedelta(days=90)
    medicaments = Medicament.objects.filter(statut=Medicament.Statut.ACTIF)
    lots = LotStock.objects.select_related("medicament")
    ventes_du_jour = (
        Vente.objects.filter(date_vente__date=aujourd_hui, statut=Vente.Statut.PAYEE)
        .aggregate(total=Coalesce(Sum("total"), Decimal("0.00")))["total"]
    )
    ruptures = lots.filter(quantite_disponible__lte=0).count()
    faibles = (
        medicaments.annotate(
            stock_total=Coalesce(Sum("lots__quantite_disponible"), 0)
        )
        .filter(stock_total__lte=F("seuil_alerte"))
        .count()
    )
    peremptions_proches = lots.filter(
        date_peremption__gte=aujourd_hui,
        date_peremption__lte=fin_periode,
        quantite_disponible__gt=0,
        bloque=False,
    ).count()
    produits_vendus = list(
        LigneVente.objects.filter(vente__statut=Vente.Statut.PAYEE)
        .values("lot__medicament__nom_commercial")
        .annotate(quantite=Sum("quantite"))
        .order_by("-quantite")[:5]
    )
    quantite_max = max((item["quantite"] for item in produits_vendus), default=0)
    plus_vendus = [
        {
            "nom": item["lot__medicament__nom_commercial"],
            "quantite": item["quantite"],
            "pourcentage": round(item["quantite"] * 100 / quantite_max) if quantite_max else 0,
        }
        for item in produits_vendus
    ]
    stats = {
        "medicaments_actifs": medicaments.count(),
        "ventes_jour": f"{ventes_du_jour:,.0f}".replace(",", " ") + " Ar",
        "stocks_faibles": faibles,
        "peremptions_proches": peremptions_proches,
        "ruptures": ruptures,
    }
    debut_graphique = aujourd_hui - timedelta(days=29)
    ventes_journalieres = {
        row["jour"]: row["montant"]
        for row in Vente.objects.filter(statut=Vente.Statut.PAYEE, date_vente__date__gte=debut_graphique, date_vente__date__lte=aujourd_hui)
        .annotate(jour=TruncDate("date_vente"))
        .values("jour")
        .annotate(montant=Sum("total"))
    }
    dates_graphique = [debut_graphique + timedelta(days=i) for i in range(30)]
    valeurs = [float(ventes_journalieres.get(jour, 0)) for jour in dates_graphique]
    labels = [jour.strftime("%d %b") for jour in dates_graphique]
    achats_periode = CommandeAchat.objects.filter(date_commande__date__gte=debut_graphique, date_commande__date__lte=aujourd_hui).aggregate(total=Coalesce(Sum("montant_total"), Decimal("0.00")))["total"]
    stats["achats_periode"] = f"{achats_periode:,.0f}".replace(",", " ") + " Ar"
    data = {
        "stats": stats,
        "plus_vendus": plus_vendus,
        "medicaments": medicaments[:5],
        "ventes_graphique": {"j14": {"labels": labels[-14:], "values": valeurs[-14:]}, "j30": {"labels": labels, "values": valeurs}},
    }
    return render(request, "rapports/dashboard.html", data)


@roles_required('administrateur', 'responsable de gestion', 'pharmacien responsable')
def liste_rapports(request):
    return render(request, "rapports/liste.html")


@roles_required('administrateur', 'responsable de gestion', 'pharmacien responsable')
def rapport_stock(request):
    return render(request, "rapports/stock.html", {"lots": LotStock.objects.select_related("medicament").order_by("date_peremption")[:200], "today": timezone.localdate()})


@roles_required('administrateur', 'responsable de gestion', 'pharmacien responsable')
def rapport_ventes(request):
    return render(request, "rapports/ventes.html", {"ventes": Vente.objects.select_related("client", "utilisateur")[:200]})


@roles_required('administrateur', 'responsable de gestion', 'pharmacien responsable')
def rapport_achats(request):
    return render(request, "rapports/achats.html", {"commandes": CommandeAchat.objects.select_related("fournisseur", "utilisateur")[:200]})


@roles_required('administrateur', 'responsable de gestion', 'pharmacien responsable')
def rapport_peremption(request):
    today = timezone.localdate()
    return render(request, "rapports/peremption.html", {"lots": LotStock.objects.select_related("medicament").filter(date_peremption__lte=today + timedelta(days=90)).order_by("date_peremption")[:200], "today": today})


@roles_required('administrateur', 'responsable de gestion', 'pharmacien responsable')
def rapport_pdf(request, kind):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    labels = {"stock": "Rapport de stock", "ventes": "Rapport des ventes", "achats": "Rapport des achats", "peremption": "Lots proches de la péremption"}
    if kind not in labels:
        from django.http import Http404
        raise Http404
    rows = []
    if kind == "stock" or kind == "peremption":
        qs = LotStock.objects.select_related("medicament").order_by("date_peremption")
        if kind == "peremption": qs = qs.filter(date_peremption__lte=timezone.localdate() + timedelta(days=90))
        rows = [(f"{x.medicament} · {x.numero_lot}", str(x.quantite_disponible), x.date_peremption.strftime("%d/%m/%Y")) for x in qs]
    elif kind == "ventes":
        for v in Vente.objects.filter(statut=Vente.Statut.PAYEE).order_by("-date_vente")[:500]:
            rows.append((f"{v.numero} · {v.date_vente:%d/%m/%Y}", str(v.total), str(v.utilisateur)))
    else:
        for c in CommandeAchat.objects.select_related("fournisseur").order_by("-pk")[:500]:
            rows.append((f"{c.numero} · {c.fournisseur}", str(c.montant_total), c.get_statut_display()))
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="rapport-{kind}.pdf"'
    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setTitle(labels[kind])
    y = 800
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(40, y, f"PharmaGest — {labels[kind]}")
    y -= 22
    pdf.setFont("Helvetica", 9)
    pdf.drawString(40, y, f"Généré le {timezone.localtime():%d/%m/%Y %H:%M}")
    y -= 28
    for row in rows:
        pdf.drawString(40, y, str(row[0])[:65])
        pdf.drawRightString(460, y, str(row[1])[:24])
        pdf.drawRightString(560, y, str(row[2])[:20])
        y -= 16
        if y < 45:
            pdf.showPage()
            y = 800
            pdf.setFont("Helvetica", 9)
    pdf.save()
    return response
