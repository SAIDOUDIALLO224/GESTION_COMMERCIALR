from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Q, Sum, F, Count
from django import forms
from produits.models import Produit, Categorie
from clients.models import Client
from ventes.models import Vente
from stock.models import MouvementStock
from .models import Magasin
from utilisateurs.models import ProfilUtilisateur
from .utils import get_magasins_visibles, get_current_magasin


@login_required
def dashboard(request):
    today = timezone.now().date()
    current = get_current_magasin(request.user)
    magasins = get_magasins_visibles(request.user)
    
    # Statistiques du jour
    ventes_today = Vente.objects.filter(date_vente__date=today, magasin__in=magasins)
    ca_today = ventes_today.aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    nb_ventes = ventes_today.count()
    montant_encaisse = ventes_today.aggregate(Sum('montant_paye'))['montant_paye__sum'] or 0
    
    # Crédits en cours
    credits_en_cours = Vente.objects.filter(
        statut__in=['EN_ATTENTE', 'PARTIEL'], magasin__in=magasins
    ).aggregate(
        Sum('solde_restant')
    )['solde_restant__sum'] or 0
    
    # Produits en alerte (stock actuel inferieur ou egal au seuil)
    produits_alerte = Produit.objects.filter(
        actif=True,
        stock_actuel__lte=F('seuil_alerte'),
    ).filter(
Q(magasin__in=magasins)
    ).order_by('stock_actuel')[:10]
    
    # Clients avec dettes
    clients_dettes = Client.objects.filter(solde_du__gt=0).order_by('-solde_du')[:10]
    
    context = {
        'ca_today': f"{ca_today:,.0f}",
        'nb_ventes': nb_ventes,
        'montant_encaisse': f"{montant_encaisse:,.0f}",
        'credits_en_cours': f"{credits_en_cours:,.0f}",
        'produits_alerte': produits_alerte,
        'clients_dettes': clients_dettes,
        'magasins': magasins,
    }
    
    return render(request, 'core/dashboard.html', context)


def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('core:dashboard')
    return render(request, 'core/login.html', {'next': next_url})


def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('core:login')


# ─── Magasin Form ──────────────────────

