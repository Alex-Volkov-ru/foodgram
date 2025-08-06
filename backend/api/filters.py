from django.db.models import Q
from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe, Tag
from rest_framework.filters import SearchFilter


class IngredientNameFilter(SearchFilter):
    """Фильтр поиска ингредиентов по совпадению в названии"""

    def __init__(self):
        super().__init__()
        self.search_param = 'name'

    def filter_queryset(self, request, queryset, view):
        search_terms = self.get_search_terms(request)
        if not search_terms:
            return queryset

        queries = []
        for term in search_terms:
            queries.append(Q(name__istartswith=term))

        query = queries.pop()
        for item in queries:
            query |= item

        return queryset.filter(query).distinct()


class CustomRecipeFilter(FilterSet):
    """Набор фильтров для рецептов с возможностью:
    - фильтрации по тегам
    - поиска по автору
    - выборки избранных рецептов
    - выборки рецептов в списке покупок
    """

    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        label='Список тегов для фильтрации'
    )

    author_id = filters.NumberFilter(
        field_name='author__id',
        label='Идентификатор автора рецепта'
    )

    is_in_favorites = filters.BooleanFilter(
        method='filter_by_favorites',
        label='Показать только избранные рецепты'
    )

    is_in_shopping_list = filters.BooleanFilter(
        method='filter_by_shopping_list',
        label='Показать рецепты в списке покупок'
    )

    class Meta:
        model = Recipe
        fields = ['tags', 'author_id']

    def filter_by_favorites(self, queryset, name, value):
        """Отфильтровать рецепты по наличию в избранном"""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorite_recipes__user=user)
        return queryset

    def filter_by_shopping_list(self, queryset, name, value):
        """Отфильтровать рецепты по наличию в списке покупок"""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart_recipes__user=user)
        return queryset
