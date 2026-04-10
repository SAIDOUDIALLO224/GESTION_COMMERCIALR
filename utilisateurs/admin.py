from django.contrib import admin
from .models import ProfilUtilisateur


@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'actif']
    list_filter = ['role', 'actif']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
