from rest_framework import serializers
from .models import CustomUser, MagicLink, TwoFactorToken, PasswordReset, APIKey


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role', 'avatar',
            'phone_number', 'bio', 'is_verified', 'two_factor_enabled',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified']


class MagicLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = MagicLink
        fields = ['id', 'user', 'created_at', 'expires_at', 'used']
        read_only_fields = ['id', 'created_at', 'expires_at', 'used']


class TwoFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwoFactorToken
        fields = ['id', 'user', 'created_at', 'expires_at', 'used']
        read_only_fields = ['id', 'created_at', 'expires_at', 'used']


class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordReset
        fields = ['id', 'user', 'created_at', 'expires_at', 'used']
        read_only_fields = ['id', 'created_at', 'expires_at', 'used']


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'key', 'created_at', 'last_used', 'is_active']
        read_only_fields = ['id', 'key', 'created_at', 'last_used']
