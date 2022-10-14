from django.contrib.admin import register, display
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from users.models import User, Subscribe


class CustomUserCreationForm(UserCreationForm):
    """Форма создания пользователя в панели администратора."""
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name',)


class CustomUserChangeForm(UserChangeForm):
    """Форма изменения пользователя в панели администратора."""
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name',)


@register(User)
class UserAdmin(BaseUserAdmin):
    """Класс для панели администратора пользователей."""
    model = User
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = (
        'email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active'
    )
    list_filter = (
        'email', 'username',
    )
    fieldsets = (
        (None, {'fields': (
            'email', 'username', 'first_name', 'last_name', 'password',
        )}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser',)})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name', 'password1',
                'password2', 'is_staff', 'is_active',
            )
        }),
    )
    search_fields = ('email', 'username',)
    ordering = ('email', 'username',)


@register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """Класс для панели администратора подписок."""
    list_display = (
        'get_user', 'get_author'
    )
    empty_value_display = '-пусто-'

    @display(description='Пользователь')
    def get_user(self, obj):
        return obj.user.username

    @display(description='Автор')
    def get_author(self, obj):
        return obj.author.username