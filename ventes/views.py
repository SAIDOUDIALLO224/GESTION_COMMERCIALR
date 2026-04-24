from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from .models import Vente, LigneVente
from produits.models import Produit
from clients.models import Client
from paiements.models import Paiement
from stock.models import MouvementStock
from django import forms
from decimal import Decimal
import uuid
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML


class VenteForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Client (optionnel)'
    )
    mode_paiement = forms.ChoiceField(
        choices=Paiement.MODE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Mode de paiement'
    )
    montant_paye = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'step': '0.01',
            'min': '0'
        }),
        label='Montant payé'
    )


class EncaissementForm(forms.Form):
    montant = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'step': '0.01',
            'min': '0.01'
        }),
        label='Montant a encaisser'
    )
    mode_paiement = forms.ChoiceField(
        choices=Paiement.MODE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Mode de paiement'
    )
    reference = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Ex: Recu #125, virement BIC...'
        }),
        label='Reference'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Notes optionnelles'
        }),
        label='Notes'
    )


@login_required
def nouvelle_vente(request):
    if request.method == 'POST':
        form = VenteForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Créer la vente
                vente = Vente.objects.create(
                    numero=f"VTE-{uuid.uuid4().hex[:8].upper()}",
                    client=form.cleaned_data.get('client'),
                    montant_total=0,
                    utilisateur=request.user
                )
                
                # Ajouter les lignes de vente
                produits_ids = request.POST.getlist('produit_id')
                quantites = request.POST.getlist('quantite')
                prix_unitaires = request.POST.getlist('prix_unitaire')
                
                montant_total = Decimal('0')
                for produit_id, quantite, prix_personnalise in zip(produits_ids, quantites, prix_unitaires):
                    if not produit_id or not quantite:
                        continue
                    
                    produit = Produit.objects.get(pk=produit_id)
                    quantite = Decimal(quantite)
                    
                    # Vérifier le stock (on permet les stocks négatifs pour les ventes)
                    # Le stock peut devenir négatif si on vend plus que disponible
                    
                    # Utiliser le prix personnalisé si modifié par l'utilisateur, sinon le prix de vente gros
                    if prix_personnalise and Decimal(prix_personnalise) > 0:
                        prix_unitaire = Decimal(prix_personnalise)
                    else:
                        prix_unitaire = produit.prix_vente_gros
                    
                    # Si le prix est 0, erreur
                    if prix_unitaire == 0:
                        messages.error(request, f'Prix non défini pour {produit.nom}. Veuillez définir un prix de vente.')
                        vente.delete()
                        return redirect('ventes:nouvelle')
                    
                    sous_total = quantite * prix_unitaire
                    
                    LigneVente.objects.create(
                        vente=vente,
                        produit=produit,
                        quantite=quantite,
                        prix_unitaire=prix_unitaire,
                        sous_total=sous_total
                    )
                    
                    # Mettre à jour le stock
                    produit.stock_actuel -= quantite
                    produit.save()
                    
                    # Créer un mouvement de stock (SORTIE pour la vente)
                    MouvementStock.objects.create(
                        produit=produit,
                        type_mvt='SORTIE',
                        quantite=quantite,
                        motif=f'Vente {vente.numero}',
                        utilisateur=request.user
                    )
                    
                    montant_total += sous_total
                
                print(f"Montant total final: {montant_total}")
                
                # Mettre à jour la vente
                vente.montant_total = montant_total
                montant_paye_saisi = form.cleaned_data.get('montant_paye') or Decimal('0')
                montant_applique = min(montant_paye_saisi, montant_total)
                surplus = max(Decimal('0'), montant_paye_saisi - montant_total)

                vente.montant_paye = montant_applique
                vente.solde_restant = max(Decimal('0'), montant_total - montant_applique)
                
                print(f"Vente mise à jour: total={vente.montant_total}, payé={vente.montant_paye}, restant={vente.solde_restant}")
                
                if montant_applique >= montant_total:
                    vente.statut = 'SOLDE'
                elif montant_applique > 0:
                    vente.statut = 'PARTIEL'
                else:
                    vente.statut = 'EN_ATTENTE'
                
                vente.save()
                
                # Créer le paiement uniquement si la vente est rattachée a un client.
                if montant_paye_saisi > 0 and vente.client:
                    Paiement.objects.create(
                        vente=vente,
                        client=vente.client,
                        montant=montant_paye_saisi,
                        montant_surplus=surplus,
                        mode_paiement=form.cleaned_data['mode_paiement'],
                        utilisateur=request.user
                    )
                
                # Mettre à jour le solde du client
                if vente.client:
                    vente.client.solde_du += vente.solde_restant
                    if surplus > 0:
                        vente.client.credit_disponible += surplus
                    vente.client.save()
                
                if surplus > 0 and vente.client:
                    messages.success(
                        request,
                        f'Vente creee avec succes. Surplus de {surplus} GNF: l\'entreprise vous doit ce montant.'
                    )
                else:
                    messages.success(request, 'Vente créée avec succès!')
                return redirect('ventes:detail', pk=vente.pk)
    else:
        form = VenteForm()
    
    produits = Produit.objects.filter(actif=True).order_by('nom')
    context = {
        'form': form,
        'produits': produits,
    }
    return render(request, 'ventes/nouvelle.html', context)


