from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    nom = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nom


class Utilisateur(AbstractUser):
    nom_complet = models.CharField(max_length=150)
    roles = models.ManyToManyField(Role, blank=True, related_name="utilisateurs")

    def __str__(self):
        return self.nom_complet or self.username


class JournalAudit(models.Model):
    action = models.CharField(max_length=100)
    objet_type = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="journal_audit",
    )

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date:%d/%m/%Y %H:%M} - {self.action} ({self.objet_type})"