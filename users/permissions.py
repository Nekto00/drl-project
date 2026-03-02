from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение на редактирование только владельцу объекта
    """

    def has_object_permission(self, request, view, obj):
        # Разрешаем чтение всем авторизованным
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем запись только владельцу
        return obj == request.user