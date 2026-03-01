from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from .permissions import IsModerator, IsModeratorOrOwner


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Динамическое определение прав в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsModeratorOrOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        """Фильтрация queryset в зависимости от прав"""
        user = self.request.user

        # Модераторы видят все курсы
        if user.groups.filter(name='Модераторы').exists():
            return Course.objects.all()

        # Обычные пользователи видят свои курсы
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        """При создании курса привязываем его к текущему пользователю"""
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """При обновлении сохраняем владельца"""
        serializer.save()


class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, IsModeratorOrOwner]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user

        # Модераторы видят все уроки
        if user.groups.filter(name='Модераторы').exists():
            return Lesson.objects.all()

        # Обычные пользователи видят свои уроки
        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        """При создании урока привязываем его к текущему пользователю"""
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            self.permission_classes = [IsAuthenticated, IsModeratorOrOwner]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user

        # Модераторы видят все уроки
        if user.groups.filter(name='Модераторы').exists():
            return Lesson.objects.all()

        # Обычные пользователи видят свои уроки
        return Lesson.objects.filter(owner=user)