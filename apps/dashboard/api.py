from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import CustomUser


class DashboardViewSet(viewsets.ViewSet):
    """Dashboard API endpoints for core analytics."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats = CustomUser.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            verified=Count('id', filter=Q(is_verified=True)),
        )

        data = {
            'total_users': stats['total'],
            'active_users': stats['active'],
            'verified_users': stats['verified'],
            'registrations_30d': CustomUser.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def chart_signups(self, request):
        months_back = int(request.query_params.get('months', 6))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months_back * 30)

        signups = CustomUser.objects.filter(
            created_at__range=[start_date, end_date]
        ).annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')

        labels = [signup['date'].strftime('%Y-%m-%d') for signup in signups]
        data = [signup['count'] for signup in signups]

        return Response({'labels': labels, 'data': data})
