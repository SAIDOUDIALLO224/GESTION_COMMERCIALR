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
from datetime import date, datetime, timedelta


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
    if not request.user.is_superuser:
        messages.error(request, "Accès réservé au superadmin.")
        return redirect('core:dashboard')
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

    # Dates par défaut pour la modale du relevé (date du jour - 1 mois → aujourd'hui)
    aujourd_hui = date.today()
    date_debut_defaut = (aujourd_hui.replace(day=1) - timedelta(days=1)).replace(day=1)

    context = {
        'comptes': comptes,
        'title': 'Comptes Ecobanque',
        'total_montants_sortis_global': total_montants_sortis_global,
        'total_montants_entrants_global': total_montants_entrants_global,
        'montant_exact_compte': montant_exact_compte,
        'date_debut_defaut': date_debut_defaut.isoformat(),
        'date_fin_defaut': aujourd_hui.isoformat(),
    }
    return render(request, 'paiements/comptes_ecobanque_liste.html', context)


@login_required
def comptes_ecobanque_form(request, pk=None):
    if not request.user.is_superuser:
        messages.error(request, "Accès réservé au superadmin.")
        return redirect('core:dashboard')
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
    if not request.user.is_superuser:
        messages.error(request, "Accès réservé au superadmin.")
        return redirect('core:dashboard')
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


@login_required
def releve_banque(request):
    """Génère le relevé de banque PDF entre deux dates.

    Chaque ligne = une opération CompteEcoBanqueClient (entrée ou sortie).
    Le solde de départ est recalculé à rebours depuis le solde_courant actuel
    stocké dans Configuration, en retirant les opérations survenues depuis
    date_debut. Le solde final affiché doit correspondre au solde bancaire actuel.
    """
    if not request.user.is_superuser:
        messages.error(request, "Accès réservé au superadmin.")
        return redirect('core:dashboard')

    aujourd_hui = date.today()
    date_debut_defaut = (aujourd_hui.replace(day=1) - timedelta(days=1)).replace(day=1)

    date_debut_str = request.GET.get('date_debut', '')
    date_fin_str = request.GET.get('date_fin', '')

    try:
        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date() if date_debut_str else date_debut_defaut
    except ValueError:
        date_debut = date_debut_defaut

    try:
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date() if date_fin_str else aujourd_hui
    except ValueError:
        date_fin = aujourd_hui

    solde_bancaire_actuel = get_solde_compte_bancaire()

    # Toutes les opérations (CompteEcoBanqueClient) depuis date_debut
    # pour recalculer le solde de départ à rebours
    from django.db.models import Sum as DSum, F as DF

    # Opérations après date_debut (pour le calcul du solde de départ)
    ops_depuis_debut = CompteEcoBanqueClient.objects.filter(
        date_creation__date__gte=date_debut
    )
    total_entrants_depuis = ops_depuis_debut.aggregate(
        total=DSum(DF('montant_verset') + DF('montant_initial'))
    )['total'] or Decimal('0')
    total_sortis_depuis = ops_depuis_debut.aggregate(
        total=DSum('montant_sorti')
    )['total'] or Decimal('0')

    # Solde de départ = solde actuel - entrants depuis debut + sortis depuis debut
    solde_depart = solde_bancaire_actuel - total_entrants_depuis + total_sortis_depuis

    # Opérations dans la période (date_debut → date_fin)
    ops_periode = CompteEcoBanqueClient.objects.filter(
        date_creation__date__gte=date_debut,
        date_creation__date__lte=date_fin,
    ).select_related('client', 'utilisateur').order_by('date_creation')

    # Construction des lignes du relevé avec solde courant
    lignes = []
    solde_courant = solde_depart
    for op in ops_periode:
        entrant = op.montant_verset + op.montant_initial
        sorti = op.montant_sorti
        solde_courant = solde_courant + entrant - sorti
        lignes.append({
            'date': op.date_operation or op.date_creation.date(),
            'client': op.client.nom,
            'motif': op.motif or '',
            'debit': sorti if sorti > 0 else Decimal('0'),
            'credit': entrant if entrant > 0 else Decimal('0'),
            'solde': solde_courant,
        })

    solde_final = solde_courant

    # Totaux de la période
    total_debit_periode = sum(l['debit'] for l in lignes)
    total_credit_periode = sum(l['credit'] for l in lignes)

    context = {
        'date_debut': date_debut,
        'date_fin': date_fin,
        'solde_depart': solde_depart,
        'lignes': lignes,
        'solde_final': solde_final,
        'total_debit_periode': total_debit_periode,
        'total_credit_periode': total_credit_periode,
    }

    html_string = render_to_string('paiements/pdf_releve_banque.html', context, request=request)
    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    nom_fichier = f"releve_banque_{date_debut}_{date_fin}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    return response
