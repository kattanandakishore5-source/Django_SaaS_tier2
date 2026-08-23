from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, MagicLink, TwoFactorToken, PasswordReset


@shared_task
def send_weekly_digest():
    """Send weekly digest email to all active users"""
    users = CustomUser.objects.filter(is_active=True)
    for user in users:
        send_mail(
            'Your Weekly Django Admin Pro Digest',
            'Check your dashboard for this week\'s activity',
            'noreply@djangoadminpro.com',
            [user.email],
            fail_silently=True,
        )
    return f"Sent digest to {users.count()} users"


@shared_task
def cleanup_expired_sessions():
    """Clean up expired magic links, 2FA tokens, and password resets"""
    now = timezone.now()

    # Delete expired magic links
    expired_magic_links = MagicLink.objects.filter(expires_at__lt=now)
    magic_link_count = expired_magic_links.count()
    expired_magic_links.delete()

    # Delete expired 2FA tokens
    expired_otp = TwoFactorToken.objects.filter(expires_at__lt=now)
    otp_count = expired_otp.count()
    expired_otp.delete()

    # Delete expired password resets
    expired_resets = PasswordReset.objects.filter(expires_at__lt=now)
    reset_count = expired_resets.count()
    expired_resets.delete()

    return f"Cleaned up: {magic_link_count} magic links, {otp_count} OTPs, {reset_count} resets"


@shared_task
def send_verification_email(user_id):
    """Send verification email to user"""
    try:
        user = CustomUser.objects.get(id=user_id)
        send_mail(
            'Verify Your Email',
            f'Welcome {user.first_name}! Verify your email to continue.',
            'noreply@djangoadminpro.com',
            [user.email],
            fail_silently=True,
        )
        return f"Verification email sent to {user.email}"
    except CustomUser.DoesNotExist:
        return "User not found"
