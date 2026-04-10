from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MouvementStock
from produits.models import Produit
from django import forms


class AjustementStockForm(forms.Form):
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Produit'
    )
    quantite = forms.DecimalField(
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
        label='Quantité'
    )
    type_mvt = forms.ChoiceField(
        choices=MouvementStock.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Type de mouvement'
    )
    motif = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Motif (obligatoire)'
    )


@login_required
def ajuster_stock(request):
    if request.method == 'POST':
        form = AjustementStockForm(request.POST)
        if form.is_valid():
            produit = form.cleaned_data['produit']
            quantite = form.cleaned_data['quantite']
            type_mvt = form.cleaned_data['type_mvt']
            motif = form.cleaned_data['motif']
            
            # Créer le mouvement
            MouvementStock.objects.create(
                produit=produit,
                type_mvt=type_mvt,
                quantite=quantite,
                motif=motif,
                utilisateur=request.user
            )
            
            # Mettre à jour le stock
            if type_mvt == 'ENTREE':
                produit.stock_actuel += quantite
            else:
                produit.stock_actuel -= quantite
            
            produit.save()
            
            messages.success(request, 'Ajustement de stock enregistré!')
            return redirect('stock:ajuster')
    else:
        form = AjustementStockForm()
    
    mouvements = MouvementStock.objects.all().order_by('-created_at')[:20]
    
    context = {
        'form': form,
        'mouvements': mouvements,
    }
    return render(request, 'stock/ajuster.html', context)
