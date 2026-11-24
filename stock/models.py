from django.conf import settings
from django.db import models


class LotStock(models.Model):
    medicament = models.ForeignKey(
        "medicaments.Medicament", on_delete=models.PROTECT, related_name="lots"
    )
    numero_lot = models.CharField(max_length=50)
    date_peremption = models.DateField()
    quantite_recue = models.PositiveIntegerField(default=0)
    quantite_disponible = models.PositiveIntegerField(default=0)
    bloque = models.BooleanField(default=False)

    class Meta:
        ordering = ["date_peremption"]
        constraints = [
            models.UniqueConstraint(
                fields=["medicament", "numero_lot"],
                name="lot_unique_par_medicament",
            ),
        ]

    def __str__(self):
        return f"{self.medicament} - Lot {self.numero_lot}"


class MouvementStock(models.Model):
    class Type(models.TextChoices):
        ENTREE = "entree", "Entrée"
        SORTIE = "sortie", "Sortie"
        RETOUR = "retour", "Retour"
        AJUSTEMENT = "ajustement", "Ajustement"

    type = models.CharField(max_length=20, choices=Type.choices)
    quantite = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    motif = models.CharField(max_length=255, blank=True)
    medicament = models.ForeignKey(
        "medicaments.Medicament", on_delete=models.PROTECT, related_name="mouvements"
    )
    lot = models.ForeignKey(
        LotStock, on_delete=models.PROTECT, related_name="mouvements"
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mouvements_stock"
    )

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.get_type_display()} {self.quantite} - {self.medicament}"
