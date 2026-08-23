from functools import wraps
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status


def role_required(*allowed_roles):
    """Decorator to check user role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required")

            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("You do not have permission to access this resource")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def owner_required(view_func):
    """Decorator to check if user is owner"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication required")

        if request.user.role != 'owner':
            return HttpResponseForbidden("Only owners can access this resource")

        return view_func(request, *args, **kwargs)
    return wrapper


class RoleRequiredMixin:
    """Mixin for class-based views"""
    required_role = 'viewer'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication required")

        if request.user.role != self.required_role and request.user.role != 'owner':
            return HttpResponseForbidden("You do not have permission to access this resource")

        return super().dispatch(request, *args, **kwargs)


class RolePermission:
    """DRF Permission class for role-based access"""

    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in self.allowed_roles or request.user.role == 'owner'

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in self.allowed_roles or request.user.role == 'owner'
