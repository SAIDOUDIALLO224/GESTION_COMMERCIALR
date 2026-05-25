from .models import Magasin


def _get_profil(user):
    try:
        return user.profilutilisateur
    except Exception:
        return None


def get_magasins_visibles(user):
    if user.is_superuser:
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
        return None
    profil = _get_profil(user)
    if profil and profil.magasin:
        return profil.magasin
    return None
