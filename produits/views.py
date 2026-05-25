from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, DecimalField, Value, F, Case, When, Max
from django.db.models.functions import Coalesce, Greatest
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Produit, Categorie


def _produits_visibles(magasins):
    return Produit.objects.select_related('categorie').filter(
        Q(magasin__in=magasins)
    )
from stock.models import MouvementStock
from django import forms
from weasyprint import HTML
from utilisateurs.decorators import gerant_required
from core.utils import get_magasins_visibles, get_current_magasin


class ProduitForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        magasin = kwargs.pop('magasin', None)
        super().__init__(*args, **kwargs)
        if not self.instance or not self.instance.pk:
            self.fields['code'].required = False
        else:
            self.fields['code'].disabled = True
            # Stocker les anciennes valeurs pour affichage
            self.ancien_prix_achat = self.instance.prix_achat
            self.ancien_prix_vente_gros = self.instance.prix_vente_gros
            self.ancien_stock_actuel = self.instance.stock_actuel
            self.ancien_seuil_alerte = self.instance.seuil_alerte
        if magasin:
            self.fields['categorie'].queryset = Categorie.objects.filter(magasin=magasin)

    class Meta:
        model = Produit
        fields = ['code', 'nom', 'categorie', 'unite_mesure', 'prix_achat',
                  'prix_vente_gros', 'stock_actuel', 'seuil_alerte', 'photo', 'actif']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: RIZ001'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du produit'}),
            'categorie': forms.Select(attrs={'class': 'w-full px-3 py-2 border-0 rounded-lg text-sm focus:outline-none bg-white'}),
            'unite_mesure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'sac, carton, litre...'}),
            'prix_achat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prix_vente_gros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_actuel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'seuil_alerte': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Nom de la catégorie',
                'autofocus': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Description (optionnel)',
            }),
        }


@login_required
def liste_produits(request):
    search = request.GET.get('search', '')
    categorie_id = request.GET.get('categorie', '')
    magasins = get_magasins_visibles(request.user)
    produits = _produits_visibles(magasins).annotate(
        quantite_vendue=Coalesce(
            Sum('lignevente__quantite'),
            Value(0, output_field=DecimalField(max_digits=12, decimal_places=3)),
        ),
    )

    if search:
        produits = produits.filter(Q(nom__icontains=search) | Q(code__icontains=search))
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)
    produits = produits.order_by('nom')

    paginator = Paginator(produits, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    current = get_current_magasin(request.user)
    categories = Categorie.objects.filter(magasin=current).annotate(nb_produits=Count('produit')).order_by('nom')
    context = {
        'page_obj': page_obj,
        'produits': page_obj.object_list,
        'search': search,
        'categorie_id': categorie_id,
        'categories': categories,
    }

    # HTMX partial response (not for hx-boost full-page navigation)
    if request.headers.get('HX-Request') and not request.headers.get('HX-Boosted'):
        return render(request, 'produits/partials/table.html', context)

    return render(request, 'produits/liste.html', context)


@login_required
def imprimer_produits(request):
    search = request.GET.get('search', '')
    categorie_id = request.GET.get('categorie', '')

    magasins = get_magasins_visibles(request.user)
    produits = _produits_visibles(magasins).order_by('nom')
    
    if search:
        produits = produits.filter(Q(nom__icontains=search) | Q(code__icontains=search))
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)

    produits = list(produits)

    # Calculer les valeurs de stock et la date de dernière vente
    for produit in produits:
        quantite_vendue = MouvementStock.objects.filter(
            produit=produit,
            type_mvt='SORTIE'
        ).aggregate(
            total=Coalesce(Sum('quantite'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=3)))
        )['total']
        
        # Stock initial = stock actuel + quantité vendue (reconstitution)
        produit.stock_initial = produit.stock_actuel + quantite_vendue
        produit.stock_actuel_pdf = produit.stock_actuel
        produit.quantite_vendue = quantite_vendue

    categorie_nom = ''
    if categorie_id:
        categorie_nom = Categorie.objects.filter(pk=categorie_id).values_list('nom', flat=True).first() or ''

    context = {
        'produits': produits,
        'search': search,
        'categorie_nom': categorie_nom,
    }

    html_string = render_to_string('produits/pdf_inventaire.html', context, request=request)
    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventaire_produits.pdf"'
    return response


