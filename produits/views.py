from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, DecimalField, Value, F, Case, When, Max
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Produit, Categorie
from core.models import Entrepot


def _produits_visibles(magasins, entrepot=None):
    qs = Produit.objects.select_related('categorie').filter(
        Q(magasin__in=magasins)
    )
    if entrepot:
        qs = qs.filter(entrepot=entrepot)
    return qs
from stock.models import MouvementStock
from django import forms
from weasyprint import HTML
from utilisateurs.decorators import gerant_required
from core.utils import get_magasins_visibles, get_current_magasin, get_categories_autorisees


class ProduitForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        magasin = kwargs.pop('magasin', None)
        cat_ids = kwargs.pop('cat_ids', None)
        super().__init__(*args, **kwargs)
        self._cat_ids = cat_ids
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
            qs = Categorie.objects.filter(magasin=magasin)
            if cat_ids is not None:
                qs = qs.filter(pk__in=cat_ids)
            self.fields['categorie'].queryset = qs
            # Le champ entrepôt n'apparaît que si le magasin COURANT n'est pas le
            # magasin principal. Quand l'admin bascule sur un petit magasin via
            # le sélecteur d'en-tête, il doit voir l'entrepôt comme un gérant normal
            if not magasin.est_principal:
                entrepots_qs = Entrepot.objects.filter(magasin=magasin).order_by('nom')
                self.fields['entrepot'] = forms.ModelChoiceField(
                    queryset=entrepots_qs, required=True,
                    label="Entrepôt",
                    widget=forms.Select(attrs={
                        'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white',
                    }),
                )
                if self.instance and self.instance.pk and self.instance.entrepot_id:
                    self.initial['entrepot'] = self.instance.entrepot

    def clean_categorie(self):
        cat = self.cleaned_data.get('categorie')
        if self._cat_ids is not None and cat is not None and cat.pk not in self._cat_ids:
            raise forms.ValidationError("Vous n'êtes pas autorisé à utiliser cette catégorie.")
        return cat

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
    entrepot_id = request.GET.get('entrepot', '')
    magasins = get_magasins_visibles(request.user)
    cat_ids = get_categories_autorisees(request.user)
    produits = _produits_visibles(magasins).annotate(
        quantite_vendue=Coalesce(
            Sum('lignevente__quantite'),
            Value(0, output_field=DecimalField(max_digits=12, decimal_places=3)),
        ),
    )
    if cat_ids is not None:
        produits = produits.filter(categorie_id__in=cat_ids)

    if search:
        produits = produits.filter(Q(nom__icontains=search) | Q(code__icontains=search))
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)
    if entrepot_id and entrepot_id.isdigit():
        produits = produits.filter(entrepot_id=int(entrepot_id))
    produits = produits.order_by('nom')

    paginator = Paginator(produits, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    current = get_current_magasin(request.user)
    categories_filtre = Categorie.objects.filter(magasin=current)
    if cat_ids is not None:
        categories_filtre = categories_filtre.filter(pk__in=cat_ids)
    categories = categories_filtre.annotate(nb_produits=Count('produit')).order_by('nom')
    entrepots_liste = Entrepot.objects.filter(magasin=current).order_by('nom') if current and not current.est_principal else []
    context = {
        'page_obj': page_obj,
        'produits': page_obj.object_list,
        'search': search,
        'categorie_id': categorie_id,
        'categories': categories,
        'show_entrepot': current and not current.est_principal,
        'entrepots_liste': entrepots_liste,
        'selected_entrepot': entrepot_id,
    }

    # HTMX partial response (not for hx-boost full-page navigation)
    if request.headers.get('HX-Request') and not request.headers.get('HX-Boosted'):
        return render(request, 'produits/partials/table.html', context)

    return render(request, 'produits/liste.html', context)


@login_required
def imprimer_produits(request):
    search = request.GET.get('search', '')
    categorie_id = request.GET.get('categorie', '')
    entrepot_id = request.GET.get('entrepot', '')

    magasins = get_magasins_visibles(request.user)
    cat_ids = get_categories_autorisees(request.user)
    produits = _produits_visibles(magasins)
    if cat_ids is not None:
        produits = produits.filter(categorie_id__in=cat_ids)
    if entrepot_id and entrepot_id.isdigit():
        produits = produits.filter(entrepot_id=int(entrepot_id))
    produits = produits.order_by('nom')
    
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
    cat_ids = get_categories_autorisees(request.user)
    qs = _produits_visibles(magasins)
    if cat_ids is not None:
        qs = qs.filter(categorie_id__in=cat_ids)
    produit = get_object_or_404(
        qs.annotate(
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
    cat_ids = get_categories_autorisees(request.user)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, magasin=magasin, cat_ids=cat_ids)
        if form.is_valid():
            produit = form.save(commit=False)
            produit.magasin = magasin
            if 'entrepot' in form.cleaned_data and form.cleaned_data['entrepot']:
                produit.entrepot = form.cleaned_data['entrepot']
            produit.save()
            if request.headers.get('HX-Request'):
                messages.success(request, 'Produit créé avec succès!')
                return render(request, 'partials/modal_success.html', {'redirect_url': 'javascript:location.reload()'})
            else:
                messages.success(request, 'Produit créé avec succès!')
                return redirect('produits:liste')
    else:
        form = ProduitForm(magasin=magasin, cat_ids=cat_ids)

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
    cat_ids = get_categories_autorisees(request.user)
    qs = _produits_visibles(magasins)
    if cat_ids is not None:
        qs = qs.filter(categorie_id__in=cat_ids)
    produit = get_object_or_404(qs, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit, magasin=magasin, cat_ids=cat_ids)
        if form.is_valid():
            produit = form.save(commit=False)
            if 'entrepot' in form.cleaned_data and form.cleaned_data['entrepot']:
                produit.entrepot = form.cleaned_data['entrepot']
            produit.save()
            messages.success(request, 'Produit modifié avec succès!')
            return redirect('produits:detail', pk=produit.pk)
    else:
        form = ProduitForm(instance=produit, magasin=magasin, cat_ids=cat_ids)

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
    cat_ids = get_categories_autorisees(request.user)
    qs = _produits_visibles(magasins)
    if cat_ids is not None:
        qs = qs.filter(categorie_id__in=cat_ids)
    produit = get_object_or_404(qs, pk=pk)
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
            # Ajouter automatiquement aux categories autorisees du gerant
            try:
                request.user.profilutilisateur.categories_autorisees.add(categorie)
            except Exception:
                pass
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