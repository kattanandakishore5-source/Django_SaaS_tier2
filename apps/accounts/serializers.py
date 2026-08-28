from rest_framework import serializers

from .models import CustomUser, PasswordReset


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'avatar',
            'phone_number', 'bio', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified']


class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordReset
        fields = ['id', 'user', 'created_at', 'expires_at', 'used']
        read_only_fields = ['id', 'created_at', 'expires_at', 'used']
