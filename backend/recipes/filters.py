from django_filters import FilterSet, CharFilter
from recipes.models import Recipe, ShoppingCart, Ingredient


class RecipeFilter(FilterSet):
    """Фильтрация рецептов."""
    is_favorited = CharFilter(method='is_favorited_recipe')
    in_shopping_cart = CharFilter(method='is_in_shopping_cart_recipe')

    class Meta:
        model = Recipe
        fields = ('author', 'tags__slug', 'is_favorited', 'in_shopping_cart')

    def is_favorited_recipe(self, queryset, name, value):
        if not value:
            return queryset
        favorites = self.request.user.favorite.all()
        if value == '1' and not self.request.user.is_anonymous:
            return queryset.filter(
                id__in=(favorite.recipe.id for favorite in favorites)
                                )
        elif value == '0' and not self.request.user.is_anonymous:
            return queryset.exclude(
                id__in=(favorite.recipe.id for favorite in favorites)
                                )
        return Recipe.objects.none()

    def is_in_shopping_cart_recipe(self, queryset, name, value):
        if not value:
            return queryset
        user_shoppingcart = (
                ShoppingCart.objects.filter(user=self.request.user)
            )
        if value == '1' and not self.request.user.is_anonymous:
            return queryset.filter(
                pk__in=(recipe.pk for recipe in user_shoppingcart)
                                )
        elif value == '0' and not self.request.user.is_anonymous:
            return queryset.exclude(
                pk__in=(recipe.pk for recipe in user_shoppingcart)
                        )
        return Recipe.objects.none()


class IngredientsSearchFilter(FilterSet):
    """Поиск иенгредиентов."""
    name = CharFilter(method='searching_by_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def searching_by_name(self, queryset, name, value):
        if not value:
            return queryset
        startswith_ingredients = (
            queryset.filter(name__istartswith=value)
        )
        contain__ingredients = queryset.filter(name__icontains=value)
        return (startswith_ingredients | contain__ingredients).distinct()