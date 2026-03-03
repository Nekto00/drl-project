from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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
            permission_classes = [AllowAny]
        elif self.action in ['list', 'destroy']:
            permission_classes = [IsAuthenticated]
        elif self.action == 'me':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        method='get',
        operation_description="Получение профиля текущего пользователя",
        responses={200: UserProfileSerializer()}
    )
    @swagger_auto_schema(
        method='put',
        operation_description="Полное обновление профиля текущего пользователя",
        request_body=UserProfileSerializer,
        responses={200: UserProfileSerializer()}
    )
    @swagger_auto_schema(
        method='patch',
        operation_description="Частичное обновление профиля текущего пользователя",
        request_body=UserProfileSerializer,
        responses={200: UserProfileSerializer()}
    )
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