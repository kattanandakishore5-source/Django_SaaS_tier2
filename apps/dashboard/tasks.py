from celery import shared_task
from django.utils import timezone
from apps.audit.models import AuditLog
from apps.accounts.models import CustomUser


@shared_task
def generate_daily_report():
    """Generate daily dashboard report"""
    today = timezone.now().date()

    # Get today's statistics
    users_count = CustomUser.objects.filter(is_active=True).count()
    activities_count = AuditLog.objects.filter(created_at__date=today).count()

    report_data = {
        'date': today.isoformat(),
        'users_count': users_count,
        'activities_count': activities_count,
    }

    return f"Generated report for {today}: {report_data}"
