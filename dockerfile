FROM python:3.13-slim

# Устанавливаем netcat для проверки доступности сервисов
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    DJANGO_SETTINGS_MODULE=config.settings

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Создаем директории для статики и медиа
RUN mkdir -p /app/static /app/media

# Делаем скрипт исполняемым
RUN chmod +x /app/entrypoint.sh

# Команда по умолчанию
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]