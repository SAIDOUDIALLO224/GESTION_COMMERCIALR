from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from decimal import Decimal
from ventes.models import Vente
from clients.models import Client


class Paiement(models.Model):
    """Paiements"""
    MODE_CHOICES = [
        ('ESPECES', _('Espèces')),
        ('CHEQUE', _('Chèque')),
        ('VIREMENT', _('Virement')),
        ('CREDIT', _('Crédit')),
    ]
    
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='paiements', verbose_name=_("Vente"))
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name=_("Client"))
    montant = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name=_("Montant")
    )
    montant_surplus = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)],
        verbose_name=_("Surplus")
    )
    mode_paiement = models.CharField(
        max_length=30, choices=MODE_CHOICES, verbose_name=_("Mode de paiement")
    )
    reference = models.CharField(max_length=100, blank=True, verbose_name=_("Référence"))
    date_paiement = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de paiement"))
    utilisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Utilisateur")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ['-date_paiement']

    @property
    def surplus_effectif(self):
        if self.montant_surplus and self.montant_surplus > 0:
            return self.montant_surplus

        # Fallback for legacy records: one payment greater than sale total.
        if self.vente_id:
            paiements_count = self.vente.paiements.count()
            if paiements_count == 1 and self.montant > self.vente.montant_total:
                return max(Decimal('0'), self.montant - self.vente.montant_total)

        return Decimal('0')

    def __str__(self):
        return f"{self.montant}GNF - {self.get_mode_paiement_display()}"
