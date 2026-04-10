from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from weasyprint import HTML, CSS
from ventes.models import Vente
from .models import Facture
import io


@login_required
def generer_facture_pdf(request, pk):
    vente = get_object_or_404(Vente, pk=pk)
    
    # Créer ou récupérer la facture
    facture, created = Facture.objects.get_or_create(
        vente=vente,
        defaults={'numero_facture': f"FAC-{vente.numero}"}
    )
    
    # Préparer le contexte
    context = {
        'facture': facture,
        'vente': vente,
        'lignes': vente.lignes.all(),
        'magasin': 'Magasin Madina',
        'adresse': 'Marché de Madina, Conakry, Guinée',
    }
    
    # Rendre le template HTML
    html_string = render_to_string('factures/facture_pdf.html', context)
    
    # Convertir en PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    # Retourner le PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{vente.numero}.pdf"'
    return response
