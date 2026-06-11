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
from core.utils import get_magasins_visibles, get_current_magasin, get_categories_autorisees, get_or_create_consommateur


class VenteForm(forms.Form):
    def __init__(self, *args, **kwargs):
        magasin = kwargs.pop('magasin', None)
        super().__init__(*args, **kwargs)
        if magasin:
            self.fields['client'].queryset = Client.objects.filter(magasin=magasin)

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


class EncaissementClientForm(forms.Form):
    def __init__(self, *args, **kwargs):
        magasin = kwargs.pop('magasin', None)
        super().__init__(*args, **kwargs)
        if magasin:
            self.fields['client'].queryset = Client.objects.filter(actif=True, magasin=magasin)

    client = forms.ModelChoiceField(
        queryset=Client.objects.filter(actif=True),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Client'
    )
    montant = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'step': '0.01',
        }),
        label='Montant à encaisser (GNF)'
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
        }),
        label='Référence (optionnel)'
    )


class ModifierPaiementForm(forms.Form):
    montant = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'step': '0.01',
        }),
        label='Nouveau montant (GNF)'
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
        }),
        label='Référence (optionnel)'
    )


@login_required
def nouvelle_vente(request):
    magasins = get_magasins_visibles(request.user)
    magasin = get_current_magasin(request.user)
    cat_ids = get_categories_autorisees(request.user)
    if request.method == 'POST':
        form = VenteForm(request.POST, magasin=magasin)
        if form.is_valid():
            with transaction.atomic():
                # Si pas de client sélectionné, utiliser le client "Consommateur"
                client = form.cleaned_data.get('client')
                if not client:
                    client = get_or_create_consommateur(magasin)
                # Créer la vente
                vente = Vente.objects.create(
                    numero=f"VTE-{uuid.uuid4().hex[:8].upper()}",
                    client=client,
                    montant_total=0,
                    utilisateur=request.user,
                    magasin=get_current_magasin(request.user),
                )
                
                # Ajouter les lignes de vente
                produits_ids = request.POST.getlist('produit_id')
                quantites = request.POST.getlist('quantite')
                prix_unitaires = request.POST.getlist('prix_unitaire')
                
                montant_total = Decimal('0')
                for produit_id, quantite, prix_personnalise in zip(produits_ids, quantites, prix_unitaires):
                    if not produit_id or not quantite:
                        continue
                    
                    produit = Produit.objects.filter(pk=produit_id).filter(
                        Q(magasin__in=magasins)
                    ).first()
                    if not produit:
                        continue
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
                        utilisateur=request.user,
                        magasin=vente.magasin,
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
                
                # Appliquer le credit_disponible du client automatiquement
                credit_used = Decimal('0')
                client = vente.client
                if client and client.credit_disponible > 0 and vente.solde_restant > 0:
                    credit_used = min(client.credit_disponible, vente.solde_restant)
                    client.credit_disponible -= credit_used
                    vente.montant_paye += credit_used
                    vente.solde_restant = max(Decimal('0'), vente.solde_restant - credit_used)
                
                if vente.montant_paye >= montant_total:
                    vente.statut = 'SOLDE'
                elif vente.montant_paye > 0:
                    vente.statut = 'PARTIEL'
                else:
                    vente.statut = 'EN_ATTENTE'
                
                vente.save()
                
                # Paiement pour la portion en espèce/chèque/virement
                if montant_paye_saisi > 0 and client:
                    Paiement.objects.create(
                        vente=vente,
                        client=client,
                        montant=montant_paye_saisi,
                        montant_surplus=surplus,
                        mode_paiement=form.cleaned_data['mode_paiement'],
                        utilisateur=request.user
                    )
                
                # Paiement pour la portion couverte par le crédit disponible
                if credit_used > 0 and client:
                    Paiement.objects.create(
                        vente=vente,
                        client=client,
                        montant=credit_used,
                        montant_surplus=Decimal('0'),
                        mode_paiement='CREDIT',
                        notes='Crédit disponible appliqué automatiquement',
                        utilisateur=request.user,
                    )
                
                # Mettre à jour le solde du client
                if client:
                    client.solde_du += vente.solde_restant
                    client.save(update_fields=['solde_du', 'credit_disponible'])
                
                if surplus > 0 and client:
                    total_solde_restant = sum(
                        v.solde_restant for v in Vente.objects.filter(client=client).filter(
                            Q(magasin__in=magasins)
                        )
                    )
                    if total_solde_restant == 0:
                        client.credit_disponible += surplus
                        client.save(update_fields=['credit_disponible'])
                        messages.success(
                            request,
                            f'Vente creee avec succes. Surplus de {surplus} GNF: l\'entreprise vous doit ce montant.'
                        )
                    else:
                        messages.success(request, 'Vente creee avec succes.')
                else:
                    messages.success(request, 'Vente creee avec succes.')
                return redirect('ventes:detail', pk=vente.pk)
    else:
        form = VenteForm(magasin=magasin)
    
    produits = Produit.objects.filter(actif=True).filter(
        Q(magasin__in=magasins)
    )
    if cat_ids is not None:
        produits = produits.filter(categorie_id__in=cat_ids)
    produits = produits.select_related('categorie').order_by('categorie__nom', 'nom')
    context = {
        'form': form,
        'produits': produits,
    }
    return render(request, 'ventes/nouvelle.html', context)


