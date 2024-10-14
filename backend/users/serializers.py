from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers


User = get_user_model()


class FoodgramUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password'
        )

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с пользователями."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        follower = self.context.get('request').user
        return follower.is_authenticated and obj.followings.filter(
            follower=follower).exists()


class AvatarPutSerializer(serializers.ModelSerializer):
    '''Сериализатор для установки аватара.'''

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)
