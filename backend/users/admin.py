from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import FoodgramUser


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',
                    'recipes', 'followings')
    # Следующие 2 строки взял из django.contrib.auth.admin.UserAdmin
    # без изменений. Скажи, если нужно какие-то поля добавить,
    # вроде всего хватает. Ничего не удалял.
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    @admin.display(description='Количество рецептов')
    def recipes(self, obj):
        return obj.recipes.count()

    @admin.display(description='Количество подписчиков')
    def followings(self, obj):
        return obj.followings.count()
