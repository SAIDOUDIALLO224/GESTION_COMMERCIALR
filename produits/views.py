from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Produit, Categorie
from django import forms
from utilisateurs.decorators import gerant_required


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['code', 'nom', 'categorie', 'unite_mesure', 'prix_achat', 
                  'prix_vente_gros', 'prix_vente_detail', 'stock_actuel', 'seuil_alerte', 'photo', 'actif']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: RIZ001'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du produit'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'unite_mesure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'sac, carton, litre...'}),
            'prix_achat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prix_vente_gros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prix_vente_detail': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_actuel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'seuil_alerte': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


@login_required
def liste_produits(request):
    search = request.GET.get('search', '')
    produits = Produit.objects.all()
    
    if search:
        produits = produits.filter(Q(nom__icontains=search) | Q(code__icontains=search))
    
    context = {
        'produits': produits,
        'search': search,
    }
    return render(request, 'produits/liste.html', context)


@login_required
def detail_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    context = {'produit': produit}
    return render(request, 'produits/detail.html', context)


@login_required
@gerant_required
def creer_produit(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit créé avec succès!')
            return redirect('produits:liste')
    else:
        form = ProduitForm()
    
    context = {'form': form, 'title': 'Créer un produit'}
    return render(request, 'produits/form.html', context)


@login_required
@gerant_required
def modifier_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit modifié avec succès!')
            return redirect('produits:detail', pk=produit.pk)
    else:
        form = ProduitForm(instance=produit)
    
    context = {'form': form, 'produit': produit, 'title': 'Modifier le produit'}
    return render(request, 'produits/form.html', context)
