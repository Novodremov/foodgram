from rest_framework.permissions import IsAuthenticatedOrReadOnly


class TagIngredientMixin:
    '''
    Миксин для установки разрешений и удаления пагинации
    для тегов и ингредиентов.
    '''

    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None
