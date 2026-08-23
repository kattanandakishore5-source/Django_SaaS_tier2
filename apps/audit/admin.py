from django.contrib import admin
from .models import AuditLog, AuditExport


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'object_repr', 'status_code', 'created_at']
    list_filter = ['action', 'status_code', 'created_at', 'method']
    search_fields = ['user__email', 'object_repr', 'ip_address', 'path']
    readonly_fields = ['created_at', 'changes', 'user_agent']
    date_hierarchy = 'created_at'


@admin.register(AuditExport)
class AuditExportAdmin(admin.ModelAdmin):
    list_display = ['user', 'format', 'row_count', 'created_at']
    list_filter = ['format', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at']
