from rest_framework.pagination import PageNumberPagination

from foodgram.constants import RECIPE_PAGINATION


class CustomRecipePaginator(PageNumberPagination):
    """Нумерация страниц."""

    page_size = RECIPE_PAGINATION
    page_size_query_param = 'name'