@login_required
def detail_produit(request, pk):
    magasins = get_magasins_visibles(request.user)
    produit = get_object_or_404(
        _produits_visibles(magasins).annotate(
            quantite_vendue=Coalesce(
                Sum('lignevente__quantite'),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=3)),
            ),
        ),
        pk=pk,
    )
    context = {'produit': produit}
    return render(request, 'produits/detail.html', context)


@login_required
@gerant_required
def creer_produit(request):
    magasin = get_current_magasin(request.user)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, magasin=magasin)
        if form.is_valid():
            produit = form.save(commit=False)
            produit.magasin = magasin
            produit.save()
            if request.headers.get('HX-Request'):
                messages.success(request, 'Produit créé avec succès!')
                return render(request, 'partials/modal_success.html', {'redirect_url': 'javascript:location.reload()'})
            else:
                messages.success(request, 'Produit créé avec succès!')
                return redirect('produits:liste')
    else:
        form = ProduitForm(magasin=magasin)

    context = {
        'form': form,
        'title': 'Créer un produit',
        'has_categories': Categorie.objects.filter(magasin=magasin).exists(),
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'partials/modal_form.html', context)
    
    return render(request, 'produits/form.html', context)


@login_required
@gerant_required
def modifier_produit(request, pk):
    magasins = get_magasins_visibles(request.user)
    magasin = get_current_magasin(request.user)
    produit = get_object_or_404(_produits_visibles(magasins), pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit, magasin=magasin)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit modifié avec succès!')
            return redirect('produits:detail', pk=produit.pk)
    else:
        form = ProduitForm(instance=produit, magasin=magasin)

    context = {
        'form': form,
        'produit': produit,
        'title': 'Modifier le produit',
        'has_categories': Categorie.objects.filter(magasin=magasin).exists(),
    }
    return render(request, 'produits/form.html', context)


@login_required
@gerant_required
def supprimer_produit(request, pk):
    magasins = get_magasins_visibles(request.user)
    produit = get_object_or_404(_produits_visibles(magasins), pk=pk)
    if request.method == 'POST':
        nom = produit.nom
        produit.delete()
        messages.success(request, f'Produit "{nom}" supprimé.')
        return redirect('produits:liste')
    context = {'produit': produit}
    return render(request, 'produits/confirm_delete.html', context)


# ─── Catégories (HTMX inline) ────────────────────────────

def _categories_list_response(request):
    """Helper: returns the categories partial with fresh data."""
    current = get_current_magasin(request.user)
    categories = Categorie.objects.filter(magasin=current).annotate(nb_produits=Count('produit')).order_by('nom')
    return render(request, 'produits/partials/categories.html', {'categories': categories})


@login_required
@gerant_required
def creer_categorie(request):
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            categorie = form.save(commit=False)
            categorie.magasin = get_current_magasin(request.user)
            categorie.save()
            return _categories_list_response(request)
        return render(request, 'produits/partials/categorie_form.html',
                      {'form': form, 'action_url': request.path})
    form = CategorieForm()
    return render(request, 'produits/partials/categorie_form.html',
                  {'form': form, 'action_url': request.path})


@login_required
@gerant_required
def modifier_categorie(request, pk):
    current = get_current_magasin(request.user)
    categorie = get_object_or_404(Categorie.objects.filter(magasin=current), pk=pk)
    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            return _categories_list_response(request)
        return render(request, 'produits/partials/categorie_form.html',
                      {'form': form, 'categorie': categorie, 'action_url': request.path})
    form = CategorieForm(instance=categorie)
    return render(request, 'produits/partials/categorie_form.html',
                  {'form': form, 'categorie': categorie, 'action_url': request.path})


@login_required
@gerant_required
def supprimer_categorie(request, pk):
    current = get_current_magasin(request.user)
    categorie = get_object_or_404(Categorie.objects.filter(magasin=current), pk=pk)
    if request.method == 'POST':
        try:
            categorie.delete()
        except Exception:
            categories = Categorie.objects.filter(magasin=current).annotate(nb_produits=Count('produit')).order_by('nom')
            return render(request, 'produits/partials/categories.html', {
                'categories': categories,
                'delete_error': f'Impossible de supprimer «{categorie.nom}» : des produits y sont rattachés.',
            })
        return _categories_list_response(request)
    return render(request, 'produits/partials/categorie_confirm_delete.html',
                  {'categorie': categorie})
