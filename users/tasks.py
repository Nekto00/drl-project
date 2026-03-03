from celery import shared_task
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@shared_task
def test_celery():
    """
    Простая тестовая задача для проверки работы Celery
    """
    logger.info("Celery задача test_celery выполняется")
    print("✅ Celery задача test_celery выполняется")

    # Используем только JSON-совместимые типы (строки, числа, списки, словари)
    result = {
        'status': 'success',
        'message': 'Celery работает правильно',
        'task': 'test_celery',
        'time': str(datetime.now())  # Конвертируем datetime в строку
    }

    logger.info(f"Celery задача test_celery завершена")
    return result


@shared_task
def simple_test():
    """Очень простая тестовая задача"""
    print("✅ simple_test выполнена")
    return "OK"


@shared_task
def block_inactive_users():
    """
    Блокировка пользователей, которые не заходили более месяца
    """
    from django.utils import timezone
    from django.contrib.auth import get_user_model
    from datetime import timedelta

    User = get_user_model()

    try:
        one_month_ago = timezone.now() - timedelta(days=30)

        inactive_users = User.objects.filter(
            last_login__lt=one_month_ago,
            is_active=True,
            is_superuser=False
        )

        count = inactive_users.count()

        for user in inactive_users:
            user.is_active = False
            user.save()
            print(f"Пользователь {user.email} заблокирован")

        return f"Blocked {count} inactive users at {str(timezone.now())}"

    except Exception as e:
        error_msg = f"Error blocking inactive users: {str(e)}"
        print(error_msg)
        return error_msg


@shared_task
def send_course_update_email(course_id, user_email, course_title):
    """
    Отправка уведомления об обновлении курса
    """
    from django.core.mail import send_mail
    from django.conf import settings

    try:
        subject = f'Обновление курса: {course_title}'
        message = f'''
        Здравствуйте!

        Курс "{course_title}" был обновлен.

        С уважением,
        Команда образовательной платформы
        '''

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        return f"Email sent to {user_email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"