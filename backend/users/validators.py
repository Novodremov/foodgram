import re
from django.core.exceptions import ValidationError


def validate_username(username):
    '''Валидатор допустимости username.'''

    if username:
        regex = r'^[\w.@+-]+\Z'
        if not re.match(regex, username):
            raise ValidationError('Username может содержать только буквы, '
                                  'цифры и следующие символы: .@+-_')
