from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Разрешает чтение всем, но редактирование только автору объекта."""
    def has_permission(self, request, view):
        """
        Проверяет общие права доступа.
        Разрешает доступ, если пользователь аутентифицирован
        ИЛИ метод безопасный (GET, HEAD, OPTIONS).
        """
        return (request.user.is_authenticated
                or request.method in SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        """
        Проверяет права доступа к конкретному объекту.
        Разрешает доступ, если метод безопасный
        ИЛИ пользователь - автор объекта.
        """
        return (request.method in SAFE_METHODS
                or obj.author == request.user)
