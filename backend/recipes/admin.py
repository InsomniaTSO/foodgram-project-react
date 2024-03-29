from django.contrib import admin
from django.contrib.admin import display, register

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag, TagRecipe)


@register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Класс тэгов в панели администратора."""
    list_display = ('name', 'color', 'slug',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Класс ингедиентов в панели администратора."""
    list_display = ('name', 'measurement_unit',)
    sortable_by = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Класс рецепта в панели администратора."""
    list_display = ('name', 'text', 'author', 'get_favorite')
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name', 'author',)
    empty_value_display = '-пусто-'

    @display(description='Число добавлений в избранное')
    def get_favorite(self, obj):
        """Получение числа добавлений рецепта в избранное."""
        return obj.in_favorite.count()


@register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    """Класс ингедиентов в рецепте в панели администратора."""
    list_display = (
        'id', 'ingredient', 'amount', 'get_measurement', 'get_recipe'
    )
    readonly_fields = ('get_measurement',)
    list_filter = ('ingredient',)
    ordering = ('ingredient',)
    empty_value_display = '-пусто-'

    @display(description='Единица измерения')
    def get_measurement(self, obj):
        """Получение единиц измерения ингредиента."""
        return obj.ingredient.measurement_unit

    @display(description='Рецепт')
    def get_recipe(self, obj):
        """Получение рецепта для записи модели IngredientRecipe."""
        return f'"{obj.recipe}" -- {obj.recipe.author}'


@register(TagRecipe)
class TagRecipeAdmin(admin.ModelAdmin):
    """Класс тегов в рецепте в панели администратора."""
    list_display = (
        'get_tag', 'get_recipe'
    )
    empty_value_display = '-пусто-'

    @display(description='Тег')
    def get_tag(self, obj):
        """Получение тега для записи модели TagRecipe."""
        return obj.tag

    @display(description='Рецепт')
    def get_recipe(self, obj):
        """Получение рецепта для записи модели TagRecipe."""
        return f'"{obj.recipe}" -- {obj.recipe.author}'


@register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Класс избранных авторов в панели администратора."""
    list_display = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    empty_value_display = '-пусто-'


@register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Класс списка покупок в панели администратора."""
    list_display = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    empty_value_display = '-пусто-'
