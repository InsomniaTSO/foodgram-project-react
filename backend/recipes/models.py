from django.core.validators import MinValueValidator
from django.db import models
from users.models import User

MIN_AMOUNT = 1
MIN_TIME = 1
ZERO_MESSAGE = 'Не может быть нулем.'


class Tag(models.Model):
    """Модель тегов."""
    id = models.AutoField(primary_key=True)

    name = models.CharField('Название тега', max_length=200)

    color = models.CharField('Цвет', max_length=7)

    slug = models.SlugField('Уникальный слаг', max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    id = models.AutoField(primary_key=True)

    name = models.CharField('Название ингредиента', max_length=200)

    measurement_unit = models.CharField('Единицы измерения', max_length=200)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    id = models.AutoField(primary_key=True)

    name = models.CharField('Название рецепта', max_length=200)

    text = models.CharField('Описание', max_length=200)

    cooking_time = models.IntegerField('Время приготовления (в минутах)',
                                       validators=(MinValueValidator(
                                                   MIN_TIME,
                                                   message=ZERO_MESSAGE),)
                                       )

    image = models.ImageField('Картинка',
                              upload_to='recipe/images/',
                              null=True,
                              default=None)

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )

    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        related_name='recipes',
        verbose_name='Теги'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recipes',
        verbose_name='Автор',
    )

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True)

    REQUIRED_FIELDS = ['_all_']

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Модель количества ингредиентов в рецепте."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='amount',
        verbose_name='Ингредиент в рецепте',
    )

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='amount',
                               verbose_name='Рецепт ингредиента',)

    amount = models.PositiveIntegerField(
        'Количество',
        validators=(MinValueValidator(
                    MIN_AMOUNT,
                    message=ZERO_MESSAGE),)
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class TagRecipe(models.Model):
    """Модель тегов в рецепте."""
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Тэг в рецепте'
        verbose_name_plural = 'Тэги в рецепте'

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_card',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_card',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorite',
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_user_recipe',
            ),
        )
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.recipe} в избранном {self.user}'
