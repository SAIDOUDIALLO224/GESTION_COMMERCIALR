from django.db import models
from django.utils.translation import gettext_lazy as _


class Client(models.Model):
    """Clients"""
    TYPE_CHOICES = [
        ('REVENDEUR', _('Revendeur')),
        ('PARTICULIER', _('Particulier')),
        ('RESTAURATEUR', _('Restaurateur')),
        ('AUTRE', _('Autre')),
    ]
    
    nom = models.CharField(max_length=150, verbose_name=_("Nom"))
    telephone = models.CharField(max_length=20, verbose_name=_("Téléphone"))
    telephone2 = models.CharField(max_length=20, blank=True, verbose_name=_("Téléphone secondaire"))
    quartier = models.CharField(max_length=100, blank=True, verbose_name=_("Quartier"))
    type_client = models.CharField(
        max_length=30, choices=TYPE_CHOICES, default='PARTICULIER',
        verbose_name=_("Type de client")
    )
    solde_du = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name=_("Solde dû")
    )
    credit_disponible = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name=_("Crédit disponible")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ['nom']

    def __str__(self):
        return self.nom
