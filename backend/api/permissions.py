from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    '''Разрешение для автора либо для администратора.'''

    def has_object_permission(self, request, view, obj):
        is_safe_method = request.method in permissions.SAFE_METHODS
        is_auth = request.user.is_authenticated
        return is_safe_method or is_auth and obj.author == request.user
