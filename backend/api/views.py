from collections import defaultdict

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly,
                                        SAFE_METHODS)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.mixins import TagIngredientMixin
from api.paginators import FoodgramPageNumberPagination
from api.permissions import IsAuthorOrIsAdminOrReadOnly
from api.serializers import (IngredientGetSerializer,
                             RecipeFavoriteSerializer,
                             RecipeGetSerializer,
                             RecipePostSerializer,
                             RecipeShoppingCartSerializer,
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
        "author").prefetch_related(
        "tags", "ingredients")
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthenticatedOrReadOnly,
                          IsAuthorOrIsAdminOrReadOnly,)
    pagination_class = FoodgramPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipePostSerializer

    def perform_create(self, serializer):
        recipe = serializer.save(author=self.request.user)
        response_serializer = RecipeGetSerializer(
            recipe,
            context={'request': self.request}
        )
        return Response(response_serializer.data,
                        status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        recipe = serializer.save(author=self.request.user)
        response_serializer = RecipeGetSerializer(
            recipe,
            context={'request': self.request}
        )
        return Response(response_serializer.data,
                        status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.perform_create(serializer)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        return self.perform_update(serializer)

    @action(detail=True,
            methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        '''Экшн-метод для добавление/удаления рецептов в избранное.'''

        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = RecipeFavoriteSerializer(recipe)
            try:
                Favorite.objects.create(user=request.user,
                                        recipe=recipe)
                recipe.favorite_count = F('favorite_count') + 1
                recipe.save(update_fields=['favorite_count'])
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"error": "Рецепт уже есть в избранном."},
                    status=status.HTTP_400_BAD_REQUEST)
        favorite = Favorite.objects.filter(user=request.user,
                                           recipe=recipe).first()
        if not favorite:
            return Response({'detail': 'В избранном нет такого рецепта.'},
                            status=status.HTTP_400_BAD_REQUEST)
        favorite.delete()
        recipe.favorite_count = F('favorite_count') - 1
        recipe.save(update_fields=['favorite_count'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        '''Экшн-метод для добавление/удаления рецептов в список покупок.'''

        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = RecipeShoppingCartSerializer(recipe)
            try:
                ShoppingCart.objects.create(user=request.user,
                                            recipe=recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"error": "Рецепт уже есть в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST)
        shopping_cart_recipe = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe).first()
        if not shopping_cart_recipe:
            return Response({'detail': 'В списке покупок нет такого рецепта.'},
                            status=status.HTTP_400_BAD_REQUEST)
        shopping_cart_recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        '''Экшн-метод для загрузки списка покупок ингредиентов.'''

        user = request.user
        shopping_cart_items = ShoppingCart.objects.filter(
            user=user).prefetch_related('recipe__ingredients')
        ingredients = defaultdict(lambda: {'amount': 0, 'unit': None})

        for item in shopping_cart_items:
            recipe = item.recipe
            for ingredient in recipe.ingredients.all():
                ingredient_recipe = IngredientRecipe.objects.get(
                    recipe=recipe,
                    ingredient=ingredient)
                ingredients[ingredient.name]['amount'] += (
                    ingredient_recipe.amount)

                if ingredients[ingredient.name]['unit'] is None:
                    ingredients[ingredient.name]['unit'] = (
                        ingredient.measurement_unit)

        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"')

        for ingredient_name, data in ingredients.items():
            total_amount = data['amount']
            unit = data['unit']
            response.write(f"{ingredient_name} ({unit}) — {total_amount}\n")
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
            original_url = request.build_absolute_uri(
                recipe.get_absolute_url())
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
