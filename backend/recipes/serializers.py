import base64

import webcolors
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.serializers import ReadOnlyField, SerializerMethodField

from api.consatants import (ALREADY_EXIST_ING, ALREADY_EXIST_TAG, NOT_NAMBER,
                            ALREDY_PUBLISHED, COLOR_NAME, EMPTY_INGREDIENTS,
                            EMPTY_TAGS, MAX_AMOUNT, MAX_MESSAGE, MIN_AMOUNT)
from users.models import Subscribe
from users.serializers import CustomUserSerializer
from .models import Ingredient, IngredientRecipe, Recipe, Tag, TagRecipe


class Hex2NameColor(serializers.Field):
    """Сериализатор для цветов в HEX-формате."""
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError(COLOR_NAME)
        return webcolors.hex_to_name(data)


class Base64ImageField(serializers.ImageField):
    """Сериализатор для изображений в формате Base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagViewSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class IngredientViewSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=IngredientRecipe.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра рецептов."""
    is_favorited = SerializerMethodField('is_favorited_recipe')
    is_in_shopping_cart = SerializerMethodField('is_in_shopping_cart_recipe')
    author = CustomUserSerializer(read_only=True)
    tags = TagViewSerializer(many=True, read_only=True)
    ingredients = IngredientRecipeSerializer(source='ingredients_amount',
                                             many=True, read_only=True,)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author',
                  'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time',
                  )

    def is_favorited_recipe(self, obj):
        """Получение boolean значения нахождения рецепта в избранном."""
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.in_favorite.filter(user=user).exists()
        )

    def is_in_shopping_cart_recipe(self, obj):
        """
        Получение boolean значения нахождения рецепта в
        списке покупок.
        """
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.shopping_cart.filter(user=user).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор добавления и редактирования рецептов."""
    image = Base64ImageField(required=False, allow_null=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(source='ingredients_amount',
                                             many=True, read_only=True)
    tags = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author',
                  'ingredients', 'name',
                  'image', 'text', 'cooking_time',
                  )

    def validate(self, data):
        """
        Проверка входящих данных на наличие полей 'ingredients' и 'tags',
        поверка существования тегов и ингредиентов,
        а так же рецепта с таким названием и автором.
        """
        author = self.context.get('request').user
        name = self.initial_data.get('name')
        cooking_time = self.initial_data.get('cooking_time')
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
        if int(cooking_time) < 1 or int(cooking_time) >= 720:
            raise serializers.ValidationError(MAX_MESSAGE)
        recipe = Recipe.objects.filter(name=name, author=author)
        if recipe.exists() and self.context.get('request').method == 'POST':
            raise serializers.ValidationError(ALREDY_PUBLISHED)
        if 'ingredients' not in self.initial_data:
            raise serializers.ValidationError(EMPTY_INGREDIENTS)
        elif 'tags' not in self.initial_data:
            raise serializers.ValidationError(EMPTY_TAGS)
        ingredient_list = []
        tags_list = []
        for ingredient in ingredients:
            get_object_or_404(Ingredient, id=ingredient['id'])
            id = int(ingredient['id'])
            try:
                amount = int(ingredient['amount'])
            except ValueError:
                raise serializers.ValidationError(NOT_NAMBER)
            if id in ingredient_list:
                raise serializers.ValidationError(ALREADY_EXIST_ING)
            if amount > MAX_AMOUNT or amount < MIN_AMOUNT:
                raise serializers.ValidationError(MAX_MESSAGE)
            ingredient_list.append(id)
        for tag in tags:
            get_object_or_404(Tag, id=int(tag))
            if tag in tags_list:
                raise serializers.ValidationError(ALREADY_EXIST_TAG)
            tags_list.append(tag)
        data['ingredients'] = ingredients
        data['tags'] = tags
        data['name'] = name
        data['cooking_time'] = cooking_time
        return data

    def ingredients_and_tags_adding(self, recipe, ingredients, tags):
        """
        Создание записей для моделей IngredientRecipe и TagRecipe для связи
        ингредиентов и тегов с рецептом.
        """
        IngredientRecipe.objects.bulk_create([IngredientRecipe(
            ingredient=get_object_or_404(Ingredient, id=ingredient['id']),
            recipe=recipe,
            amount=ingredient['amount'])
            for ingredient in ingredients])
        TagRecipe.objects.bulk_create([TagRecipe(
            tag=get_object_or_404(Tag, id=int(tag)),
            recipe=recipe)
            for tag in tags])

    def create(self, validated_data):
        """
        Создание рецепта, а затем записей для моделей IngredientRecipe
        и TagRecipe для связи ингредиентов и тегов с рецептом.
        Возвращает рецепт.
        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.ingredients_and_tags_adding(recipe, ingredients, tags)
        return recipe

    def update(self, recipe, validated_data):
        """
        Очищаеет записи IngredientRecipe и TagRecipe для редактиуемого рецепта
        и создает новые на основе входных данных. Обновляет остальные поля
        рецепта.
        """
        recipe.ingredients.clear()
        recipe.tags.clear()
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.ingredients_and_tags_adding(recipe, ingredients, tags)
        return super().update(recipe, validated_data)


class CompactRecipeSerializer(serializers.ModelSerializer):
    """Сокращенный сериализатор рецептов."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""
    id = ReadOnlyField(source='author.id')
    email = ReadOnlyField(source='author.email')
    username = ReadOnlyField(source='author.username')
    first_name = ReadOnlyField(source='author.first_name')
    last_name = ReadOnlyField(source='author.last_name')
    is_subscribed = SerializerMethodField('is_subscribed_user')
    recipes = SerializerMethodField('get_recipes')
    recipes_count = SerializerMethodField('get_recipes_count')

    class Meta:
        model = Subscribe
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def is_subscribed_user(self, obj):
        return True

    def get_recipes(self, obj):
        """
        Возвращет список рецептов автора из подписок.
        Ограничивает количество рецептров в выдаче в соответствии
        со знанением параметра 'recipes_limit' в запросе. Рецепты
        выдаются по времени публикации (последние в начале)
        в сокращенном виде.
        """
        request = self.context.get('request')
        queryset = Recipe.objects.filter(author=obj.author)
        if request is not None:
            limit = request.GET.get('recipes_limit')
            if limit:
                queryset = queryset[:int(limit)]
        return CompactRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        """Возвращет общее количество рецептов автора в подписке."""
        return Recipe.objects.filter(author=obj.author).count()
