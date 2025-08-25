# flake8: noqa: F401
# -*- coding: utf-8 -*-
from typing import Optional
import base64

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

# 1×1 прозрачный PNG (без Pillow), чтобы пройти required ImageField
PNG_1PX_B64 = (
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMA"
    b"AQAABQABDQottAAAAABJRU5ErkJggg=="
)


def get_placeholder_bytes() -> bytes:
    return base64.b64decode(PNG_1PX_B64)


TAGS = [
    {"name": "Завтрак", "slug": "breakfast"},
    {"name": "Обед", "slug": "lunch"},
    {"name": "Ужин", "slug": "dinner"},
]

# Справочник единиц
U = {
    "g": "г",
    "ml": "мл",
    "pcs": "шт",
    "tsp": "ч.л.",
    "tbsp": "ст.л.",
    "pinch": "щепотка",
    "slice": "ломтик",
    "leaf": "лист",
}

# Рецепты
RECIPES = [
    {
        "name": "Овсяноблин с бананом",
        "time": 15,
        "tags": ["breakfast"],
        "text": (
            "1) Измельчите хлопья, смешайте с яйцом, молоком и солью.\n"
            "2) Разогрейте сковороду, смажьте маслом, вылейте тесто.\n"
            "3) Жарьте 2–3 мин с каждой стороны.\n"
            "4) Положите внутрь ломтики банана и сложите пополам."
        ),
        "components": [
            ("Овсяные хлопья", 50, U["g"]),
            ("Яйцо", 1, U["pcs"]),
            ("Молоко", 60, U["ml"]),
            ("Банан", 1, U["pcs"]),
            ("Соль", 1, U["pinch"]),
            ("Масло растительное", 1, U["tsp"]),
        ],
    },
    {
        "name": "Шакшука",
        "time": 25,
        "tags": ["breakfast", "lunch"],
        "text": (
            "1) Обжарьте лук и перец 5 мин.\n"
            "2) Добавьте чеснок, паприку и тмин на 30 сек.\n"
            "3) Влейте томаты, тушите 7–8 мин, посолите.\n"
            "4) Сделайте лунки, вбейте яйца, накройте и доведите до готовности."
        ),
        "components": [
            ("Яйцо", 3, U["pcs"]),
            ("Томаты в собственном соку", 300, U["g"]),
            ("Перец болгарский", 1, U["pcs"]),
            ("Лук репчатый", 1, U["pcs"]),
            ("Чеснок", 2, U["pcs"]),
            ("Паприка молотая", 1, U["tsp"]),
            ("Тмин молотый", 1, U["tsp"]),
            ("Масло растительное", 1, U["tbsp"]),
            ("Соль", 1, U["pinch"]),
            ("Перец чёрный молотый", 1, U["pinch"]),
            ("Зелень", 5, U["leaf"]),
        ],
    },
    {
        "name": "Сырники запечённые",
        "time": 30,
        "tags": ["breakfast"],
        "text": (
            "1) Смешайте творог, яйцо, сахар, манку, разрыхлитель и ваниль.\n"
            "2) Сформуйте сырники, присыпьте мукой.\n"
            "3) Выпекайте при 190°C 15–18 мин."
        ),
        "components": [
            ("Творог", 400, U["g"]),
            ("Яйцо", 1, U["pcs"]),
            ("Сахар", 2, U["tbsp"]),
            ("Манка", 2, U["tbsp"]),
            ("Разрыхлитель", 1, U["tsp"]),
            ("Ваниль", 1, U["pinch"]),
            ("Мука пшеничная", 2, U["tbsp"]),
        ],
    },
    {
        "name": "Суп-пюре из тыквы",
        "time": 35,
        "tags": ["lunch", "dinner"],
        "text": (
            "1) Обжарьте лук и морковь 3–4 мин.\n"
            "2) Добавьте тыкву и бульон, варите 15–18 мин.\n"
            "3) Измельчите, введите сливки, посолите и поперчите."
        ),
        "components": [
            ("Тыква", 600, U["g"]),
            ("Лук репчатый", 1, U["pcs"]),
            ("Морковь", 1, U["pcs"]),
            ("Бульон овощной", 700, U["ml"]),
            ("Сливки 20%", 150, U["ml"]),
            ("Масло растительное", 1, U["tbsp"]),
            ("Соль", 1, U["pinch"]),
            ("Перец чёрный молотый", 1, U["pinch"]),
            ("Тыквенные семечки", 1, U["tbsp"]),
        ],
    },
    {
        "name": "Паста с томатами и базиликом",
        "time": 20,
        "tags": ["lunch", "dinner"],
        "text": (
            "1) Отварите пасту до al dente.\n"
            "2) На масле прогрейте чеснок, добавьте томаты, тушите 5–6 мин.\n"
            "3) Смешайте с пастой, добавьте базилик и пармезан."
        ),
        "components": [
            ("Спагетти", 200, U["g"]),
            ("Помидоры черри", 250, U["g"]),
            ("Чеснок", 3, U["pcs"]),
            ("Масло оливковое", 2, U["tbsp"]),
            ("Базилик свежий", 12, U["leaf"]),
            ("Пармезан", 30, U["g"]),
            ("Соль", 1, U["pinch"]),
            ("Перец чёрный молотый", 1, U["pinch"]),
        ],
    },
    {
        "name": "Гречка с грибами и луком",
        "time": 25,
        "tags": ["dinner", "lunch"],
        "text": (
            "1) Варите гречку 15 мин.\n"
            "2) Обжарьте лук и морковь, добавьте грибы 5–6 мин.\n"
            "3) Смешайте с гречкой, посолите и поперчите."
        ),
        "components": [
            ("Гречка", 200, U["g"]),
            ("Вода", 400, U["ml"]),
            ("Шампиньоны", 300, U["g"]),
            ("Лук репчатый", 1, U["pcs"]),
            ("Морковь", 1, U["pcs"]),
            ("Масло растительное", 2, U["tbsp"]),
            ("Соль", 1, U["pinch"]),
            ("Перец чёрный молотый", 1, U["pinch"]),
            ("Зелень", 5, U["leaf"]),
        ],
    },
    {
        "name": "Куриные котлеты на пару с пюре",
        "time": 40,
        "tags": ["lunch", "dinner"],
        "text": (
            "1) Смешайте фарш с размоченным хлебом, луком и яйцом.\n"
            "2) Сформируйте котлеты и готовьте на пару 15–18 мин.\n"
            "3) Отварите картофель и сделайте пюре с молоком и маслом."
        ),
        "components": [
            ("Фарш куриный", 500, U["g"]),
            ("Лук репчатый", 1, U["pcs"]),
            ("Хлеб пшеничный", 1, U["slice"]),
            ("Молоко", 150, U["ml"]),  # 50 в фарш + 100 в пюре
            ("Яйцо", 1, U["pcs"]),
            ("Соль", 1, U["pinch"]),
            ("Перец чёрный молотый", 1, U["pinch"]),
            ("Картофель", 600, U["g"]),
            ("Сливочное масло", 30, U["g"]),
        ],
    },
    {
        "name": "Лосось в медово-горчичном соусе с брокколи",
        "time": 25,
        "tags": ["dinner"],
        "text": (
            "1) Смешайте мёд, горчицу, соевый соус и лимонный сок.\n"
            "2) Обмажьте лосося и запекайте при 200°C 12–14 мин.\n"
            "3) Брокколи отварите/на пару 3–4 мин и подайте вместе."
        ),
        "components": [
            ("Лосось (стейки/филе)", 300, U["g"]),
            ("Мёд", 1, U["tbsp"]),
            ("Горчица дижонская", 1, U["tbsp"]),
            ("Соевый соус", 1, U["tbsp"]),
            ("Сок лимонный", 1, U["tbsp"]),
            ("Масло оливковое", 1, U["tbsp"]),
            ("Брокколи", 300, U["g"]),
            ("Соль", 1, U["pinch"]),
            ("Перец чёрный молотый", 1, U["pinch"]),
        ],
    },
    {
        "name": "Тёплый салат с киноа и фетой",
        "time": 25,
        "tags": ["lunch", "dinner"],
        "text": (
            "1) Промойте киноа и варите 12–15 мин.\n"
            "2) Быстро обжарьте сладкий перец 2–3 мин.\n"
            "3) Смешайте с черри и оливками, заправьте маслом и лимоном.\n"
            "4) Добавьте фету кубиками."
        ),
        "components": [
            ("Киноа", 150, U["g"]),
            ("Вода", 300, U["ml"]),
            ("Перец болгарский", 1, U["pcs"]),
            ("Помидоры черри", 150, U["g"]),
            ("Сыр фета", 120, U["g"]),
            ("Оливки", 50, U["g"]),
            ("Масло оливковое", 2, U["tbsp"]),
            ("Сок лимонный", 1, U["tbsp"]),
            ("Соль", 1, U["pinch"]),
            ("Перец чёрный молотый", 1, U["pinch"]),
        ],
    },
    {
        "name": "Чили кон карне (простой)",
        "time": 35,
        "tags": ["dinner"],
        "text": (
            "1) Обжарьте лук, добавьте говяжий фарш и доведите до румяности.\n"
            "2) Введите чеснок и специи.\n"
            "3) Добавьте томаты, фасоль и кукурузу; томите 15 мин."
        ),
        "components": [
            ("Говяжий фарш", 400, U["g"]),
            ("Фасоль красная консервированная", 400, U["g"]),
            ("Томаты в собственном соку", 400, U["g"]),
            ("Кукуруза консервированная", 150, U["g"]),
            ("Лук репчатый", 1, U["pcs"]),
            ("Чеснок", 2, U["pcs"]),
            ("Паприка молотая", 1, U["tsp"]),
            ("Чили молотый", 1, U["tsp"]),
            ("Тмин молотый", 1, U["tsp"]),
            ("Масло растительное", 1, U["tbsp"]),
            ("Соль", 1, U["pinch"]),
            ("Перец чёрный молотый", 1, U["pinch"]),
        ],
    },
    {
        "name": "Борщ со сметаной",
        "time": 90,
        "tags": ["lunch", "dinner"],
        "text": (
            "Классический борщ: говядина, свёкла, капуста, картофель, морковь, "
            "лук. Подача со сметаной и зеленью."
        ),
        "components": [
            ("Говядина на кости", 600, U["g"]),
            ("Свёкла", 2, U["pcs"]),
            ("Капуста белокочанная", 300, U["g"]),
            ("Картофель", 400, U["g"]),
            ("Морковь", 1, U["pcs"]),
            ("Лук репчатый", 1, U["pcs"]),
            ("Томатная паста", 1, U["tbsp"]),
            ("Чеснок", 2, U["pcs"]),
            ("Соль", 1, U["pinch"]),
            ("Перец чёрный молотый", 1, U["pinch"]),
            ("Сметана", 2, U["tbsp"]),
            ("Зелень", 5, U["leaf"]),
        ],
    },
]


