from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnlyPermission(BasePermission):
    """Определение прав доступа."""

    def has_permission(self, request, view):
        """Проверка прав доступа для пользоватей."""
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """Проверка прав доступа для пользоватей с объектом."""
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
