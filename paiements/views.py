from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.db import models
from decimal import Decimal
from .models import Paiement, CompteEcoBanqueClient
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CompteEcoBanqueClientForm


@login_required
def imprimer_recu(request, pk):
	paiement = get_object_or_404(
		Paiement.objects.select_related('vente', 'client', 'utilisateur'),
		pk=pk,
	)

	context = {
		'paiement': paiement,
	}
	html_string = render_to_string('paiements/recu_pdf.html', context)
	pdf = HTML(string=html_string).write_pdf()

	response = HttpResponse(pdf, content_type='application/pdf')
	response['Content-Disposition'] = f'inline; filename="recu_paiement_{paiement.id}.pdf"'
	return response


@login_required
def comptes_ecobanque_liste(request):
    comptes = CompteEcoBanqueClient.objects.select_related('client', 'utilisateur').order_by('-date_creation')
    
    # Calculer les totaux globaux
    total_montants_sortis_global = comptes.aggregate(total=models.Sum('montant_sorti'))['total'] or Decimal('0')
    total_montants_entrants_global = comptes.aggregate(
        total=models.Sum(models.F('montant_verset') + models.F('montant_initial'))
    )['total'] or Decimal('0')
    
    # Gérer la mise à jour manuelle du montant exact du compte
    montant_exact_compte = None
    if request.method == 'POST' and 'update_montant_exact' in request.POST:
        montant_exact = request.POST.get('montant_exact_compte')
        if montant_exact:
            try:
                montant_exact_compte = Decimal(montant_exact)
                # Sauvegarder en session pour persister entre les requêtes
                request.session['montant_exact_compte_global'] = str(montant_exact_compte)
                messages.success(request, f"Montant exact du compte bancaire mis à jour : {montant_exact_compte} GNF")
            except (ValueError, TypeError):
                messages.error(request, "Montant invalide.")
        else:
            messages.error(request, "Veuillez saisir un montant.")
    
    # Récupérer le montant exact depuis la session
    if 'montant_exact_compte_global' in request.session:
        montant_exact_compte = Decimal(request.session['montant_exact_compte_global'])
    
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
            
            # Calculer la différence pour ajuster le montant exact du compte
            ancien_montant_entrant = Decimal('0')
            ancien_montant_sorti = Decimal('0')
            if compte.pk:  # Si c'est une modification
                ancien_compte = CompteEcoBanqueClient.objects.get(pk=compte.pk)
                ancien_montant_entrant = ancien_compte.montant_verset + ancien_compte.montant_initial
                ancien_montant_sorti = ancien_compte.montant_sorti
            
            nouveau_montant_entrant = compte.montant_verset + compte.montant_initial
            nouveau_montant_sorti = compte.montant_sorti
            
            difference_entrant = nouveau_montant_entrant - ancien_montant_entrant
            difference_sorti = nouveau_montant_sorti - ancien_montant_sorti
            
            # Ajuster le montant exact du compte : + entrants, - sortis
            ajustement_total = difference_entrant - difference_sorti
            
            if ajustement_total != 0 and 'montant_exact_compte_global' in request.session:
                montant_exact_actuel = Decimal(request.session['montant_exact_compte_global'])
                nouveau_montant_exact = montant_exact_actuel + ajustement_total
                request.session['montant_exact_compte_global'] = str(nouveau_montant_exact)
            
            compte.save()
            messages.success(request, f"Compte {compte.client.nom} enregistré avec succès.")
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
    
    # Soustraire les montants entrants du montant exact du compte
    montant_entrant_a_soustraire = compte.montant_verset + compte.montant_initial
    if 'montant_exact_compte' in request.session:
        montant_exact_actuel = Decimal(request.session['montant_exact_compte'])
        nouveau_montant_exact = montant_exact_actuel - montant_entrant_a_soustraire
        request.session['montant_exact_compte'] = str(nouveau_montant_exact)
    
    compte.delete()
    messages.success(request, f"Compte de {client_nom} supprimé avec succès.")
    return redirect('paiements:comptes_ecobanque_liste')


@login_required
def imprimer_recu(request, pk):
	paiement = get_object_or_404(
		Paiement.objects.select_related('vente', 'client', 'utilisateur'),
		pk=pk,
	)

	context = {
		'paiement': paiement,
	}
	html_string = render_to_string('paiements/recu_pdf.html', context)
	pdf = HTML(string=html_string).write_pdf()

	response = HttpResponse(pdf, content_type='application/pdf')
	response['Content-Disposition'] = f'inline; filename="recu_paiement_{paiement.id}.pdf"'
	return response
