from foodgram.constants import PAGE_SIZE
from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    """Нумерация страниц."""

    page_size = PAGE_SIZE
    page_size_query_param = 'name'
