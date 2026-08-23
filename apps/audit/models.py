from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from apps.accounts.models import CustomUser
import json


class AuditLog(models.Model):
    """System-wide audit logging"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('download', 'Download'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('permission_change', 'Permission Changed'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=255, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.object_repr}"


class AuditExport(models.Model):
    """Track data exports"""
    EXPORT_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('pdf', 'PDF'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='exports')
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    format = models.CharField(max_length=10, choices=EXPORT_FORMAT_CHOICES)
    filters = models.JSONField(default=dict, blank=True)
    row_count = models.IntegerField(default=0)
    file_path = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Export {self.id} by {self.user.email}"
