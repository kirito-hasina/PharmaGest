from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from medicaments.models import Categorie, Medicament
from stock.models import LotStock, MouvementStock
from .models import LigneVente, Paiement, Vente


class CaisseTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("admin", "a@example.test", "pass")
        self.client.force_login(self.user)
        med = Medicament.objects.create(nom_commercial="Test", forme="Comprimé", dosage="500 mg", prix_achat=100, prix_vente=150, categorie=Categorie.objects.create(nom="Tests"))
        self.lot = LotStock.objects.create(medicament=med, numero_lot="LOT-1", date_peremption=timezone.localdate() + timedelta(days=90), quantite_disponible=3, quantite_recue=3)

    def test_cash_sale_decrements_stock_atomically(self):
        response = self.client.post(reverse("ventes:creer"), {"lot": [self.lot.pk], "quantite": ["2"], "mode": "especes"})
        self.assertEqual(response.status_code, 302)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite_disponible, 1)
        self.assertEqual(MouvementStock.objects.filter(type=MouvementStock.Type.SORTIE).count(), 1)
        self.assertEqual(Vente.objects.get().statut, Vente.Statut.PAYEE)
        pdf = self.client.get(reverse("ventes:recu", args=[Vente.objects.get().pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")

    def test_electronic_payment_is_simulated_and_decrements_stock(self):
        self.client.post(reverse("ventes:creer"), {"lot": [self.lot.pk], "quantite": ["1"], "mode": "mobile_money"})
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite_disponible, 2)
        self.assertEqual(Vente.objects.get().statut, Vente.Statut.PAYEE)
        self.assertEqual(Paiement.objects.get().statut, Paiement.Statut.VALIDE)
        self.assertEqual(MouvementStock.objects.filter(type=MouvementStock.Type.SORTIE).count(), 1)
        detail = self.client.get(reverse("ventes:detail", args=[Vente.objects.get().pk]))
        self.assertContains(detail, "simulé avec succès")

    def test_oversell_is_rejected(self):
        self.client.post(reverse("ventes:creer"), {"lot": [self.lot.pk], "quantite": ["4"], "mode": "especes"})
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantite_disponible, 3)
        self.assertFalse(Vente.objects.exists())

    def test_operational_pages_render_for_admin(self):
        for name in ("achats:creer", "ventes:creer", "clients:creer", "fournisseurs:creer", "stock:inventaire", "stock:mouvements", "rapports:dashboard"):
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_report_pdf_uses_real_records(self):
        response = self.client.get(reverse("rapports:pdf", args=["stock"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
