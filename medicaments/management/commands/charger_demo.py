"""Charge un jeu de données fictives (livrable 9 du cahier des charges).

Usage :
    python manage.py charger_demo                       # données seulement
    python manage.py charger_demo --mot-de-passe XXXX   # + un compte de démonstration par rôle

Les données sont créées une seule fois : relancer la commande ne duplique rien.
"""
import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from achats.models import CommandeAchat, LigneAchat, LigneReception, ReceptionAchat
from clients.models import Client
from fournisseurs.models import Fournisseur
from medicaments.models import Categorie, Medicament
from stock.models import LotStock, MouvementStock
from utilisateurs.models import Role
from ventes.models import LigneVente, Paiement, Vente

CATEGORIES = ["Antalgiques", "Antibiotiques", "Vitamines", "Antiseptiques"]

# (nom, générique, catégorie, forme, dosage, labo, code-barres, achat, vente, seuil)
MEDICAMENTS = [
    ("Paracétamol 500", "Paracétamol", "Antalgiques", "Comprimé", "500 mg", "Pharmalab", "3400000000011", 150, 250, 50),
    ("Ibuprofène 400", "Ibuprofène", "Antalgiques", "Comprimé", "400 mg", "Pharmalab", "3400000000028", 300, 500, 30),
    ("Amoxicilline 500", "Amoxicilline", "Antibiotiques", "Gélule", "500 mg", "MedPharma", "3400000000035", 450, 750, 40),
    ("Azithromycine 250", "Azithromycine", "Antibiotiques", "Comprimé", "250 mg", "MedPharma", "3400000000042", 1800, 2800, 15),
    ("Vitamine C 1000", "Acide ascorbique", "Vitamines", "Comprimé effervescent", "1000 mg", "VitaSud", "3400000000059", 600, 1000, 25),
    ("Multivitamines Enfant", "", "Vitamines", "Sirop", "150 ml", "VitaSud", "3400000000066", 4500, 6500, 10),
    ("Chlorhexidine 0,5 %", "Chlorhexidine", "Antiseptiques", "Solution", "100 ml", "Hygia", "3400000000073", 1200, 2000, 10),
    ("Povidone iodée", "Povidone iodée", "Antiseptiques", "Solution", "125 ml", "Hygia", "3400000000080", 1500, 2400, 10),
]

FOURNISSEURS = [
    ("Grossiste Tana Pharma", "0341100001", "contact@tanapharma.example", "Antananarivo", "Mme Rasoa"),
    ("Océan Indien Médical", "0331100002", "commandes@oim.example", "Toamasina", "M. Andry"),
    ("Laboratoire Analakely", "0321100003", "", "Antananarivo", ""),
]


