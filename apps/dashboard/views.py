from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.models import CustomUser


@login_required
def dashboard_home(request):
    context = {'user': request.user}
    return render(request, 'dashboard/home.html', context)


@login_required
def dashboard_users(request):
    users = CustomUser.objects.all()
    context = {'users': users, 'total': users.count()}
    return render(request, 'dashboard/users.html', context)


@login_required
def dashboard_settings(request):
    context = {'user': request.user}
    return render(request, 'dashboard/settings.html', context)


@login_required
def dashboard_profile(request):
    context = {'user': request.user}
    return render(request, 'dashboard/profile.html', context)
