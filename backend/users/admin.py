from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import TokenProxy

from .models import Follow, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'last_name',
        'first_name',
        'get_followers_count',
        'get_following_count',
        'get_recipes_count'
    )
    search_fields = ('email', 'username', 'last_name', 'first_name')
    list_filter = ('email', 'username')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            followers_count=Count('followers', distinct=True),
            following_count=Count('following_authors', distinct=True),
            recipes_count=Count('recipes', distinct=True)
        )
        return queryset

    def get_followers_count(self, obj):
        return obj.followers_count
    get_followers_count.short_description = _('Подписчики')
    get_followers_count.admin_order_field = 'followers_count'

    def get_following_count(self, obj):
        return obj.following_count
    get_following_count.short_description = _('Подписки')
    get_following_count.admin_order_field = 'following_count'

    def get_recipes_count(self, obj):
        return obj.recipes_count
    get_recipes_count.short_description = _('Рецепты')
    get_recipes_count.admin_order_field = 'recipes_count'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following')
    search_fields = (
        'following__email',
        'following__username',
        'follower__email',
        'follower__username'
    )
    list_filter = ('following', 'follower')
    raw_id_fields = ('follower', 'following')


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
