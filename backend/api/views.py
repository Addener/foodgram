import io
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.permissions import IsAuthorOrReadOnlyPermission
from api.serializers import (
    CreateRecipeSerializer,
    FavouritesSerializer,
    FollowCreateSerializer,
    FollowSerializer,
    IngredientSerializer,
    ReadRecipeSerializer,
    ShoppingListSerializer,
    TagSerializer,
    UserAvatarSerializer,
)
from recipes.models import (
    Favourite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingList,
    Tag,
)
from users.models import Follow
User = get_user_model()


class FoodgramUserViewSet(UserViewSet):
    """Вьюсет пользователя."""

    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(detail=False,
            methods=('PUT', 'DELETE',),
            url_path='me/avatar',
            permission_classes=(IsAuthenticated,))
    def avatar(self, request):
        """Добавление/удаление аватара."""
        user = self.request.user
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK
            )
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False,
            methods=('GET',),
            url_path='subscriptions',
            url_name='subscriptions')
    def subscriptions(self, request):
        """Просмотр подписок пользователя."""
        queryset = User.objects.filter(follower__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request, 'user': request.user}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=('POST', 'DELETE',),
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        """Подписка на автора."""
        user = request.user

        if request.method == 'POST':
            author = get_object_or_404(User, id=id)  # Fetch author only for POST
            if user == author:
                return Response({'errors': 'Подписаться на себя нельзя!'}, status=status.HTTP_400_BAD_REQUEST)
            follow_data = {'user': user, 'author': author}
            serializer = FollowCreateSerializer(
                data=follow_data,
                context={'request': request, 'user': user}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            author = get_object_or_404(User, id=id) # Fetch author for DELETE
            delete_count, _ = Follow.objects.filter(user=user, author=author).delete()
            if delete_count == 0:
                return Response({'errors': 'Вы уже отписались!'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)


class FoodgramReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Модель 'только для чтения' с настройками."""

    permission_classes = (AllowAny,)
    pagination_class = None


class TagViewSet(FoodgramReadOnlyModelViewSet):
    """Получение конкретного тега или их списка."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(FoodgramReadOnlyModelViewSet):
    """Получение конкретного ингредиента, или списка ингредиентов."""

    permission_classes = (IsAuthorOrReadOnlyPermission,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления рецептами."""

    queryset = Recipe.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnlyPermission,)

    def get_serializer_class(self):
        """Метод вызова определенного сериализатора."""
        if self.action in ('create', 'partial_update'):
            return CreateRecipeSerializer
        return ReadRecipeSerializer

    @action(methods=('GET',), detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        """Получение короткой ссылки рецепта."""
        recipe = self.get_object()
        short_link = request.build_absolute_uri(f'/{recipe.short_url}')
        data = {'short-link': short_link}
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=('POST', 'DELETE',),
            detail=True,
            permission_classes=(IsAuthenticated,),
            url_name='shopping_cart',
            url_path='shopping_cart')
    def add_shopping_item(self, request, pk=None):
        """Добавление/удаление рецепта из покупок."""
        get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.__create_obj_recipes(
                ShoppingListSerializer, request, pk
            )
        return self.__delete_obj_recipes(request, ShoppingList, pk)

    @action(methods=('GET',),
            detail=False,
            permission_classes=(IsAuthenticated,),
            url_path='download_shopping_cart',
            url_name='download_shopping_cart')
    def generate_shopping_list(user):
        """Generates the shopping list as a bytes object."""
        ingredients = IngredientRecipe.objects.filter(
            recipe__shopping_recipe__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount')).order_by('ingredient__name')

        shopping_list_buffer = io.BytesIO()
        for ingredient in ingredients:
            line = f"{ingredient['ingredient__name']} - {ingredient['sum']}
            ({ingredient['ingredient__measurement_unit']})\n".encode('utf-8')
            shopping_list_buffer.write(line)
        shopping_list_buffer.seek(0)
        return shopping_list_buffer


    def download_shopping_list(self, request):
        """Downloads the shopping list."""
        shopping_list_file = self.generate_shopping_list(request.user)
        response = HttpResponse(shopping_list_file, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(methods=('POST', 'DELETE'),
            detail=True,
            permission_classes=(IsAuthenticated,),
            url_path='favorite',
            url_name='favorite')
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.__create_obj_recipes(
                FavouritesSerializer, request, pk
            )
        return self.__delete_obj_recipes(request, Favourites, pk)

    def __create_obj_recipes(self, serializer, request, pk):
        """Добавить."""
        data = {'user': request.user.id, 'recipe': int(pk)}
        serializer_obj = serializer(data=data)
        serializer_obj.is_valid(raise_exception=True)
        serializer_obj.save()
        return Response(serializer_obj.data, status=status.HTTP_201_CREATED)

    def __delete_obj_recipes(self, request, model, pk):
        """Удалить."""
        delete_count, _ = model.objects.filter(
            user=request.user, recipe__id=pk
        ).delete()
        if delete_count == 0:
            return Response({'errors': 'Рецепт уже удален'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
