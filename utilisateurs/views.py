from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import ProfilUtilisateur


class UtilisateurCreationForm(forms.Form):
	username = forms.CharField(
		max_length=150,
		label="Nom d'utilisateur",
		widget=forms.TextInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'placeholder': 'ex: admin_madina',
		}),
	)
	first_name = forms.CharField(
		max_length=150,
		required=False,
		label='Prenom',
		widget=forms.TextInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'placeholder': 'Prenom',
		}),
	)
	last_name = forms.CharField(
		max_length=150,
		required=False,
		label='Nom',
		widget=forms.TextInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'placeholder': 'Nom',
		}),
	)
	email = forms.EmailField(
		required=False,
		label='Email',
		widget=forms.EmailInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'placeholder': 'email@exemple.com',
		}),
	)
	telephone = forms.CharField(
		max_length=20,
		required=False,
		label='Telephone',
		widget=forms.TextInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'placeholder': '+224...',
		}),
	)
	role = forms.ChoiceField(
		choices=ProfilUtilisateur.ROLE_CHOICES,
		label='Role',
		widget=forms.Select(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500',
		}),
	)
	est_admin = forms.BooleanField(
		required=False,
		label='Donner les droits administrateur (staff)',
		widget=forms.CheckboxInput(attrs={
			'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500',
		}),
	)
	password1 = forms.CharField(
		label='Mot de passe',
		widget=forms.PasswordInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
		}),
	)
	password2 = forms.CharField(
		label='Confirmer le mot de passe',
		widget=forms.PasswordInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
		}),
	)

	def clean_username(self):
		username = self.cleaned_data['username'].strip()
		if User.objects.filter(username__iexact=username).exists():
			raise forms.ValidationError("Ce nom d'utilisateur existe deja.")
		return username

	def clean(self):
		cleaned_data = super().clean()
		if cleaned_data.get('password1') and cleaned_data.get('password2'):
			if cleaned_data['password1'] != cleaned_data['password2']:
				self.add_error('password2', 'Les mots de passe ne correspondent pas.')
		return cleaned_data


class UtilisateurEditionForm(forms.Form):
	first_name = forms.CharField(
		max_length=150,
		required=False,
		label='Prenom',
		widget=forms.TextInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'placeholder': 'Prenom',
		}),
	)
	last_name = forms.CharField(
		max_length=150,
		required=False,
		label='Nom',
		widget=forms.TextInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'placeholder': 'Nom',
		}),
	)
	email = forms.EmailField(
		required=False,
		label='Email',
		widget=forms.EmailInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'placeholder': 'email@exemple.com',
		}),
	)
	telephone = forms.CharField(
		max_length=20,
		required=False,
		label='Telephone',
		widget=forms.TextInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
			'placeholder': '+224...',
		}),
	)
	role = forms.ChoiceField(
		choices=ProfilUtilisateur.ROLE_CHOICES,
		label='Role',
		widget=forms.Select(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500',
		}),
	)
	est_admin = forms.BooleanField(
		required=False,
		label='Donner les droits administrateur (staff)',
		widget=forms.CheckboxInput(attrs={
			'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500',
		}),
	)
	reset_password = forms.CharField(
		required=False,
		label='Nouveau mot de passe (optionnel)',
		widget=forms.PasswordInput(attrs={
			'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
		}),
	)


def _superadmin_required(request):
	if request.user.is_superuser:
		return True
	messages.error(request, 'Acces reserve a l\'administrateur.')
	return False


@login_required
def liste_utilisateurs(request):
	if not _superadmin_required(request):
		return redirect('core:dashboard')

	search = request.GET.get('search', '').strip()
	statut = request.GET.get('statut', 'all')
	type_compte = request.GET.get('type_compte', 'all')
	role = request.GET.get('role', 'all')

	utilisateurs = User.objects.all()

	if search:
		utilisateurs = utilisateurs.filter(
			Q(username__icontains=search)
			| Q(first_name__icontains=search)
			| Q(last_name__icontains=search)
			| Q(email__icontains=search)
		)

	if statut == 'actif':
		utilisateurs = utilisateurs.filter(is_active=True)
	elif statut == 'inactif':
		utilisateurs = utilisateurs.filter(is_active=False)

	if type_compte == 'superadmin':
		utilisateurs = utilisateurs.filter(is_superuser=True)
	elif type_compte == 'admin':
		utilisateurs = utilisateurs.filter(is_superuser=False, is_staff=True)
	elif type_compte == 'user':
		utilisateurs = utilisateurs.filter(is_superuser=False, is_staff=False)

	if role in {'GERANT', 'EMPLOYE'}:
		utilisateurs = utilisateurs.filter(profilutilisateur__role=role)

	utilisateurs = utilisateurs.order_by('username')
	paginator = Paginator(utilisateurs, 15)
	page_obj = paginator.get_page(request.GET.get('page'))

	profils = {
		profil.user_id: profil
		for profil in ProfilUtilisateur.objects.select_related('user').all()
	}
	lignes = [
		{
			'user': user,
			'profil': profils.get(user.id),
		}
		for user in page_obj.object_list
	]
	context = {
		'lignes': lignes,
		'page_obj': page_obj,
		'search': search,
		'statut': statut,
		'type_compte': type_compte,
		'role': role,
	}
	return render(request, 'utilisateurs/liste.html', context)


