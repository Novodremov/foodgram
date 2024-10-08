from rest_framework.pagination import PageNumberPagination


class FoodgramPageNumberPagination(PageNumberPagination):
    '''Пагинатор для списка пользователей.'''
    page_size_query_param = 'limit'
    page_query_param = 'page'
    max_page_size = 30
