from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Permission to check if user is owner"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'owner'

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.role == 'owner'


class IsManager(permissions.BasePermission):
    """Permission to check if user is manager or owner"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['manager', 'owner']

    def has_object_permission(self, request, view, obj):
        return request.user and request.user.role in ['manager', 'owner']


class IsViewer(permissions.BasePermission):
    """Permission for viewers (can read)"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS and request.user and request.user.is_authenticated


class OwnerOrReadOnly(permissions.BasePermission):
    """Only owners can edit"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == 'owner'
