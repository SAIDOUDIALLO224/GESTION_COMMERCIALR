from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class ProfilUtilisateur(models.Model):
    """Profil utilisateur étendu"""
    ROLE_CHOICES = [
        ('GERANT', _('Gérant')),
        ('EMPLOYE', _('Employé')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("Utilisateur"))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name=_("Rôle"))
    telephone = models.CharField(max_length=20, blank=True, verbose_name=_("Téléphone"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))

    class Meta:
        verbose_name = _("Profil utilisateur")
        verbose_name_plural = _("Profils utilisateurs")

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"
