from django.urls import path

from .views import (
    forgot_password_view,
    login_view,
    logout_view,
    password_reset_confirm_view,
    signup_view,
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password_view, name='password_reset_request'),
    path('reset/<str:token>/', password_reset_confirm_view, name='password_reset_token'),
]
