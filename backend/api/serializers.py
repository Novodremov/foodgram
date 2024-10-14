from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Ingredient, IngredientRecipe, Recipe,
                            ShortenedURL, Subscription, Tag)
from users.serializers import FoodgramUserSerializer


User = get_user_model()


class IngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для GET-запросов ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для извлечения ингредиентов при GET-запросах рецептов."""

    id = serializers.IntegerField(
        source='ingredient.id', read_only=True)
    name = serializers.CharField(
        source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientRecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт."""

    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id',
                  'amount',
                  )

    def validate_id(self, id):
        if not Ingredient.objects.filter(id=id).exists():
            raise serializers.ValidationError(
                f'Ингредиент с id {id} не существует.')
        return id


class TagGetSerializer(serializers.ModelSerializer):
    """Сериализатор для GET-запросов тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для GET-запросов с рецептами."""

    author = FoodgramUserSerializer(read_only=True)
    ingredients = IngredientRecipeGetSerializer(many=True,
                                                source='recipe_ingredients',
                                                read_only=True)
    tags = TagGetSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'name',
                  'image',
                  'text',
                  'cooking_time',
                  )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and obj.favorites.filter(
            user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return user.is_authenticated and obj.shopping_carts.filter(
            user=user).exists()


class RecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор для POST-запросов с рецептами."""

    ingredients = IngredientRecipePostSerializer(many=True,
                                                 required=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all(),
                                              required=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients',
                  'tags',
                  'name',
                  'image',
                  'text',
                  'cooking_time',
                  )

    def validate(self, data):
        ingredients = data.get('ingredients')
        if ingredients is None:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно.'})
        if not ingredients:
            raise serializers.ValidationError('Нужно указать ингредиенты.')
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')

        tags = data.get('tags')
        if tags is None:
            raise serializers.ValidationError(
                {'tags': 'Это поле обязательно.'})
        if not tags:
            raise serializers.ValidationError('Нужно указать тег/теги.')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return data

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(
                'Поле изображения не должно быть пустым')
        return image

    def add_ingredients_and_tags(self, recipe, ingredients_data, tags_data):
        '''Добавление в рецепт ингредиентов и тегов.'''
        ingredient_recipe_objs = [
            IngredientRecipe(recipe=recipe,
                             ingredient=Ingredient.objects.get(
                                 id=ingredient_data['id']),
                             amount=ingredient_data['amount']
                             ) for ingredient_data in ingredients_data
        ]
        IngredientRecipe.objects.bulk_create(ingredient_recipe_objs)
        recipe.tags.set(tags_data)
        return recipe

    def create(self, validated_data):
        # validated_data['author'] = self.context.get('request').user
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        return self.add_ingredients_and_tags(
            recipe, ingredients_data, tags_data)

    def update(self, instance, validated_data):
        # validated_data['author'] = self.context.get('request').user
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        super().update(instance, validated_data)
        instance.ingredients.clear()
        return self.add_ingredients_and_tags(
            instance, ingredients_data, tags_data)


class RecipeSubscribeSerializer(serializers.ModelSerializer):
    '''Сериализатор для представления рецептов в подписках.'''

    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeFavoriteSerializer(RecipeSubscribeSerializer):
    '''Сериализатор для представления рецептов в избранном.'''


class RecipeShoppingCartSerializer(RecipeSubscribeSerializer):
    '''Сериализатор для представления рецептов в списке покупок.'''


class ShortenedURLSerializer(serializers.ModelSerializer):
    '''Сериализатор для предоставления коротких ссылок на рецепты.'''

    short_url = serializers.SerializerMethodField()

    class Meta:
        model = ShortenedURL
        fields = ('short_url',)

    def get_short_url(self, obj):
        return self.context['request'].build_absolute_uri(
            f"/s/{obj.short_url}/")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return {
            'short-link': representation['short_url'],
        }


class SubscribeUserSerializer(FoodgramUserSerializer):
    """Сериализатор для работы с подписками."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = FoodgramUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )
        read_only_fields = fields

    def validate(self, data):
        follower = self.context['request'].user
        following = self.instance
        if follower == following:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя.")
        if Subscription.objects.filter(
                follower=follower, following=following).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя.")
        return data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()
        if limit := request.query_params.get('recipes_limit'):
            try:
                limit = int(limit)
                if limit <= 0:
                    raise ValueError(
                        'recipes_limit должен быть положительным числом')
                recipes = recipes[:limit]
            except ValueError:
                raise serializers.ValidationError(
                    'recipes_limit должен быть числом')
        serializer = RecipeSubscribeSerializer(recipes,
                                               many=True,
                                               read_only=True,
                                               context=self.context)
        return serializer.data
