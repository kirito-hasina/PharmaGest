from django import forms

from .models import Fournisseur


class FournisseurForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["actif"].widget.attrs["class"] = "form-check-input"

    class Meta:
        model = Fournisseur
        fields = ["raison_sociale", "telephone", "adresse", "email", "identifiant_fiscal", "contact_principal", "actif"]
        widgets = {"adresse": forms.Textarea(attrs={"rows": 3})}
