from sqids import Sqids
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import UniqueConstraint
from django.db import models

NAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 254
NAME_MAX_LENGTH_RECIPES = 256
MAX_LENGTH_RECIPES_UNIT_MEASUREMENT = 64
MAX_LENGTH_SHORT_URL = 20
MIN_VALUE = 1
MAX_LENGTH_TAG_SLUG = 32
MAX_LENGTH_TAG_NAME = 32
NAME_MAX_LENGTH_INGREDIENT = 128

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        'Название тега',
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True
    )
    slug = models.SlugField(
        'Уникальный слаг тега',
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True
    )

    class Meta:
        ordering = ('name', 'slug',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:50]


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        'Название ингредиента', max_length=NAME_MAX_LENGTH_INGREDIENT
    )
    measurement_unit = models.CharField(
        'Единица измерения', max_length=MAX_LENGTH_RECIPES_UNIT_MEASUREMENT
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
        return self.name[:50]

    def clean(self):
        if Ingredient.objects.filter(
            name=self.name,
            measurement_unit=self.measurement_unit
        ).exists():
            raise ValidationError({
                'name': 'Ингредиент с данной единицей измерения существует.'
            })


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
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    name = models.CharField(
        'Название рецепта', max_length=NAME_MAX_LENGTH_RECIPES
    )
    pub_date = models.DateTimeField(
        'Дата публикации рецепта', auto_now_add=True
    )
    text = models.TextField(
        'Описание рецепта', help_text='Заполните описание рецепта'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления в минутах',
        validators=(MinValueValidator(MIN_VALUE),)
    )
    image = models.ImageField(
        'Изображение для рецепта', upload_to='recipes/'
    )

    short_url = models.CharField(
        max_length=MAX_LENGTH_SHORT_URL,
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
        if not self.short_url:
            today = datetime.today()
            keys_for_short_url = [
                round(today.timestamp() * 1000),
                self.author.id,
                self.cooking_time
            ]
            sqids = Sqids()
            code = sqids.encode(keys_for_short_url)
            self.short_url = code
        return super(Recipe, self).save(*args, **kwargs)


class IngredientRecipe(models.Model):
    """Модель для связи рецепта и ингредиентов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество ингридиентов',
        validators=(MinValueValidator(MIN_VALUE),)
    )

    class Meta:
        verbose_name = 'Ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'

    def __str__(self):
        return self.ingredient


class TagRecipe(models.Model):
    """Модель тегов в рецепте."""

    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт', on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tag, verbose_name='Тег', on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Теги'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class FavouritesAndShoppingList(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Favourites(FavouritesAndShoppingList):
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

    def clean(self):
        if Favourites.objects.filter(
            user=self.user,
            recipe=self.recipe
        ).exists():
            raise ValidationError({
                'recipe': 'Рецепт уже в избранном.'
            })


class ShoppingList(FavouritesAndShoppingList):
    """Список покупок."""

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
        return f'Рецепт {self.recipe} в списке покупок {self.user.username}'

    def clean(self):
        if ShoppingList.objects.filter(
            user=self.user,
            recipe=self.recipe
        ).exists():
            raise ValidationError({
                'recipe': 'Рецепт уже в списке покупок.'
            })
