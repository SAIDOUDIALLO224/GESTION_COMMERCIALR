from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.db import models
from django.db.models import Q
from decimal import Decimal
from .models import Paiement, CompteEcoBanqueClient
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CompteEcoBanqueClientForm
from core.models import Configuration
from core.utils import get_magasins_visibles


@login_required
def imprimer_recu(request, pk):
    magasins = get_magasins_visibles(request.user)
    paiement = get_object_or_404(
        Paiement.objects.select_related('vente', 'client', 'utilisateur').filter(
            Q(vente__magasin__in=magasins)
        ),
        pk=pk,
    )

    magasin_nom = paiement.vente.magasin.nom if paiement.vente.magasin else 'Magasin Madina'
    adresse = paiement.vente.magasin.adresse if paiement.vente.magasin and paiement.vente.magasin.adresse else 'Marché de Madina, Conakry, Guinée'

    context = {
        'paiement': paiement,
        'magasin': magasin_nom,
        'adresse': adresse,
    }
    html_string = render_to_string('paiements/recu_pdf.html', context, request=request)
    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="recu_paiement_{paiement.id}.pdf"'
    return response


def _get_config():
    config, created = Configuration.objects.get_or_create(
        pk=1, defaults={'nom_magasin': 'Magasin Madina'}
    )
    return config

def get_solde_compte_bancaire():
    return _get_config().solde_compte_bancaire

def set_solde_compte_bancaire(montant):
    config = _get_config()
    config.solde_compte_bancaire = montant
    config.save(update_fields=['solde_compte_bancaire'])

def ajouter_solde_compte_bancaire(montant):
    config = _get_config()
    config.solde_compte_bancaire += montant
    config.save(update_fields=['solde_compte_bancaire'])


@login_required
def comptes_ecobanque_liste(request):
    comptes = CompteEcoBanqueClient.objects.select_related('client', 'utilisateur').order_by('-date_creation')
    
    total_montants_sortis_global = comptes.aggregate(total=models.Sum('montant_sorti'))['total'] or Decimal('0')
    total_montants_entrants_global = comptes.aggregate(
        total=models.Sum(models.F('montant_verset') + models.F('montant_initial'))
    )['total'] or Decimal('0')
    
    montant_exact_compte = get_solde_compte_bancaire()
    
    if request.method == 'POST' and 'update_montant_exact' in request.POST:
        montant_exact = request.POST.get('montant_exact_compte')
        if montant_exact:
            try:
                montant_exact_compte = Decimal(montant_exact)
                set_solde_compte_bancaire(montant_exact_compte)
                montant_exact_compte = get_solde_compte_bancaire()
                messages.success(request, f"Montant exact du compte bancaire mis a jour : {montant_exact_compte} GNF")
            except (ValueError, TypeError):
                messages.error(request, "Montant invalide.")
        else:
            messages.error(request, "Veuillez saisir un montant.")
    
    context = {
        'comptes': comptes,
        'title': 'Comptes Ecobanque',
        'total_montants_sortis_global': total_montants_sortis_global,
        'total_montants_entrants_global': total_montants_entrants_global,
        'montant_exact_compte': montant_exact_compte,
    }
    return render(request, 'paiements/comptes_ecobanque_liste.html', context)


@login_required
def comptes_ecobanque_form(request, pk=None):
    if pk:
        compte = get_object_or_404(CompteEcoBanqueClient, pk=pk)
        title = f"Modifier le compte {compte.client.nom}"
    else:
        compte = None
        title = "Nouveau compte Ecobanque"

    if request.method == 'POST':
        form = CompteEcoBanqueClientForm(request.POST, instance=compte)
        if form.is_valid():
            compte = form.save(commit=False)
            compte.utilisateur = request.user
            
            ancien_montant_entrant = Decimal('0')
            ancien_montant_sorti = Decimal('0')
            if compte.pk:
                ancien_compte = CompteEcoBanqueClient.objects.get(pk=compte.pk)
                ancien_montant_entrant = ancien_compte.montant_verset + ancien_compte.montant_initial
                ancien_montant_sorti = ancien_compte.montant_sorti
            
            nouveau_montant_entrant = compte.montant_verset + compte.montant_initial
            nouveau_montant_sorti = compte.montant_sorti
            
            difference_entrant = nouveau_montant_entrant - ancien_montant_entrant
            difference_sorti = nouveau_montant_sorti - ancien_montant_sorti
            
            ajustement_total = difference_entrant - difference_sorti
            
            if ajustement_total != 0:
                solde_actuel = get_solde_compte_bancaire()
                set_solde_compte_bancaire(solde_actuel + ajustement_total)
            
            compte.save()
            messages.success(request, f"Compte {compte.client.nom} enregistre avec succes.")
            return redirect('paiements:comptes_ecobanque_liste')
    else:
        form = CompteEcoBanqueClientForm(instance=compte)

    context = {
        'form': form,
        'title': title,
        'compte': compte
    }
    return render(request, 'paiements/comptes_ecobanque_form.html', context)


@login_required
def compte_ecobanque_supprimer(request, pk):
    compte = get_object_or_404(CompteEcoBanqueClient, pk=pk)
    client_nom = compte.client.nom
    
    montant_entrant_a_soustraire = compte.montant_verset + compte.montant_initial
    montant_sorti_a_ajouter = compte.montant_sorti
    ajustement = montant_sorti_a_ajouter - montant_entrant_a_soustraire
    
    solde_actuel = get_solde_compte_bancaire()
    set_solde_compte_bancaire(solde_actuel + ajustement)
    
    compte.delete()
    messages.success(request, f"Compte de {client_nom} supprime avec succes.")
    return redirect('paiements:comptes_ecobanque_liste')
