from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from .models import Vente, LigneVente
from produits.models import Produit
from clients.models import Client
from paiements.models import Paiement
from django import forms
import uuid


class VenteForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Client (optionnel)'
    )
    mode_paiement = forms.ChoiceField(
        choices=Paiement.MODE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Mode de paiement'
    )
    montant_paye = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Montant payé'
    )


@login_required
def nouvelle_vente(request):
    if request.method == 'POST':
        form = VenteForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Créer la vente
                vente = Vente.objects.create(
                    numero=f"VTE-{uuid.uuid4().hex[:8].upper()}",
                    client=form.cleaned_data.get('client'),
                    montant_total=0,
                    utilisateur=request.user
                )
                
                # Ajouter les lignes de vente
                produits_ids = request.POST.getlist('produit_id')
                quantites = request.POST.getlist('quantite')
                
                montant_total = 0
                for produit_id, quantite in zip(produits_ids, quantites):
                    if not produit_id or not quantite:
                        continue
                    
                    produit = Produit.objects.get(pk=produit_id)
                    quantite = float(quantite)
                    
                    # Vérifier le stock
                    if produit.stock_actuel < quantite:
                        messages.error(request, f'Stock insuffisant pour {produit.nom}')
                        vente.delete()
                        return redirect('ventes:nouvelle')
                    
                    sous_total = quantite * produit.prix_vente_gros
                    LigneVente.objects.create(
                        vente=vente,
                        produit=produit,
                        quantite=quantite,
                        prix_unitaire=produit.prix_vente_gros,
                        sous_total=sous_total
                    )
                    
                    # Mettre à jour le stock
                    produit.stock_actuel -= quantite
                    produit.save()
                    
                    montant_total += sous_total
                
                # Mettre à jour la vente
                vente.montant_total = montant_total
                montant_paye = form.cleaned_data.get('montant_paye') or 0
                vente.montant_paye = montant_paye
                vente.solde_restant = montant_total - montant_paye
                
                if montant_paye >= montant_total:
                    vente.statut = 'SOLDE'
                elif montant_paye > 0:
                    vente.statut = 'PARTIEL'
                else:
                    vente.statut = 'EN_ATTENTE'
                
                vente.save()
                
                # Créer le paiement
                if montant_paye > 0:
                    Paiement.objects.create(
                        vente=vente,
                        client=vente.client,
                        montant=montant_paye,
                        mode_paiement=form.cleaned_data['mode_paiement'],
                        utilisateur=request.user
                    )
                
                # Mettre à jour le solde du client
                if vente.client:
                    vente.client.solde_du += vente.solde_restant
                    vente.client.save()
                
                messages.success(request, 'Vente créée avec succès!')
                return redirect('ventes:detail', pk=vente.pk)
    else:
        form = VenteForm()
    
    produits = Produit.objects.filter(actif=True)
    context = {
        'form': form,
        'produits': produits,
    }
    return render(request, 'ventes/nouvelle.html', context)


@login_required
def detail_vente(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    lignes = vente.lignes.all()
    paiements = vente.paiements.all()
    
    context = {
        'vente': vente,
        'lignes': lignes,
        'paiements': paiements,
    }
    return render(request, 'ventes/detail.html', context)


@login_required
def liste_ventes(request):
    search = request.GET.get('search', '')
    ventes = Vente.objects.all().order_by('-date_vente')
    
    if search:
        ventes = ventes.filter(Q(numero__icontains=search) | Q(client__nom__icontains=search))
    
    context = {
        'ventes': ventes,
        'search': search,
    }
    return render(request, 'ventes/liste.html', context)
