from colorfield.fields import ColorField
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from hashids import Hashids

from foodgram.constants import (AMOUNT_MAX, AMOUNT_MIN, COOKING_MAX_TIME,
                                COOKING_MIN_TIME, INGREDIENT_MAX_LENGHT,
                                RECIPE_NAME_MAX_LENGHT, TAG_MAX_LENGHT)
from users.models import CustomUser


class Tag(models.Model):
    """Теги."""

    name = models.CharField(
        unique=True,
        max_length=TAG_MAX_LENGHT,
        verbose_name='Название'
    )
    color = ColorField(
        default='#FF0000',
        unique=False,
        verbose_name='Цвет'
    )
    slug = models.SlugField(
        unique=True,
        max_length=TAG_MAX_LENGHT,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингридиенты."""

    name = models.CharField(
        max_length=INGREDIENT_MAX_LENGHT,
        verbose_name='Наименование'
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MAX_LENGHT,
        verbose_name='Единица измерения'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            ),
        ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Рецепты."""

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        related_name='tags'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        name=False,
        blank=False,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGHT,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes_image/images/',
        null=True,
        default=None,
        verbose_name='Фото блюда'
    )
    text = models.TextField(
        null=False,
        blank=False,
        verbose_name='Описание рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                COOKING_MIN_TIME,
                message=f'Время готовки не может быть ниже {COOKING_MIN_TIME}.'
            ),
            MaxValueValidator(
                COOKING_MAX_TIME,
                message=f'Время готовки не может быть выше {COOKING_MAX_TIME}.'
            )],
        verbose_name='Время приготовления'
    )

    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время публикации'
    )

    @property
    def short_hash(self):
        hashids = Hashids(salt=settings.SECRET_KEY, min_length=3)
        return hashids.encode(self.id)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель для связи рецепт-ингридиент."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='for_recipe',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                COOKING_MIN_TIME,
                message=f'Кол-во не может быть ниже {AMOUNT_MIN}.'
            ),
            MaxValueValidator(
                COOKING_MAX_TIME,
                message=f'Кол-во не может быть выше {AMOUNT_MAX}.')
        ])


class Favorite(models.Model):
    """Избранные рецепты."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorite_user',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique favorite')]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    """Модель КОРЗИНА."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart_user',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart_recipe',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique shopping cart')]

    def __str__(self):
        return f'{self.user} - {self.recipe}'
