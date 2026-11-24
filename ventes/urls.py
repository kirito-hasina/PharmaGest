from django.urls import path

from . import views

app_name = "ventes"

urlpatterns = [
    path("retours/", views.retours, name="retours"),
    path("caisse/recherche/", views.recherche_caisse, name="recherche_caisse"),
    path("", views.liste_ventes, name="liste"),
    path("creer/", views.creer_vente, name="creer"),
    path("<int:pk>/", views.detail_vente, name="detail"),
    path("<int:pk>/recu.pdf", views.recu_vente, name="recu"),
    path("<int:pk>/payer/", views.payer_vente, name="payer"),
    path("<int:pk>/retour/", views.retour_vente, name="retour"),
]
