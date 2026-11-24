from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q

ROLE_ALIAS = {
    "admin": "administrateur",
    "pharmacien": "pharmacien responsable",
    "gestionnaire": "gestionnaire de stock",
    "responsable": "responsable de gestion",
}


def roles_required(*roles):
    def decorate(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_staff or user.is_superuser:
                return view(request, *args, **kwargs)
            query = Q()
            for role in roles:
                aliases = [alias for alias, canonical in ROLE_ALIAS.items() if canonical == role]
                query |= Q(nom__iexact=role)
                for alias in aliases:
                    query |= Q(nom__iexact=alias)
            if not user.roles.filter(query).exists():
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorate


ROLES_CANONIQUES = (
    "administrateur",
    "pharmacien responsable",
    "gestionnaire de stock",
    "caissier",
    "responsable de gestion",
)

# Miroir des décorateurs @roles_required de chaque application (sert à l'interface :
# menu, page d'accueil). Si vous changez un décorateur, changez-le aussi ici.
ACCES = {
    "dashboard": ("administrateur", "responsable de gestion", "pharmacien responsable"),
    "medicaments": ("administrateur", "pharmacien responsable"),
    "fournisseurs": ("administrateur", "gestionnaire de stock"),
    "clients": ("administrateur", "caissier"),
    "achats": ("administrateur", "gestionnaire de stock", "pharmacien responsable"),
    "stock": ("administrateur", "gestionnaire de stock", "pharmacien responsable"),
    "ventes": ("administrateur", "caissier", "pharmacien responsable"),
    "rapports": ("administrateur", "responsable de gestion", "pharmacien responsable"),
}

ACCUEIL = (
    ("ventes", "ventes:creer"),
    ("stock", "stock:liste"),
    ("achats", "achats:liste"),
    ("fournisseurs", "fournisseurs:liste"),
    ("clients", "clients:liste"),
    ("medicaments", "medicaments:liste"),
)


def roles_canoniques(user):
    if not user.is_authenticated:
        return set()
    if user.is_staff or user.is_superuser:
        return set(ROLES_CANONIQUES)
    noms = {nom.lower() for nom in user.roles.values_list("nom", flat=True)}
    return {ROLE_ALIAS.get(nom, nom) for nom in noms}


def acces_modules(user):
    roles = roles_canoniques(user)
    acces = {module: bool(roles.intersection(autorises)) for module, autorises in ACCES.items()}
    acces["utilisateurs"] = bool(user.is_authenticated and (user.is_staff or user.is_superuser))
    return acces


def page_accueil(user):
    """Première page accessible à l'utilisateur (le tableau de bord n'est pas ouvert à tous)."""
    acces = acces_modules(user)
    for module, url in ACCUEIL:
        if acces[module]:
            return url
    return None
