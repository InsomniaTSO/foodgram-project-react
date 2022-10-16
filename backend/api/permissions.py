from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Разрешение на действие с объектом только владельцу и администратору."""
    message = 'Доступ только у владельца!'

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.user.is_staff
