from rest_framework.pagination import PageNumberPagination

from foodgram.constants import PAGE_SIZE


class RecipePagination(PageNumberPagination):
    """Нумерация страниц."""

    page_size = PAGE_SIZE
    page_size_query_param = 'name'