class Command(BaseCommand):
    help = "Charge un jeu de données fictives pour tester l'application."

    def add_arguments(self, parser):
        parser.add_argument("--mot-de-passe", help="Crée aussi un compte de démonstration par rôle avec ce mot de passe.")

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        acteur = User.objects.filter(is_superuser=True).first()
        if acteur is None:
            raise CommandError("Créez d'abord un super-utilisateur : python manage.py createsuperuser")
        if Medicament.objects.exists():
            self.stdout.write(self.style.WARNING("Des médicaments existent déjà : rien n'a été chargé."))
        else:
            self._charger(acteur)
        if options["mot_de_passe"]:
            self._comptes(options["mot_de_passe"])

    def _charger(self, acteur):
        aujourdhui = timezone.localdate()
        categories = {nom: Categorie.objects.create(nom=nom) for nom in CATEGORIES}
        meds = {}
        for nom, generique, cat, forme, dosage, labo, code, achat, vente, seuil in MEDICAMENTS:
            meds[nom] = Medicament.objects.create(
                nom_commercial=nom, denomination_generique=generique, categorie=categories[cat], forme=forme,
                dosage=dosage, laboratoire=labo, code_barres=code, prix_achat=achat, prix_vente=vente, seuil_alerte=seuil,
            )
        fournisseurs = [Fournisseur.objects.create(raison_sociale=n, telephone=t, email=e, adresse=a, contact_principal=c)
                        for n, t, e, a, c in FOURNISSEURS]
        clients = [Client.objects.create(nom="Rakoto Jean", telephone="0341200001"),
                   Client.objects.create(nom="Rasoamanana Lalao", telephone="0331200002")]

        # Commande entièrement reçue : elle crée les premiers lots (dont un proche de la péremption).
        reçus = [
            ("Paracétamol 500", 200, "PAR-2601", 540),
            ("Ibuprofène 400", 100, "IBU-2601", 400),
            ("Amoxicilline 500", 80, "AMX-2601", 60),     # péremption proche
            ("Vitamine C 1000", 12, "VTC-2601", 300),     # stock faible (seuil 25)
        ]
        commande = CommandeAchat.objects.create(numero="ACH-DEMO-0001", statut=CommandeAchat.Statut.RECUE, fournisseur=fournisseurs[0], utilisateur=acteur)
        reception = ReceptionAchat.objects.create(commande=commande, utilisateur=acteur, validee=True)
        total = 0
        lots = {}
        for nom, qte, numero, jours in reçus:
            med = meds[nom]
            ligne = LigneAchat.objects.create(commande=commande, medicament=med, quantite_commandee=qte, prix_achat=med.prix_achat)
            LigneReception.objects.create(reception=reception, ligne_achat=ligne, quantite_recue=qte, numero_lot=numero,
                                          date_peremption=aujourdhui + datetime.timedelta(days=jours))
            lots[nom] = self._lot(med, numero, aujourdhui + datetime.timedelta(days=jours), qte, acteur, f"Réception {commande.numero}")
            total += qte * med.prix_achat
        commande.montant_total = total
        commande.save(update_fields=["montant_total"])

        # Lots historiques : un périmé, un épuisé (pour voir les alertes et les filtres).
        self._lot(meds["Azithromycine 250"], "AZI-2501", aujourdhui - datetime.timedelta(days=20), 6, acteur, "Stock initial")
        self._lot(meds["Povidone iodée"], "POV-2602", aujourdhui + datetime.timedelta(days=500), 0, acteur, "Stock initial")
        self._lot(meds["Chlorhexidine 0,5 %"], "CHL-2602", aujourdhui + datetime.timedelta(days=700), 40, acteur, "Stock initial")

        # Une commande à réceptionner et un brouillon.
        for numero, statut, fournisseur, nom, qte in [
            ("ACH-DEMO-0002", CommandeAchat.Statut.ENVOYEE, fournisseurs[1], "Vitamine C 1000", 100),
            ("ACH-DEMO-0003", CommandeAchat.Statut.BROUILLON, fournisseurs[2], "Multivitamines Enfant", 20),
        ]:
            cmd = CommandeAchat.objects.create(numero=numero, statut=statut, fournisseur=fournisseur, utilisateur=acteur,
                                               montant_total=qte * meds[nom].prix_achat)
            LigneAchat.objects.create(commande=cmd, medicament=meds[nom], quantite_commandee=qte, prix_achat=meds[nom].prix_achat)

        # Une vente payée de 2 lignes, avec sortie de stock tracée.
        vente = Vente.objects.create(numero="VT-DEMO-0001", statut=Vente.Statut.PAYEE, client=clients[0], utilisateur=acteur)
        total = 0
        for nom, qte in [("Paracétamol 500", 4), ("Ibuprofène 400", 2)]:
            lot, med = lots[nom], meds[nom]
            LigneVente.objects.create(vente=vente, lot=lot, quantite=qte, prix_applique=med.prix_vente)
            lot.quantite_disponible -= qte
            lot.save(update_fields=["quantite_disponible"])
            MouvementStock.objects.create(type=MouvementStock.Type.SORTIE, quantite=qte, motif=f"Vente {vente.numero}",
                                          medicament=med, lot=lot, utilisateur=acteur)
            total += qte * med.prix_vente
        vente.total = total
        vente.save(update_fields=["total"])
        Paiement.objects.create(vente=vente, mode=Paiement.Mode.ESPECES, montant=total, statut=Paiement.Statut.VALIDE, utilisateur=acteur)
        self.stdout.write(self.style.SUCCESS("Jeu de données chargé : 8 médicaments, 3 fournisseurs, 2 clients, 3 commandes, 1 vente."))

    def _lot(self, med, numero, peremption, quantite, acteur, motif):
        lot = LotStock.objects.create(medicament=med, numero_lot=numero, date_peremption=peremption,
                                      quantite_recue=quantite, quantite_disponible=quantite)
        if quantite:
            MouvementStock.objects.create(type=MouvementStock.Type.ENTREE, quantite=quantite, motif=motif,
                                          medicament=med, lot=lot, utilisateur=acteur)
        return lot

    def _comptes(self, mot_de_passe):
        User = get_user_model()
        for username, role in [("pharmacien", "Pharmacien responsable"), ("gestionnaire", "Gestionnaire de stock"),
                               ("caissier", "Caissier"), ("responsable", "Responsable de gestion")]:
            user, cree = User.objects.get_or_create(username=username, defaults={"first_name": role})
            if cree:
                user.set_password(mot_de_passe)
                user.save()
            user.roles.add(Role.objects.get(nom=role))
            self.stdout.write(f"Compte {username} ({role}) {'créé' if cree else 'déjà présent'}.")
