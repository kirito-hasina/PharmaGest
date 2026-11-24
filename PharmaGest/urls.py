from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("rapports.urls")),
    path("utilisateurs/", include("utilisateurs.urls")),
    path("medicaments/", include("medicaments.urls")),
    path("fournisseurs/", include("fournisseurs.urls")),
    path("clients/", include("clients.urls")),
    path("achats/", include("achats.urls")),
    path("stock/", include("stock.urls")),
    path("ventes/", include("ventes.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