@login_required
def detail_vente(request, pk):
    magasins = get_magasins_visibles(request.user)
    vente = get_object_or_404(
        Vente.objects.select_related('client', 'utilisateur').filter(
            Q(magasin__in=magasins)
        ),
        pk=pk,
    )
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
    magasins = get_magasins_visibles(request.user)
    vente = get_object_or_404(
        Vente.objects.select_related('client').filter(
            Q(magasin__in=magasins)
        ),
        pk=pk,
    )

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
                    montant_surplus=Decimal('0'),
                    mode_paiement=form.cleaned_data['mode_paiement'],
                    reference=form.cleaned_data.get('reference', ''),
                    notes=form.cleaned_data.get('notes', ''),
                    utilisateur=request.user
                )

                vente.montant_paye = min(vente.montant_total, vente.montant_paye + montant_applique)
                vente.solde_restant = max(Decimal('0'), vente.montant_total - vente.montant_paye)
                vente.statut = 'SOLDE' if vente.solde_restant == 0 else 'PARTIEL'
                vente.save(update_fields=['montant_paye', 'solde_restant', 'statut'])

                total_solde_restant = sum(v.solde_restant for v in Vente.objects.filter(client=vente.client))
                vente.client.solde_du = total_solde_restant
                vente.client.save(update_fields=['solde_du'])

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

    magasins = get_magasins_visibles(request.user)
    vente = get_object_or_404(
        Vente.objects.select_related('client').filter(
            Q(magasin__in=magasins)
        ),
        pk=pk,
    )

    with transaction.atomic():
        for ligne in vente.lignes.select_related('produit'):
            produit = ligne.produit
            produit.stock_actuel += ligne.quantite
            produit.save(update_fields=['stock_actuel'])

        if vente.client:
            montant_paye = vente.montant_total - vente.solde_restant
            vente.client.solde_du = max(Decimal('0'), vente.client.solde_du - vente.solde_restant)
            vente.client.credit_disponible += montant_paye
            vente.client.save(update_fields=['solde_du', 'credit_disponible'])

        numero_vente = vente.numero
        vente.delete()

    messages.success(request, f'Vente {numero_vente} supprimee avec succes.')
    return redirect('ventes:liste')