class MagasinForm(forms.ModelForm):
    copier_depuis = forms.ModelChoiceField(
        queryset=Magasin.objects.all(),
        required=False,
        label="Copier les produits depuis",
        help_text="Nouveau magasin : copie le catalogue d'un magasin existant (produits uniquement).",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
        }),
    )

    class Meta:
        model = Magasin
        fields = ['nom', 'adresse', 'actif', 'est_principal', 'magasins_visibles']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
            }),
            'magasins_visibles': forms.SelectMultiple(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields['copier_depuis']
            self.fields['magasins_visibles'].queryset = Magasin.objects.exclude(pk=self.instance.pk)
        else:
            self.fields['magasins_visibles'].queryset = Magasin.objects.all()


# ─── Magasin CRUD ──────────────────────

def _superadmin_required(request):
    if request.user.is_superuser:
        return True
    messages.error(request, 'Accès réservé à l\'administrateur.')
    return False


@login_required
def migrer_donnees(request):
    if not _superadmin_required(request):
        return redirect('core:dashboard')
    magasin_id = request.GET.get('magasin_id')
    if magasin_id:
        magasin = get_object_or_404(Magasin, pk=magasin_id)
    else:
        magasin = get_current_magasin(request.user)
    if not magasin:
        messages.error(request, 'Aucun magasin cible. Créez d\'abord un magasin.')
        return redirect('core:liste_magasins')
    count_produits = Produit.objects.filter(magasin__isnull=True).update(magasin=magasin)
    count_ventes = Vente.objects.filter(magasin__isnull=True).update(magasin=magasin)
    count_mouvements = MouvementStock.objects.filter(magasin__isnull=True).update(magasin=magasin)
    total = count_produits + count_ventes + count_mouvements
    if total == 0:
        messages.info(request, 'Aucune donnée orpheline à migrer.')
    else:
        messages.success(request,
            f'{count_produits} produit(s), {count_ventes} vente(s) et {count_mouvements} mouvement(s) '
            f'rattaché(s) à "{magasin.nom}".')
    return redirect('core:liste_magasins')


@login_required
def changer_magasin(request):
    if request.method == 'POST':
        magasin_id = request.POST.get('magasin_id')
        magasins = get_magasins_visibles(request.user)
        magasin = get_object_or_404(magasins, pk=magasin_id)
        profil, created = ProfilUtilisateur.objects.get_or_create(
            user=request.user,
            defaults={'role': 'GERANT', 'magasin': magasin}
        )
        profil.magasin = magasin
        profil.save()
        messages.success(request, f'Vous travaillez maintenant dans "{magasin.nom}".')
    return redirect(request.META.get('HTTP_REFERER', 'core:dashboard'))


@login_required
def liste_magasins(request):
    magasins = Magasin.objects.annotate(
        nb_utilisateurs=Count('profilutilisateur'),
    ).order_by('nom')
    total_orphelins = (
        Produit.objects.filter(magasin__isnull=True).count()
        + Vente.objects.filter(magasin__isnull=True).count()
        + MouvementStock.objects.filter(magasin__isnull=True).count()
    )
    context = {'magasins': magasins, 'total_orphelins': total_orphelins}
    return render(request, 'core/magasin_liste.html', context)


@login_required
def creer_magasin(request):
    if not _superadmin_required(request):
        return redirect('core:dashboard')
    if request.method == 'POST':
        form = MagasinForm(request.POST)
        if form.is_valid():
            source = form.cleaned_data.get('copier_depuis')
            magasin = form.save(commit=False)
            if not source:
                magasin.save()
            else:
                magasin.save()
                # Copier les produits du magasin source
                produits_source = Produit.objects.filter(magasin=source)
                count = 0
                for p in produits_source:
                    Produit.objects.create(
                        magasin=magasin,
                        code=p.code,
                        nom=p.nom,
                        categorie=p.categorie,
                        prix_vente_gros=p.prix_vente_gros,
                        stock_actuel=0,
                        seuil_alerte=p.seuil_alerte,
                        actif=p.actif,
                    )
                    count += 1
                messages.success(request, f'Catalogue copié ({count} produits depuis "{source.nom}").')
            profil, created = ProfilUtilisateur.objects.get_or_create(
                user=request.user,
                defaults={'role': 'GERANT', 'magasin': magasin}
            )
            if not profil.magasin:
                profil.magasin = magasin
                profil.save()
            # Rattachement automatique des données orphelines si c'est le magasin principal
            if magasin.est_principal:
                count_produits = Produit.objects.filter(magasin__isnull=True).update(magasin=magasin)
                count_ventes = Vente.objects.filter(magasin__isnull=True).update(magasin=magasin)
                count_mouvements = MouvementStock.objects.filter(magasin__isnull=True).update(magasin=magasin)
                total = count_produits + count_ventes + count_mouvements
                if total > 0:
                    messages.success(request,
                        f'{count_produits} produit(s), {count_ventes} vente(s) et {count_mouvements} mouvement(s) '
                        f'rattaché(s) automatiquement à "{magasin.nom}".')
            messages.success(request, f'Magasin "{magasin.nom}" créé.')
            return redirect('core:detail_magasin', pk=magasin.pk)
    else:
        form = MagasinForm()
    context = {'form': form, 'title': 'Créer un magasin'}
    return render(request, 'core/magasin_form.html', context)


@login_required
def modifier_magasin(request, pk):
    if not _superadmin_required(request):
        return redirect('core:dashboard')
    magasin = get_object_or_404(Magasin, pk=pk)
    if request.method == 'POST':
        form = MagasinForm(request.POST, instance=magasin)
        if form.is_valid():
            form.save()
            messages.success(request, 'Magasin modifié avec succès.')
            return redirect('core:liste_magasins')
    else:
        form = MagasinForm(instance=magasin)
    context = {'form': form, 'magasin': magasin, 'title': 'Modifier le magasin'}
    return render(request, 'core/magasin_form.html', context)


@login_required
def supprimer_magasin(request, pk):
    if not _superadmin_required(request):
        return redirect('core:dashboard')
    magasin = get_object_or_404(Magasin, pk=pk)
    if request.method == 'POST':
        nom = magasin.nom
        magasin.delete()
        messages.success(request, f'Magasin "{nom}" supprimé.')
    return redirect('core:liste_magasins')


@login_required
def detail_magasin(request, pk):
    magasin = get_object_or_404(Magasin.objects.annotate(
        nb_utilisateurs=Count('profilutilisateur'),
    ), pk=pk)

    from django.utils import timezone
    aujourd_hui = timezone.now().date()

    produits = Produit.objects.filter(magasin=magasin).select_related('categorie')
    ventes = Vente.objects.filter(magasin=magasin).select_related('client')
    mouvements = MouvementStock.objects.filter(magasin=magasin).select_related('produit').order_by('-created_at')[:20]
    utilisateurs = ProfilUtilisateur.objects.filter(magasin=magasin).select_related('user')

    total_produits = produits.count()
    total_ventes = ventes.count()
    total_ventes_aujourdhui = ventes.filter(date_vente__date=aujourd_hui).count()
    total_revenue = ventes.aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    total_solde_restant = ventes.aggregate(Sum('solde_restant'))['solde_restant__sum'] or 0
    produits_rupture = produits.filter(stock_actuel__lte=F('seuil_alerte')).count()
    produits_en_alerte = produits.filter(stock_actuel__gt=0, stock_actuel__lte=F('seuil_alerte'))
    dernieres_ventes = ventes.order_by('-date_vente')[:10]

    context = {
        'magasin': magasin,
        'total_produits': total_produits,
        'total_ventes': total_ventes,
        'total_ventes_aujourdhui': total_ventes_aujourdhui,
        'total_revenue': total_revenue,
        'total_solde_restant': total_solde_restant,
        'produits_rupture': produits_rupture,
        'produits_en_alerte': produits_en_alerte,
        'dernieres_ventes': dernieres_ventes,
        'mouvements': mouvements,
        'utilisateurs': utilisateurs,
    }
    return render(request, 'core/magasin_detail.html', context)
