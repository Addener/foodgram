from django.contrib import admin

from recipes.models import (Tag, Ingredient, Favourite, Recipe,
                            IngredientRecipe, ShoppingList)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Теги."""

    list_display = ['id', 'name', 'slug']
    list_display_links = ['id', 'name']
    list_filter = ('id', 'name')
    search_fields = ('name',)
    empty_value_display = 'Поле не заполнено'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Ингредиент."""

    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ['id', 'name']
    search_fields = ('id', 'name')
    empty_value_display = 'Поле не заполнено'


class IngredientsInLine(admin.StackedInline):
    """Ингредиент."""

    model = IngredientRecipe
    extra = 1


class TagsInLine(admin.StackedInline):
    """Теги."""

    model = IngredientRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Рецепты."""

    list_display = ['id', 'name', 'author', 'pub_date', 'text']
    list_display_links = ['id', 'name', 'author']
    search_fields = ('name', 'author')
    list_filter = ('author', 'name', 'tags')
    inlines = (IngredientsInLine, TagsInLine)
    empty_value_display = 'Поле не заполнено'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('author') \
                           .prefetch_related('tags', 'ingredients')
        return queryset


class IngredientRecipeAdmin(admin.ModelAdmin):
    """Ингредиенты в рецептах."""

    list_display = ('id', 'recipe', 'ingredient', 'amount',)
    empty_value_display = 'Поле не заполнено'


class TagRecipeAdmin(admin.ModelAdmin):
    """Теги в рецептах."""

    list_display = ('recipe', 'tag',)
    empty_value_display = 'Поле не заполнено'


@admin.register(Favourite)
class FavouriteRecipeAdmin(admin.ModelAdmin):
    """Избранные рецепты."""

    list_display = ['id', 'user', 'recipe']
    list_display_links = ['id', 'user']
    list_filter = ('id', 'user')
    empty_value_display = 'Поле не заполнено'


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    """Список покупок."""

    list_display = ['id', 'user', 'recipe']
    list_display_links = ['id', 'user']
    empty_value_display = 'Поле не заполнено'