@login_required
def encaisser_client(request):
    magasins = get_magasins_visibles(request.user)
    magasin = get_current_magasin(request.user)
    if request.method == 'POST':
        form = EncaissementClientForm(request.POST, magasin=magasin)
        if form.is_valid():
            client = form.cleaned_data['client']
            montant = form.cleaned_data['montant']
            mode_paiement = form.cleaned_data['mode_paiement']
            reference = form.cleaned_data.get('reference', '')
            
            total_solde_restant = sum(
                v.solde_restant for v in Vente.objects.filter(client=client).filter(
                    Q(magasin__in=magasins)
                )
            )
            
            if total_solde_restant <= 0:
                messages.error(request, f'{client.nom} n\'a pas de dette en cours.')
                return redirect('ventes:encaisser_client')
            
            if montant > total_solde_restant:
                surplus = montant - total_solde_restant
            else:
                surplus = Decimal('0')
            
            restant_a_distribuer = montant
            
            with transaction.atomic():
                ventes_impayees = Vente.objects.filter(
                    client=client,
                    solde_restant__gt=0,
                ).filter(
                    Q(magasin__in=magasins)
                ).order_by('date_vente')
                
                if not ventes_impayees.exists():
                    messages.error(request, f'Aucune vente impayée pour {client.nom}.')
                    return redirect('ventes:encaisser_client')
                
                paiement_principal = None
                for vente in ventes_impayees:
                    if restant_a_distribuer <= 0:
                        break
                    
                    montant_vente = min(restant_a_distribuer, vente.solde_restant)
                    
                    paiement = Paiement.objects.create(
                        vente=vente,
                        client=client,
                        montant=montant_vente,
                        montant_surplus=Decimal('0'),
                        mode_paiement=mode_paiement,
                        reference=reference,
                        utilisateur=request.user,
                    )
                    if paiement_principal is None:
                        paiement_principal = paiement
                    
                    vente.montant_paye = min(vente.montant_total, vente.montant_paye + montant_vente)
                    vente.solde_restant = max(Decimal('0'), vente.montant_total - vente.montant_paye)
                    vente.statut = 'SOLDE' if vente.solde_restant == 0 else 'PARTIEL'
                    vente.save(update_fields=['montant_paye', 'solde_restant', 'statut'])
                    
                    restant_a_distribuer -= montant_vente
                
                if surplus > 0 and paiement_principal:
                    paiement_principal.montant_surplus = surplus
                    paiement_principal.save(update_fields=['montant_surplus'])
                
                nouveau_solde_restant = sum(
                    v.solde_restant for v in Vente.objects.filter(client=client).filter(
                        Q(magasin__in=magasins)
                    )
                )
                client.solde_du = nouveau_solde_restant
                
                if surplus > 0 and nouveau_solde_restant == 0:
                    client.credit_disponible += surplus
                    client.save(update_fields=['solde_du', 'credit_disponible'])
                else:
                    client.save(update_fields=['solde_du'])
            
            if surplus > 0:
                messages.success(request, f'Encaissement de {montant:,.0f} GNF pour {client.nom}. Surplus de {surplus:,.0f} GNF ajouté au crédit disponible.')
            else:
                messages.success(request, f'Encaissement de {montant:,.0f} GNF pour {client.nom}.')
            
            return redirect('clients:detail', pk=client.pk)
    else:
        form = EncaissementClientForm(magasin=magasin)
    
    context = {
        'form': form,
        'title': 'Encaissement client',
    }
    return render(request, 'ventes/encaisser_client.html', context)


