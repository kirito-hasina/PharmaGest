from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.urls import path

from . import views

app_name = "utilisateurs"

urlpatterns = [
    path("", views.liste_utilisateurs, name="liste"),
    path("<int:pk>/activer/", views.basculer_utilisateur, name="basculer"),
    path("connexion/", views.login_view, name="connexion"),
    path("inscription/", views.register_view, name="inscription"),
    path("mot-de-passe-oublie/", auth_views.PasswordResetView.as_view(template_name="utilisateurs/forgot_password.html", email_template_name="utilisateurs/password_reset_email.txt", success_url=reverse_lazy("utilisateurs:password_reset_done")), name="password_reset"),
    path("mot-de-passe-envoye/", auth_views.PasswordResetDoneView.as_view(template_name="utilisateurs/password_reset_done.html"), name="password_reset_done"),
    path("reinitialiser/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="utilisateurs/password_reset_confirm.html", success_url=reverse_lazy("utilisateurs:password_reset_complete")), name="password_reset_confirm"),
    path("mot-de-passe-modifie/", auth_views.PasswordResetCompleteView.as_view(template_name="utilisateurs/password_reset_complete.html"), name="password_reset_complete"),
    path("mot-de-passe/", auth_views.PasswordChangeView.as_view(template_name="utilisateurs/password_change.html", success_url=reverse_lazy("utilisateurs:password_change_done")), name="password_change"),
    path("mot-de-passe-modifie-session/", auth_views.PasswordChangeDoneView.as_view(template_name="utilisateurs/password_change_done.html"), name="password_change_done"),
    path("deconnexion/", LogoutView.as_view(next_page="utilisateurs:connexion"), name="deconnexion"),
]
