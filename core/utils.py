from .models import Magasin


def _get_profil(user):
    try:
        return user.profilutilisateur
    except Exception:
        return None


def get_magasins_visibles(user):
    if user.is_superuser:
        current = get_current_magasin(user)
        if current:
            return Magasin.objects.filter(pk=current.pk)
        return Magasin.objects.all()
    profil = _get_profil(user)
    if not profil or not profil.magasin:
        return Magasin.objects.none()
    ids = [profil.magasin.id]
    ids += list(profil.magasin.magasins_visibles.values_list('id', flat=True))
    return Magasin.objects.filter(id__in=ids)


def get_current_magasin(user):
    if user.is_superuser:
        profil = _get_profil(user)
        if profil and profil.magasin:
            return profil.magasin
        # Fallback au magasin principal si pas de profil/magasin
        principal = Magasin.objects.filter(est_principal=True).first()
        if principal:
            return principal
        return Magasin.objects.first()
    profil = _get_profil(user)
    if profil and profil.magasin:
        return profil.magasin
    return None


def get_categories_autorisees(user):
    """Retourne les IDs des catégories autorisées pour un utilisateur.
    None = pas de restriction."""
    if user.is_superuser:
        return None
    profil = _get_profil(user)
    if not profil:
        return None
    cats = profil.categories_autorisees.all()
    if not cats:
        return None
    return list(cats.values_list('id', flat=True))


def get_or_create_consommateur(magasin):
    """Retourne le client générique 'Consommateur' pour un magasin."""
    from clients.models import Client
    conso, _ = Client.objects.get_or_create(
        nom="Consommateur",
        magasin=magasin,
        defaults={'telephone': '', 'actif': True},
    )
    return conso
