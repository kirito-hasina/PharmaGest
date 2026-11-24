from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Role


class UtilisateursTests(TestCase):
    def test_public_registration_creates_inactive_account_pending_activation(self):
        response = self.client.post(reverse("utilisateurs:inscription"), {
            "firstName": "Jean",
            "lastName": "Rakoto",
            "regUsername": "jean.rakoto",
            "regEmail": "jean@example.test",
            "regPassword": "Secret123!",
            "confirmPassword": "Secret123!",
            "privacyConsent": "on",
        })
        self.assertRedirects(response, reverse("utilisateurs:connexion"))
        user = get_user_model().objects.get(username="jean.rakoto")
        self.assertFalse(user.is_active)
        self.assertEqual(user.nom_complet, "Jean Rakoto")
        self.assertFalse(user.roles.exists())

    def test_registration_rejects_duplicate_username(self):
        get_user_model().objects.create_user("intrus", password="Secret123!")
        response = self.client.post(reverse("utilisateurs:inscription"), {
            "firstName": "Jean",
            "lastName": "Rakoto",
            "regUsername": "INTRUS",
            "regEmail": "jean@example.test",
            "regPassword": "Secret123!",
            "confirmPassword": "Secret123!",
            "privacyConsent": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cet identifiant est déjà utilisé")

    def test_user_list_requires_admin_access(self):
        user = get_user_model().objects.create_user("staff", password="Secret123!", is_staff=False)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("utilisateurs:liste")).status_code, 302)

    def test_admin_can_select_all_pharmacy_roles_when_creating_user(self):
        admin = get_user_model().objects.create_superuser("admin", "admin@example.test", "Secret123!")
        self.client.force_login(admin)

        response = self.client.get(reverse("admin:utilisateurs_utilisateur_add"))

        self.assertEqual(response.status_code, 200)
        self.assertSetEqual(
            set(Role.objects.values_list("nom", flat=True)),
            {
                "Administrateur",
                "Pharmacien responsable",
                "Gestionnaire de stock",
                "Caissier",
                "Responsable de gestion",
            },
        )
        for role in Role.objects.all():
            self.assertContains(response, role.nom)

    def test_login_accepts_username_and_email(self):
        get_user_model().objects.create_user(
            "login-test",
            email="login@example.test",
            password="Secret123!",
        )
        for identifiant in ("login-test", "login@example.test"):
            self.client.logout()
            response = self.client.post(reverse("utilisateurs:connexion"), {
                "username": identifiant,
                "password": "Secret123!",
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse("rapports:dashboard"))

    def test_login_reports_pending_activation_separately(self):
        get_user_model().objects.create_user(
            "en-attente",
            password="Secret123!",
            is_active=False,
        )
        response = self.client.post(reverse("utilisateurs:connexion"), {
            "username": "en-attente",
            "password": "Secret123!",
        })
        self.assertContains(response, "attend encore l’activation")


class AccueilParRoleTests(TestCase):
    def utilisateur(self, nom_role):
        utilisateur = get_user_model().objects.create_user(nom_role.replace(" ", "_"), password="Secret123!")
        utilisateur.roles.add(Role.objects.get(nom=nom_role))
        self.client.force_login(utilisateur)

    def test_caissier_arrive_sur_la_caisse_et_non_sur_une_403(self):
        self.utilisateur("Caissier")
        self.assertRedirects(self.client.get(reverse("rapports:dashboard")), reverse("ventes:creer"))

    def test_gestionnaire_arrive_sur_le_stock(self):
        self.utilisateur("Gestionnaire de stock")
        self.assertRedirects(self.client.get(reverse("rapports:dashboard")), reverse("stock:liste"))

    def test_caissier_ne_voit_pas_les_medicaments(self):
        self.utilisateur("Caissier")
        self.assertEqual(self.client.get(reverse("medicaments:liste")).status_code, 403)

    def test_menu_limite_aux_modules_du_role(self):
        self.utilisateur("Caissier")
        page = self.client.get(reverse("ventes:creer"))
        self.assertContains(page, reverse("ventes:liste"))
        self.assertNotContains(page, 'href="%s"' % reverse("fournisseurs:liste"))
        self.assertNotContains(page, 'href="%s"' % reverse("utilisateurs:liste"))

    def test_deconnexion_se_fait_en_post(self):
        self.utilisateur("Caissier")
        page = self.client.get(reverse("ventes:creer"))
        self.assertContains(page, 'action="%s"' % reverse("utilisateurs:deconnexion"))
