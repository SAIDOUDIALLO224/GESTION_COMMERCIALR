from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from weasyprint import HTML, CSS
from ventes.models import Vente
from .models import Facture
from core.utils import get_magasins_visibles
import io


@login_required
def generer_facture_pdf(request, pk):
    magasins = get_magasins_visibles(request.user)
    vente = get_object_or_404(
        Vente.objects.filter(Q(magasin__in=magasins)),
        pk=pk,
    )
    
    # Créer ou récupérer la facture
    facture, created = Facture.objects.get_or_create(
        vente=vente,
        defaults={'numero_facture': f"FAC-{vente.numero}"}
    )
    
    magasin_nom = vente.magasin.nom if vente.magasin else 'Magasin Madina'
    adresse = vente.magasin.adresse if vente.magasin and vente.magasin.adresse else 'Marché de Madina, Conakry, Guinée'
    
    # Préparer le contexte
    context = {
        'facture': facture,
        'vente': vente,
        'lignes': vente.lignes.all(),
        'magasin': magasin_nom,
        'adresse': adresse,
    }
    
    # Rendre le template HTML
    html_string = render_to_string('factures/facture_pdf.html', context, request=request)
    
    # Convertir en PDF
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    # Retourner le PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{vente.numero}.pdf"'
    return response