@login_required
def modifier_paiement(request, pk):
    magasins = get_magasins_visibles(request.user)
    paiement = get_object_or_404(
        Paiement.objects.select_related('vente').filter(
            Q(vente__magasin__in=magasins)
        ),
        pk=pk,
    )
    
    if request.method == 'POST':
        form = ModifierPaiementForm(request.POST)
        if form.is_valid():
            ancien_montant = paiement.montant
            ancien_surplus = paiement.surplus_effectif
            nouveau_montant = form.cleaned_data['montant']
            
            vente = paiement.vente
            client = paiement.client
            
            diff = nouveau_montant - ancien_montant
            
            with transaction.atomic():
                # Supprimer l'ancien surplus du crédit disponible
                if ancien_surplus > 0:
                    client.credit_disponible = max(Decimal('0'), client.credit_disponible - ancien_surplus)
                
                paiement.montant = nouveau_montant
                paiement.mode_paiement = form.cleaned_data['mode_paiement']
                paiement.reference = form.cleaned_data.get('reference', '')
                paiement.montant_surplus = Decimal('0')
                paiement.save()
                
                if diff > 0:
                    vente.montant_paye += diff
                    vente.solde_restant = max(Decimal('0'), vente.montant_total - vente.montant_paye)
                    vente.statut = 'SOLDE' if vente.solde_restant == 0 else 'PARTIEL'
                    vente.save(update_fields=['montant_paye', 'solde_restant', 'statut'])
                else:
                    vente.montant_paye = max(Decimal('0'), vente.montant_paye + diff)
                    vente.solde_restant += abs(diff)
                    vente.statut = 'PARTIEL'
                    vente.save(update_fields=['montant_paye', 'solde_restant', 'statut'])
                
                total_solde_restant = sum(
                    v.solde_restant for v in Vente.objects.filter(client=client).filter(
                        Q(magasin__in=magasins)
                    )
                )
                client.solde_du = total_solde_restant
                
                # Calculer le nouveau surplus si toutes les dettes sont soldées
                if total_solde_restant == 0:
                    total_paid = Paiement.objects.filter(client=client).filter(
                        Q(vente__magasin__in=magasins)
                    ).aggregate(t=Sum('montant'))['t'] or Decimal('0')
                    total_billed = Vente.objects.filter(client=client).filter(
                        Q(magasin__in=magasins)
                    ).aggregate(t=Sum('montant_total'))['t'] or Decimal('0')
                    nouveau_surplus = max(Decimal('0'), total_paid - total_billed)
                    if nouveau_surplus > 0:
                        client.credit_disponible += nouveau_surplus
                        paiement.montant_surplus = nouveau_surplus
                        paiement.save(update_fields=['montant_surplus'])
                
                client.save(update_fields=['solde_du', 'credit_disponible'])
            
            messages.success(request, f'Paiement modifié de {ancien_montant:,.0f} GNF vers {nouveau_montant:,.0f} GNF.')
            return redirect('clients:detail', pk=client.pk)
    else:
        form = ModifierPaiementForm(initial={
            'montant': paiement.montant,
            'mode_paiement': paiement.mode_paiement,
            'reference': paiement.reference,
        })
    
    context = {
        'form': form,
        'paiement': paiement,
        'title': 'Modifier le paiement',
    }
    return render(request, 'paiements/modifier_paiement.html', context)


@login_required
def supprimer_paiement(request, pk):
    magasins = get_magasins_visibles(request.user)
    paiement = get_object_or_404(
        Paiement.objects.select_related('vente').filter(
            Q(vente__magasin__in=magasins)
        ),
        pk=pk,
    )
    client_pk = paiement.client.pk
    vente = paiement.vente
    surplus_paiement = paiement.surplus_effectif
    
    with transaction.atomic():
        vente.montant_paye = max(Decimal('0'), vente.montant_paye - paiement.montant)
        vente.solde_restant = vente.montant_total - vente.montant_paye
        vente.statut = 'EN_ATTENTE' if vente.solde_restant == vente.montant_total else ('PARTIEL' if vente.solde_restant > 0 else 'SOLDE')
        vente.save(update_fields=['montant_paye', 'solde_restant', 'statut'])
        
        client = paiement.client
        if surplus_paiement > 0:
            client.credit_disponible = max(Decimal('0'), client.credit_disponible - surplus_paiement)
        
        total_solde_restant = sum(
            v.solde_restant for v in Vente.objects.filter(client=client).filter(
                Q(magasin__in=magasins)
            )
        )
        client.solde_du = total_solde_restant
        client.save(update_fields=['solde_du', 'credit_disponible'])
        
        paiement.delete()
    
    messages.success(request, f'Paiement supprime et solde restaure.')
    return redirect('clients:detail', pk=client_pk)


@login_required
def liste_ventes(request):
    search = request.GET.get('search', '')
    magasins = get_magasins_visibles(request.user)
    ventes = Vente.objects.select_related('client').filter(
        Q(magasin__in=magasins)
    ).order_by('-date_vente')
    
    if search:
        ventes = ventes.filter(Q(numero__icontains=search) | Q(client__nom__icontains=search))

    paginator = Paginator(ventes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_ventes = Vente.objects.filter(
        Q(magasin__in=magasins)
    ).count()
    total_montant = Vente.objects.filter(
        Q(magasin__in=magasins)
    ).aggregate(total=Sum('montant_total'))['total'] or 0
    total_restant = Vente.objects.filter(
        Q(magasin__in=magasins)
    ).aggregate(total=Sum('solde_restant'))['total'] or 0
    
    context = {
        'ventes': page_obj.object_list,
        'page_obj': page_obj,
        'search': search,
        'total_ventes': total_ventes,
        'total_montant': total_montant,
        'total_restant': total_restant,
    }
    return render(request, 'ventes/liste.html', context)
