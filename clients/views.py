from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from utilisateurs.models import JournalAudit
from utilisateurs.permissions import roles_required

from .models import Client


@roles_required('administrateur', 'caissier')
def liste_clients(request):
    qs = Client.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(nom__icontains=q) | Q(telephone__icontains=q))
    page = Paginator(qs.order_by("nom"), 20).get_page(request.GET.get("page"))
    return render(request, "clients/liste.html", {"clients": page, "page_obj": page})


@roles_required('administrateur', 'caissier')
def creer_client(request):
    form = ClientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        client = form.save()
        JournalAudit.objects.create(action="Client créé", objet_type=f"Client {client.pk}", utilisateur=request.user)
        messages.success(request, "Client enregistré.")
        return redirect("clients:detail", pk=client.pk)
    return render(request, "clients/creer.html", {"form": form})


@roles_required('administrateur', 'caissier')
def detail_client(request, pk):
    return render(request, "clients/detail.html", {"client": get_object_or_404(Client, pk=pk)})


@roles_required('administrateur', 'caissier')
def modifier_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == "POST" and form.is_valid():
        form.save()
        JournalAudit.objects.create(action="Client modifié", objet_type=f"Client {pk}", utilisateur=request.user)
        messages.success(request, "Client modifié.")
        return redirect("clients:detail", pk=pk)
    return render(request, "clients/modifier.html", {"client": client, "form": form})
