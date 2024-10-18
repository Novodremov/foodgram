import tempfile

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,
                                        SAFE_METHODS)
from rest_framework.response import Response

from api.constants import SIZE_OF_PREFIX
from api.filters import IngredientFilter, RecipeFilter
from api.mixins import TagIngredientMixin
from api.paginators import FoodgramPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (IngredientGetSerializer,
                             RecipeGetSerializer,
                             RecipePostSerializer,
                             RecipeFavoritePostSerializer,
                             RecipeShoppingCartPostSerializer,
                             ShortenedURLSerializer,
                             TagGetSerializer,)
from recipes.models import (Ingredient, IngredientRecipe, Favorite, Recipe,
                            ShoppingCart, ShortenedURL, Tag)


User = get_user_model()


class IngredientViewSet(TagIngredientMixin, viewsets.ReadOnlyModelViewSet):
    """Вьюсет для операций с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientGetSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(TagIngredientMixin, viewsets.ReadOnlyModelViewSet):
    """Вьюсет для операций с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagGetSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для операций с рецептами."""

    queryset = Recipe.objects.select_related(
        "author"
    ).prefetch_related(
        "tags", "ingredients")
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnly,)
    pagination_class = FoodgramPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipePostSerializer

    def create_delete_object_for_recipe(self, request, id, model, serializer):
        '''Общий метод для операций с моделями, связанными с рецептом.'''
        recipe = get_object_or_404(Recipe, id=id)
        if request.method == 'POST':
            serializer = serializer(
                data={'recipe': recipe.id},
                context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subj = model.objects.filter(user=request.user,
                                    recipe=recipe).first()
        if not subj:
            return Response({'detail': 'В избранном нет такого рецепта.'},
                            status=status.HTTP_400_BAD_REQUEST)
        subj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        '''Экшн-метод для добавление/удаления рецептов в избранное.'''
        return self.create_delete_object_for_recipe(
            request, pk, Favorite, RecipeFavoritePostSerializer)

    @action(detail=True,
            methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        '''Экшн-метод для добавление/удаления рецептов в список покупок.'''
        return self.create_delete_object_for_recipe(
            request, pk, ShoppingCart, RecipeShoppingCartPostSerializer)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        '''Экшн-метод для загрузки списка покупок ингредиентов.'''
        user = request.user
        ingredients = (
            IngredientRecipe.objects.filter(
                recipe__shopping_carts__user=user
            )
            .values(
                'ingredient__name',
                'ingredient__measurement_unit'
            )
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        return self.writing_data(ingredients)

    def writing_data(self, ingredients):
        '''Создание файла со списком покупок.'''
        with tempfile.NamedTemporaryFile(
            delete=False, suffix='.txt'
        ) as tmp_file:
            for item in ingredients:
                ingredient_name = item['ingredient__name']
                total_amount = item['amount']
                unit = item['ingredient__measurement_unit']
                tmp_file.write(
                    f"{ingredient_name} ({unit}) — {total_amount}\n".encode(
                        'utf-8'))
            tmp_file_path = tmp_file.name
        response = FileResponse(open(tmp_file_path, 'rb'),
                                content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"')
        return response

    @action(detail=True,
            methods=['get'],
            url_path='get-link',
            permission_classes=(IsAuthenticatedOrReadOnly,))
    def get_link(self, request, pk=None):
        '''Экшн-метод для создания коротких ссылок на рецепты.'''
        recipe = self.get_object()
        shortened_url = ShortenedURL.objects.filter(recipe=recipe).first()
        if not shortened_url:
            original_url = request.META.get('HTTP_REFERER')
            if not original_url:
                original_url = request.build_absolute_uri(
                    recipe.get_absolute_url()[SIZE_OF_PREFIX:])
            shortened_url = ShortenedURL(original_url=original_url,
                                         recipe=recipe)
            shortened_url.save()

        serializer = ShortenedURLSerializer(shortened_url,
                                            context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


def redirect_from_short_url(request, short_url):
    '''Вью-функция для перенаправления с коротких ссылок на рецепты.'''
    shortened_url_instance = get_object_or_404(ShortenedURL,
                                               short_url=short_url)
    return redirect(shortened_url_instance.original_url)
