from django.contrib import admin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import User, Follow


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'get_followers_count',
        'get_recipes_count'
    )
    list_filter = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    def get_followers_count(self, obj):
        return obj.followed.count()
    get_followers_count.short_description = 'Подписчиков'

    def get_recipes_count(self, obj):
        return obj.recipes.count()
    get_recipes_count.short_description = 'Рецептов'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    list_filter = ('user', 'following')
    search_fields = (
        'user__username',
        'user__email',
        'following__username',
        'following__email'
    )


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
