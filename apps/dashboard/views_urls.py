from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('users/', views.dashboard_users, name='dashboard_users'),
    path('audit/', views.dashboard_audit, name='dashboard_audit'),
    path('settings/', views.dashboard_settings, name='dashboard_settings'),
    path('profile/', views.dashboard_profile, name='dashboard_profile'),
    path('api-keys/', views.dashboard_api_keys, name='dashboard_api_keys'),
]
