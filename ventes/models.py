from django.conf import settings
from django.db import models
from django.utils import timezone


class Vente(models.Model):
    class Statut(models.TextChoices):
        EN_COURS = "en_cours", "En cours"
        PAYEE = "payee", "Payée"
        ANNULEE = "annulee", "Annulée"

    numero = models.CharField(max_length=30, unique=True)
    date_vente = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_COURS)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    client = models.ForeignKey(
        "clients.Client", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="ventes",
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ventes"
    )

    class Meta:
        ordering = ["-date_vente"]

    def __str__(self):
        return self.numero


class LigneVente(models.Model):
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name="lignes")
    lot = models.ForeignKey(
        "stock.LotStock", on_delete=models.PROTECT, related_name="lignes_vente"
    )
    quantite = models.PositiveIntegerField()
    prix_applique = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.lot.medicament} x {self.quantite}"


class Paiement(models.Model):
    class Mode(models.TextChoices):
        ESPECES = "especes", "Espèces"
        MOBILE_MONEY = "mobile_money", "Mobile Money (MVola, Orange, Airtel)"
        CARTE = "carte", "Carte bancaire"
        CHEQUE = "cheque", "Chèque"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        VALIDE = "valide", "Validé"
        REFUSE = "refuse", "Refusé"

    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name="paiements")
    mode = models.CharField(max_length=20, choices=Mode.choices)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    date = models.DateTimeField(default=timezone.now)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="paiements_enregistres",
    )

    def __str__(self):
        return f"{self.get_mode_display()} - {self.montant}"


class RetourVente(models.Model):
    ligne_vente = models.ForeignKey(
        LigneVente, on_delete=models.PROTECT, related_name="retours"
    )
    quantite_retournee = models.PositiveIntegerField()
    motif = models.TextField()
    remise_en_stock = models.BooleanField(default=False)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="retours_traites"
    )
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Retour {self.pk} - {self.ligne_vente}"
