from random import choices
from string import ascii_letters, digits

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from recipes.constants import (MAX_INGREDIENT_NAME_LENGTH,
                               MAX_RECIPE_NAME_LENGTH, MAX_TAG_NAME_LENGTH,
                               MAX_SLUG_LENGTH, MAX_UNIT_LENGTH,
                               MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT,
                               NUMBER_OF_CHARS_FOR_SHORT_URL,
                               STR_VIEW_LENGTH)


User = get_user_model()


class Ingredient(models.Model):
    '''Модель ингредиента.'''

    name = models.CharField(
        max_length=MAX_INGREDIENT_NAME_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_UNIT_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        # default_related_name = 'ingredients'

    def __str__(self):
        return self.name[:STR_VIEW_LENGTH]


class Tag(models.Model):
    '''Модель тега.'''

    name = models.CharField(
        max_length=MAX_TAG_NAME_LENGTH,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        default_related_name = 'tags'

    def __str__(self):
        return self.slug


class Recipe(models.Model):
    '''Модель рецепта.'''

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipes/',
        null=True,
        blank=True,
        default=None,
        verbose_name='Изображение'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.SmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=(MinValueValidator(MIN_COOKING_TIME),)
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'

    def __str__(self):
        return self.name[:STR_VIEW_LENGTH]

    def get_absolute_url(self):
        return reverse('api:recipes-detail', kwargs={'pk': self.pk})


class IngredientRecipe(models.Model):
    '''Модель, связывающая ингредиенты и рецепты.'''

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='ingredients_for_recipe',
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
    )
    amount = models.SmallIntegerField(
        verbose_name='Количество',
        validators=(MinValueValidator(MIN_INGREDIENT_AMOUNT),)
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient',
            ),
        )
        default_related_name = 'recipe_ingredients'
        verbose_name = 'Ингредиент для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'

    def __str__(self):
        return f'{self.recipe} - {self.ingredient}'


class Favorite(models.Model):
    '''Модель, связывающая пользователя и рецепт (избранное).'''

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='рецепт'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_user_recipe',
            ),
        )
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        default_related_name = 'favorites'

    def __str__(self):
        return f'{self.recipe} в любимых рецептах {self.user}'


class Shopping_cart(models.Model):
    '''Модель, связывающая пользователя и рецепт (списки покупок).'''

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='рецепт'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_user_recipe',
            ),
        )
        verbose_name = 'список покупок'
        verbose_name_plural = 'рецепты в списке покупок'
        default_related_name = 'shopping_cart'

    def __str__(self):
        return f'{self.recipe} в списке покупок у {self.user}'


class Subscription(models.Model):
    '''Модель подписки.'''

    follower = models.ForeignKey(
        User,
        related_name='followers',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        User,
        related_name='followings',
        on_delete=models.CASCADE,
        verbose_name='На кого подписан'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('follower', 'following'),
                name='unique_follower_following'
            )
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'

    def __str__(self):
        return f'Подписка {self.follower} на {self.following}'


class ShortenedURL(models.Model):
    '''Модель короткой ссылки.'''

    original_url = models.URLField(unique=True)
    short_url = models.CharField(max_length=10,
                                 unique=True)
    recipe = models.OneToOneField(Recipe,
                                  on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'короткая ссылка'
        verbose_name_plural = 'короткие ссылки'

    def save(self, *args, **kwargs):
        if not self.short_url:
            self.short_url = self.generate_short_url()
        super().save(*args, **kwargs)

    def generate_short_url(self):
        characters = ascii_letters + digits
        while True:
            short_url = ''.join(choices(characters,
                                        k=NUMBER_OF_CHARS_FOR_SHORT_URL))
            if not ShortenedURL.objects.filter(short_url=short_url).exists():
                return short_url
