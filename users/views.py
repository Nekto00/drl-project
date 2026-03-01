from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer, UserProfileSerializer
from .permissions import IsOwnerOrReadOnly

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return UserProfileSerializer
        elif self.action == 'me':
            return UserProfileSerializer
        return UserSerializer

    def get_permissions(self):
        """Разные права для разных действий"""
        if self.action == 'create':
            # Регистрация доступна всем
            permission_classes = [AllowAny]
        elif self.action in ['list', 'destroy']:
            # Список пользователей и удаление только для админов
            permission_classes = [IsAuthenticated]
        elif self.action == 'me':
            # Профиль текущего пользователя
            permission_classes = [IsAuthenticated]
        else:
            # Остальное только авторизованным и владельцам
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Получение и обновление профиля текущего пользователя"""
        user = request.user

        if not user.is_authenticated:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(
                user,
                data=request.data,
                partial=request.method == 'PATCH'
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)