class Command(BaseCommand):
    help = "Загружает тестовые теги, ингредиенты и 10 рецептов."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-email",
            type=str,
            help=(
                "Email автора для новых рецептов "
                "(по умолчанию берётся первый суперпользователь/любой пользователь)."
            ),
        )
        parser.add_argument(
            "--image",
            type=str,
            help="Путь к картинке по умолчанию для всех рецептов (необязательно).",
        )

    def _resolve_author(self, email: Optional[str]) -> User:
        if email:
            try:
                return User.objects.get(email=email)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"Пользователь с email {email} не найден."
                ))
        author = User.objects.filter(
            is_superuser=True).first() or User.objects.first()
        if not author:
            raise SystemExit(
                "Не найдено ни одного пользователя. Создайте пользователя и повторите.")
        return author

    def _get_or_create_tag(self, name: str, slug: str) -> Tag:
        return Tag.objects.get_or_create(name=name, slug=slug)[0]

    def _get_or_create_ingredient(self, name: str, unit: str) -> Ingredient:
        obj, _ = Ingredient.objects.get_or_create(
            name=name.strip(),
            measurement_unit=unit.strip(),
        )
        return obj

    @transaction.atomic
    def handle(self, *args, **options):
        author = self._resolve_author(options.get("user_email"))
        default_image_path = options.get("image")

        # Получим байты изображения одной раз
        if default_image_path:
            try:
                with open(default_image_path, "rb") as fh:
                    raw_image_bytes = fh.read()
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Не удалось прочитать файл {default_image_path}: {e}. "
                    f"Будет использован плейсхолдер 1×1 PNG."
                ))
                raw_image_bytes = get_placeholder_bytes()
        else:
            raw_image_bytes = get_placeholder_bytes()

        # Теги
        tags_map: dict[str, Tag] = {}
        for t in TAGS:
            tag = self._get_or_create_tag(t["name"], t["slug"])
            tags_map[t["slug"]] = tag
        self.stdout.write(self.style.SUCCESS(
            f"Теги готовы: {', '.join([t.name for t in tags_map.values()])}"
        ))

        created, skipped = 0, 0

        for item in RECIPES:
            if Recipe.objects.filter(name=item["name"]).exists():
                skipped += 1
                self.stdout.write(
                    f'— пропуск: рецепт "{item["name"]}" уже существует')
                continue

            recipe = Recipe(
                name=item["name"],
                author=author,
                text=item["text"],
                cooking_time=item["time"],
            )

            # каждому рецепту — новый ContentFile из одних и тех же байтов
            image_name = f'{slugify(item["name"])}.png'
            recipe.image.save(
                image_name, ContentFile(raw_image_bytes), save=False)
            recipe.save()

            # Теги
            recipe.tags.set([tags_map[slug] for slug in item["tags"]])

            # Ингредиенты и связи
            for name, amount, unit in item["components"]:
                ingr = self._get_or_create_ingredient(name, unit)
                RecipeIngredient.objects.create(
                    recipe=recipe, ingredient=ingr, amount=int(amount)
                )

            created += 1
            self.stdout.write(
                self.style.SUCCESS(f'✓ создан рецепт: "{recipe.name}"'))

        self.stdout.write(self.style.SUCCESS(
            f"Готово! Создано: {created}, пропущено (существовали): {skipped}."
        ))
