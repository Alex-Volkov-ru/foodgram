from api.views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet)
from django.urls import include, path
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('s/<int:pk>/', RedirectView.as_view(url='/api/recipes/%(pk)s/'),
         name='recipe-short-link'),
]
