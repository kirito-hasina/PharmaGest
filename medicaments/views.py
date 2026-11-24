from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from utilisateurs.permissions import roles_required
from utilisateurs.models import JournalAudit

from .models import Categorie, Medicament


def createMedicament(data):
    """Crée un médicament à partir d'un dictionnaire de données brut."""
    errors = []
    required_fields = [
        "nom_commercial",
        "forme",
        "dosage",
        "prix_achat",
        "prix_vente",
        "categorie",
    ]

    for field_name in required_fields:
        value = data.get(field_name)
        if value in (None, ""):
            errors.append(f"Le champ {field_name} est obligatoire.")

    if errors:
        return None, errors

    try:
        prix_achat = Decimal(str(data["prix_achat"]).replace(",", "."))
        prix_vente = Decimal(str(data["prix_vente"]).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None, ["Les prix doivent être des montants valides."]

    if prix_achat <= 0 or prix_vente <= 0:
        errors.append("Les prix doivent être strictement positifs.")

    if prix_vente < prix_achat:
        errors.append("Le prix de vente ne peut pas être inférieur au prix d'achat.")

    categorie_id = data.get("categorie")
    if hasattr(categorie_id, "pk"):
        categorie_id = categorie_id.pk
    if categorie_id is not None and not Categorie.objects.filter(pk=categorie_id).exists():
        errors.append("La catégorie sélectionnée est introuvable.")

    if errors:
        return None, errors

    image = data.get("photo")
    if image:
        extension = image.name.lower().split(".")[-1] if hasattr(image, "name") else ""
        if extension not in {"jpg", "jpeg", "png", "webp"}:
            errors.append("Le fichier photo doit être au format JPG, PNG ou WEBP.")
        if getattr(image, "size", 0) > 2 * 1024 * 1024:
            errors.append("La photo ne doit pas dépasser 2 Mo.")

    if errors:
        return None, errors

    medicament = Medicament(
        nom_commercial=data["nom_commercial"].strip(),
        denomination_generique=(data.get("denomination_generique") or "").strip() or None,
        laboratoire=(data.get("laboratoire") or "").strip() or None,
        forme=data["forme"].strip(),
        dosage=data["dosage"].strip(),
        prix_achat=prix_achat,
        prix_vente=prix_vente,
        seuil_alerte=int(data.get("seuil_alerte") or 0),
        statut=data.get("statut") or Medicament.Statut.ACTIF,
        code_barres=(data.get("code_barres") or "").strip() or None,
        photo=image,
        categorie_id=categorie_id,
    )

    try:
        medicament.full_clean()
        medicament.save()
    except ValidationError as exc:
        return None, list(exc.messages)

    return medicament, []


def create_medicament(data):
    return createMedicament(data)


@roles_required('administrateur', 'pharmacien responsable')
def liste_medicaments(request):
    queryset = Medicament.objects.select_related("categorie").annotate(stock_total=Coalesce(Sum("lots__quantite_disponible"), 0))
    q = request.GET.get("q", "").strip()
    categorie = request.GET.get("categorie")
    statut = request.GET.get("statut")
    tri = request.GET.get("tri", "nom_commercial")
    if tri.lstrip("-") not in {"nom_commercial", "prix_vente", "date_creation"}:
        tri = "nom_commercial"
    queryset = queryset.order_by(tri)

    if q:
        queryset = queryset.filter(Q(nom_commercial__icontains=q) | Q(code_barres__icontains=q))
    if categorie:
        queryset = queryset.filter(categorie_id=categorie)
    if statut:
        queryset = queryset.filter(statut=statut)

    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "medicaments/liste.html",
        {"medicaments": page_obj, "page_obj": page_obj, "categories": Categorie.objects.all(), "request": request},
    )


@roles_required('administrateur', 'pharmacien responsable')
def detail_medicament(request, pk):
    medicament = get_object_or_404(Medicament, pk=pk)
    return render(request, "medicaments/detail.html", {"medicament": medicament})


@roles_required('administrateur', 'pharmacien responsable')
def creer_medicament(request):
    categories = Categorie.objects.all()
    if request.method == "POST":
        medicament, errors = createMedicament({**request.POST.dict(), **request.FILES.dict()})
        if medicament is not None:
            JournalAudit.objects.create(action="Médicament créé", objet_type=f"Médicament {medicament.pk}", utilisateur=request.user)
            messages.success(request, "Médicament enregistré avec succès.")
            return redirect("medicaments:detail", pk=medicament.pk)
        for error in errors:
            messages.error(request, error)
    return render(request, "medicaments/creer.html", {"categories": categories, "form_data": request.POST})


