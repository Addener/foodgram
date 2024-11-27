from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from users.models import Follow, FoodgramUser


admin.site.unregister(Group)


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    """Создание объекта пользователя в админ панели."""

    list_display = [
        'username', 'email', 'first_name', 'last_name'
    ]
    list_display_links = ['username', 'email']
    list_filter = ('email', 'username', 'first_name', 'last_name')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    empty_value_display = 'Поле не заполнено'


@admin.register(Follow)
class SubscriptionAdmin(admin.ModelAdmin):
    """Создание объекта подписки в админ панели."""

    list_display = ['id', 'user', 'author']
    list_display_links = ['id', 'user']
    search_fields = ('user', 'author')
    empty_value_display = 'Поле не заполнено'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user', 'author')
        return queryset
