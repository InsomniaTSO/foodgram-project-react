from datetime import datetime


from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST)

from api.permissions import IsOwnerOrReadOnly
from api.pagination import LimitPageNumberPagination
from .filters import IngredientsSearchFilter, RecipeFilter
from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag)
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
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление модели рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    permission_classes = (IsOwnerOrReadOnly,)
    pagination_class = LimitPageNumberPagination
    filterset_class = RecipeFilter

    def get_permissions(self):
        """
        Получение разрешения для метода 'create' на
        создание рецепта авторизованным пользователем.
        """
        if self.action == 'create':
            return [(IsAuthenticated())]
        return super().get_permissions()

    def get_serializer_class(self):
        """
        Получение сериализатора просмотра рецепта
        RecipeViewSerializer для для безопасных методов.
        """
        if self.request.method in SAFE_METHODS:
            return RecipeViewSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Получение данных текущего пользоваеля при создании рецепта."""
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Создание рецепта с RecipeCreateSerializer и возвращение
        результата с RecipeViewSerializer.
        """
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
        """
        Редактирование рецепта с RecipeCreateSerializer и
        возвращение результата с RecipeViewSerializer.
        """
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
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """
        Добавление рецепта в избранное методом POST и
        удаление методом DELETE. Если рецепт уже в избранном
        или уже удален возвращает соответствующие сообщения.
        """
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
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
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """
        Добавление рецепта в список покупок методом POST и
        удаление методом DELETE. Если рецепт уже в в списоке
        покупок или уже удален возвращает соответствующие сообщения.
        """
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

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Получает название, единицы измерения и количество ингредиентов
        из рецептов в списке покупок, в полученном результате суммирует
        дублирующиеся ингредиенты по параметру 'amount'. Возвращает txt-файл
        со списком ингредиентов (название, количество, единица измерения).
        """
        user = self.request.user
        if not user.shopping_cart.exists():
            return Response(status=HTTP_400_BAD_REQUEST)
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            ingredient_f=F('ingredient__name'),
            measure_f=F('ingredient__measurement_unit')
        ).annotate(amount_f=Sum('amount'))
        today = datetime.today().strftime('%d-%m-%Y')
        filename = f'{today}_shopping_list.txt'
        shopping_list = f'Список покупок от {today}\n\n'
        for i in ingredients:
            shopping_list += (f'{i["ingredient_f"]}:  '
                              f'{i["amount_f"]} {i["measure_f"]}\n')
        shopping_list += '\nЗагружено из Foodgram'
        response = HttpResponse(
            shopping_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
