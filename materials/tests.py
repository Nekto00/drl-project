from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import Course, Lesson, Subscription, Payment

User = get_user_model()


class LessonTestCase(APITestCase):
    """
    Тесты для CRUD уроков
    """

    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем группу модераторов
        self.moderator_group, created = Group.objects.get_or_create(name='Модераторы')

        # Создаем обычного пользователя
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            first_name='Обычный',
            last_name='Пользователь'
        )

        # Создаем модератора
        self.moderator = User.objects.create_user(
            email='moderator@test.com',
            password='modpass123',
            first_name='Модератор',
            last_name='Тестовый'
        )
        self.moderator.groups.add(self.moderator_group)

        # Создаем курс
        self.course = Course.objects.create(
            title='Тестовый курс',
            description='Описание тестового курса',
            owner=self.user
        )

        # Создаем урок
        self.lesson = Lesson.objects.create(
            title='Тестовый урок',
            description='Описание тестового урока',
            video_url='https://www.youtube.com/watch?v=test123',
            course=self.course,
            owner=self.user
        )

        # Настраиваем клиент
        self.client = APIClient()

        # URLs
        self.lesson_list_url = reverse('lesson-list')
        self.lesson_detail_url = reverse('lesson-detail', args=[self.lesson.id])

    def test_lesson_list_authenticated(self):
        """Тест получения списка уроков авторизованным пользователем"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.lesson_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_lesson_list_unauthenticated(self):
        """Тест получения списка уроков неавторизованным пользователем"""
        response = self.client.get(self.lesson_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lesson_create_owner(self):
        """Тест создания урока владельцем"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Новый урок',
            'description': 'Описание нового урока',
            'video_url': 'https://www.youtube.com/watch?v=new123',
            'course': self.course.id
        }
        response = self.client.post(self.lesson_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)
        self.assertEqual(Lesson.objects.last().owner, self.user)

    def test_lesson_create_moderator(self):
        """Тест создания урока модератором (должен быть запрещен)"""
        self.client.force_authenticate(user=self.moderator)
        data = {
            'title': 'Новый урок',
            'description': 'Описание нового урока',
            'video_url': 'https://www.youtube.com/watch?v=new123',
            'course': self.course.id
        }
        response = self.client.post(self.lesson_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_update_owner(self):
        """Тест обновления урока владельцем"""
        self.client.force_authenticate(user=self.user)
        data = {'title': 'Обновленный урок'}
        response = self.client.patch(self.lesson_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Обновленный урок')

    def test_lesson_update_moderator(self):
        """Тест обновления урока модератором (должен быть разрешен)"""
        self.client.force_authenticate(user=self.moderator)
        data = {'title': 'Обновлено модератором'}
        response = self.client.patch(self.lesson_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Обновлено модератором')

    def test_lesson_update_other_user(self):
        """Тест обновления урока другим пользователем (должен быть запрещен)"""
        other_user = User.objects.create_user(
            email='other@test.com',
            password='otherpass123'
        )
        self.client.force_authenticate(user=other_user)
        data = {'title': 'Обновлено другим'}
        response = self.client.patch(self.lesson_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_delete_owner(self):
        """Тест удаления урока владельцем"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.lesson_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_lesson_delete_moderator(self):
        """Тест удаления урока модератором (должен быть запрещен)"""
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.lesson_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_video_url_validator(self):
        """Тест валидации ссылки на видео"""
        self.client.force_authenticate(user=self.user)

        # Тест с правильной YouTube ссылкой
        data = {
            'title': 'Урок с YouTube',
            'description': 'Описание',
            'video_url': 'https://www.youtube.com/watch?v=valid123',
            'course': self.course.id
        }
        response = self.client.post(self.lesson_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Тест с неправильной ссылкой
        data['video_url'] = 'https://vimeo.com/12345'
        response = self.client.post(self.lesson_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_url', response.data)


class SubscriptionTestCase(APITestCase):
    """
    Тесты для подписки на курс
    """

    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123'
        )

        self.course = Course.objects.create(
            title='Тестовый курс',
            description='Описание тестового курса',
            owner=self.user
        )

        self.client = APIClient()
        self.subscribe_url = reverse('subscribe')

    def test_subscribe_to_course(self):
        """Тест подписки на курс"""
        self.client.force_authenticate(user=self.user)
        data = {'course_id': self.course.id}

        response = self.client.post(self.subscribe_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Подписка добавлена')
        self.assertTrue(Subscription.objects.filter(
            user=self.user,
            course=self.course
        ).exists())

    def test_unsubscribe_from_course(self):
        """Тест отписки от курса"""
        # Сначала подписываемся
        Subscription.objects.create(
            user=self.user,
            course=self.course
        )

        self.client.force_authenticate(user=self.user)
        data = {'course_id': self.course.id}

        response = self.client.post(self.subscribe_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Подписка удалена')
        self.assertFalse(Subscription.objects.filter(
            user=self.user,
            course=self.course
        ).exists())

    def test_subscribe_without_course_id(self):
        """Тест подписки без указания ID курса"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.subscribe_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscribe_unauthenticated(self):
        """Тест подписки неавторизованным пользователем"""
        data = {'course_id': self.course.id}
        response = self.client.post(self.subscribe_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_course_serializer_has_subscription_info(self):
        """Тест наличия информации о подписке в сериализаторе курса"""
        from rest_framework.test import APIRequestFactory
        from materials.serializers import CourseSerializer

        # Подписываем пользователя
        Subscription.objects.create(
            user=self.user,
            course=self.course
        )

        # Создаем запрос с авторизованным пользователем
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.user

        # Сериализуем курс
        serializer = CourseSerializer(
            self.course,
            context={'request': request}
        )

        self.assertIn('is_subscribed', serializer.data)
        self.assertTrue(serializer.data['is_subscribed'])

        # Проверяем для другого пользователя
        other_user = User.objects.create_user(
            email='other@test.com',
            password='otherpass123'
        )
        request.user = other_user
        serializer = CourseSerializer(
            self.course,
            context={'request': request}
        )
        self.assertFalse(serializer.data['is_subscribed'])


class PaymentTestCase(APITestCase):
    """
    Тесты для платежей
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com',
            password='testpass123'
        )

        self.course = Course.objects.create(
            title='Тестовый курс',
            description='Описание',
            owner=self.user
        )

        self.client = APIClient()
        self.payment_create_url = reverse('payment-create')

    @patch('materials.services.stripe_service.create_stripe_product')
    @patch('materials.services.stripe_service.create_stripe_price')
    @patch('materials.services.stripe_service.create_stripe_checkout_session')
    def test_create_payment(self, mock_session, mock_price, mock_product):
        """Тест создания платежа"""
        # Настройка моков
        mock_product.return_value = {
            'success': True,
            'product_id': 'prod_test123'
        }
        mock_price.return_value = {
            'success': True,
            'price_id': 'price_test123'
        }
        mock_session.return_value = {
            'success': True,
            'session_id': 'session_test123',
            'session_url': 'https://checkout.stripe.com/test'
        }

        self.client.force_authenticate(user=self.user)
        data = {
            'course_id': self.course.id,
            'success_url': 'http://localhost:8000/success/',
            'cancel_url': 'http://localhost:8000/cancel/'
        }

        response = self.client.post(self.payment_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Payment.objects.first().user, self.user)