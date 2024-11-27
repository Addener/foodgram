from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone
from sqids import Sqids

NAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 254
NAME_MAX_LENGTH_RECIPES = 256
RECIPES_UNIT_MEASUREMENT_MAX_LENGTH = 64
SHORT_URL_MAX_LENGTH = 20
MIN_VALUE = 1
TAG_SLUG_MAX_LENGTH = 32
TAG_NAME_MAX_LENGTH = 32
INGREDIENT_NAME_MAX_LENGTH = 128

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        'Название тега',
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Уникальный слаг тега',
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True
    )

    class Meta:
        ordering = ('name', 'slug',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        'Название ингредиента', max_length=INGREDIENT_NAME_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        'Единица измерения', max_length=RECIPES_UNIT_MEASUREMENT_MAX_LENGTH
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='nique_name_and_measurement_unit',
            ),
        )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        through_fields=('recipe', 'ingredient'),
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    name = models.CharField(
        'Название рецепта', max_length=NAME_MAX_LENGTH_RECIPES
    )
    pub_date = models.DateTimeField(
        'Дата публикации рецепта', auto_now_add=True
    )
    text = models.TextField(
        'Описание рецепта', help_text='Заполните описание рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        validators=(MinValueValidator(MIN_VALUE),)
    )
    image = models.ImageField(
        'Изображение для рецепта', upload_to='recipes/'
    )

    short_url = models.CharField(
        max_length=SHORT_URL_MAX_LENGTH,
        unique=True,
        db_index=True,
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Создание короткой ссылки."""
        if not self.short_url:
            now = timezone.now()
            keys_for_short_url = [
                round(now.timestamp() * 1000),
                self.author.id,
                self.cooking_time
            ]
            sqids = Sqids()
            code = sqids.encode(keys_for_short_url)
            self.short_url = code
        return super(Recipe, self).save(*args, **kwargs)


class IngredientRecipe(models.Model):
    """Модель для связи рецепта и ингредиентов в нем."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингридиентов',
        validators=(MinValueValidator(MIN_VALUE),)
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return self.ingredient


class FavouriteAndShoppingList(models.Model):
    """Общая структура для моделей 'Избранное' и 'Список покупок'."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Favourite(FavouriteAndShoppingList):
    """Модель избранного."""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'
        constraints = (
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_and_recipe_in_Favourites',
            ),
        )

    def __str__(self):
        return f'Рецепт {self.recipe} в избранном у {self.user.username}'


class ShoppingList(FavouriteAndShoppingList):
    """Список списка покупок."""

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        default_related_name = 'shopping_recipe'
        constraints = (
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_and_recipe_in_ShoppingList',
            ),
        )

    def __str__(self):
        return (f'Рецепт {self.recipe} добавлен в список '
                f'покупок {self.user.username}')
