from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe, Tag
from rest_framework.filters import SearchFilter


class IngredientSearchFilter(SearchFilter):
    """Фильтр ингридиента."""
    search_param = 'name'


class RecipesFilter(FilterSet):
    """Набор фильтров для рецептов.
    Позволяет фильтровать по:
    - тегам (slug)
    - автору
    - наличию в избранном
    - наличию в корзине покупок
    """
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )
    is_favorited = filters.NumberFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = filters.NumberFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags']

    def get_is_favorited(self, queryset, value, *args, **kwargs):
        """Фильтрует рецепты, находящиеся в избранном у пользователя.
        Args:
            queryset: Исходный queryset рецептов
            value: Флаг фильтрации (1/0)
        Returns:
            Отфильтрованный queryset или исходный,
            если пользователь не аутентифицирован
        """
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, value, *args, **kwargs):
        """Фильтрует рецепты, находящиеся в корзине покупок пользователя.
        Args:
            queryset: Исходный queryset рецептов
            value: Флаг фильтрации (1/0)
        Returns:
            Отфильтрованный queryset или исходный,
            если пользователь не аутентифицирован
        """
        if value and self.request.user.is_authenticated:
            return queryset.filter(
                shopping_cart_recipe__user=self.request.user
            )
        return queryset
