from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShortenedURL, ShoppingCart, Subscription, Tag)
from users.serializers import FoodgramUserSerializer


User = get_user_model()


class IngredientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для GET-запросов ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для извлечения ингредиентов при GET-запросах рецептов."""

    ingredient = IngredientGetSerializer(read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('ingredient',
                  'amount',
                  )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return {
            'id': representation['ingredient']['id'],
            'name': representation['ingredient']['name'],
            'measurement_unit':
                representation['ingredient']['measurement_unit'],
            'amount': representation['amount'],
        }


class IngredientRecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингредиентов в рецепт."""

    id = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id',
                  'amount',
                  )


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
        if user.is_authenticated:
            return Favorite.objects.filter(
                user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=user, recipe=obj).exists()
        return False


class RecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор для POST-запросов с рецептами."""

    ingredients = IngredientRecipePostSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
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

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(
                'Поле изображения не должно быть пустым')
        return image

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Нужно указать ингредиенты.')
        ingredient_ids = []
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.')
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} не существует.')
            ingredient_ids.append(ingredient_id)
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Нужно указать тег/теги.')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return tags

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            amount = ingredient_data['amount']
            IngredientRecipe.objects.create(recipe=recipe,
                                            ingredient=ingredient,
                                            amount=amount)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.get('ingredients', None)
        tags_data = validated_data.get('tags', None)
        if ingredients_data is None:
            raise serializers.ValidationError(
                {'ingredients': 'Это поле обязательно для обновления.'})
        if tags_data is None:
            raise serializers.ValidationError(
                {'tags': 'Это поле обязательно для обновления.'})
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.save()

        instance.ingredients.clear()
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            amount = ingredient_data['amount']
            IngredientRecipe.objects.create(recipe=instance,
                                            ingredient=ingredient,
                                            amount=amount)
        instance.tags.set(tags_data)
        return instance


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
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeSubscribeSerializer(recipes,
                                               many=True,
                                               read_only=True)
        return serializer.data
