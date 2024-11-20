from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from recipes.models import Recipe


def redirect_to_full_recipe(request, short_url):
    """Перенаправление к полному рецепту."""
    recipe = get_object_or_404(Recipe, short_url=short_url)
    full_url = f'/recipes/{recipe.id}'
    return HttpResponseRedirect(full_url)
