from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Q, Sum, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import MouvementStock
from produits.models import Produit
from fournisseurs.models import Fournisseur
from weasyprint import HTML
from django import forms
from core.utils import get_magasins_visibles, get_current_magasin, get_categories_autorisees


class ProduitAvecCategorieField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        cat = obj.categorie.nom if obj.categorie else 'Sans catégorie'
        return f'[{cat}] {obj.nom}'


class AjustementStockForm(forms.Form):
    def __init__(self, *args, **kwargs):
        magasins = kwargs.pop('magasins', None)
        cat_ids = kwargs.pop('cat_ids', None)
        entrepot = kwargs.pop('entrepot', None)
        super().__init__(*args, **kwargs)
        if magasins is not None:
            qs = Produit.objects.filter(Q(magasin__in=magasins)).select_related('categorie')
            if cat_ids is not None:
                qs = qs.filter(categorie_id__in=cat_ids)
            if entrepot:
                qs = qs.filter(entrepot=entrepot)
            self.fields['produit'].queryset = qs
            self.fields['fournisseur'].queryset = Fournisseur.objects.filter(
                Q(magasin__in=magasins)
            ).order_by('nom')

    produit = ProduitAvecCategorieField(
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
    fournisseur = forms.ModelChoiceField(
        queryset=Fournisseur.objects.all().order_by('nom'),
        required=False,
        empty_label='Sélectionner un fournisseur',
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Fournisseur (obligatoire pour une entrée)'
    )
    motif = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Ex: correction inventaire, casse, retour fournisseur...'
        }),
        label='Motif (obligatoire)'
    )

    def clean(self):
        cleaned_data = super().clean()
        type_mvt = cleaned_data.get('type_mvt')
        fournisseur = cleaned_data.get('fournisseur')
        if type_mvt == 'ENTREE' and not fournisseur:
            self.add_error('fournisseur', 'Veuillez sélectionner le fournisseur pour une entrée de stock.')
        return cleaned_data


@login_required
def ajuster_stock(request):
    magasins = get_magasins_visibles(request.user)
    cat_ids = get_categories_autorisees(request.user)
    if request.method == 'POST':
        form = AjustementStockForm(request.POST, magasins=magasins, cat_ids=cat_ids)
        if form.is_valid():
            produit = form.cleaned_data['produit']
            quantite = form.cleaned_data['quantite']
            type_mvt = form.cleaned_data['type_mvt']
            fournisseur = form.cleaned_data.get('fournisseur')
            motif = form.cleaned_data['motif']
            
            # Créer le mouvement
            MouvementStock.objects.create(
                produit=produit,
                type_mvt=type_mvt,
                quantite=quantite,
                fournisseur=fournisseur,
                motif=motif,
                utilisateur=request.user,
                magasin=get_current_magasin(request.user),
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
        form = AjustementStockForm(magasins=magasins, cat_ids=cat_ids)
    
    mouvements = MouvementStock.objects.select_related('produit', 'utilisateur', 'fournisseur').filter(Q(magasin__in=magasins)).order_by('-created_at')[:20]
    total_mouvements = MouvementStock.objects.filter(Q(magasin__in=magasins)).count()
    total_entrees = MouvementStock.objects.filter(Q(magasin__in=magasins), type_mvt='ENTREE').count()
    total_sorties = MouvementStock.objects.filter(Q(magasin__in=magasins), type_mvt='SORTIE').count()
    produits_alerte = Produit.objects.filter(
        stock_actuel__lte=F('seuil_alerte')
    ).filter(Q(magasin__in=magasins)).count()
    
    context = {
        'form': form,
        'mouvements': mouvements,
        'total_mouvements': total_mouvements,
        'total_entrees': total_entrees,
        'total_sorties': total_sorties,
        'produits_alerte': produits_alerte,
    }
    return render(request, 'stock/ajuster.html', context)


@login_required
def imprimer_inventaire(request):
    search = request.GET.get('search', '')
    categorie_id = request.GET.get('categorie', '')

    magasins = get_magasins_visibles(request.user)
    produits = Produit.objects.select_related('categorie').filter(
        Q(magasin__in=magasins)
    ).annotate(
        valeur_stock=ExpressionWrapper(
            F('stock_actuel') * F('prix_achat'),
            output_field=DecimalField(max_digits=18, decimal_places=2)
        )
    ).order_by('nom')

    if search:
        produits = produits.filter(Q(nom__icontains=search) | Q(code__icontains=search))
    if categorie_id:
        produits = produits.filter(categorie_id=categorie_id)

    # Calculer les valeurs de stock à partir des mouvements pour garantir la concordance
    from produits.models import Categorie
    for produit in produits:
        stock_initial = MouvementStock.objects.filter(
            produit=produit,
            type_mvt__in=['ENTREE', 'AJUSTEMENT', 'INVENTAIRE'],
            magasin__in=magasins,
        ).aggregate(
            total=Coalesce(Sum('quantite'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=3)))
        )['total']
        quantite_sortie = MouvementStock.objects.filter(
            produit=produit,
            type_mvt='SORTIE',
            magasin__in=magasins,
        ).aggregate(
            total=Coalesce(Sum('quantite'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=3)))
        )['total']
        produit.stock_initial = stock_initial
        produit.quantite_sortie = quantite_sortie
        produit.stock_restant = produit.stock_actuel

    categorie_nom = ''
    if categorie_id:
        categorie_nom = Categorie.objects.filter(pk=categorie_id).values_list('nom', flat=True).first() or ''

    context = {
        'produits': produits,
        'total_produits': produits.count(),
        'total_stock': produits.aggregate(total=Sum('stock_actuel'))['total'] or 0,
        'total_valeur': produits.aggregate(total=Sum('valeur_stock'))['total'] or 0,
        'search': search,
        'categorie_nom': categorie_nom,
    }

    html_string = render_to_string('stock/inventaire_pdf.html', context, request=request)
    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventaire_stock.pdf"'
    return response
