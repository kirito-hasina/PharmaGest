from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Categorie, Medicament


class MedicamentFormulaireTests(TestCase):
    def setUp(self):
        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.test", "pass"))
        self.categorie = Categorie.objects.create(nom="Antalgiques")

    def donnees(self, **extra):
        base = {"nom_commercial": "Doliprane", "forme": "Comprimé", "dosage": "500 mg", "prix_achat": "100", "prix_vente": "150", "categorie": self.categorie.pk, "seuil_alerte": "5"}
        return {**base, **extra}

    def test_creation_via_le_formulaire_html(self):
        reponse = self.client.post(reverse("medicaments:creer"), self.donnees(laboratoire="Sanofi"))
        self.assertEqual(reponse.status_code, 302)
        self.assertEqual(Medicament.objects.get().laboratoire, "Sanofi")

    def test_prix_de_vente_inferieur_au_prix_d_achat_refuse(self):
        reponse = self.client.post(reverse("medicaments:creer"), self.donnees(prix_vente="50"))
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(Medicament.objects.exists())

    def test_modification_conserve_le_laboratoire(self):
        self.client.post(reverse("medicaments:creer"), self.donnees())
        medicament = Medicament.objects.get()
        self.client.post(reverse("medicaments:modifier", args=[medicament.pk]), self.donnees(laboratoire="Pfizer"))
        medicament.refresh_from_db()
        self.assertEqual(medicament.laboratoire, "Pfizer")

    def test_categorie_utilisee_non_supprimable(self):
        self.client.post(reverse("medicaments:creer"), self.donnees())
        self.client.post(reverse("medicaments:supprimer_categorie", args=[self.categorie.pk]))
        self.assertTrue(Categorie.objects.filter(pk=self.categorie.pk).exists())


class ChargerDemoTests(TestCase):
    def test_charge_les_donnees_une_seule_fois(self):
        from io import StringIO

        from django.core.management import call_command

        from stock.models import LotStock
        from utilisateurs.models import Role

        get_user_model().objects.create_superuser("admin", "a@example.test", "pass")
        call_command("charger_demo", "--mot-de-passe", "Demo-2026!", stdout=StringIO())
        call_command("charger_demo", stdout=StringIO())
        self.assertEqual(Medicament.objects.count(), 8)
        self.assertTrue(LotStock.objects.filter(quantite_disponible=0).exists())
        self.assertTrue(get_user_model().objects.get(username="caissier").roles.filter(nom="Caissier").exists())
        self.assertEqual(Role.objects.filter(nom="Caissier").count(), 1)
