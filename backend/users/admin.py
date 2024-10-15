from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import FoodgramUser


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',
                    'recipes', 'followings')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    @admin.display(description='Количество рецептов')
    def recipes(self, obj):
        return obj.recipes.count()

    @admin.display(description='Количество подписчиков')
    def followings(self, obj):
        return obj.followings.count()
