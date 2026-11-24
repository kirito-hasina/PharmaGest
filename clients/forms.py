from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["actif"].widget.attrs["class"] = "form-check-input"

    class Meta:
        model = Client
        fields = ["nom", "telephone", "email", "adresse", "actif"]
        widgets = {"adresse": forms.Textarea(attrs={"rows": 3})}
