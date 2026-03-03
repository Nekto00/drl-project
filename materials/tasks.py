from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Course, Subscription


@shared_task
def send_course_update_email(course_id, user_email, course_title):
    """
    Отправка уведомления об обновлении курса одному пользователю
    """
    subject = f'Обновление курса: {course_title}'
    message = f'''
    Здравствуйте!

    Курс "{course_title}" был обновлен. 
    Перейдите в свой профиль, чтобы посмотреть новые материалы.

    С уважением,
    Команда образовательной платформы
    '''

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        return f"Email sent to {user_email}"
    except Exception as e:
        return f"Failed to send email to {user_email}: {str(e)}"


@shared_task
def notify_course_subscribers(course_id):
    """
    Отправка уведомлений всем подписчикам курса
    """
    try:
        course = Course.objects.get(id=course_id)
        subscriptions = Subscription.objects.filter(course=course).select_related('user')

        emails_sent = 0
        for subscription in subscriptions:
            send_course_update_email.delay(
                course_id,
                subscription.user.email,
                course.title
            )
            emails_sent += 1

        return f"Notification sent to {emails_sent} subscribers for course '{course.title}'"

    except Course.DoesNotExist:
        return f"Course with id {course_id} not found"
    except Exception as e:
        return f"Error notifying subscribers: {str(e)}"


@shared_task
def notify_course_update_with_check(course_id, last_update_time):
    """
    Отправка уведомлений с проверкой времени последнего обновления
    """
    try:
        course = Course.objects.get(id=course_id)

        # Проверяем, прошло ли более 4 часов с последнего обновления
        time_since_update = timezone.now() - last_update_time
        if time_since_update > timedelta(hours=4):
            return notify_course_subscribers(course_id)
        else:
            return f"Course '{course.title}' updated recently. Notification skipped."

    except Course.DoesNotExist:
        return f"Course with id {course_id} not found"