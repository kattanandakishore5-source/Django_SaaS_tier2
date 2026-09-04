from django.urls import path

from .views import (
    forgot_password_view,
    login_view,
    logout_view,
    magic_link_request_view,
    magic_link_verify_view,
    password_reset_confirm_view,
    signup_view,
    two_factor_setup_view,
    two_factor_verify_view,
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password_view, name='password_reset_request'),
    path('reset/<str:token>/', password_reset_confirm_view, name='password_reset_token'),
    path('magic-link/request/', magic_link_request_view, name='magic_link_request'),
    path('magic-link/verify/<str:token>/', magic_link_verify_view, name='magic_link_verify'),
    path('2fa/setup/', two_factor_setup_view, name='2fa_setup'),
    path('2fa/verify/', two_factor_verify_view, name='2fa_verify'),
]
