from rest_framework import serializers
from .models import AuditLog, AuditExport


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'action', 'content_type', 'object_id',
            'object_repr', 'changes', 'ip_address', 'user_agent', 'method',
            'path', 'status_code', 'created_at'
        ]
        read_only_fields = '__all__'


class AuditExportSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = AuditExport
        fields = [
            'id', 'user', 'user_email', 'content_type', 'format', 'filters',
            'row_count', 'file_path', 'created_at'
        ]
        read_only_fields = '__all__'
