from django.contrib.auth.models import AbstractUser
from django.db import models

from users.constants import (MAX_EMAIL_LENGTH, MAX_NAME_LENGTH,
                             MAX_USERNAME_LENGTH, MAX_SURNAME_LENGTH)
from users.validators import validate_username


class FoodgramUser(AbstractUser):
    '''Кастомная модель пользователя.'''

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        verbose_name='Логин',
        # включил валидацию на 'me' в валидатор
        validators=[validate_username],
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        verbose_name='Электронная почта',
    )
    first_name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=MAX_SURNAME_LENGTH,
        verbose_name='Фамилия',
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        default=None
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
