from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from .models import MouvementStock
from produits.models import Produit
from django import forms


class AjustementStockForm(forms.Form):
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Produit'
    )
    quantite = forms.DecimalField(
        max_digits=10,
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'step': '0.001',
            'min': '0.001',
        }),
        label='Quantité'
    )
    type_mvt = forms.ChoiceField(
        choices=MouvementStock.TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Type de mouvement'
    )
    motif = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Ex: correction inventaire, casse, retour fournisseur...'
        }),
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
    
    mouvements = MouvementStock.objects.select_related('produit', 'utilisateur').all().order_by('-created_at')[:20]
    total_mouvements = MouvementStock.objects.count()
    total_entrees = MouvementStock.objects.filter(type_mvt='ENTREE').count()
    total_sorties = MouvementStock.objects.filter(type_mvt='SORTIE').count()
    produits_alerte = Produit.objects.filter(stock_actuel__lte=F('seuil_alerte')).count()
    
    context = {
        'form': form,
        'mouvements': mouvements,
        'total_mouvements': total_mouvements,
        'total_entrees': total_entrees,
        'total_sorties': total_sorties,
        'produits_alerte': produits_alerte,
    }
    return render(request, 'stock/ajuster.html', context)
