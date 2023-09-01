from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import (
    IngredientFilter,
    RecipeFilter
)
from api.mixins import CustomViewSetMixin
from api.pagination import Paginator
from api.permissions import IsAuthorOrAdminOrReadOnly
from api.serializers import (
    CreateRecipeSerializer,
    CustomUserSerializer,
    FavoriteSerializer,
    GetRecipeSerializer,
    IngredientSerializer,
    ShoppingListSerializer,
    SubscriptionSerializer,
    TagSerializer
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


class TagViewSet(CustomViewSetMixin):
    """Класс-вьюсет для модели Tag."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(CustomViewSetMixin):
    """Класс-вьюсет для модели Ingredient."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """Класс-вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = Paginator

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        return serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return GetRecipeSerializer
        return CreateRecipeSerializer

    @action(detail=True, methods=['POST'])
    def shopping_cart(self, request, pk):
        return self._base_add_favorite_shopping_list(
            request,
            pk,
            ShoppingListSerializer
        )

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk):
        get_object_or_404(
            ShoppingList,
            recipe__id=pk,
            user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'])
    def favorite(self, request, pk):
        return self._base_add_favorite_shopping_list(
            request,
            pk,
            FavoriteSerializer
        )

    @favorite.mapping.delete
    def delete_from_favorite(self, request, pk):
        get_object_or_404(
            Favorite,
            recipe=get_object_or_404(Recipe, id=pk),
            user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_list__user=request.user).values(
            'ingredient__name',
            'ingredient__measurement_unit').annotate(amount=Sum('amount'))

        shopping_list_data = [
            f"{ingredient['ingredient__name']} - "
            f"{ingredient['ingredient__measurement_unit']} | "
            f"{ingredient['amount']}"
            for ingredient in ingredients
        ]
        shopping_list_text = '\n'.join(shopping_list_data)

        filename = 'shopping_list.txt'
        headers = {'Content-Disposition': f'attachment; filename={filename}'}
        return HttpResponse(
            shopping_list_text,
            content_type='text/plain; charset=UTF-8',
            headers=headers
        )

    def _base_add_favorite_shopping_list(self,
                                         request,
                                         pk,
                                         serializer_class):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = serializer_class(
            data={'recipe': recipe.id, 'user': request.user.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class CustomUserViewSet(UserViewSet):
    """Класс-вьюсет для модели User."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = Paginator
    lookup_field = 'id'

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            subscriber = Subscription.objects.create(
                user=user,
                author=author
            )
            serializer = SubscriptionSerializer(
                subscriber,
                context={'request': request}
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        subscriber = get_object_or_404(
            Subscription,
            user=user,
            author=author
        )
        subscriber.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'])
    def subscriptions(self, request):
        subscriber = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(subscriber)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)
