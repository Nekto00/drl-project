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


class IsModeratorOrOwnerForCourse(permissions.BasePermission):
    """
    Права для CourseViewSet (ViewSet)
    Модераторы могут читать и редактировать любые объекты, но не удалять и создавать
    Владельцы могут всё со своими объектами
    """

    def has_permission(self, request, view):
        # Для ViewSet используем view.action
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


class IsModeratorOrOwnerForLesson(permissions.BasePermission):
    """
    Права для Lesson view (Generic-классы)
    Модераторы могут читать и редактировать любые объекты, но не удалять и создавать
    Владельцы могут всё со своими объектами
    """

    def has_permission(self, request, view):
        # Для Generic-классов используем request.method
        # Все авторизованные пользователи могут просматривать список
        if hasattr(view, 'action'):
            # Для ViewSet
            return True
        else:
            # Для Generic-классов
            if request.method in permissions.SAFE_METHODS:
                return True

            # Модераторы не могут создавать
            if request.method == 'POST' and request.user.groups.filter(name='Модераторы').exists():
                return False

            # Владельцы могут создавать
            if request.method == 'POST':
                return True

            return True

    def has_object_permission(self, request, view, obj):
        # Проверка для модераторов
        if request.user.groups.filter(name='Модераторы').exists():
            # Модераторы не могут удалять
            if request.method == 'DELETE':
                return False
            # Модераторы могут просматривать и редактировать любые объекты
            return True

        # Проверка для владельцев
        if obj.owner == request.user:
            return True

        # Для остальных - только чтение
        if request.method in permissions.SAFE_METHODS:
            return True

        return False