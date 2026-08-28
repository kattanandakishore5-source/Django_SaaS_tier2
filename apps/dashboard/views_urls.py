from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('users/', views.dashboard_users, name='dashboard_users'),
    path('settings/', views.dashboard_settings, name='dashboard_settings'),
    path('profile/', views.dashboard_profile, name='dashboard_profile'),
]