@login_required
def detail_vente(request, pk):
    vente = get_object_or_404(Vente.objects.select_related('client', 'utilisateur'), pk=pk)
    lignes = vente.lignes.all()
    paiements = vente.paiements.all()
    
    context = {
        'vente': vente,
        'lignes': lignes,
        'paiements': paiements,
    }
    return render(request, 'ventes/detail.html', context)


@login_required
def encaisser_paiement(request, pk):
    vente = get_object_or_404(Vente.objects.select_related('client'), pk=pk)

    if not vente.client:
        messages.error(request, 'Impossible d\'encaisser: cette vente est anonyme (sans client).')
        return redirect('ventes:detail', pk=vente.pk)

    if vente.solde_restant <= 0:
        messages.info(request, 'Cette vente est deja soldee.')
        return redirect('ventes:detail', pk=vente.pk)

    if request.method == 'POST':
        form = EncaissementForm(request.POST)
        if form.is_valid():
            montant = form.cleaned_data['montant']

            with transaction.atomic():
                montant_applique = min(montant, vente.solde_restant)
                surplus = max(Decimal('0'), montant - montant_applique)

                Paiement.objects.create(
                    vente=vente,
                    client=vente.client,
                    montant=montant,
                    montant_surplus=surplus,
                    mode_paiement=form.cleaned_data['mode_paiement'],
                    reference=form.cleaned_data.get('reference', ''),
                    notes=form.cleaned_data.get('notes', ''),
                    utilisateur=request.user
                )

                vente.montant_paye = min(vente.montant_total, vente.montant_paye + montant_applique)
                vente.solde_restant = max(Decimal('0'), vente.montant_total - vente.montant_paye)
                vente.statut = 'SOLDE' if vente.solde_restant == 0 else 'PARTIEL'
                vente.save(update_fields=['montant_paye', 'solde_restant', 'statut'])

                vente.client.solde_du = max(Decimal('0'), vente.client.solde_du - montant_applique)
                if surplus > 0:
                    vente.client.credit_disponible += surplus
                    vente.client.save(update_fields=['solde_du', 'credit_disponible'])
                else:
                    vente.client.save(update_fields=['solde_du'])
                
                # Si le client a tout payé, réinitialiser le crédit disponible
                if vente.client.solde_du == 0:
                    vente.client.credit_disponible = Decimal('0')
                    vente.client.save(update_fields=['credit_disponible'])

            if surplus > 0:
                messages.success(
                    request,
                    f'Paiement enregistre: {montant} GNF. Surplus de {surplus} GNF: l\'entreprise vous doit ce montant.'
                )
            else:
                messages.success(request, f'Paiement enregistre: {montant} GNF pour la vente {vente.numero}.')
            return redirect('ventes:detail', pk=vente.pk)
    else:
        form = EncaissementForm(initial={'mode_paiement': 'ESPECES'})

    context = {
        'vente': vente,
        'form': form,
    }
    return render(request, 'ventes/paiement.html', context)


@login_required
def supprimer_vente(request, pk):
    if request.method != 'POST':
        messages.error(request, 'Methode non autorisee.')
        return redirect('ventes:liste')

    vente = get_object_or_404(Vente.objects.select_related('client'), pk=pk)

    with transaction.atomic():
        for ligne in vente.lignes.select_related('produit'):
            produit = ligne.produit
            produit.stock_actuel += ligne.quantite
            produit.save(update_fields=['stock_actuel'])

        if vente.client and vente.solde_restant > 0:
            vente.client.solde_du = max(Decimal('0'), vente.client.solde_du - vente.solde_restant)
            vente.client.save(update_fields=['solde_du'])

        numero_vente = vente.numero
        vente.delete()

    messages.success(request, f'Vente {numero_vente} supprimee avec succes.')
    return redirect('ventes:liste')


@login_required
def liste_ventes(request):
    search = request.GET.get('search', '')
    ventes = Vente.objects.select_related('client').all().order_by('-date_vente')
    
    if search:
        ventes = ventes.filter(Q(numero__icontains=search) | Q(client__nom__icontains=search))

    paginator = Paginator(ventes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_ventes = Vente.objects.count()
    total_montant = Vente.objects.aggregate(total=Sum('montant_total'))['total'] or 0
    total_restant = Vente.objects.aggregate(total=Sum('solde_restant'))['total'] or 0
    
    context = {
        'ventes': page_obj.object_list,
        'page_obj': page_obj,
        'search': search,
        'total_ventes': total_ventes,
        'total_montant': total_montant,
        'total_restant': total_restant,
    }
    return render(request, 'ventes/liste.html', context)
