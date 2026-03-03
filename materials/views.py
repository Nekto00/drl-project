from decimal import Decimal
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from config import settings
from .models import Course, Lesson, Subscription, Payment
from .serializers import CourseSerializer, LessonSerializer, PaymentSerializer, PaymentCreateSerializer
from .services import stripe_service
from .permissions import (
    IsModeratorOrOwnerForCourse,
    IsModeratorOrOwnerForLesson
)
from .paginators import CoursePaginator, LessonPaginator


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CoursePaginator

    def get_permissions(self):
        """Динамическое определение прав в зависимости от действия"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsModeratorOrOwnerForCourse]
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
    pagination_class = LessonPaginator

    def get_permissions(self):
        """Разные права для разных методов"""
        if self.request.method == 'POST':
            self.permission_classes = [IsAuthenticated, IsModeratorOrOwnerForLesson]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        """Фильтрация queryset в зависимости от прав"""
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
        """Разные права для разных методов"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            self.permission_classes = [IsAuthenticated, IsModeratorOrOwnerForLesson]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        """Не фильтруем queryset здесь, чтобы 404 не возникало раньше времени"""
        return Lesson.objects.all()  # Убираем фильтрацию

    def get_object(self):
        """Переопределяем get_object для проверки прав доступа"""
        obj = super().get_object()
        user = self.request.user

        # Если пользователь не модератор и не владелец, возвращаем 403
        if not user.groups.filter(name='Модераторы').exists() and obj.owner != user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("У вас нет прав для доступа к этому уроку")

        return obj


class SubscriptionView(APIView):
    """
    View для управления подпиской на курс
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['course_id'],
            properties={
                'course_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID курса для подписки/отписки'
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description='Подписка удалена',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            201: openapi.Response(
                description='Подписка добавлена',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Не указан ID курса',
            401: 'Не авторизован',
            404: 'Курс не найден',
        },
        operation_description="Управление подпиской на курс (создание/удаление)"
    )

    def post(self, request):
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "Не указан ID курса"},
                status=status.HTTP_400_BAD_REQUEST
            )

        course = get_object_or_404(Course, id=course_id)

        # Проверяем существование подписки
        subscription = Subscription.objects.filter(
            user=user,
            course=course
        )

        if subscription.exists():
            # Если подписка есть - удаляем
            subscription.delete()
            message = 'Подписка удалена'
            status_code = status.HTTP_200_OK
        else:
            # Если подписки нет - создаем
            Subscription.objects.create(
                user=user,
                course=course
            )
            message = 'Подписка добавлена'
            status_code = status.HTTP_201_CREATED

        return Response(
            {"message": message},
            status=status_code
        )


class PaymentCreateView(APIView):
    """
    View для создания платежа
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=PaymentCreateSerializer,
        responses={
            201: PaymentSerializer(),
            400: 'Ошибка валидации',
            401: 'Не авторизован',
            404: 'Курс не найден',
            500: 'Ошибка Stripe'
        }
    )
    def post(self, request):
        # Проверяем наличие ключей Stripe
        if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PUBLIC_KEY:
            return Response(
                {"error": "Stripe не настроен. Обратитесь к администратору."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course_id = serializer.validated_data['course_id']
        success_url = serializer.validated_data['success_url']
        cancel_url = serializer.validated_data['cancel_url']

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Курс не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Создаем продукт в Stripe
        product_result = stripe_service.create_stripe_product(
            name=course.title,
            description=course.description
        )

        if not product_result['success']:
            return Response(
                {"error": f"Ошибка создания продукта: {product_result['error']}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем цену в Stripe
        price_result = stripe_service.create_stripe_price(
            amount=Decimal('1000.00'),
            product_id=product_result['product_id']
        )

        if not price_result['success']:
            return Response(
                {"error": f"Ошибка создания цены: {price_result['error']}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем сессию оплаты
        session_result = stripe_service.create_stripe_checkout_session(
            price_id=price_result['price_id'],
            success_url=success_url,
            cancel_url=cancel_url
        )

        if not session_result['success']:
            return Response(
                {"error": f"Ошибка создания сессии: {session_result['error']}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создаем запись о платеже в БД
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=Decimal('1000.00'),
            stripe_product_id=product_result['product_id'],
            stripe_price_id=price_result['price_id'],
            stripe_session_id=session_result['session_id'],
            payment_url=session_result['session_url']
        )

        response_serializer = PaymentSerializer(payment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PaymentRetrieveView(APIView):
    """
    View для получения информации о платеже
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: PaymentSerializer(),
            401: 'Не авторизован',
            403: 'Нет доступа',
            404: 'Платеж не найден'
        }
    )
    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Платеж не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем, что пользователь имеет доступ к платежу
        if payment.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "Нет доступа к этому платежу"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Получаем актуальный статус из Stripe
        if payment.stripe_session_id:
            session_result = stripe_service.retrieve_stripe_session(
                payment.stripe_session_id
            )
            if session_result['success']:
                # Обновляем статус в БД
                if session_result['payment_status'] == 'paid':
                    payment.status = Payment.PaymentStatus.PAID
                elif session_result['payment_status'] == 'unpaid':
                    payment.status = Payment.PaymentStatus.PENDING
                payment.save()

        serializer = PaymentSerializer(payment)
        return Response(serializer.data)