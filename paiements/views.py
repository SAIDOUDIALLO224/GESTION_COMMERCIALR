from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
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
    context = {
        'comptes': comptes,
        'title': 'Comptes Ecobanque'
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
