from django.contrib import admin

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, ShortenedURL, Subscription, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1
    verbose_name = 'Ингредиент для рецепта'
    fields = ('ingredient', 'amount',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInline,)
    list_display = ('name', 'author', 'cooking_time', 'pub_date',)
    list_display_links = ('name',)
    fields = ('id', 'name', 'author', 'image', 'text', 'cooking_time', 'tags',
              'favorite_count',)
    readonly_fields = ('id', 'favorite_count',)
    filter_horizontal = ('tags',)
    search_fields = ('author', 'name')
    list_filter = ('tags',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following')


@admin.register(ShortenedURL)
class ShortenedURLAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'short_url')
