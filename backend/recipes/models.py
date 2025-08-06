from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from hashids import Hashids
from users.models import User

from foodgram.constants import (BASIC_MIN_VALUE, DISH_NAME_LIMIT,
                                ITEM_NAME_LIMIT, LABEL_CHARACTER_LIMIT,
                                MAXIMUM_QUANTITY, MINIMUM_QUANTITY,
                                PREP_TIME_LOWER, PREP_TIME_UPPER)


class RecipeIngredient(models.Model):
    """Связь между рецептом и ингредиентами"""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='ingredient_connections',
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='recipe_uses',
        verbose_name='Ингредиент'
    )

    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                BASIC_MIN_VALUE,
                message=f'Минимальное количество: {MINIMUM_QUANTITY}'
            ),
            MaxValueValidator(
                MAXIMUM_QUANTITY,
                message=f'Максимальное количество: {MAXIMUM_QUANTITY}'
            )
        ],
        verbose_name='Количество'
    )


class Recipe(models.Model):
    """Модель рецептов"""

    name = models.CharField(
        max_length=DISH_NAME_LIMIT,
        verbose_name='Название блюда'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )

    text = models.TextField(
        verbose_name='Описание рецепта'
    )

    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение блюда'
    )

    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                PREP_TIME_LOWER,
                message=f'Минимальное время: {PREP_TIME_LOWER}'
            ),
            MaxValueValidator(
                PREP_TIME_UPPER,
                message=f'Максимальное время: {PREP_TIME_UPPER}'
            )
        ],
        verbose_name='Время приготовления (мин)'
    )

    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        verbose_name='Теги'
    )

    ingredients = models.ManyToManyField(
        'Ingredient',
        through=RecipeIngredient,
        verbose_name='Ингредиенты'
    )

    @property
    def short_hash(self):
        encoder = Hashids(salt=settings.SECRET_KEY, min_length=3)
        return encoder.encode(self.id)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов"""

    name = models.CharField(
        max_length=ITEM_NAME_LIMIT,
        verbose_name='Название ингредиента'
    )

    measurement_unit = models.CharField(
        max_length=ITEM_NAME_LIMIT,
        verbose_name='Единица измерения'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тегов"""

    name = models.CharField(
        unique=True,
        max_length=LABEL_CHARACTER_LIMIT,
        verbose_name='Название тега'
    )

    slug = models.SlugField(
        unique=True,
        max_length=LABEL_CHARACTER_LIMIT,
        verbose_name='Слаг тега'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Favorite(models.Model):
    """Избранные рецепты"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    """Список покупок"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_carts',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'

    def __str__(self):
        return f'{self.user}\'s cart - {self.recipe}'
