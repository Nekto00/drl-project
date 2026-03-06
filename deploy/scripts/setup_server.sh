#!/bin/bash
# Скрипт для первоначальной настройки сервера
# Запускать: bash setup_server.sh

set -e  # Остановка при ошибке

echo "========================================="
echo "🚀 Настройка сервера для Django проекта"
echo "========================================="

# 1. Обновление системы
echo "📦 Обновление пакетов..."
sudo apt update && sudo apt upgrade -y

# 2. Установка необходимых пакетов
echo "📦 Установка Python и зависимостей..."
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y postgresql postgresql-contrib libpq-dev
sudo apt install -y nginx git curl redis-server
sudo apt install -y build-essential

# 3. Настройка PostgreSQL
echo "🗄️ Настройка PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 4. Настройка Redis
echo "⚡ Настройка Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 5. Создание пользователя для приложения
echo "👤 Создание пользователя deploy..."
sudo useradd -m -s /bin/bash deploy || echo "Пользователь уже существует"
echo "deploy ALL=(ALL) NOPASSWD: /bin/systemctl" | sudo tee /etc/sudoers.d/deploy

# 6. Создание структуры папок
echo "📁 Создание структуры проекта..."
sudo mkdir -p /var/www/drl-project
sudo chown -R deploy:deploy /var/www/drl-project

echo "========================================="
echo "✅ Базовая настройка сервера завершена!"
echo "========================================="
echo ""
echo "Далее вам нужно:"
echo "1. Скопировать SSH ключ: ssh-copy-id deploy@ваш-сервер"
echo "2. Создать файл .env с переменными окружения"
echo "3. Настроить GitHub Secrets для автоматического деплоя"
echo ""
echo "IP сервера: $(curl -s ifconfig.me)"