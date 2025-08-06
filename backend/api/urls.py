from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet
from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter

app_name = 'api'

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', TokenCreateView.as_view(), name='token-login'),
    path('auth/token/logout/', TokenDestroyView.as_view(),
         name='token-logout'),
    path('users/<int:id>/subscribe/',
         UserViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}),
         name='user-subscribe'),
    path('users/subscriptions/',
         UserViewSet.as_view({'get': 'subscriptions'}),
         name='user-subscriptions'),
    path('recipes/<int:pk>/favorite/',
         RecipeViewSet.as_view({'post': 'favorite', 'delete': 'favorite'}),
         name='recipe-favorite'),
    path('recipes/<int:pk>/shopping_cart/',
         RecipeViewSet.as_view(
             {'post': 'shopping_cart', 'delete': 'shopping_cart'}),
         name='recipe-shopping-cart'),
    path('recipes/download_shopping_cart/',
         RecipeViewSet.as_view({'get': 'download_shopping_cart'}),
         name='download-shopping-cart'),
    path('recipes/<int:pk>/get-link/',
         RecipeViewSet.as_view({'get': 'get_short_link'}),
         name='recipe-get-link'),
]
