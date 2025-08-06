from rest_framework.permissions import SAFE_METHODS, BasePermission


class ContentOwnerAccessControl(BasePermission):
    """
    Контроль доступа к контенту:
    - Чтение разрешено всем
    - Изменение только владельцу контента
    - Создание для авторизованных пользователей
    """

    def check_global_access(self, request):
        """Проверка общих прав доступа"""
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def check_ownership(self, request, obj):
        """Проверка прав владения объектом"""
        if request.method in SAFE_METHODS:
            return True
        return hasattr(obj, 'created_by') and obj.created_by == request.user

    def has_permission(self, request, view):
        """Проверка прав на уровне запроса"""
        return self.check_global_access(request)

    def has_object_permission(self, request, view, obj):
        """Проверка прав на уровне объекта"""
        return self.check_ownership(request, obj)
