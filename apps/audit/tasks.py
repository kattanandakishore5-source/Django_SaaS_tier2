from celery import shared_task
from .models import AuditLog
from apps.accounts.models import CustomUser

@shared_task
def log_audit_action_async(user_id, action, method, path, status_code, ip_address, user_agent):
    user = None
    if user_id:
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            pass

    AuditLog.objects.create(
        user=user,
        action=action,
        method=method,
        path=path,
        status_code=status_code,
        ip_address=ip_address,
        user_agent=user_agent,
    )
