from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import Client
from ventes.models import Vente
from paiements.models import Paiement
from django import forms


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


@login_required
def liste_clients(request):
    search = request.GET.get('search', '')
    clients = Client.objects.all()
    
    if search:
        clients = clients.filter(Q(nom__icontains=search) | Q(telephone__icontains=search))

    paginator = Paginator(clients, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_clients = Client.objects.count()
    clients_actifs = Client.objects.filter(actif=True).count()
    total_solde_solde = Vente.objects.filter(client__isnull=False, statut='SOLDE').aggregate(
        total=Sum('montant_total')
    )['total'] or 0
    total_solde_du = Client.objects.aggregate(total=Sum('solde_du'))['total'] or 0
    total_credit = Client.objects.aggregate(total=Sum('credit_disponible'))['total'] or 0
    
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
    client = get_object_or_404(Client, pk=pk)
    ventes = Vente.objects.filter(client=client).order_by('-date_vente')[:30]
    ventes_a_encaisser = Vente.objects.filter(client=client, solde_restant__gt=0).order_by('-date_vente')
    paiements = Paiement.objects.filter(client=client).order_by('-date_paiement')[:30]

    total_ventes = ventes.aggregate(total=Sum('montant_total'))['total'] or 0
    total_paye = ventes.aggregate(total=Sum('montant_paye'))['total'] or 0
    total_surplus = paiements.aggregate(total=Sum('montant_surplus'))['total'] or 0
    
    context = {
        'client': client,
        'ventes': ventes,
        'ventes_a_encaisser': ventes_a_encaisser,
        'paiements': paiements,
        'total_ventes': total_ventes,
        'total_paye': total_paye,
        'total_surplus': total_surplus,
    }
    return render(request, 'clients/detail.html', context)


@login_required
def creer_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
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
    client = get_object_or_404(Client, pk=pk)
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
    client = get_object_or_404(Client, pk=pk)
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
    
    # Clients avec solde dû > 0
    clients_debiteurs = Client.objects.filter(solde_du__gt=0).order_by('nom')
    
    total_montant_du = clients_debiteurs.aggregate(total=Sum('solde_du'))['total'] or 0
    
    context = {
        'clients': clients_debiteurs,
        'total_clients': clients_debiteurs.count(),
        'total_montant_du': total_montant_du,
    }
    
    html_string = render_to_string('clients/pdf_debiteurs.html', context)
    pdf = HTML(string=html_string).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="clients_debiteurs.pdf"'
    return response
