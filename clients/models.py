from django.core.validators import RegexValidator
from django.db import models

validateur_telephone = RegexValidator(
    regex=r"^(\+261|0)3[2-9]\d{7}$|^(\+261|0)20\d{7}$",
    message="Format invalide. Exemple : 0341234567 ou +261341234567",
)


class Client(models.Model):
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=15, validators=[validateur_telephone], blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom
