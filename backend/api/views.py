from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from hashids import Hashids
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser, Follow

from .filters import IngredientSearchFilter, RecipesFilter
from .pagination import RecipePagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomUserListRetrieveSerializer, FavoriteSerializer,
                          FollowGetSerializer, FollowSerializer,
                          IngredientSerializer, RecipeSerializer,
                          RecipeUpdateSerializer, ShoppingCartSerializer,
                          TagSerializer)


def recipe_redirect(request, short_hash):
    """Редирект на рецепт по короткому hash-id."""
    hashids = Hashids(salt=settings.SECRET_KEY, min_length=3)
    try:
        decoded = hashids.decode(short_hash)
        if not decoded:
            raise ValueError("Invalid hash")
        pk = decoded[0]
        return RedirectView.as_view(url=f'/api/recipes/{pk}/')(request)
    except (ValueError, IndexError):
        return Response(
            {"detail": "Рецепт не найден"},
            status=status.HTTP_404_NOT_FOUND
        )


class CustomUserViewSet(UserViewSet):
    """Вьюсет для пользователей с подписками и аватаром."""

    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = CustomUserListRetrieveSerializer
    pagination_class = LimitOffsetPagination

    @action(
        detail=False,
        methods=['get'],
        url_path='me', url_name='me',
        permission_classes=(IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        """Возвращает данные текущего пользователя."""

        serializer = CustomUserListRetrieveSerializer(
            request.user,
            context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        methods=['post'],
        detail=True
    )
    def subscribe(self, request, **kwargs):
        """Оформить подписку на пользователя."""

        user = request.user
        following_id = self.kwargs.get('id')
        following = get_object_or_404(CustomUser, pk=following_id)
        data = {"user": user.pk, "following": following.pk}
        serializer = FollowSerializer(
            data=data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, **kwargs):
        """Удалить подписку с пользователя."""

        user = request.user
        following_id = self.kwargs.get('id')
        following = get_object_or_404(CustomUser, id=following_id)
        deleted_obj, _ = Follow.objects.filter(
            user=user,
            following=following
        ).delete()
        if not deleted_obj:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        pagination_class=RecipePagination,
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """Список всех подписок пользователя."""
        queryset = CustomUser.objects.filter(follows__user=request.user)
        paggination = self.paginate_queryset(queryset)
        serializer = FollowGetSerializer(
            paggination,
            many=True,
            context={'request': request},)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'patch', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='me-avatar'
    )
    def update_avatar(self, request):
        """Обновить или удалить аватар пользователя."""
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            serializer = CustomUserListRetrieveSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    http_method_names = ['get']


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов с поиском."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов с избранным, корзиной и ссылкой."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipesFilter
    filter_backends = (DjangoFilterBackend,)
    pagination_class = RecipePagination
    http_method_names = ['get', 'post', 'delete', 'patch']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от метода."""
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeUpdateSerializer

    @action(
        detail=False,
        methods=('get',),
        pagination_class=None,
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,),)
    def download_file(self, request):
        """Скачать список покупок."""
        user = request.user
        if not ShoppingCart.objects.filter(user_id=user.id).exists():
            return Response(
                'В корзине нет товаров.', status=status.HTTP_400_BAD_REQUEST)
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart_recipe__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        shopping_list = (
            f'Список покупок пользователя {user.get_full_name()}\n\n'
        )
        shopping_list += '\n'.join([
            f' - {ingredient["ingredient__name"]} '
            f' {ingredient["ingredient__measurement_unit"]}'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += '\n\nFoodgram num1718.'
        filename = f'{user.username}_shopping_cart.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @classmethod
    def add_obj(self, model, request, model_serializer, pk):
        """Добавить рецепт в избранное или корзину."""
        serializer = model_serializer(
            data={"recipe": pk, "user": request.user.pk},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_obj(self, model, user, pk):
        """Удалить рецепт из избранного или корзины."""
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_objects, _ = model.objects.filter(
            user=user,
            recipe=recipe
        ).delete()
        if not deleted_objects:
            return Response({
                'errors': 'Рецепта нет.'
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,),)
    def favorite(self, request, pk=None):
        """Добавить рецепт в избранное."""
        return self.add_obj(model=Favorite,
                            request=request,
                            model_serializer=FavoriteSerializer,
                            pk=pk
                            )

    @favorite.mapping.delete
    def favourite_delete(self, request, pk=None):
        """Удалить рецепт из избранного."""
        return self.delete_obj(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,),)
    def shopping_cart(self, request, pk=None):
        """Добавить рецепт в корзину покупок."""
        return self.add_obj(
            model=ShoppingCart,
            request=request,
            model_serializer=ShoppingCartSerializer,
            pk=pk
        )

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        """Удалить рецепт из корзины покупок."""
        return self.delete_obj(ShoppingCart, request.user, pk)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_short_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()
        return Response({
            "short-link": f"{settings.BASE_URL}/s/{recipe.short_hash}"
        })
