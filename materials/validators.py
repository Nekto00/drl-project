import re
from rest_framework import serializers
from django.core.exceptions import ValidationError


def validate_youtube_url(value):
    """
    Валидатор для проверки, что ссылка ведет на youtube.com
    """
    # Разрешаем только ссылки на youtube.com или youtu.be
    youtube_domains = [
        r'^https?://(www\.)?youtube\.com/watch\?v=',
        r'^https?://(www\.)?youtu\.be/',
        r'^https?://(www\.)?youtube\.com/embed/',
        r'^https?://(www\.)?youtube\.com/shorts/',
    ]

    # Проверяем, соответствует ли ссылка одному из паттернов YouTube
    for pattern in youtube_domains:
        if re.match(pattern, value):
            return value

    # Если ссылка не прошла проверку, выбрасываем ошибку
    raise ValidationError(
        'Разрешены только ссылки на YouTube (youtube.com, youtu.be)'
    )


class YouTubeUrlValidator:
    """
    Класс-валидатор для проверки ссылок на YouTube
    """

    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        # Разрешаем только ссылки на youtube.com или youtu.be
        youtube_domains = [
            r'^https?://(www\.)?youtube\.com/watch\?v=',
            r'^https?://(www\.)?youtu\.be/',
            r'^https?://(www\.)?youtube\.com/embed/',
            r'^https?://(www\.)?youtube\.com/shorts/',
        ]

        for pattern in youtube_domains:
            if re.match(pattern, value):
                return value

        raise ValidationError(
            f'Поле {self.field} должно содержать только ссылки на YouTube (youtube.com, youtu.be)'
        )