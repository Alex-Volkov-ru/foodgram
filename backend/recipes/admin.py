from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from foodgram.constants import BASIC_MIN_VALUE

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeIngredientInline(admin.TabularInline):
    """Встроенная админка для связи рецепт-ингредиент"""
    model = RecipeIngredient
    extra = 1
    min_num = BASIC_MIN_VALUE
    verbose_name = _('Ингредиент рецепта')
    verbose_name_plural = _('Ингредиенты рецепта')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Администрирование тегов"""
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    list_editable = ('name', 'slug')
    ordering = ('id',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Администрирование ингредиентов"""
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    list_editable = ('name', 'measurement_unit')
    ordering = ('id',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Администрирование рецептов"""
    list_display = (
        'id', 'name', 'author', 'cooking_time',
        'favorites_count', 'shopping_carts_count',
        'ingredients_count', 'pub_date', 'image_preview'
    )
    list_filter = ('tags', 'author')
    search_fields = (
        'name', 'author__username',
        'author__email', 'tags__name'
    )
    readonly_fields = (
        'favorites_count', 'shopping_carts_count', 'pub_date', 'image_preview')
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInline,)
    date_hierarchy = 'pub_date'
    ordering = ('-pub_date',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _favorites_count=Count('in_favorites', distinct=True),
            _shopping_carts_count=Count('in_shopping_carts', distinct=True),
            _ingredients_count=Count('ingredients', distinct=True)
        )
        return queryset

    def favorites_count(self, obj):
        return obj._favorites_count
    favorites_count.short_description = _('В избранном')
    favorites_count.admin_order_field = '_favorites_count'

    def shopping_carts_count(self, obj):
        return obj._shopping_carts_count
    shopping_carts_count.short_description = _('В корзинах')
    shopping_carts_count.admin_order_field = '_shopping_carts_count'

    def ingredients_count(self, obj):
        return obj._ingredients_count
    ingredients_count.short_description = _('Ингредиентов')
    ingredients_count.admin_order_field = '_ingredients_count'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image.url)
        return "-"
    image_preview.short_description = _('Превью')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Администрирование избранных рецептов"""
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_filter = ('user', 'recipe')
    raw_id_fields = ('user', 'recipe')
    ordering = ('id',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Администрирование списка покупок"""
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_filter = ('user', 'recipe')
    raw_id_fields = ('user', 'recipe')
    ordering = ('id',)
