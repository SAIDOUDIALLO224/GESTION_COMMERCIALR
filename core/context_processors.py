from .utils import get_current_magasin, get_magasins_visibles
from .models import Magasin


def current_magasin(request):
    ctx = {}
    if request.user.is_authenticated:
        ctx['current_magasin'] = get_current_magasin(request.user)
        if request.user.is_superuser:
            ctx['magasins_liste'] = Magasin.objects.all().order_by('-est_principal', 'nom')
        else:
            ctx['magasins_liste'] = get_magasins_visibles(request.user)
    return ctx
