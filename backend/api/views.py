from django.conf import settings
from django.db.models import Count, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from hashids import Hashids
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite, Ingredient, Recipe,
    RecipeIngredient, ShoppingCart, Tag
)
from users.models import Follow, User
from .filters import CustomRecipeFilter, IngredientNameFilter
from .pagination import CustomRecipePaginator
from .permissions import ContentOwnerAccessControl
from .serializers import (
    FavoriteSerializer,
    FollowCreateHandlerSerializer,
    FollowDetailViewSerializer,
    IngredientViewSerializer,
    RecipeDetailSerializer,
    RecipeEditHandlerSerializer,
    ShoppingCartSerializer,
    TagViewSerializer,
    UserProfileViewSerializer,
)


def get_recipe_by_hash(request, short_hash):
    """Редирект по короткому хэшу /s/<hash> → /recipes/<pk>."""
    hashids = Hashids(salt=settings.SECRET_KEY, min_length=3)
    try:
        decoded = hashids.decode(short_hash)
        if not decoded:
            raise ValueError('Invalid hash')
        pk = decoded[0]
        return redirect(f'/recipes/{pk}')
    except (ValueError, IndexError):
        raise Http404('Рецепт не найден')


class UserViewSet(DjoserUserViewSet):
    """Профили/подписки пользователей."""
    queryset = User.objects.all()
    serializer_class = UserProfileViewSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [AllowAny]

    lookup_field = 'id'
    lookup_url_kwarg = 'id'

    @action(detail=False,
            methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        return super().set_password(request)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        queryset = (
            User.objects.filter(followers__follower=request.user)
            .annotate(recipes_count=Count('recipes', distinct=True))
        )
        page = self.paginate_queryset(queryset)
        serializer = FollowDetailViewSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        """POST — подписаться; DELETE — отписаться."""
        lookup_kwarg = self.lookup_url_kwarg or self.lookup_field
        user_id = (
            kwargs.get(lookup_kwarg) or kwargs.get('pk') or kwargs.get('id'))
        author = get_object_or_404(User, **{self.lookup_field: user_id})
        user = request.user

        if request.method == 'POST':
            serializer = FollowCreateHandlerSerializer(
                data={'follower': user.id, 'following': author.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Follow.objects.filter(
            follower=user, following=author).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'patch', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def update_avatar(self, request):
        user = request.user

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Теги."""
    queryset = Tag.objects.all()
    serializer_class = TagViewSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ингредиенты."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientViewSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [IngredientNameFilter]
    search_fields = ['^name']


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепты."""
    queryset = Recipe.objects.all()
    permission_classes = [ContentOwnerAccessControl]
    pagination_class = CustomRecipePaginator
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomRecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeEditHandlerSerializer
        return RecipeDetailSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_short_link']:
            return [AllowAny()]
        return [ContentOwnerAccessControl()]

    @action(detail=True,
            methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self._handle_relation_action(
            request, pk, Favorite, FavoriteSerializer)

    @action(detail=True,
            methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self._handle_relation_action(
            request, pk, ShoppingCart, ShoppingCartSerializer)

    def _handle_relation_action(self, request, pk, model, serializer_class):
        """Общий обработчик для избранного/корзины."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
            serializer = serializer_class(
                data={'user': user.id, 'recipe': recipe.id},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return Response(
                serializer.to_representation(instance),
                status=status.HTTP_201_CREATED,
            )

        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепт не был добавлен'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок (txt)."""
        recipe_ids = ShoppingCart.objects.filter(
            user=request.user
        ).values_list('recipe_id', flat=True)

        ingredients = (
            RecipeIngredient.objects.filter(recipe_id__in=recipe_ids)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        lines = ['Список покупок:\n']
        for item in ingredients:
            lines.append(
                f"{item['ingredient__name']} - "
                f"{item['total_amount']} "
                f"{item['ingredient__measurement_unit']}"
            )

        response = HttpResponse('\n'.join(lines), content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
        return response

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link',
    )
    def get_short_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()
        return Response(
            {'short-link': f'{settings.BASE_URL}/s/{recipe.short_hash}'})
