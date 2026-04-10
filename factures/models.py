from django.db import models
from django.utils.translation import gettext_lazy as _
from ventes.models import Vente


class Facture(models.Model):
    """Factures"""
    vente = models.OneToOneField(Vente, on_delete=models.CASCADE, verbose_name=_("Vente"))
    numero_facture = models.CharField(max_length=30, unique=True, verbose_name=_("Numéro de facture"))
    date_emission = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'émission"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))

    class Meta:
        verbose_name = _("Facture")
        verbose_name_plural = _("Factures")
        ordering = ['-date_emission']

    def __str__(self):
        return self.numero_facture
