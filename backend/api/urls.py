from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views
from users.views import UserViewSet


app_name = 'api'

router = DefaultRouter()
router.register('recipes',
                views.RecipeViewSet,
                basename='recipes')
router.register('ingredients',
                views.IngredientViewSet,
                basename='ingredients')
router.register('tags',
                views.TagViewSet,
                basename='tags')
router.register('users',
                UserViewSet,
                basename='users')


djoser_urls = [
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path('', include(router.urls)),
    path('', include(djoser_urls)),
]
