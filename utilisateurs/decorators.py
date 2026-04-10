from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def gerant_required(view_func):
    """Restrict view access to manager role users only."""

    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        profil = getattr(request.user, 'profilutilisateur', None)
        if profil and profil.actif and profil.role == 'GERANT':
            return view_func(request, *args, **kwargs)

        messages.error(request, "Acces refuse: cette action est reservee au gerant.")
        return redirect('core:dashboard')

    return _wrapped_view
