# Финальный проект спринта - foodgram

## Описание проекта:
Проект Foodgram написанный на DjangoRF и React веб-сервис, 
который позволяет работать с кулинарными рецептами. Сервис предоставляет возможность 
создавать свои рецепты, следить за чужими, подписываться на авторов рецептов, 
добавлять рецепты в избранные и делать покупки.

* Веб-сервис доступен по домену - [https://foodgramforum.duckdns.org]

## Как запустить проект в Docker:
* Клонировать репозиторий и перейти в него в командной строке;


* Запустить docker-compose:

`cd infra`

`docker compose up --detach`


* Выполнить миграции, собрать статику и скопировать ее в папку для раздачи:

`docker compose exec backend python3 manage.py makemigrations`

`docker compose exec backend python3 manage.py migrate`

`docker compose exec backend python3 manage.py collectstatic`

`docker compose exec backend cp -r /app/collected_static/. /backend_static/static/`


* Наполнить БД ингредиентами:

`docker compose exec backend python3 manage.py load_ingredients_sqlite data/ingredients.csv`



## Примеры запросов к API:
* Получение токена.

`POST "/api/auth/login/"
body={"email": "string", "password": "string"}`


* Получение рецептов.

`GET "/api/recipes"`

* Создание рецептов.

`POST "/api/auth/login/"
{
    "ingredients": [
        {
            "id": 1123,
            "amount": 10
        }
    ],
    "tags": [
        1,
        2
    ],
    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
    "name": "string",
    "text": "string",
    "cooking_time": 1
}`

* Получение ингредиетов.

`GET "/api/ingredients`


* Подписаться на автора рецепта.

`POST "/api/users/{id}/subscribe`

Другие запросы и более подробную информацию о них можно посмотреть по адресу `"api/docs"`

## Основной стэк используемых технологий:
Django==4.2.11
djangorestframework==3.15.1
djoser==2.2.2
psycopg2-binary==2.9.9
Pillow==10.3.0
django-cleanup==8.1.0
django-filter==2.4.0
gunicorn==21.2.0
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

**Автор работы** - [Волков Александр](https://t.me/ximikat01)