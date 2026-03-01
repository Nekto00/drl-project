from rest_framework import permissions


class IsModerator(permissions.BasePermission):
    """
    Проверка, является ли пользователь модератором
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(name='Модераторы').exists()


class IsOwner(permissions.BasePermission):
    """
    Проверка, является ли пользователь владельцем объекта
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsModeratorOrOwner(permissions.BasePermission):
    """
    Доступ для модераторов или владельцев
    Модераторы могут читать и редактировать любые объекты, но не удалять
    Владельцы могут всё со своими объектами
    """

    def has_permission(self, request, view):
        # Все авторизованные пользователи могут просматривать список
        if view.action == 'list':
            return True

        # Модераторы не могут создавать
        if view.action == 'create' and request.user.groups.filter(name='Модераторы').exists():
            return False

        # Владельцы могут создавать
        if view.action == 'create':
            return True

        return True

    def has_object_permission(self, request, view, obj):
        # Проверка для модераторов
        if request.user.groups.filter(name='Модераторы').exists():
            # Модераторы не могут удалять
            if view.action == 'destroy':
                return False
            # Модераторы могут просматривать и редактировать любые объекты
            return True

        # Проверка для владельцев
        if obj.owner == request.user:
            return True

        # Для остальных - только чтение
        if view.action in ['retrieve']:
            return True

        return False