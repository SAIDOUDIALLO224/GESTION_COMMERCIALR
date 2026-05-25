from .utils import get_current_magasin, get_magasins_visibles


def current_magasin(request):
    ctx = {}
    if request.user.is_authenticated:
        ctx['current_magasin'] = get_current_magasin(request.user)
        ctx['magasins_liste'] = get_magasins_visibles(request.user)
    return ctx
