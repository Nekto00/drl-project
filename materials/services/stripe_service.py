import stripe
from django.conf import settings
from decimal import Decimal

# Проверяем наличие ключа перед инициализацией
if not settings.STRIPE_SECRET_KEY:
    raise Exception("STRIPE_SECRET_KEY не настроен. Проверьте .env файл")

# Инициализация Stripe с секретным ключом
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(name, description=None):
    """
    Создание продукта в Stripe
    """
    try:
        print(f"Создание продукта: {name}")  # Для отладки
        product = stripe.Product.create(
            name=name,
            description=description or ""
        )
        print(f"Продукт создан: {product.id}")  # Для отладки
        return {
            'success': True,
            'product_id': product.id,
            'product': product
        }
    except stripe.error.StripeError as e:
        print(f"Ошибка Stripe: {str(e)}")  # Для отладки
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        print(f"Неизвестная ошибка: {str(e)}")  # Для отладки
        return {
            'success': False,
            'error': f"Неизвестная ошибка: {str(e)}"
        }


def create_stripe_price(amount, product_id, currency='rub'):
    """
    Создание цены для продукта в Stripe
    """
    try:
        print(f"Создание цены: {amount} {currency} для продукта {product_id}")  # Для отладки
        amount_in_cents = int(amount * 100)

        price = stripe.Price.create(
            unit_amount=amount_in_cents,
            currency=currency,
            product=product_id,
        )
        print(f"Цена создана: {price.id}")  # Для отладки
        return {
            'success': True,
            'price_id': price.id,
            'price': price
        }
    except stripe.error.StripeError as e:
        print(f"Ошибка Stripe: {str(e)}")  # Для отладки
        return {
            'success': False,
            'error': str(e)
        }


def create_stripe_checkout_session(price_id, success_url, cancel_url):
    """
    Создание сессии для оплаты в Stripe
    """
    try:
        print(f"Создание сессии с ценой: {price_id}")  # Для отладки
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        print(f"Сессия создана: {session.id}")  # Для отладки
        return {
            'success': True,
            'session_id': session.id,
            'session_url': session.url,
            'session': session
        }
    except stripe.error.StripeError as e:
        print(f"Ошибка Stripe: {str(e)}")  # Для отладки
        return {
            'success': False,
            'error': str(e)
        }


def retrieve_stripe_session(session_id):
    """
    Получение информации о сессии оплаты
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            'success': True,
            'session': session,
            'payment_status': session.payment_status,
            'status': session.status
        }
    except stripe.error.StripeError as e:
        return {
            'success': False,
            'error': str(e)
        }