from django.db import models
from django.utils.translation import gettext_lazy as _


class Rapport(models.Model):
    """Rapports générés"""
    TYPE_CHOICES = [
        ('VENTES', _('Ventes')),
        ('STOCK', _('Stock')),
        ('CLIENTS', _('Clients')),
        ('BENEFICES', _('Bénéfices')),
        ('FOURNISSEURS', _('Fournisseurs')),
        ('DETTES', _('Dettes')),
    ]
    
    type_rapport = models.CharField(max_length=30, choices=TYPE_CHOICES, verbose_name=_("Type"))
    date_generation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de génération"))
    donnees = models.JSONField(verbose_name=_("Données"))

    class Meta:
        verbose_name = _("Rapport")
        verbose_name_plural = _("Rapports")
        ordering = ['-date_generation']

    def __str__(self):
        return f"{self.get_type_rapport_display()} - {self.date_generation}"
