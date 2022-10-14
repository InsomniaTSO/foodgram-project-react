from api.permissions import IsOwnerOrReadOnly
from django.shortcuts import get_object_or_404
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST)

from .filters import IngredientsSearchFilter, RecipeFilter
from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .serializers import (CompactRecipeSerializer, IngredientViewSerializer,
                          RecipeCreateSerializer, RecipeViewSerializer,
                          TagViewSerializer)

ALREADY_IN_FAVORITE = 'Вы уже подписаны.'
SELF_FAVORITE = 'Нельзя полписаться на себя.'
ALREADY_IN_CART = 'Вы уже добавили этот рецепт в список покупок.'


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление модели ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientViewSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientsSearchFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление модели тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagViewSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление модели рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeViewSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = RecipeViewSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        serializer = RecipeViewSerializer(
            instance=serializer.instance,
            context={'request': self.request},
        )
        return Response(
            serializer.data, status=HTTP_200_OK
        )

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if user == recipe.author:
                return Response({'detail': SELF_FAVORITE},
                                status=HTTP_200_OK)
            favorite, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe
            )
            if created is True:
                serializer = CompactRecipeSerializer()
                return Response(
                    serializer.to_representation(instance=recipe),
                    status=HTTP_201_CREATED
                )
            return Response({'detail': ALREADY_IN_FAVORITE},
                            status=HTTP_200_OK)
        if request.method == 'DELETE':
            Favorite.objects.filter(
                user=user,
                recipe=recipe
            ).delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            cart, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe
            )
            if created is True:
                serializer = CompactRecipeSerializer()
                return Response(
                    serializer.to_representation(instance=recipe),
                    status=HTTP_201_CREATED
                )
            return Response(
                {'detail': ALREADY_IN_CART},
                status=HTTP_200_OK)
        if request.method == 'DELETE':
            ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST)
