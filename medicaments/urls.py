from django.urls import path

from . import views

app_name = "medicaments"

urlpatterns = [
    path("", views.liste_medicaments, name="liste"),
    path("creer/", views.creer_medicament, name="creer"),
    path("categories/", views.categories, name="categories"),
    path("categories/creer/", views.creer_categorie, name="creer_categorie"),
    path("categories/<int:pk>/modifier/", views.modifier_categorie, name="modifier_categorie"),
    path("categories/<int:pk>/supprimer/", views.supprimer_categorie, name="supprimer_categorie"),
    path("<int:pk>/", views.detail_medicament, name="detail"),
    path("<int:pk>/modifier/", views.modifier_medicament, name="modifier"),
    path("<int:pk>/archiver/", views.archiver_medicament, name="archiver"),
]
