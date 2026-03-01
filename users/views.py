from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from .models import Payment
from .serializers import PaymentSerializer
from django_filters import rest_framework as django_filters


class PaymentFilter(django_filters.FilterSet):
    """Фильтр для платежей"""
    course = django_filters.NumberFilter(field_name='paid_course__id')
    lesson = django_filters.NumberFilter(field_name='paid_lesson__id')
    payment_method = django_filters.ChoiceFilter(choices=Payment.PAYMENT_METHOD_CHOICES)

    class Meta:
        model = Payment
        fields = ['paid_course', 'paid_lesson', 'payment_method']


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с платежами"""
    queryset = Payment.objects.all().select_related('user', 'paid_course', 'paid_lesson')
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_class = PaymentFilter
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']  # Сортировка по умолчанию
    search_fields = ['user__email', 'paid_course__title', 'paid_lesson__title']