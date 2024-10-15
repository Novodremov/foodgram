from rest_framework.pagination import PageNumberPagination

from api.constants import (MAX_PAGE_SIZE, PAGE_QUERY_PARAM,
                           PAGE_SIZE_QUERY_PARAM)


class FoodgramPageNumberPagination(PageNumberPagination):
    '''Пагинатор для списка пользователей.'''

    page_size_query_param = PAGE_SIZE_QUERY_PARAM
    page_query_param = PAGE_QUERY_PARAM
    max_page_size = MAX_PAGE_SIZE
