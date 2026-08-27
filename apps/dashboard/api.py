from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import CustomUser
from apps.audit.models import AuditLog


class DashboardViewSet(viewsets.ViewSet):
    """Dashboard API endpoints for metrics and analytics"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dashboard statistics"""
        stats = CustomUser.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            verified=Count('id', filter=Q(is_verified=True))
        )
        total_users = stats['total']
        active_users = stats['active']
        verified_users = stats['verified']

        # Users by role
        users_by_role = CustomUser.objects.values('role').annotate(count=Count('id'))

        # Recent registrations
        thirty_days_ago = timezone.now() - timedelta(days=30)
        registrations_30d = CustomUser.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()

        data = {
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'users_by_role': dict((r['role'], r['count']) for r in users_by_role),
            'registrations_30d': registrations_30d,
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def chart_signups(self, request):
        """Get user signup data by month"""
        months_back = int(request.query_params.get('months', 6))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months_back * 30)

        signups = CustomUser.objects.filter(
            created_at__range=[start_date, end_date]
        ).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')

        labels = [s['date'].strftime('%Y-%m-%d') for s in signups]
        data = [s['count'] for s in signups]

        return Response({
            'labels': labels,
            'data': data,
        })

    @action(detail=False, methods=['get'])
    def chart_activity(self, request):
        """Get activity data (audits) by date"""
        days_back = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days_back)

        activities = AuditLog.objects.filter(
            created_at__range=[start_date, end_date]
        ).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')

        labels = [a['date'].strftime('%Y-%m-%d') for a in activities]
        data = [a['count'] for a in activities]

        return Response({
            'labels': labels,
            'data': data,
        })

    @action(detail=False, methods=['get'])
    def chart_role_distribution(self, request):
        """Get user distribution by role"""
        distribution = CustomUser.objects.values('role').annotate(count=Count('id')).order_by('-count')

        labels = [d['role'].capitalize() for d in distribution]
        data = [d['count'] for d in distribution]

        return Response({
            'labels': labels,
            'data': data,
        })

    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent audit logs"""
        limit = int(request.query_params.get('limit', 10))
        logs = AuditLog.objects.all().order_by('-created_at')[:limit]

        data = [{
            'id': log.id,
            'user': log.user.email if log.user else 'Unknown',
            'action': log.action,
            'content_type': log.content_type,
            'object_id': log.object_id,
            'changes': log.changes,
            'created_at': log.created_at.isoformat(),
        } for log in logs]

        return Response(data)
