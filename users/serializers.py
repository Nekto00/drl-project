from rest_framework import serializers
from users.models import User, Payment
from materials.models import Course, Lesson


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    course_title = serializers.ReadOnlyField(source='paid_course.title', default=None)
    lesson_title = serializers.ReadOnlyField(source='paid_lesson.title', default=None)

    class Meta:
        model = Payment
        fields = ('id', 'user', 'user_email', 'payment_date', 'paid_course',
                  'paid_lesson', 'course_title', 'lesson_title', 'amount', 'payment_method')