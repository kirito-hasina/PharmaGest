from django.db import migrations


ROLES = (
    "Administrateur",
    "Pharmacien responsable",
    "Gestionnaire de stock",
    "Caissier",
    "Responsable de gestion",
)


def ajouter_roles(apps, schema_editor):
    Role = apps.get_model("utilisateurs", "Role")
    for nom in ROLES:
        Role.objects.get_or_create(nom=nom)


class Migration(migrations.Migration):
    dependencies = [("utilisateurs", "0001_initial")]

    operations = [migrations.RunPython(ajouter_roles, migrations.RunPython.noop)]
