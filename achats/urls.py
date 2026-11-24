from django.urls import path

from . import views

app_name = "achats"

urlpatterns = [
    path("reception/", views.ecran_reception, name="reception_ecran"),
    path("", views.liste_commandes, name="liste"),
    path("creer/", views.creer_commande, name="creer"),
    path("<int:pk>/", views.detail_commande, name="detail"),
    path("<int:pk>/modifier/", views.modifier_commande, name="modifier"),
    path("<int:pk>/valider/", views.valider_commande, name="valider"),
    path("<int:pk>/annuler/", views.annuler_commande, name="annuler"),
    path("<int:pk>/reception/", views.reception_commande, name="reception"),
    path("<int:pk>/bon.pdf", views.bon_commande, name="bon_commande"),
    path("<int:pk>/reception/<int:reception_pk>.pdf", views.bon_reception, name="bon_reception"),
]
