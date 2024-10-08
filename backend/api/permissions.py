from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    '''Разрешение для администратора либо для безопасных запросов.'''

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_staff)


class IsAuthorOrIsAdminOrReadOnly(permissions.BasePermission):
    '''Разрешение для автора либо для администратора.'''

    def has_object_permission(self, request, view, obj):
        is_safe_method = request.method in permissions.SAFE_METHODS
        is_auth = request.user.is_authenticated

        return is_safe_method or is_auth and (
            request.user.is_staff
            or obj.author == request.user
        )


class IsAdmin(permissions.BasePermission):
    '''Разрешение, позволяющее доступ только администратору.'''

    def has_permission(self, request, view):
        return request.user.is_staff
