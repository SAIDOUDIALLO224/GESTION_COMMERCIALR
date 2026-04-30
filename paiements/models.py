from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from decimal import Decimal
from ventes.models import Vente
from clients.models import Client


class CompteEcobanque(models.Model):
    """Compte Ecobanque pour suivre les dépôts et retraits."""
    nom = models.CharField(max_length=150, verbose_name=_("Nom du compte"))
    numero_compte = models.CharField(max_length=100, blank=True, verbose_name=_("Numéro de compte"))
    solde_initial = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name=_("Solde initial")
    )
    solde_courant = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name=_("Solde courant")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))

    class Meta:
        verbose_name = _("Compte Ecobanque")
        verbose_name_plural = _("Comptes Ecobanque")
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self._state.adding and self.solde_courant == Decimal('0'):
            self.solde_courant = self.solde_initial
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} ({self.numero_compte})" if self.numero_compte else self.nom


class EcobanqueOperation(models.Model):
    """Opérations Ecobanque : dépôt (remise) et retrait (débit)."""
    TYPE_CHOICES = [
        ('DEBIT', _('Débit')),
        ('REMISE', _('Remise')),
    ]

    compte = models.ForeignKey(
        CompteEcobanque,
        on_delete=models.CASCADE,
        related_name='operations',
        verbose_name=_("Compte Ecobanque")
    )
    type_operation = models.CharField(
        max_length=10, choices=TYPE_CHOICES,
        verbose_name=_("Type d'opération")
    )
    montant = models.DecimalField(
        max_digits=18, decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant")
    )
    reference = models.CharField(max_length=150, blank=True, verbose_name=_("Référence"))
    motif = models.TextField(blank=True, verbose_name=_("Motif"))
    solde_avant = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        verbose_name=_("Solde avant opération")
    )
    solde_apres = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        verbose_name=_("Solde après opération")
    )
    date_operation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de l'opération"))
    utilisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Utilisateur")
    )

    class Meta:
        verbose_name = _("Opération Ecobanque")
        verbose_name_plural = _("Opérations Ecobanque")
        ordering = ['-date_operation']
        indexes = [
            models.Index(fields=['compte']),
            models.Index(fields=['type_operation']),
            models.Index(fields=['-date_operation']),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.solde_avant = self.compte.solde_courant
            if self.type_operation == 'DEBIT':
                self.solde_apres = self.solde_avant - self.montant
            else:
                self.solde_apres = self.solde_avant + self.montant
        super().save(*args, **kwargs)
        if self._state.adding:
            self.compte.solde_courant = self.solde_apres
            self.compte.save(update_fields=['solde_courant'])

    def __str__(self):
        return f"{self.get_type_operation_display()} {self.montant} GNF - {self.compte}"


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


class CompteEcoBanqueClient(models.Model):
    """Compte Ecobanque pour les clients : suivi des montants versés, initiaux, restants et sortis."""
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE,
        related_name='comptes_ecobanque', verbose_name=_("Client")
    )
    montant_verset = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name=_("Montant versé")
    )
    montant_initial = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name=_("Montant initial")
    )
    montant_restant = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name=_("Montant restant")
    )
    montant_sorti = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name=_("Montant sorti")
    )
    montant_exact_compte = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], verbose_name=_("Montant exact du compte")
    )
    date_operation = models.DateField(null=True, blank=True, verbose_name=_("Date d'opération"))
    motif = models.TextField(blank=True, verbose_name=_("Motif"))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    utilisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Utilisateur")
    )

    def save(self, *args, **kwargs):
        # Le montant_exact_compte est saisi manuellement et représente le solde bancaire actuel
        # Il n'est pas calculé automatiquement dans ce modèle, seulement ajusté si nécessaire lors des opérations
        
        # Si c'est une nouvelle opération avec des montants, on pourrait ajuster un solde global
        # Mais pour l'instant, gardons la logique simple : le montant_exact_compte est saisi manuellement
        super().save(*args, **kwargs)

    @property
    def total_montants_sortis(self):
        """Total de tous les montants sortis pour ce client"""
        return CompteEcoBanqueClient.objects.filter(client=self.client).aggregate(
            total=models.Sum('montant_sorti')
        )['total'] or Decimal('0')

    @property
    def total_montants_entrants(self):
        """Total de tous les montants entrants (versés + initiaux) pour ce client"""
        return CompteEcoBanqueClient.objects.filter(client=self.client).aggregate(
            total=models.Sum(models.F('montant_verset') + models.F('montant_initial'))
        )['total'] or Decimal('0')

    @property
    def total_montants_sortis(self):
        """Total des montants sortis pour ce client"""
        return self.montant_sorti

    @property
    def total_montants_entrants(self):
        """Total des montants entrants (versés + initial) pour ce client"""
        return self.montant_verset + self.montant_initial
