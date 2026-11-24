from django.urls import path

from . import views

app_name = "stock"

urlpatterns = [
    path("", views.liste_stock, name="liste"),
    path("lots/", views.lots, name="lots"),
    path("mouvements/", views.mouvements, name="mouvements"),
    path("inventaire/", views.inventaire, name="inventaire"),
    path("<int:pk>/", views.detail_lot, name="detail"),
]
