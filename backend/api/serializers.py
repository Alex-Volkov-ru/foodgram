import base64
import uuid

from django.core.files.base import ContentFile
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from users.models import Follow, User


class CompactRecipeViewSerializer(serializers.ModelSerializer):
    """Компактное отображение рецепта"""
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


class FavoriteSerializer(UnionFavoriteShoppingCartSerializer):
    """Добавление рецептов в избранное."""
    class Meta:
        model = Favorite
        fields = ('recipe', 'user')

    def validate(self, data):
        data = super().validate(data)
        if data['user'].favorite_user.filter(recipe=data['recipe']).exists():
            raise ValidationError('Рецепт уже добавлен в избранное.')
        return data


class ShoppingCartSerializer(UnionFavoriteShoppingCartSerializer):
    """Добавление рецептов в корзину."""
    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')

    def validate(self, data):
        data = super().validate(data)
        if data['user'].shopping_cart_user.filter(
                recipe=data['recipe']
        ).exists():
            raise ValidationError('Рецепт уже добавлен в список покупок.')
        return data


class Base64ImageConverter(serializers.ImageField):
    """Конвертер для изображений в формате base64"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr),
                                   name=f'{uuid.uuid4()}.{ext}')
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
    """Полное представление рецепта."""
    id = serializers.ReadOnlyField(source='ingredient.id',)
    name = serializers.ReadOnlyField(source='ingredient.name',)
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
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
            return Follow.objects.filter(
                follower=request.user,  # Было: user=request.user
                following=obj
            ).exists()
        return False


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Полное представление рецепта."""
    author = UserProfileViewSerializer(read_only=True)
    image = Base64ImageConverter()
    ingredients = serializers.SerializerMethodField(read_only=True)
    tags = TagViewSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'text',
                  'is_favorited', 'is_in_shopping_cart', 'author', 'image',
                  'cooking_time', 'name')

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return bool(
            user
            and user.is_authenticated
            and Favorite.objects.filter(user=user, recipe_id=obj.id).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return bool(
            user
            and user.is_authenticated
            and ShoppingCart.objects.filter(
                user=user,
                recipe_id=obj.id
            ).exists()
        )

    def get_ingredients(self, obj):
        return RecipeComponentViewSerializer(
            RecipeIngredient.objects.filter(recipe=obj),
            many=True, allow_null=False
        ).data


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
        fields = ('ingredients', 'tags', 'image', 'name',
                  'text', 'cooking_time', 'id', 'author')

    def validate(self, data):
        """Проверка ингредиентов и тегов на наличие и уникальность."""
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                {'В рецепте должен быть как минимум один ингредиент.'}
            )
        if not tags:
            raise serializers.ValidationError(
                {'В рецепте должен быть как минимум один тег.'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'Ингредиенты не должны повторяться.'}
            )
        if len(ingredients) != len(set([item['id'] for item in ingredients])):
            raise serializers.ValidationError(
                {'Ингредиенты не должны повторяться.'}
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
            ) for ingredient in ingredients])

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
        self.create_ingredients(recipe=recipe,
                                ingredients=ingredients)
        return recipe

    def to_representation(self, instance):
        """Сериализация объекта после обновления/создания."""
        request = self.context.get('request')
        context = {'request': request}
        return RecipeDetailSerializer(instance,
                                      context=context).data


class FollowDetailViewSerializer(UserProfileViewSerializer):
    """Сериализатор для отображения подписок с рецептами."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserProfileViewSerializer.Meta):
        fields = UserProfileViewSerializer.Meta.fields + (
            'recipes_count',
            'recipes'
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed')

    @staticmethod
    def get_recipes_count(obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        context = {'request': request}
        recipe_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipe_limit:
            try:
                recipes = recipes[:int(recipe_limit)]
            except ValueError:
                pass
        serializer = CompactRecipeViewSerializer(
            recipes, context=context, many=True
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
            raise ValidationError('Нельзя подписаться на самого себя')
        if Follow.objects.filter(
                follower=subscriber, following=author).exists():
            raise ValidationError('Подписка уже существует')
        return data

    def validate(self, data):
        return self.verify_subscription(data)

    def to_representation(self, instance):
        request = self.context.get('request')
        return FollowDetailViewSerializer(
            instance.following,
            context={'request': request}
        ).data
