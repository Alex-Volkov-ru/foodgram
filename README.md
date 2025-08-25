# Финальный проект спринта — Foodgram

Проект **Foodgram** — это веб‑сервис на **Django + DRF** и **React**, где пользователи публикуют рецепты, подписываются на авторов, добавляют рецепты в избранное и формируют список покупок (с суммированием ингредиентов).

- Продакшен: **https://foodgramforum.duckdns.org**
- Документация API (ReDoc): **https://foodgramforum.duckdns.org/api/docs/**
- Админка: **https://foodgramforum.duckdns.org/admin/**

> Примечания по маршрутам:
> - `/admin` без завершающего слэша автоматически перенаправляется на `/admin/` на уровне Nginx.
> - Короткие ссылки рецептов имеют вид `/s/<hash>` и обрабатываются бэкендом (декодирование и редирект).

---

## Содержание
- [Стек технологий](#стек-технологий)
- [Архитектура и инфраструктура](#архитектура-и-инфраструктура)
- [CI/CD](#cicd)
- [Быстрый старт в Docker](#быстрый-старт-в-docker)
  - [Локальная разработка (Docker + PostgreSQL)](#локальная-разработка-docker--postgresql)
  - [Продакшен (Docker на сервере)](#продакшен-docker-на-сервере)
- [Запуск без Docker (SQLite)](#запуск-без-docker-sqlite)
- [Переменные окружения (.env)](#переменные-окружения-env)
- [Загрузка ингредиентов](#загрузка-ингредиентов)
- [Примеры запросов к API](#примеры-запросов-к-api)
- [Права доступа и роли](#права-доступа-и-роли)
- [Автор](#автор)

---

## Стек технологий

**Backend**
- Python 3.9
- Django 4.2.x
- Django REST Framework 3.15.x
- Djoser 2.2.x (token auth)
- PostgreSQL + psycopg2-binary
- Gunicorn
- django-filter, drf-extra-fields, Pillow, hashids, fpdf2


**DevOps**
- Docker, Docker Compose
- Nginx
- GitHub Actions (CI/CD)

---

## Архитектура и инфраструктура

- Контейнеры: `backend` (Django+Gunicorn), `db` (PostgreSQL), `nginx`, а также сборочный `frontend` (кладёт билд в общий том).
- Nginx:
  - `/` — SPA фронтенд (из тома `frontend_volume`)
  - `/api/` и `/admin/` — проксируются в `backend:8000`
  - `/api/docs/` — **статическая** документация ReDoc (alias на каталог с файлами)
  - `/django_static/` и `/media/` — alias на тома `backend`-контейнера
  - `/s/<hash>` — короткие ссылки → прокси в бэкенд (декодирование и редирект)
  - `/admin` → 301 на `/admin/`
- Данные и файлы хранятся в volumes: БД, статика, медиа, билд фронта.

---

## CI/CD

Проект автоматически деплоится на сервер через **GitHub Actions** и **Docker**: при пуше в ветку `main` происходит сборка образов (backend / frontend), публикация в реестр и перезапуск контейнеров на сервере, затем выполняются миграции и сборка статики.

---

## Быстрый старт в Docker

> Все команды ниже выполняются из каталога `infra/` репозитория.

### Локальная разработка (Docker + PostgreSQL)

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/ximikat01/foodgram-project-react.git
   cd foodgram-project-react/infra
   ```

2. Создайте файл `.env` (пример для локали — см. ниже в разделе **Переменные окружения**).

3. Поднимите контейнеры:
   ```bash
   docker compose -f docker-compose.local.yml up -d
   ```

4. Примените миграции, создайте суперпользователя, соберите статику:
   ```bash
   docker compose -f docker-compose.local.yml exec backend python manage.py migrate
   docker compose -f docker-compose.local.yml exec backend python manage.py createsuperuser
   docker compose -f docker-compose.local.yml exec backend python manage.py collectstatic --noinput
   ```

5. Загрузите ингредиенты (см. раздел **Загрузка ингредиентов**).

6. Проверьте:
   - Frontend: http://localhost
   - API docs: http://localhost/api/docs/

### Продакшен (Docker на сервере)

1. На сервере в `infra/` подготовьте `.env` (пример ниже).

2. Убедитесь, что в `docker-compose.production.yml` смонтированы:
   - статика/медиа/фронт,
   - **документация**: `./docs/:/usr/share/nginx/html/api/docs/:ro` (для `/api/docs/`).

3. Запустите:
   ```bash
   docker compose -f docker-compose.production.yml up -d
   docker compose -f docker-compose.production.yml exec backend python manage.py migrate
   docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
   ```

4. (Опционально) создайте суперпользователя:
   ```bash
   docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
   ```

5. Загрузите ингредиенты (см. ниже).

---

## Запуск без Docker (SQLite)

1. Клонируйте репозиторий и установите зависимости:
   ```bash
   git clone https://github.com/ximikat01/foodgram-project-react.git
   cd foodgram-project-react/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Создайте `.env` (минимум: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `BASE_URL`).

3. Выполните миграции, создайте суперпользователя и соберите статику:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```

4. Импортируйте ингредиенты (см. ниже) и запустите сервер:
   ```bash
   python manage.py runserver
   ```

---

## Переменные окружения (.env)

### Пример для локальной разработки (Docker)
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
BASE_URL=http://localhost

POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
```

### Пример для продакшена (Docker на сервере)
```
SECRET_KEY=prod-secret
DEBUG=False
ALLOWED_HOSTS=foodgramforum.duckdns.org
CSRF_TRUSTED_ORIGINS=https://foodgramforum.duckdns.org
BASE_URL=https://foodgramforum.duckdns.org

POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=<strong-pass>
DB_HOST=db
DB_PORT=5432
```

> Важно: переменные `POSTGRES_*` используются контейнером БД и читаются Django-настройками.
> Значение `BASE_URL` применяется для генерации коротких ссылок вида `BASE_URL/s/<hash>`.

---

## Загрузка ингредиентов

Файл с данными: `backend/data/ingredients.csv` (или из репозитория).

- **SQLite (без Docker):**
  ```bash
  python manage.py load_ingredients_sqlite data/ingredients.csv
  ```

- **PostgreSQL (в Docker):**
  ```bash
  docker compose -f infra/docker-compose.local.yml exec backend     python manage.py load_ingredients_pg data/ingredients.csv
  # или для продакшена
  docker compose -f infra/docker-compose.production.yml exec backend     python manage.py load_ingredients_pg data/ingredients.csv
  ```

---

## Примеры запросов к API

Аутентификация (Djoser, token):
```http
POST /api/auth/token/login/
Content-Type: application/json

{"email": "user@example.com", "password": "string"}
```
```http
POST /api/auth/token/logout/
```

Рецепты:
```http
GET /api/recipes/
```
Создание рецепта:
```http
POST /api/recipes/
Content-Type: application/json

{
  "ingredients": [{"id": 1123, "amount": 10}],
  "tags": [1, 2],
  "image": "data:image/png;base64,...",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```

Ингредиенты (поиск по началу названия, регистронезависимо):
```http
GET /api/ingredients/?name=са
```

Подписки:
```http
POST /api/users/{id}/subscribe/
DELETE /api/users/{id}/subscribe/
GET  /api/users/subscriptions/
```

Избранное и список покупок:
```http
POST   /api/recipes/{id}/favorite/
DELETE /api/recipes/{id}/favorite/

POST   /api/recipes/{id}/shopping_cart/
DELETE /api/recipes/{id}/shopping_cart/
GET    /api/recipes/download_shopping_cart/   # .txt, ингредиенты суммируются
```

Полная спецификация: **/api/docs/**

---

## Права доступа и роли

- **Гость:** просмотр рецептов, страниц пользователей, регистрация/вход.
- **Авторизованный:** создание/редактирование/удаление собственных рецептов; избранное; корзина; подписки; смена пароля; аватар.
- **Админ:** админ-зона со всеми моделями; поиск и фильтрация по требованиям.

Сортировка рецептов — по дате публикации (новые выше). Пагинация — PageNumber (по умолчанию `page_size=6`, параметр `limit`).

---

## Автор

**Волков Александр** — https://t.me/ximikat01
