from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, MagicLink, TwoFactorToken, PasswordReset, APIKey


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_verified', 'created_at']
    list_filter = ['role', 'is_verified', 'two_factor_enabled', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'avatar', 'phone_number', 'bio')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'is_verified')}),
        ('2FA', {'fields': ('two_factor_enabled', 'two_factor_method')}),
        ('Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'used']
    list_filter = ['used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'expires_at', 'token']


@admin.register(TwoFactorToken)
class TwoFactorTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'used']
    list_filter = ['used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'expires_at']


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'used']
    list_filter = ['used', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'expires_at']


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'is_active', 'created_at', 'last_used']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'name']
    readonly_fields = ['created_at', 'key']
