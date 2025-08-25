import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Follow, User
from foodgram.constants import BASIC_MIN_VALUE, MAXIMUM_QUANTITY


class CompactRecipeViewSerializer(serializers.ModelSerializer):
    """Компактное отображение рецепта."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UnionFavoriteShoppingCartSerializer(serializers.ModelSerializer):
    """
    Универсальный сериализатор для представления рецептов
    в избранном и корзине.
    """
    def to_representation(self, instance):
        if isinstance(instance, Recipe):
            return CompactRecipeViewSerializer(
                instance,
                context=self.context
            ).data
        return CompactRecipeViewSerializer(
            instance.recipe,
            context=self.context
        ).data


class BaseUserRecipeRelationSerializer(UnionFavoriteShoppingCartSerializer):
    """Базовая валидация на дубликаты user–recipe по related_name."""
    related_name: str = ''
    duplicate_error_message: str = 'Дубликат.'

    def validate(self, data):
        data = super().validate(data)
        user = data['user']
        recipe = data['recipe']
        manager = getattr(user, self.related_name)
        if manager.filter(recipe=recipe).exists():
            raise ValidationError(self.duplicate_error_message)
        return data


class FavoriteSerializer(BaseUserRecipeRelationSerializer):
    """Добавление рецептов в избранное."""
    related_name = 'favorites'
    duplicate_error_message = 'Рецепт уже добавлен в избранное.'

    class Meta:
        model = Favorite
        fields = ('recipe', 'user')


class ShoppingCartSerializer(BaseUserRecipeRelationSerializer):
    """Добавление рецептов в корзину."""
    related_name = 'shopping_carts'
    duplicate_error_message = 'Рецепт уже добавлен в список покупок.'

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')


class Base64ImageConverter(serializers.ImageField):
    """Конвертер для изображений в формате base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'{uuid.uuid4()}.{ext}',
                )
            except Exception:
                raise serializers.ValidationError('Некорректное изображение.')
        return super().to_internal_value(data)


class TagViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeComponentViewSerializer(serializers.ModelSerializer):
    """Ингредиент в составе рецепта."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeComponentEditSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления ингредиентов в рецепте.
    Используется для валидации и передачи информации
    об ингредиенте и его количестве.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        allow_null=False
    )
    # Явная валидация количества по константам проекта
    amount = serializers.IntegerField(
        min_value=BASIC_MIN_VALUE,
        max_value=MAXIMUM_QUANTITY
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class UserProfileViewSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных пользователя с проверкой подписки."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageConverter(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Проверяет подписку текущего пользователя на просматриваемого."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.following_authors.filter(
                following=obj
            ).exists()
        return False


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Полное представление рецепта."""
    author = UserProfileViewSerializer(read_only=True)
    image = Base64ImageConverter()
    ingredients = RecipeComponentViewSerializer(
        source='ingredient_connections', many=True, read_only=True
    )
    tags = TagViewSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'text',
            'is_favorited',
            'is_in_shopping_cart',
            'author',
            'image',
            'cooking_time',
            'name',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return user.shopping_carts.filter(recipe=obj).exists()


class RecipeEditHandlerSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления рецепта.
    Обрабатывает вложенные ингредиенты и теги, выполняет валидацию,
    создание и обновление объектов рецепта.
    """
    author = UserProfileViewSerializer(read_only=True)
    image = Base64ImageConverter()
    ingredients = RecipeComponentEditSerializer(
        many=True,
        required=True,
        allow_null=False,
        partial=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        allow_null=False,
        allow_empty=False,
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'id',
            'author',
        )

    def validate(self, data):
        """Проверка ингредиентов и тегов на наличие и уникальность."""
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients':
                 'В рецепте должен быть как минимум один ингредиент.'}
            )
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'В рецепте должен быть как минимум один тег.'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )
        ids = [item['id'] for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )
        return data

    @staticmethod
    def create_ingredients(ingredients, recipe):
        """Создание связей рецепт-ингредиенты."""
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    def create(self, validate_data):
        """Создание рецепта."""
        ingredients = validate_data.pop('ingredients')
        tags = validate_data.pop('tags')
        validate_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validate_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, recipe, validate_data):
        """Обновление рецепта."""
        ingredients = validate_data.pop('ingredients')
        tags = validate_data.pop('tags')
        recipe = super().update(recipe, validate_data)
        recipe.tags.clear()
        recipe.ingredients.clear()
        recipe.tags.set(tags)
        self.create_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    def to_representation(self, instance):
        """Сериализация объекта после обновления/создания."""
        request = self.context.get('request')
        context = {'request': request}
        return RecipeDetailSerializer(instance, context=context).data


class FollowDetailViewSerializer(UserProfileViewSerializer):
    """Сериализатор для отображения подписок с рецептами."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta(UserProfileViewSerializer.Meta):
        fields = UserProfileViewSerializer.Meta.fields + (
            'recipes_count',
            'recipes',
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        context = {'request': request}
        recipe_limit = request.query_params.get(
            'recipes_limit') if request else None
        recipes_qs = obj.recipes.all()
        if recipe_limit:
            try:
                recipes_qs = recipes_qs[:int(recipe_limit)]
            except ValueError:
                pass
        serializer = CompactRecipeViewSerializer(
            recipes_qs, context=context, many=True
        )
        return serializer.data


class FollowCreateHandlerSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписок."""
    class Meta:
        model = Follow
        fields = ('follower', 'following')

    def verify_subscription(self, data):
        subscriber = data['follower']
        author = data['following']
        if subscriber == author:
            raise ValidationError('Нельзя подписаться на самого себя.')
        if Follow.objects.filter(
            follower=subscriber, following=author
        ).exists():
            raise ValidationError('Подписка уже существует.')
        return data

    def validate(self, data):
        return self.verify_subscription(data)

    def to_representation(self, instance):
        request = self.context.get('request')
        return FollowDetailViewSerializer(
            instance.following,
            context={'request': request}
        ).data
