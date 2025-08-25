from django.db.models import Q
from django_filters import rest_framework as filters

from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientNameFilter(SearchFilter):
    """Фильтр поиска ингредиентов по совпадению в начале названия."""
    def __init__(self):
        super().__init__()
        self.search_param = 'name'

    def filter_queryset(self, request, queryset, view):
        search_terms = self.get_search_terms(request)
        if not search_terms:
            return queryset

        query = Q()
        for term in search_terms:
            query |= Q(name__istartswith=term)

        return queryset.filter(query).distinct()


class CustomRecipeFilter(filters.FilterSet):
    """
    Фильтры для рецептов:
    - по тегам (slug),
    - по автору (id),
    - только избранные текущего пользователя,
    - только в корзине текущего пользователя.
    """

    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        label='Список тегов для фильтрации',
    )

    author = filters.NumberFilter(
        field_name='author__id',
        label='Идентификатор автора рецепта',
    )

    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        label='Показать только избранные рецепты',
    )

    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        label='Показать рецепты в списке покупок',
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if value and user and user.is_authenticated:

            return queryset.filter(in_favorites__user=user).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if value and user and user.is_authenticated:
            return queryset.filter(in_shopping_carts__user=user).distinct()
        return queryset
