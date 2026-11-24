from .permissions import acces_modules


def acces(request):
    user = request.user
    if not user.is_authenticated:
        return {}
    noms = [role.nom for role in user.roles.all()]
    if not noms and (user.is_staff or user.is_superuser):
        noms = ["Administrateur"]
    return {"acces": acces_modules(user), "roles_affiches": noms}
