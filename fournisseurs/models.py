from django.core.validators import RegexValidator
from django.db import models

validateur_telephone = RegexValidator(
    regex=r"^(\+261|0)3[2-9]\d{7}$|^(\+261|0)20\d{7}$",
    message="Format invalide. Exemple : 0341234567 ou +261341234567",
)


class Fournisseur(models.Model):
    raison_sociale = models.CharField(max_length=150)
    telephone = models.CharField(max_length=15, validators=[validateur_telephone])
    adresse = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    identifiant_fiscal = models.CharField(max_length=80, blank=True)
    contact_principal = models.CharField(max_length=150, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["raison_sociale"]

    def __str__(self):
        return self.raison_sociale
