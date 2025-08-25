from rest_framework.permissions import SAFE_METHODS, BasePermission


class ContentOwnerAccessControl(BasePermission):
    """
    Чтение для всех. Создание/изменение/удаление — только для авторизованных.
    Изменять/удалять рецепт может только его автор.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(
            obj, 'author_id', None) == getattr(request.user, 'id', None)
