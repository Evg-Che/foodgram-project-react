from django.contrib import admin

from users.models import Subscription, User

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Класс управления отображением данных пользователя Foodgram."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name'
    )
    search_fields = (
        'email',
        'username'
    )
    list_filter = (
        'first_name',
        'last_name'
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Класс управления отображением данных подписчиков Foodgram."""

    list_display = (
        'user', 'author'
    )
