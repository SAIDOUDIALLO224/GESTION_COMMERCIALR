from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, DecimalField, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Produit, Categorie
from django import forms
from weasyprint import HTML
from utilisateurs.decorators import gerant_required


class ProduitForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance or not self.instance.pk:
            self.fields['code'].required = False
        else:
            self.fields['code'].disabled = True

    class Meta:
        model = Produit
        fields = ['code', 'nom', 'categorie', 'unite_mesure', 'prix_achat',
                  'prix_vente_gros', 'prix_vente_detail', 'stock_actuel', 'seuil_alerte', 'photo', 'actif']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: RIZ001'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du produit'}),
            'categorie': forms.Select(attrs={'class': 'w-full px-3 py-2 border-0 rounded-lg text-sm focus:outline-none bg-white'}),
            'unite_mesure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'sac, carton, litre...'}),
            'prix_achat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prix_vente_gros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'prix_vente_detail': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
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
    produits = Produit.objects.select_related('categorie').annotate(
        quantite_vendue=Coalesce(
            Sum('lignevente__quantite'),
            Value(0, output_field=DecimalField(max_digits=12, decimal_places=3)),
        ),
    )

    if search:
        produits = produits.filter(Q(nom__icontains=search) | Q(code__icontains=search))
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)

    paginator = Paginator(produits, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Categorie.objects.annotate(nb_produits=Count('produit')).order_by('nom')
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

    produits = Produit.objects.select_related('categorie').all().order_by('nom')
    if search:
        produits = produits.filter(Q(nom__icontains=search) | Q(code__icontains=search))
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)

    categorie_nom = ''
    if categorie_id:
        categorie_nom = Categorie.objects.filter(pk=categorie_id).values_list('nom', flat=True).first() or ''

    context = {
        'produits': produits,
        'search': search,
        'categorie_nom': categorie_nom,
    }

    html_string = render_to_string('produits/pdf_inventaire.html', context)
    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventaire_produits.pdf"'
    return response


@login_required
def detail_produit(request, pk):
    produit = get_object_or_404(
        Produit.objects.select_related('categorie').annotate(
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


@login_required
@gerant_required
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
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
    categories = Categorie.objects.annotate(nb_produits=Count('produit')).order_by('nom')
    return render(request, 'produits/partials/categories.html', {'categories': categories})


@login_required
@gerant_required
def creer_categorie(request):
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            form.save()
            return _categories_list_response(request)
        return render(request, 'produits/partials/categorie_form.html',
                      {'form': form, 'action_url': request.path})
    form = CategorieForm()
    return render(request, 'produits/partials/categorie_form.html',
                  {'form': form, 'action_url': request.path})


@login_required
@gerant_required
def modifier_categorie(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
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
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        try:
            categorie.delete()
        except Exception:
            categories = Categorie.objects.annotate(nb_produits=Count('produit')).order_by('nom')
            return render(request, 'produits/partials/categories.html', {
                'categories': categories,
                'delete_error': f'Impossible de supprimer «{categorie.nom}» : des produits y sont rattachés.',
            })
        return _categories_list_response(request)
    return render(request, 'produits/partials/categorie_confirm_delete.html',
                  {'categorie': categorie})
