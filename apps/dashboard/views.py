from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from apps.accounts.models import CustomUser
from apps.audit.models import AuditLog


@login_required
def dashboard_home(request):
    """Main dashboard page"""
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def dashboard_users(request):
    """Users management page"""
    users = CustomUser.objects.all()
    context = {
        'users': users,
        'total': users.count(),
    }
    return render(request, 'dashboard/users.html', context)


@login_required
def dashboard_audit(request):
    """Audit logs page"""
    logs = AuditLog.objects.all().order_by('-created_at')
    context = {
        'logs': logs,
    }
    return render(request, 'dashboard/audit.html', context)


@login_required
def dashboard_settings(request):
    """Settings page"""
    return render(request, 'dashboard/settings.html')


@login_required
def dashboard_profile(request):
    """User profile page"""
    return render(request, 'dashboard/profile.html')


@login_required
def dashboard_api_keys(request):
    """API keys management page"""
    return render(request, 'dashboard/api_keys.html')
