import re
from django.core.exceptions import ValidationError

from users.constants import CURRENT_USER_ENDPOINT


def validate_username(username):
    '''Валидатор допустимости username.'''
    if username:
        if username.lower() == CURRENT_USER_ENDPOINT:
            raise ValidationError(
                f'Нельзя выбрать "{username}" в качестве username.')
        regex = r'^[\w.@+-]+\Z'
        if not re.match(regex, username):
            raise ValidationError('Username может содержать только буквы, '
                                  'цифры и следующие символы: .@+-_')
