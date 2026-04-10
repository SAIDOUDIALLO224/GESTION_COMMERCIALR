from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import F, Sum, DecimalField, ExpressionWrapper, Count
from django.db.models.functions import TruncDate
from django.template.loader import render_to_string
from ventes.models import Vente
from produits.models import Produit
from stock.models import MouvementStock
from weasyprint import HTML
from utilisateurs.decorators import gerant_required


@login_required
@gerant_required
def rapports_index(request):
    return render(request, 'rapports/index.html')


@login_required
@gerant_required
def rapport_ventes(request):
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    # Defensive sanitization for query-string values like 'None' or empty strings.
    date_debut = None if date_debut in (None, '', 'None') else date_debut
    date_fin = None if date_fin in (None, '', 'None') else date_fin

    ventes = Vente.objects.select_related('client').all().order_by('-date_vente')
    if date_debut:
        ventes = ventes.filter(date_vente__date__gte=date_debut)
    if date_fin:
        ventes = ventes.filter(date_vente__date__lte=date_fin)
    
    total_ventes = ventes.aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    total_paye = ventes.aggregate(Sum('montant_paye'))['montant_paye__sum'] or 0
    total_restant = ventes.aggregate(Sum('solde_restant'))['solde_restant__sum'] or 0
    nb_ventes = ventes.count()

    ventes_par_jour = (
        ventes.annotate(jour=TruncDate('date_vente'))
        .values('jour')
        .annotate(total=Sum('montant_total'))
        .order_by('jour')
    )
    graph_jours = [v['jour'].strftime('%d/%m') for v in ventes_par_jour if v['jour']]
    graph_totaux = [float(v['total'] or 0) for v in ventes_par_jour]

    statuts = ventes.values('statut').annotate(total=Count('id')).order_by('statut')
    statut_map = dict(Vente.STATUT_CHOICES)
    graph_statut_labels = [statut_map.get(s['statut'], s['statut']) for s in statuts]
    graph_statut_values = [s['total'] for s in statuts]
    
    context = {
        'ventes': ventes,
        'total_ventes': total_ventes,
        'total_paye': total_paye,
        'total_restant': total_restant,
        'nb_ventes': nb_ventes,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'graph_jours': graph_jours,
        'graph_totaux': graph_totaux,
        'graph_statut_labels': graph_statut_labels,
        'graph_statut_values': graph_statut_values,
    }
    return render(request, 'rapports/ventes.html', context)


@login_required
@gerant_required
def rapport_stock(request):
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    date_debut = None if date_debut in (None, '', 'None') else date_debut
    date_fin = None if date_fin in (None, '', 'None') else date_fin

    produits = Produit.objects.select_related('categorie').annotate(
        valeur_stock=ExpressionWrapper(
            F('stock_actuel') * F('prix_achat'),
            output_field=DecimalField(max_digits=18, decimal_places=2)
        )
    )

    total_stock_value = produits.aggregate(Sum('valeur_stock'))['valeur_stock__sum'] or 0
    produits_alerte = produits.filter(stock_actuel__lte=F('seuil_alerte'))

    mouvements = MouvementStock.objects.select_related('produit', 'utilisateur').order_by('-created_at')
    if date_debut:
        mouvements = mouvements.filter(created_at__date__gte=date_debut)
    if date_fin:
        mouvements = mouvements.filter(created_at__date__lte=date_fin)
    mouvements = mouvements[:50]

    categories = (
        produits.values('categorie__nom')
        .annotate(total=Sum('valeur_stock'))
        .order_by('categorie__nom')
    )
    graph_categories = [c['categorie__nom'] or 'Sans categorie' for c in categories]
    graph_valeurs = [float(c['total'] or 0) for c in categories]

    nb_alertes = produits_alerte.count()
    nb_ok = max(produits.count() - nb_alertes, 0)
    
    context = {
        'produits': produits,
        'total_stock_value': total_stock_value,
        'produits_alerte': produits_alerte,
        'nb_produits': produits.count(),
        'nb_alertes': nb_alertes,
        'mouvements': mouvements,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'graph_categories': graph_categories,
        'graph_valeurs': graph_valeurs,
        'graph_alertes_labels': ['Produits OK', 'Produits en alerte'],
        'graph_alertes_values': [nb_ok, nb_alertes],
    }
    return render(request, 'rapports/stock.html', context)


@login_required
@gerant_required
def export_pdf_ventes(request):
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    date_debut = None if date_debut in (None, '', 'None') else date_debut
    date_fin = None if date_fin in (None, '', 'None') else date_fin

    ventes = Vente.objects.select_related('client').all().order_by('-date_vente')
    if date_debut:
        ventes = ventes.filter(date_vente__date__gte=date_debut)
    if date_fin:
        ventes = ventes.filter(date_vente__date__lte=date_fin)

    context = {
        'ventes': ventes,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'total_ventes': ventes.aggregate(Sum('montant_total'))['montant_total__sum'] or 0,
        'total_paye': ventes.aggregate(Sum('montant_paye'))['montant_paye__sum'] or 0,
        'total_restant': ventes.aggregate(Sum('solde_restant'))['solde_restant__sum'] or 0,
    }
    html_string = render_to_string('rapports/pdf_ventes.html', context)
    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_ventes.pdf"'
    return response


@login_required
@gerant_required
def export_pdf_stock(request):
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    date_debut = None if date_debut in (None, '', 'None') else date_debut
    date_fin = None if date_fin in (None, '', 'None') else date_fin

    produits = Produit.objects.select_related('categorie').annotate(
        valeur_stock=ExpressionWrapper(
            F('stock_actuel') * F('prix_achat'),
            output_field=DecimalField(max_digits=18, decimal_places=2)
        )
    )
    mouvements = MouvementStock.objects.select_related('produit', 'utilisateur').order_by('-created_at')
    if date_debut:
        mouvements = mouvements.filter(created_at__date__gte=date_debut)
    if date_fin:
        mouvements = mouvements.filter(created_at__date__lte=date_fin)
    mouvements = mouvements[:50]
    produits_alerte = produits.filter(stock_actuel__lte=F('seuil_alerte'))

    context = {
        'produits': produits,
        'mouvements': mouvements,
        'nb_produits': produits.count(),
        'nb_alertes': produits_alerte.count(),
        'total_stock_value': produits.aggregate(Sum('valeur_stock'))['valeur_stock__sum'] or 0,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    html_string = render_to_string('rapports/pdf_stock.html', context)
    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rapport_stock.pdf"'
    return response