@roles_required('administrateur', 'pharmacien responsable')
def modifier_medicament(request, pk):
    medicament = get_object_or_404(Medicament, pk=pk)
    if request.method == "POST":
        medicament.nom_commercial = request.POST.get("nom_commercial", medicament.nom_commercial)
        medicament.denomination_generique = request.POST.get("denomination_generique") or medicament.denomination_generique
        medicament.laboratoire = (request.POST.get("laboratoire") or "").strip() or None
        medicament.forme = request.POST.get("forme", medicament.forme)
        medicament.dosage = request.POST.get("dosage", medicament.dosage)
        medicament.prix_achat = request.POST.get("prix_achat", medicament.prix_achat)
        medicament.prix_vente = request.POST.get("prix_vente", medicament.prix_vente)
        medicament.categorie_id = request.POST.get("categorie", medicament.categorie_id)
        medicament.seuil_alerte = request.POST.get("seuil_alerte", medicament.seuil_alerte)
        medicament.statut = request.POST.get("statut", medicament.statut)
        medicament.code_barres = request.POST.get("code_barres", medicament.code_barres) or None
        if request.FILES.get("photo"):
            photo = request.FILES["photo"]
            extension = photo.name.lower().rsplit(".", 1)[-1] if "." in photo.name else ""
            if extension not in {"jpg", "jpeg", "png", "webp"} or photo.size > 2 * 1024 * 1024:
                messages.error(request, "La photo doit être JPG, PNG ou WEBP et ne pas dépasser 2 Mo.")
                return render(request, "medicaments/modifier.html", {"medicament": medicament, "categories": Categorie.objects.all()})
            medicament.photo = photo
        try:
            medicament.save()
        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)
        else:
            JournalAudit.objects.create(action="Médicament modifié", objet_type=f"Médicament {medicament.pk}", utilisateur=request.user)
            messages.success(request, "Médicament modifié.")
            return redirect("medicaments:detail", pk=medicament.pk)
    return render(request, "medicaments/modifier.html", {"medicament": medicament, "categories": Categorie.objects.all()})


@roles_required('administrateur', 'pharmacien responsable')
def archiver_medicament(request, pk):
    medicament = get_object_or_404(Medicament, pk=pk)
    if request.method != "POST":
        return redirect("medicaments:detail", pk=pk)
    medicament.statut = Medicament.Statut.INACTIF
    medicament.save(update_fields=["statut"])
    JournalAudit.objects.create(action="Médicament archivé", objet_type=f"Médicament {medicament.pk}", utilisateur=request.user)
    messages.info(request, "Le médicament a été archivé.")
    return redirect("medicaments:liste")


@roles_required('administrateur', 'pharmacien responsable')
def categories(request):
    recherche = request.GET.get("q", "").strip()
    if request.method == "POST":
        nom = (request.POST.get("nom") or "").strip()
        description = (request.POST.get("description") or "").strip()
        if nom:
            if Categorie.objects.filter(nom__iexact=nom).exists():
                messages.error(request, "Une catégorie porte déjà ce nom.")
            else:
                try:
                    categorie = Categorie.objects.create(nom=nom, description=description)
                except ValidationError as exc:
                    for error in exc.messages:
                        messages.error(request, error)
                else:
                    JournalAudit.objects.create(action="Catégorie créée", objet_type=f"Catégorie {categorie.pk}", utilisateur=request.user)
                    messages.success(request, "Catégorie créée.")
        return redirect("medicaments:categories")
    queryset = Categorie.objects.all().prefetch_related("medicaments")
    if recherche:
        queryset = queryset.filter(Q(nom__icontains=recherche) | Q(description__icontains=recherche))
    return render(request, "medicaments/categories.html", {"categories": queryset, "q": recherche})


@roles_required('administrateur', 'pharmacien responsable')
def creer_categorie(request):
    return categories(request)


@roles_required('administrateur', 'pharmacien responsable')
def modifier_categorie(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == "POST":
        categorie.nom = (request.POST.get("nom") or categorie.nom).strip()
        categorie.description = (request.POST.get("description") or "").strip()
        if Categorie.objects.filter(nom__iexact=categorie.nom).exclude(pk=categorie.pk).exists():
            messages.error(request, "Une autre catégorie porte déjà ce nom.")
        else:
            try:
                categorie.save()
            except ValidationError as exc:
                for error in exc.messages: messages.error(request, error)
            else:
                JournalAudit.objects.create(action="Catégorie modifiée", objet_type=f"Catégorie {categorie.pk}", utilisateur=request.user)
                messages.success(request, "Catégorie modifiée.")
                return redirect("medicaments:categories")
    return render(request, "medicaments/modifier_categorie.html", {"categorie": categorie})


@roles_required('administrateur', 'pharmacien responsable')
def supprimer_categorie(request, pk):
    if request.method != "POST":
        return redirect("medicaments:categories")
    categorie = get_object_or_404(Categorie, pk=pk)
    if categorie.medicaments.exists():
        messages.error(request, "Cette catégorie est utilisée par des médicaments et ne peut pas être supprimée.")
        return redirect("medicaments:categories")
    categorie.delete()
    JournalAudit.objects.create(action="Catégorie supprimée", objet_type=f"Catégorie {pk}", utilisateur=request.user)
    messages.success(request, "Catégorie supprimée.")
    return redirect("medicaments:categories")


def home(request):
    return redirect("rapports:dashboard")
