from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from fournisseurs.models import Fournisseur
from medicaments.models import Categorie, Medicament
from stock.models import LotStock, MouvementStock
from .models import CommandeAchat, LigneAchat


class ReceptionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("admin", "a@example.test", "pass")
        self.client.force_login(self.user)
        self.fournisseur = Fournisseur.objects.create(raison_sociale="Grossiste", telephone="0341234567")
        self.medicament = Medicament.objects.create(nom_commercial="Test", forme="Comprimé", dosage="500 mg", prix_achat=100, prix_vente=150, categorie=Categorie.objects.create(nom="Tests"))
        self.commande = CommandeAchat.objects.create(numero="ACH-TEST", fournisseur=self.fournisseur, utilisateur=self.user, statut=CommandeAchat.Statut.ENVOYEE, montant_total=Decimal("200"))
        self.ligne = LigneAchat.objects.create(commande=self.commande, medicament=self.medicament, quantite_commandee=2, prix_achat=100)

    def test_reception_increases_stock_once_and_records_movement(self):
        url = reverse("achats:reception", args=[self.commande.pk])
        data = {f"q_{self.ligne.pk}": "2", f"lot_{self.ligne.pk}": "LOT-1", f"exp_{self.ligne.pk}": (date.today() + timedelta(days=365)).isoformat()}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(self.client.post(url, data).status_code, 302)
        lot = LotStock.objects.get(medicament=self.medicament)
        self.assertEqual(lot.quantite_disponible, 2)
        self.assertEqual(MouvementStock.objects.filter(type=MouvementStock.Type.ENTREE).count(), 1)

    def test_order_does_not_change_stock_before_reception(self):
        self.assertFalse(LotStock.objects.filter(medicament=self.medicament).exists())


class BrouillonTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("admin", "a@example.test", "pass")
        self.client.force_login(self.user)
        self.fournisseur = Fournisseur.objects.create(raison_sociale="Grossiste", telephone="0341234567")
        self.medicament = Medicament.objects.create(nom_commercial="Test", forme="Comprimé", dosage="500 mg", prix_achat=100, prix_vente=150, categorie=Categorie.objects.create(nom="Tests"))

    def poster(self, url, statut, quantite="3"):
        return self.client.post(url, {"fournisseur": self.fournisseur.pk, "medicament": [self.medicament.pk], "quantite": [quantite], "prix": ["100"], "statut": statut})

    def test_brouillon_modifiable_puis_validable_sans_toucher_au_stock(self):
        self.poster(reverse("achats:creer"), "brouillon")
        commande = CommandeAchat.objects.get()
        self.assertEqual(commande.statut, CommandeAchat.Statut.BROUILLON)
        self.poster(reverse("achats:modifier", args=[commande.pk]), "brouillon", quantite="5")
        commande.refresh_from_db()
        self.assertEqual(commande.montant_total, Decimal("500"))
        self.assertEqual(commande.lignes.get().quantite_commandee, 5)
        self.client.post(reverse("achats:valider", args=[commande.pk]))
        commande.refresh_from_db()
        self.assertEqual(commande.statut, CommandeAchat.Statut.ENVOYEE)
        self.assertFalse(LotStock.objects.exists())

    def test_commande_validee_n_est_plus_modifiable(self):
        self.poster(reverse("achats:creer"), "envoyee")
        commande = CommandeAchat.objects.get()
        self.poster(reverse("achats:modifier", args=[commande.pk]), "brouillon", quantite="9")
        self.assertEqual(commande.lignes.get().quantite_commandee, 3)
