# Drl Project - Образовательная платформа

## О проекте
Платформа для управления курсами и уроками с поддержкой подписок, платежей через Stripe и асинхронными уведомлениями.

---

## Деплой на удаленный сервер (Ubuntu 22.04)

### Предварительные требования
- Сервер Ubuntu 22.04
- Домен или IP-адрес (в примере: 51.250.111.96)
- SSH доступ к серверу
- Репозиторий на GitHub

---

### **Часть 1: Настройка сервера**

#### 1.1 Подключение к серверу
```bash
ssh ваш_пользователь@ваш_ip_сервера
# Пример: ssh august@51.250.111.96

#### 1.2 Обновление системы и установка пакетов

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y
# Установка Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev -y
# Установка PostgreSQL, Nginx, Redis
sudo apt install postgresql postgresql-contrib nginx git redis-server -y
sudo apt install build-essential libpq-dev -y

#### 1.3 Запуск сервисов

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl start redis-server
sudo systemctl enable redis-server

### **Часть 2: Клонирование проекта**

```bash
cd /var/www
sudo mkdir -p drl-project
sudo chown -R $USER:$USER drl-project
cd drl-project
# Клонирование ветки developer
git clone --branch developer https://github.com/Nekto00/drl-project.git .

### **Часть 3: Настройка виртуального окружения**

```bash
# Создание виртуального окружения
python3.12 -m venv venv
```bash
# Активация
source venv/bin/activate
```bash
# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

### **Часть 4: Настройка PostgreSQL**

```bash
# Создание базы данных и пользователя
sudo -u postgres psql
```bash
CREATE DATABASE "Drl";
CREATE USER django_user WITH PASSWORD '12345';
ALTER ROLE django_user SET client_encoding TO 'utf8';
ALTER ROLE django_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE django_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE "Drl" TO django_user;
\q
```bash
# Проверка подключения
psql -U django_user -d Drl -h localhost -W
# Пароль: 12345
# \q для выхода

### **Часть 5: Создание .env файла**

```bash
nano .env
SECRET_KEY=ваш_секретный_ключ
DEBUG=False
ALLOWED_HOSTS=ваш_ip,localhost,127.0.0.1
DB_NAME=ИМЯ_БАЗЫ
DB_USER=ПОЛЬЗОВАТЕЛЬ_БД
DB_PASSWORD=ПАРОЛЬ
DB_HOST=localhost
DB_PORT=5432
# Остальные настройки...

### **Часть 6: Миграции и запуск**

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

### **Часть 7: Настройка Gunicorn**

```bash
sudo nano /etc/systemd/system/gunicorn.service
```bash
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=ВАШ_ПОЛЬЗОВАТЕЛЬ
Group=www-data
WorkingDirectory=/var/www/drl-project
ExecStart=/var/www/drl-project/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/drl-project/drl-project.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

### **Часть 8: Настройка Nginx**

```bash
sudo nano /etc/nginx/sites-available/drl-project

```bash
server {
    listen 80;
    server_name ВАШ_IP localhost;

    location /static/ {
        alias /var/www/drl-project/static/;
    }

    location / {
        proxy_pass http://unix:/var/www/drl-project/drl-project.sock;
    }
}
```bash
sudo ln -s /etc/nginx/sites-available/drl-project /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
