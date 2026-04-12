from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django import forms
from .models import Fournisseur


class FournisseurForm(forms.ModelForm):
	class Meta:
		model = Fournisseur
		fields = ['nom', 'telephone', 'adresse', 'notes']
		widgets = {
			'nom': forms.TextInput(attrs={
				'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
				'placeholder': 'Nom du fournisseur'
			}),
			'telephone': forms.TextInput(attrs={
				'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
				'placeholder': '+224...'
			}),
			'adresse': forms.Textarea(attrs={
				'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
				'rows': 3,
				'placeholder': 'Adresse complete'
			}),
			'notes': forms.Textarea(attrs={
				'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
				'rows': 3,
				'placeholder': 'Notes optionnelles'
			}),
		}


@login_required
def liste_fournisseurs(request):
	search = request.GET.get('search', '')
	fournisseurs = Fournisseur.objects.all()

	if search:
		fournisseurs = fournisseurs.filter(
			Q(nom__icontains=search) |
			Q(telephone__icontains=search) |
			Q(adresse__icontains=search)
		)

	fournisseurs = fournisseurs.order_by('nom')
	paginator = Paginator(fournisseurs, 25)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)

	total_fournisseurs = Fournisseur.objects.count()
	total_solde_du = Fournisseur.objects.aggregate(total=Sum('solde_du'))['total'] or 0

	context = {
		'fournisseurs': page_obj.object_list,
		'page_obj': page_obj,
		'search': search,
		'total_fournisseurs': total_fournisseurs,
		'total_solde_du': total_solde_du,
	}
	return render(request, 'fournisseurs/liste.html', context)


@login_required
def detail_fournisseur(request, pk):
	fournisseur = get_object_or_404(Fournisseur, pk=pk)
	context = {'fournisseur': fournisseur}
	return render(request, 'fournisseurs/detail.html', context)


@login_required
def creer_fournisseur(request):
	if request.method == 'POST':
		form = FournisseurForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Fournisseur cree avec succes!')
			return redirect('fournisseurs:liste')
	else:
		form = FournisseurForm()

	context = {
		'form': form,
		'title': 'Ajouter un fournisseur'
	}
	return render(request, 'fournisseurs/form.html', context)


@login_required
def modifier_fournisseur(request, pk):
	fournisseur = get_object_or_404(Fournisseur, pk=pk)
	if request.method == 'POST':
		form = FournisseurForm(request.POST, instance=fournisseur)
		if form.is_valid():
			form.save()
			messages.success(request, 'Fournisseur modifie avec succes!')
			return redirect('fournisseurs:detail', pk=fournisseur.pk)
	else:
		form = FournisseurForm(instance=fournisseur)

	context = {
		'form': form,
		'fournisseur': fournisseur,
		'title': 'Modifier le fournisseur'
	}
	return render(request, 'fournisseurs/form.html', context)


@login_required
def supprimer_fournisseur(request, pk):
	if request.method != 'POST':
		messages.error(request, 'Methode non autorisee.')
		return redirect('fournisseurs:liste')

	fournisseur = get_object_or_404(Fournisseur, pk=pk)
	nom = fournisseur.nom
	fournisseur.delete()
	messages.success(request, f'Fournisseur « {nom} » supprime avec succes.')
	return redirect('fournisseurs:liste')
