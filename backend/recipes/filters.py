from django.db.models import IntegerField, Value
from django_filters import CharFilter, FilterSet, AllValuesMultipleFilter

from recipes.models import Ingredient, Recipe


class RecipeFilter(FilterSet):
    """Фильтрация рецептов по автору, тегам, избранному и списку покупок."""
    tags = AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    is_favorited = CharFilter(method='is_favorited_recipe')
    is_in_shopping_cart = CharFilter(method='is_in_shopping_cart_recipe')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited',
                  'is_in_shopping_cart')

    def is_favorited_recipe(self, queryset, name, value):
        """
        Фильтрация рецептов нахождению в избранном ее автора.
        Принимает на вход 1 или 0, при других значениях или если
        пользоваетль не авторизован возвращает пустую выдачу.
        """
        favorites = self.request.user.favorite.all()
        if value == '1' and not self.request.user.is_anonymous:
            return queryset.filter(
                id__in=(favorite.recipe.id for favorite in favorites))
        elif value == '0' and not self.request.user.is_anonymous:
            return queryset.exclude(
                id__in=(favorite.recipe.id for favorite in favorites))
        return Recipe.objects.none()

    def is_in_shopping_cart_recipe(self, queryset, name, value):
        """
        Фильтрация рецептов нахождению рецепта в списке покупок.
        Принимает на вход 1 или 0, при других значениях или если
        пользоваетль не авторизован возвращает пустую выдачу.
        """
        shopping_carts = self.request.user.shopping_cart.all()
        if value == '1' and not self.request.user.is_anonymous:
            return queryset.filter(
                id__in=(shopping_cart.recipe.id for shopping_cart
                        in shopping_carts))
        elif value == '0' and not self.request.user.is_anonymous:
            return queryset.exclude(
                id__in=(shopping_cart.recipe.id for shopping_cart
                        in shopping_carts))
        return Recipe.objects.none()


class IngredientsSearchFilter(FilterSet):
    """Поиск ингредиентов по имени."""
    name = CharFilter(method='searching_by_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def searching_by_name(self, queryset, name, value):
        """
        Поиск по имени. Сначала получет все ингредиенты, которые начинаются
        с заданных в поиске символов, затем все ингредиенты содержащие эти
        символы, исключая уже полученные на первом этапе ингредиенты.
        Вадает суммарный результат поиска двух этапов.
        """
        if not value:
            return queryset
        start_with = (
            queryset.filter(name__istartswith=value).annotate(
                order=Value(0, IntegerField())
            )
        )
        contain = (
            queryset.filter(name__icontains=value).exclude(
                pk__in=(ingredient.pk for ingredient in start_with)
            ).annotate(
                order=Value(1, IntegerField())
            )
        )
        return start_with.union(contain).order_by('order')