@login_required
def creer_utilisateur(request):
	if not _superadmin_required(request):
		return redirect('core:dashboard')

	if request.method == 'POST':
		form = UtilisateurCreationForm(request.POST)
		if form.is_valid():
			with transaction.atomic():
				user = User.objects.create_user(
					username=form.cleaned_data['username'],
					password=form.cleaned_data['password1'],
					first_name=form.cleaned_data['first_name'],
					last_name=form.cleaned_data['last_name'],
					email=form.cleaned_data['email'],
					is_staff=form.cleaned_data['est_admin'],
					is_superuser=False,
					is_active=True,
				)
				ProfilUtilisateur.objects.create(
					user=user,
					role=form.cleaned_data['role'],
					telephone=form.cleaned_data['telephone'],
					actif=True,
				)

			messages.success(request, f"Utilisateur {user.username} cree avec succes.")
			return redirect('utilisateurs:liste')
	else:
		form = UtilisateurCreationForm(initial={'role': 'EMPLOYE'})

	return render(request, 'utilisateurs/form.html', {'form': form})


@login_required
def modifier_utilisateur(request, pk):
	if not _superadmin_required(request):
		return redirect('core:dashboard')

	user_obj = get_object_or_404(User, pk=pk)
	profil, _ = ProfilUtilisateur.objects.get_or_create(
		user=user_obj,
		defaults={'role': 'EMPLOYE', 'telephone': '', 'actif': user_obj.is_active},
	)

	if request.method == 'POST':
		form = UtilisateurEditionForm(request.POST)
		if form.is_valid():
			user_obj.first_name = form.cleaned_data['first_name']
			user_obj.last_name = form.cleaned_data['last_name']
			user_obj.email = form.cleaned_data['email']
			user_obj.is_staff = form.cleaned_data['est_admin']

			new_password = form.cleaned_data.get('reset_password')
			if new_password:
				user_obj.set_password(new_password)

			user_obj.save()

			profil.role = form.cleaned_data['role']
			profil.telephone = form.cleaned_data['telephone']
			profil.actif = user_obj.is_active
			profil.save()

			messages.success(request, f'Utilisateur {user_obj.username} modifie avec succes.')
			return redirect('utilisateurs:liste')
	else:
		form = UtilisateurEditionForm(initial={
			'first_name': user_obj.first_name,
			'last_name': user_obj.last_name,
			'email': user_obj.email,
			'telephone': profil.telephone,
			'role': profil.role,
			'est_admin': user_obj.is_staff,
		})

	context = {
		'form': form,
		'is_edit': True,
		'user_obj': user_obj,
	}
	return render(request, 'utilisateurs/form.html', context)


@login_required
def toggle_actif_utilisateur(request, pk):
	if not _superadmin_required(request):
		return redirect('core:dashboard')
	if request.method != 'POST':
		return redirect('utilisateurs:liste')

	user_obj = get_object_or_404(User, pk=pk)
	if user_obj.is_superuser:
		messages.error(request, 'L\'administrateur ne peut pas etre desactive.')
		return redirect('utilisateurs:liste')

	if user_obj == request.user:
		messages.error(request, 'Vous ne pouvez pas vous desactiver vous-meme.')
		return redirect('utilisateurs:liste')

	user_obj.is_active = not user_obj.is_active
	user_obj.save(update_fields=['is_active'])

	profil, _ = ProfilUtilisateur.objects.get_or_create(
		user=user_obj,
		defaults={'role': 'EMPLOYE', 'telephone': '', 'actif': user_obj.is_active},
	)
	profil.actif = user_obj.is_active
	profil.save(update_fields=['actif'])

	if user_obj.is_active:
		messages.success(request, f'Utilisateur {user_obj.username} active.')
	else:
		messages.success(request, f'Utilisateur {user_obj.username} desactive.')
	return redirect('utilisateurs:liste')


@login_required
def supprimer_utilisateur(request, pk):
	if not _superadmin_required(request):
		return redirect('core:dashboard')
	if request.method != 'POST':
		return redirect('utilisateurs:liste')

	user_obj = get_object_or_404(User, pk=pk)
	if user_obj.is_superuser:
		messages.error(request, 'L\'administrateur ne peut pas etre supprime.')
		return redirect('utilisateurs:liste')

	if user_obj == request.user:
		messages.error(request, 'Vous ne pouvez pas supprimer votre propre compte.')
		return redirect('utilisateurs:liste')

	username = user_obj.username
	user_obj.delete()
	messages.success(request, f'Utilisateur {username} supprime avec succes.')
	return redirect('utilisateurs:liste')
