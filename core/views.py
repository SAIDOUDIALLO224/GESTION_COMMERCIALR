from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Sum, F
from produits.models import Produit
from clients.models import Client
from ventes.models import Vente


@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # Statistiques du jour
    ventes_today = Vente.objects.filter(date_vente__date=today)
    ca_today = ventes_today.aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    nb_ventes = ventes_today.count()
    montant_encaisse = ventes_today.aggregate(Sum('montant_paye'))['montant_paye__sum'] or 0
    
    # Crédits en cours
    credits_en_cours = Vente.objects.filter(statut__in=['EN_ATTENTE', 'PARTIEL']).aggregate(
        Sum('solde_restant')
    )['solde_restant__sum'] or 0
    
    # Produits en alerte (stock actuel inferieur ou egal au seuil)
    produits_alerte = Produit.objects.filter(
        actif=True,
        stock_actuel__lte=F('seuil_alerte'),
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
