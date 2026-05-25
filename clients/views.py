from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from .models import Client
from ventes.models import Vente, LigneVente
from paiements.models import Paiement
from django import forms
from decimal import Decimal
import uuid
from core.utils import get_magasins_visibles, get_current_magasin


class ClientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quartier'].label = 'Adresse'

    class Meta:
        model = Client
        fields = ['nom', 'telephone', 'telephone2', 'quartier', 'notes', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Nom complet'}),
            'telephone': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': '+224...'}),
            'telephone2': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Optionnel'}),
            'quartier': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Adresse'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'actif': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded'}),
        }


class DetteInitialeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        magasin = kwargs.pop('magasin', None)
        super().__init__(*args, **kwargs)
        if magasin:
            self.fields['client'].queryset = Client.objects.filter(magasin=magasin)

    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
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
        label='Montant de la dette (GNF)'
    )
    date_approximative = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Date approximative (optionnel)'
    )
    motif = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Ex: Stock riz pris en janvier 2024...'
        }),
        label='Motif'
    )


class RemboursementSurplusForm(forms.Form):
    montant = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'step': '0.01',
        }),
        label='Montant à rembourser (GNF)'
    )
    mode_paiement = forms.ChoiceField(
        choices=[('ESPECES', 'Espèces'), ('CHEQUE', 'Chèque'), ('VIREMENT', 'Virement')],
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label='Mode de remboursement'
    )
    motif = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 2,
        }),
        label='Motif (optionnel)'
    )


class CreditInitialForm(forms.Form):
    def __init__(self, *args, **kwargs):
        magasin = kwargs.pop('magasin', None)
        super().__init__(*args, **kwargs)
        if magasin:
            self.fields['client'].queryset = Client.objects.filter(magasin=magasin)

    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
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
        label='Montant du crédit (GNF) - L\'entreprise doit ce montant'
    )
    motif = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Ex: Trop-payé en janvier 2024, avance non utilisée...'
        }),
        label='Motif'
    )


