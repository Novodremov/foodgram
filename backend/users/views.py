from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from api.paginators import FoodgramPageNumberPagination
from api.serializers import SubscribeUserSerializer
from recipes.models import Subscription
from users.serializers import AvatarPutSerializer


User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для управления пользователями и авторизацией."""

    pagination_class = FoodgramPageNumberPagination
    permission_classes = (AllowAny,)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        '''Экшн-метод для добавления/удаления подписок на пользователей.'''

        id = self.kwargs.get('id')
        follower = request.user
        following = get_object_or_404(User, id=id)
        if request.method == 'POST':
            serializer = SubscribeUserSerializer(following,
                                                 data=request.data,
                                                 context={'request': request})
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(follower=follower,
                                        following=following)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = Subscription.objects.filter(follower=follower,
                                                   following=following).first()
        if not subscription:
            return Response({'detail': 'Подписка не найдена.'},
                            status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get'])
    def subscriptions(self, request):
        '''Экшн-метод для получения списка подписок.'''

        followings = User.objects.filter(followings__follower=request.user)
        page = self.paginate_queryset(followings)
        serializer = SubscribeUserSerializer(page,
                                             many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=False,
            methods=['put', 'delete'],
            url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        '''Экшн-метод для добавления/удаления аватара.'''

        user = request.user
        if request.method == 'PUT':
            if not request.data or 'avatar' not in request.data:
                return Response({'error': 'Поле "avatar" обязательно.'},
                                status=status.HTTP_400_BAD_REQUEST)
            serializer = AvatarPutSerializer(user,
                                             data=request.data,
                                             partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'avatar': user.avatar.url},
                                status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Аватар не установлен'},
                        status=status.HTTP_404_NOT_FOUND)

    @action(methods=['get'],
            detail=False,
            permission_classes=[IsAuthenticated],
            )
    def me(self, request, *args, **kwargs):
        """Экшн-метод для получения данных о текущем пользователе."""

        return super().me(request, *args, **kwargs)
