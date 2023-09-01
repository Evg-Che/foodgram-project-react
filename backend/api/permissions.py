from rest_framework.permissions import (
    BasePermission,
    SAFE_METHODS
)


class IsOwnerOrReadOnly(BasePermission):
    message = 'Редактировать могут только владельцы.'

    def has_object_permission(self, request, view, obj):
        return (
                request.method in SAFE_METHODS
                or request.user.is_authenticated
                and request.user == obj.author
        )


class IsAuthorOrAdminOrReadOnly(BasePermission):
    message = 'Редактировать могут только автор или админ.'

    def has_permission(self, request, view):
        return (
                request.method in SAFE_METHODS
                or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
                request.method in SAFE_METHODS
                or request.user == obj.author
                or request.user.is_superuser
        )
