from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404

from .models import Utilisateur


@user_passes_test(lambda user: user.is_staff or user.is_superuser)
def liste_utilisateurs(request):
    utilisateurs = Utilisateur.objects.all().order_by("username")
    return render(request, "utilisateurs/liste.html", {"utilisateurs": utilisateurs})


@user_passes_test(lambda user: user.is_staff or user.is_superuser)
def basculer_utilisateur(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST" and utilisateur.pk != request.user.pk:
        utilisateur.is_active = not utilisateur.is_active
        utilisateur.save(update_fields=["is_active"])
    return redirect("utilisateurs:liste")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("rapports:dashboard")

    if request.method == "POST":
        identifiant = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        utilisateur = Utilisateur.objects.filter(username__iexact=identifiant).first()
        if utilisateur is None and "@" in identifiant:
            utilisateur = Utilisateur.objects.filter(email__iexact=identifiant).first()

        if utilisateur is not None and not utilisateur.is_active:
            messages.error(
                request,
                "Ce compte existe mais attend encore l’activation par un administrateur.",
            )
        elif utilisateur is not None:
            user = authenticate(request, username=utilisateur.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Connexion réussie.")
                return redirect("rapports:dashboard")
            messages.error(
                request,
                "Mot de passe incorrect. Utilisez « Mot de passe oublié » si nécessaire.",
            )
        else:
            messages.error(request, "Identifiant ou adresse e-mail inconnu(e).")

    return render(request, "utilisateurs/login.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("rapports:dashboard")

    erreurs = {}
    valeurs = {}

    if request.method == "POST":
        valeurs = {
            "first_name": request.POST.get("firstName", "").strip(),
            "last_name": request.POST.get("lastName", "").strip(),
            "username": request.POST.get("regUsername", "").strip(),
            "email": request.POST.get("regEmail", "").strip(),
        }
        password = request.POST.get("regPassword", "")
        confirmation = request.POST.get("confirmPassword", "")
        consent = request.POST.get("privacyConsent")

        if not valeurs["first_name"]:
            erreurs["firstName"] = "Saisissez votre prénom."
        if not valeurs["last_name"]:
            erreurs["lastName"] = "Saisissez votre nom."
        if len(valeurs["username"]) < 3:
            erreurs["regUsername"] = "L’identifiant doit contenir au moins 3 caractères."
        elif (Utilisateur.objects.filter(username=valeurs["username"]).exists()
              or Utilisateur.objects.filter(username__iexact=valeurs["username"]).exists()):
            erreurs["regUsername"] = "Cet identifiant est déjà utilisé."
        if not valeurs["email"] or "@" not in valeurs["email"]:
            erreurs["regEmail"] = "Saisissez une adresse e-mail valide."
        elif Utilisateur.objects.filter(email__iexact=valeurs["email"]).exists():
            erreurs["regEmail"] = "Cette adresse e-mail est déjà utilisée."
        if password != confirmation:
            erreurs["confirmPassword"] = "Les deux mots de passe ne sont pas identiques."
        if not consent:
            erreurs["privacyConsent"] = "Vous devez accepter les conditions d’utilisation."

        if not erreurs:
            try:
                validate_password(
                    password,
                    user=Utilisateur(username=valeurs["username"], email=valeurs["email"]),
                )
            except DjangoValidationError as exception:
                erreurs["regPassword"] = " ".join(exception.messages)

        if not erreurs:
            try:
                with transaction.atomic():
                    Utilisateur.objects.create_user(
                        username=valeurs["username"],
                        email=valeurs["email"],
                        password=password,
                        first_name=valeurs["first_name"],
                        last_name=valeurs["last_name"],
                        nom_complet=f"{valeurs['first_name']} {valeurs['last_name']}".strip(),
                        is_active=False,
                    )
            except IntegrityError:
                if (Utilisateur.objects.filter(username=valeurs["username"]).exists()
                        or Utilisateur.objects.filter(username__iexact=valeurs["username"]).exists()):
                    erreurs["regUsername"] = "Cet identifiant est déjà utilisé."
                elif Utilisateur.objects.filter(email__iexact=valeurs["email"]).exists():
                    erreurs["regEmail"] = "Cette adresse e-mail est déjà utilisée."
                else:
                    erreurs["general"] = "Impossible de créer le compte. Vérifiez les informations saisies puis réessayez."
            else:
                messages.success(
                    request,
                    "Inscription enregistrée. Votre compte doit être activé par un administrateur avant la connexion.",
                )
                return redirect("utilisateurs:connexion")

    return render(
        request,
        "utilisateurs/register.html",
        {"erreurs": erreurs, "valeurs": valeurs},
    )
