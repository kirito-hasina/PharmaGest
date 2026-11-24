from django.conf import settings
from django.db import models
from django.utils import timezone


class CommandeAchat(models.Model):
    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        ENVOYEE = "envoyee", "Envoyée"
        PARTIELLE = "partielle", "Partiellement reçue"
        RECUE = "recue", "Reçue"
        ANNULEE = "annulee", "Annulée"

    numero = models.CharField(max_length=30, unique=True)
    date_commande = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.BROUILLON)
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fournisseur = models.ForeignKey(
        "fournisseurs.Fournisseur", on_delete=models.PROTECT, related_name="commandes"
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="commandes_creees"
    )

    def __str__(self):
        return self.numero


class LigneAchat(models.Model):
    commande = models.ForeignKey(
        CommandeAchat, on_delete=models.CASCADE, related_name="lignes"
    )
    medicament = models.ForeignKey(
        "medicaments.Medicament", on_delete=models.PROTECT, related_name="lignes_achat"
    )
    quantite_commandee = models.PositiveIntegerField()
    prix_achat = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.medicament} x {self.quantite_commandee}"


class ReceptionAchat(models.Model):
    date_reception = models.DateTimeField(auto_now_add=True)
    validee = models.BooleanField(default=False)
    commande = models.ForeignKey(
        CommandeAchat, on_delete=models.PROTECT, related_name="receptions"
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="receptions_validees"
    )

    class Meta:
        ordering = ["-date_reception"]

    def __str__(self):
        return f"Réception {self.pk} - {self.commande}"


class LigneReception(models.Model):
    reception = models.ForeignKey(
        ReceptionAchat, on_delete=models.CASCADE, related_name="lignes"
    )
    ligne_achat = models.ForeignKey(
        LigneAchat, on_delete=models.PROTECT, related_name="lignes_reception"
    )
    quantite_recue = models.PositiveIntegerField()
    numero_lot = models.CharField(max_length=50)
    date_peremption = models.DateField()

    def __str__(self):
        return f"{self.ligne_achat.medicament} - Lot {self.numero_lot}"
