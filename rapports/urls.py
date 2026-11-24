from django.urls import path

from . import views

app_name = "rapports"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("rapports/", views.liste_rapports, name="liste"),
    path("rapports/stock/", views.rapport_stock, name="stock"),
    path("rapports/ventes/", views.rapport_ventes, name="ventes"),
    path("rapports/achats/", views.rapport_achats, name="achats"),
    path("rapports/peremption/", views.rapport_peremption, name="peremption"),
    path("rapports/<str:kind>.pdf", views.rapport_pdf, name="pdf"),
]
