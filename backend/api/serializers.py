from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    SerializerMethodField
)

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingList,
    Tag
)
from users.models import Subscription, User


class TagSerializer(ModelSerializer):
    """Cериализатор тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    """Cериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(ModelSerializer):
    """Сериализатор списка ингредиентов с количеством для рецепта."""

    id = ReadOnlyField(
        source='ingredient.id'
    )
    name = ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class CreateIngredientSerializer(ModelSerializer):
    """Сериализатор создания списка ингредиентов с количеством для рецепта."""
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'amount'
        )


class RecipeMinifiedSerializer(ModelSerializer):
    """Упрощенный сериализатор рецептов."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class CustomUserCreateSerializer(UserCreateSerializer):
    """Cериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class CustomUserSerializer(UserSerializer):
    """Cериализатор пользователя."""

    is_subscribed = SerializerMethodField(
        read_only=True
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    lookup_field = 'username'

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and Subscription.objects.filter(
                    user=user, author=obj.id).exists())


class SubscriptionSerializer(ModelSerializer):
    """Cериализатор подписчиков."""

    id = ReadOnlyField(
        source='author.id'
    )
    username = ReadOnlyField(
        source='author.username'
    )
    first_name = ReadOnlyField(
        source='author.first_name'
    )
    last_name = ReadOnlyField(
        source='author.last_name'
    )
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()
    is_subscribed = SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            queryset = obj.author.recipes.all()[:int(recipes_limit)]
        else:
            queryset = obj.author.recipes.all()
        return RecipeMinifiedSerializer(
            queryset,
            many=True
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and Subscription.objects.filter(
                    user=user, author=obj.id).exists())


class GetRecipeListSerializer(ModelSerializer):
    """Cериализатор чтения рецептов."""

    author = CustomUserSerializer(
        read_only=True
    )
    tags = TagSerializer(
        read_only=True,
        many=True
    )
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe_ingredient'
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        )
        read_only_fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_ingredients(self, obj):
        ingredients = IngredientInRecipe.objects.filter(
            recipe=obj
        )
        return IngredientInRecipeSerializer(
            ingredients,
            many=True
        ).data

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and obj.shopping_list.filter(user=user).exists())

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and obj.favorites.filter(user=user).exists())


class CreateRecipeSerializer(ModelSerializer):
    """Сериализатор создания, изменения и удаления рецептов."""

    tags = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = CreateIngredientSerializer(
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'tags',
            'ingredients',
            'text',
            'image',
            'cooking_time'
        )

    def create_tags(self, tags, recipe):
        recipe.tags.add(*tags)

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientInRecipe.objects.get_or_create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

    @transaction.atomic
    def create(self, validated_data):
        ingredients_list = validated_data.pop('ingredients')
        tags_list = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients_list, recipe)
        self.create_tags(tags_list, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.ingredients.clear()
        tags_list = validated_data.pop('tags')
        ingredients_list = validated_data.pop('ingredients')
        instance.tags.set(tags_list)
        self.create_ingredients(ingredients_list, instance)
        self.create_tags(tags_list, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return GetRecipeListSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(ModelSerializer):
    """Сериализатор для добавления и удаления рецептов в списке избранного."""

    class Meta:
        model = Favorite
        fields = (
            'user',
            'recipe'
        )

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingListSerializer(ModelSerializer):
    """Сериалайзер для добавления и удаления рецептов в списке покупок."""

    class Meta:
        model = ShoppingList
        fields = (
            'user',
            'recipe'
        )

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
