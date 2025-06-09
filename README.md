# Финальный проект спринта - foodgram

## Описание проекта:
Проект Foodgram, написанный на DjangoRF и React — веб-сервис,  
который позволяет работать с кулинарными рецептами. Сервис предоставляет возможность  
создавать свои рецепты, следить за чужими, подписываться на авторов рецептов,  
добавлять рецепты в избранное и формировать список покупок.

* Веб-сервис доступен по адресу - [https://foodgramforum.duckdns.org](https://foodgramforum.duckdns.org)

## Автор проекта:
**Волков Александр** — [https://t.me/ximikat01](https://t.me/ximikat01)

## Технологии проекта:
* Python 3.9  
* Django==4.2.11  
* djangorestframework==3.15.1  
* PostgreSQL (psycopg2-binary==2.9.9)  
* React  
* Docker / Docker Compose  
* Nginx  
* Gunicorn==21.2.0  

Дополнительно:
```
djoser==2.2.2  
Pillow==10.3.0  
django-cleanup==8.1.0  
django-filter==2.4.0  
fpdf2==2.7.8  
uharfbuzz==0.39.1  
drf_extra_fields==3.7.0  
python-dotenv  
django-cors-headers==3.13.0  
django-colorfield==0.11.0  
webcolors==1.11.1  
pytest==6.2.4  
pytest-django==4.4.0  
pytest-pythonpath==0.7.3  
PyYAML==6.0  
hashids
```

## CI/CD:
Проект автоматически деплоится на сервер через GitHub Actions и Docker.  
При пуше в `main` происходит автоматическая сборка и выкладка на сервер с Nginx и PostgreSQL.

---

## Как запустить проект в Docker:

* Клонировать репозиторий:

`git clone https://github.com/ximikat01/foodgram-project-react.git`

* Перейти в папку `infra`, где находится `docker-compose.yml`:

`cd foodgram-project-react/infra`

* Создать файл `.env` и заполнить его переменными окружения. Пример:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

* Поднять контейнеры:

`docker compose up --detach`

* Выполнить миграции, создать суперпользователя, собрать статику:

```
docker compose exec backend python3 manage.py makemigrations
docker compose exec backend python3 manage.py migrate
docker compose exec backend python3 manage.py createsuperuser
docker compose exec backend python3 manage.py collectstatic --noinput
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```

* Загрузить ингредиенты:

`docker compose exec backend python3 manage.py load_ingredients_sqlite data/ingredients.csv`

---

## Как развернуть проект без Docker:

* Клонировать репозиторий:

`git clone https://github.com/ximikat01/foodgram-project-react.git`

* Перейти в backend проекта:

`cd foodgram-project-react/backend/`

* Создать виртуальное окружение и активировать его:

```
python3 -m venv venv
source venv/bin/activate
```

* Установить зависимости:

`pip install -r requirements.txt`

* Создать `.env` по примеру выше и указать `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` и т.д.

* Выполнить миграции и создать суперпользователя:

```
python manage.py migrate
python manage.py createsuperuser
```

* Импортировать ингредиенты:

`python manage.py load_ingredients_sqlite data/ingredients.csv`

* Собрать и применить статику:

```
python manage.py collectstatic --noinput
```

* Запустить сервер:

`python manage.py runserver`

---

## Примеры запросов к API:

* Получение токена:

`POST "/api/auth/login/"`  
`body={"email": "string", "password": "string"}`

* Получение рецептов:

`GET "/api/recipes"`

* Создание рецепта:

```
POST "/api/recipes/"
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [1, 2],
  "image": "data:image/png;base64,...",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```

* Получение ингредиентов:

`GET "/api/ingredients"`

* Подписаться на автора:

`POST "/api/users/{id}/subscribe"`

* Полная документация по API доступна по адресу:

`/api/docs/`