@login_required
def liste_clients(request):
    search = request.GET.get('search', '')
    magasin = get_current_magasin(request.user)
    clients = Client.objects.filter(magasin=magasin)
    
    if search:
        clients = clients.filter(Q(nom__icontains=search) | Q(telephone__icontains=search))
    clients = clients.order_by('nom')

    paginator = Paginator(clients, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_clients = clients.count()
    clients_actifs = clients.filter(actif=True).count()
    total_solde_solde = Vente.objects.filter(client__in=clients, statut='SOLDE').aggregate(
        total=Sum('montant_total')
    )['total'] or 0
    total_solde_du = clients.aggregate(total=Sum('solde_du'))['total'] or 0
    total_credit = clients.aggregate(total=Sum('credit_disponible'))['total'] or 0
    
    context = {
        'clients': page_obj.object_list,
        'page_obj': page_obj,
        'search': search,
        'total_clients': total_clients,
        'clients_actifs': clients_actifs,
        'total_solde_solde': total_solde_solde,
        'total_solde_du': total_solde_du,
        'total_credit': total_credit,
    }
    return render(request, 'clients/liste.html', context)


@login_required
def detail_client(request, pk):
    magasin = get_current_magasin(request.user)
    client = get_object_or_404(Client.objects.filter(magasin=magasin), pk=pk)
    magasins = get_magasins_visibles(request.user)
    ventes = Vente.objects.filter(client=client).filter(
        Q(magasin__in=magasins)
    ).order_by('-date_vente')[:30]
    ventes_a_encaisser = Vente.objects.filter(client=client, solde_restant__gt=0).filter(
        Q(magasin__in=magasins)
    ).order_by('-date_vente')
    paiements = Paiement.objects.filter(client=client).filter(
        Q(vente__magasin__in=magasins)
    ).order_by('-date_paiement')[:30]

    total_ventes = ventes.aggregate(total=Sum('montant_total'))['total'] or 0
    total_paye = ventes.aggregate(total=Sum('montant_paye'))['total'] or 0
    total_surplus = paiements.aggregate(total=Sum('montant_surplus'))['total'] or 0
    
    total_solde_restant = sum(v.solde_restant for v in Vente.objects.filter(client=client).filter(
        Q(magasin__in=magasins)
    ))
    
    context = {
        'client': client,
        'ventes': ventes,
        'ventes_a_encaisser': ventes_a_encaisser,
        'paiements': paiements,
        'total_ventes': total_ventes,
        'total_paye': total_paye,
        'total_surplus': total_surplus,
        'total_solde_restant': total_solde_restant,
    }
    return render(request, 'clients/detail.html', context)


@login_required
def creer_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.magasin = get_current_magasin(request.user)
            client.save()
            if request.headers.get('HX-Request'):
                messages.success(request, 'Client créé avec succès!')
                return render(request, 'partials/modal_success.html', {'redirect_url': 'javascript:location.reload()'})
            else:
                messages.success(request, 'Client créé avec succès!')
                return redirect('clients:liste')
    else:
        form = ClientForm()
    
    context = {'form': form, 'title': 'Créer un client'}
    
    if request.headers.get('HX-Request'):
        return render(request, 'partials/modal_form.html', context)
    
    return render(request, 'clients/form.html', context)


@login_required
def modifier_client(request, pk):
    magasin = get_current_magasin(request.user)
    client = get_object_or_404(Client.objects.filter(magasin=magasin), pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Client modifié avec succès!')
            return redirect('clients:detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    
    context = {'form': form, 'client': client, 'title': 'Modifier le client'}
    return render(request, 'clients/form.html', context)


@login_required
def supprimer_client(request, pk):
    magasin = get_current_magasin(request.user)
    client = get_object_or_404(Client.objects.filter(magasin=magasin), pk=pk)
    if request.method == 'POST':
        nom = client.nom
        client.delete()
        messages.success(request, f'Client "{nom}" supprimé.')
    return redirect('clients:liste')


@login_required
def imprimer_clients_debiteurs(request):
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    from weasyprint import HTML
    
    magasin = get_current_magasin(request.user)
    magasins = get_magasins_visibles(request.user)
    clients_du_magasin = Client.objects.filter(magasin=magasin)
    clients_debiteurs = clients_du_magasin.filter(solde_du__gt=0).filter(
        Q(vente__magasin__in=magasins)
    ).distinct().order_by('nom')
    clients_entreprise_doit = clients_du_magasin.filter(
        credit_disponible__gt=F('solde_du')
    ).filter(
        Q(vente__magasin__in=magasins)
    ).distinct().order_by('nom')
    
    clients_debiteurs_data = []
    total_net_du = Decimal('0')
    for c in clients_debiteurs:
        net = c.solde_du - c.credit_disponible
        clients_debiteurs_data.append((c, net))
        total_net_du += net
    
    clients_entreprise_doit_data = []
    for c in clients_entreprise_doit:
        net = c.credit_disponible - c.solde_du
        clients_entreprise_doit_data.append((c, net))
    
    context = {
        'clients_debiteurs': clients_debiteurs_data,
        'clients_entreprise_doit': clients_entreprise_doit_data,
        'total_clients_debiteurs': len(clients_debiteurs_data),
        'total_clients_credit': len(clients_entreprise_doit_data),
        'total_net_du': total_net_du,
    }
    
    html_string = render_to_string('clients/pdf_debiteurs.html', context, request=request)
    pdf = HTML(string=html_string).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="clients_debiteurs.pdf"'
    return response


@login_required
def dette_initiale(request):
    magasin = get_current_magasin(request.user)
    if request.method == 'POST':
        form = DetteInitialeForm(request.POST, magasin=magasin)
        if form.is_valid():
            client = form.cleaned_data['client']
            montant = form.cleaned_data['montant']
            date_approx = form.cleaned_data.get('date_approximative')
            motif = form.cleaned_data.get('motif', '')
            
            notes = f"Dette initiale enregistrée"
            if date_approx:
                notes += f" (date approx: {date_approx.strftime('%d/%m/%Y')})"
            if motif:
                notes += f" - {motif}"
            
            numero = f"DETTE-INIT-{uuid.uuid4().hex[:8].upper()}"
            
            # Appliquer le crédit disponible du client si existant
            credit_used = Decimal('0')
            if client.credit_disponible > 0:
                credit_used = min(client.credit_disponible, montant)
                client.credit_disponible -= credit_used
            
            solde_restant = montant - credit_used
            statut = 'SOLDE' if solde_restant == 0 else 'EN_ATTENTE'
            
            vente = Vente.objects.create(
                numero=numero,
                client=client,
                montant_total=montant,
                montant_paye=credit_used,
                solde_restant=solde_restant,
                statut=statut,
                notes=notes,
                utilisateur=request.user,
                magasin=get_current_magasin(request.user),
            )
            
            if credit_used > 0:
                from paiements.models import Paiement
                Paiement.objects.create(
                    vente=vente,
                    client=client,
                    montant=credit_used,
                    montant_surplus=Decimal('0'),
                    mode_paiement='CREDIT',
                    notes='Crédit disponible appliqué sur dette initiale',
                    utilisateur=request.user,
                )
            
            client.solde_du += solde_restant
            client.save(update_fields=['solde_du', 'credit_disponible'])
            
            messages.success(request, f'Dette initiale de {montant:,.0f} GNF enregistrée pour {client.nom}.')
            return redirect('clients:detail', pk=client.pk)
    else:
        form = DetteInitialeForm(magasin=magasin)
    
    context = {'form': form, 'title': 'Enregistrer une dette initiale'}
    return render(request, 'clients/dette_initiale.html', context)


@login_required
def remboursement_surplus(request, pk):
    magasin = get_current_magasin(request.user)
    client = get_object_or_404(Client.objects.filter(magasin=magasin), pk=pk)
    
    if client.credit_disponible <= 0:
        messages.error(request, 'Ce client n\'a pas de crédit disponible à rembourser.')
        return redirect('clients:detail', pk=client.pk)
    
    if request.method == 'POST':
        form = RemboursementSurplusForm(request.POST)
        if form.is_valid():
            montant = form.cleaned_data['montant']
            mode_paiement = form.cleaned_data['mode_paiement']
            motif = form.cleaned_data.get('motif', '')
            
            if montant > client.credit_disponible:
                messages.error(request, f'Le montant ne peut pas dépasser le crédit disponible ({client.credit_disponible:,.0f} GNF).')
            else:
                Vente.objects.create(
                    numero=f"REMBOURS-{uuid.uuid4().hex[:8].upper()}",
                    client=client,
                    montant_total=montant,
                    montant_paye=montant,
                    solde_restant=Decimal('0'),
                    statut='SOLDE',
                    notes=f"Remboursement surplus - Mode: {mode_paiement}" + (f" - {motif}" if motif else ""),
                    utilisateur=request.user,
                )
                
                client.credit_disponible -= montant
                if client.solde_du == 0:
                    client.credit_disponible = max(Decimal('0'), client.credit_disponible)
                client.save(update_fields=['credit_disponible'])
                
                messages.success(request, f'Remboursement de {montant:,.0f} GNF enregistré pour {client.nom}.')
                return redirect('clients:detail', pk=client.pk)
    else:
        form = RemboursementSurplusForm(initial={'montant': client.credit_disponible})
    
    context = {
        'form': form,
        'client': client,
        'title': 'Rembourser le surplus',
    }
    return render(request, 'clients/remboursement_surplus.html', context)


@login_required
def credit_disponible_initial(request):
    magasin = get_current_magasin(request.user)
    if request.method == 'POST':
        form = CreditInitialForm(request.POST, magasin=magasin)
        if form.is_valid():
            client = form.cleaned_data['client']
            montant = form.cleaned_data['montant']
            motif = form.cleaned_data.get('motif', '')
            
            notes = f"Crédit disponible initial enregistré"
            if motif:
                notes += f" - {motif}"
            
            client.credit_disponible += montant
            client.save(update_fields=['credit_disponible'])
            
            messages.success(request, f'Crédit disponible de {montant:,.0f} GNF enregistré pour {client.nom}.')
            return redirect('clients:detail', pk=client.pk)
    else:
        form = CreditInitialForm(magasin=magasin)
    
    context = {'form': form, 'title': 'Enregistrer un crédit disponible initial'}
    return render(request, 'clients/credit_initial.html', context)
