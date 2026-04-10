from django.contrib import admin
from .models import Rapport


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ['type_rapport', 'date_generation']
    list_filter = ['type_rapport', 'date_generation']
    readonly_fields = ['date_generation', 'donnees']
