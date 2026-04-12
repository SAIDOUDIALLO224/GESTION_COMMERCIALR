from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Paiement


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
