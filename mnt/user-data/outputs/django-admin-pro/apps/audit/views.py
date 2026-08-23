from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.db.models import Q
from .models import AuditLog, AuditExport
from .serializers import AuditLogSerializer, AuditExportSerializer
import csv
import json


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log endpoints"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = AuditLog.objects.all().order_by('-created_at')

        # Filter by user if specified
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(object_repr__icontains=search) | Q(user__email__icontains=search))

        return queryset

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export audit logs to CSV"""
        queryset = self.get_queryset()[:1000]  # Limit to 1000

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Action', 'Object', 'IP Address', 'Status Code', 'Created At'])

        for log in queryset:
            writer.writerow([
                log.id,
                log.user.email if log.user else 'Unknown',
                log.action,
                log.object_repr,
                log.ip_address,
                log.status_code,
                log.created_at.isoformat(),
            ])

        # Record export
        AuditExport.objects.create(
            user=request.user,
            format='csv',
            row_count=queryset.count(),
        )

        return response

    @action(detail=False, methods=['get'])
    def export_json(self, request):
        """Export audit logs to JSON"""
        queryset = self.get_queryset()[:1000]

        data = AuditLogSerializer(queryset, many=True).data

        response = HttpResponse(json.dumps(data), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.json"'

        # Record export
        AuditExport.objects.create(
            user=request.user,
            format='json',
            row_count=len(data),
        )

        return response


class AuditExportViewSet(viewsets.ReadOnlyModelViewSet):
    """Export history"""
    queryset = AuditExport.objects.all()
    serializer_class = AuditExportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AuditExport.objects.filter(user=self.request.user).order_by('-created_at')
