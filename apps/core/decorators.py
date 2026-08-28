from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden


def authentication_required(view_func):
    """Simple authenticated-user check for starter boilerplate."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Authentication required')
        return view_func(request, *args, **kwargs)
    return wrapper


def owner_required(view_func):
    """Allow only authenticated owners to access a view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Authentication required')
        if not request.user.is_superuser:
            return HttpResponseForbidden('Only superusers can access this resource')
        return view_func(request, *args, **kwargs)
    return wrapper
