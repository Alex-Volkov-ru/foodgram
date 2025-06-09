from django.contrib import admin

from foodgram.constants import MIN_VALUE

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class BaseRecipeTabularInLine(admin.TabularInline):
    min_num = MIN_VALUE


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientInLine(BaseRecipeTabularInLine):
    model = RecipeIngredient
    min_num = MIN_VALUE
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInLine,)
    list_display = (
        'name', 'author', 'get_favorites_count',
        'cooking_time', 'pub_date'
    )
    list_filter = ('tags', 'author', 'name')
    search_fields = ('name', 'author__username', 'tags__name')
    readonly_fields = ('get_favorites_count',)

    def get_favorites_count(self, obj):
        return obj.favorite_recipe.count()
    get_favorites_count.short_description = 'Добавлений в избранное'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = list_display


@admin.register(Favorite)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = list_display
