from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import JournalAudit, Role, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("PharmaGest", {"fields": ("nom_complet", "roles")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("PharmaGest", {"fields": ("nom_complet", "roles")}),)
    list_display = ("username", "nom_complet", "is_active", "is_staff")
    filter_horizontal = ("groups", "user_permissions", "roles")


admin.site.register(Role)
admin.site.register(JournalAudit)
