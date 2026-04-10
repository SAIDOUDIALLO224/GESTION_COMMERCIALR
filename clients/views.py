from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from .models import Client
from ventes.models import Vente, LigneVente
from paiements.models import Paiement
from django import forms


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'telephone', 'telephone2', 'quartier', 'type_client', 'notes', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom complet'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+224...'}),
            'telephone2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optionnel'}),
            'quartier': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Quartier/Adresse'}),
            'type_client': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


@login_required
def liste_clients(request):
    search = request.GET.get('search', '')
    clients = Client.objects.all()
    
    if search:
        clients = clients.filter(Q(nom__icontains=search) | Q(telephone__icontains=search))
    
    context = {
        'clients': clients,
        'search': search,
    }
    return render(request, 'clients/liste.html', context)


@login_required
def detail_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    ventes = Vente.objects.filter(client=client).order_by('-date_vente')
    paiements = Paiement.objects.filter(client=client).order_by('-date_paiement')
    
    context = {
        'client': client,
        'ventes': ventes,
        'paiements': paiements,
    }
    return render(request, 'clients/detail.html', context)


@login_required
def creer_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client créé avec succès!')
            return redirect('clients:liste')
    else:
        form = ClientForm()
    
    context = {'form': form, 'title': 'Créer un client'}
    return render(request, 'clients/form.html', context)


@login_required
def modifier_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client modifié avec succès!')
            return redirect('clients:detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    
    context = {'form': form, 'client': client, 'title': 'Modifier le client'}
    return render(request, 'clients/form.html', context)
