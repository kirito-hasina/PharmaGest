from django.core.exceptions import ValidationError
from django.db import models


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Medicament(models.Model):
    class Statut(models.TextChoices):
        ACTIF = "actif", "Actif"
        INACTIF = "inactif", "Inactif"
        RETIRE = "retire", "Retiré du marché"

    nom_commercial = models.CharField(max_length=150)
    denomination_generique = models.CharField(max_length=150, null=True, blank=True)
    laboratoire = models.CharField(max_length=150, null=True, blank=True)
    forme = models.CharField(max_length=50)
    dosage = models.CharField(max_length=50)
    prix_achat = models.DecimalField(max_digits=12, decimal_places=2)
    prix_vente = models.DecimalField(max_digits=12, decimal_places=2)
    seuil_alerte = models.PositiveIntegerField(default=0)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ACTIF)
    code_barres = models.CharField(max_length=100, unique=True, null=True, blank=True)
    photo = models.ImageField(upload_to="medicaments/", null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    categorie = models.ForeignKey(
        Categorie, on_delete=models.PROTECT, related_name="medicaments"
    )

    class Meta:
        ordering = ["nom_commercial"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(prix_achat__gt=0),
                name="medicament_prix_achat_positif",
            ),
            models.CheckConstraint(
                condition=models.Q(prix_vente__gt=0),
                name="medicament_prix_vente_positif",
            ),
            models.CheckConstraint(
                condition=models.Q(prix_vente__gte=models.F("prix_achat")),
                name="medicament_prix_vente_sup_ou_egal_achat",
            ),
            models.UniqueConstraint(
                fields=["nom_commercial", "dosage", "forme"],
                name="medicament_unique_nom_dosage_forme",
            ),
        ]

    def clean(self):
        super().clean()
        if self.prix_achat is not None and self.prix_vente is not None:
            if self.prix_vente < self.prix_achat:
                raise ValidationError({"prix_vente": "Le prix de vente ne peut pas être inférieur au prix d'achat."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom_commercial} {self.dosage}"
