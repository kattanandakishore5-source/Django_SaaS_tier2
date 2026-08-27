from django.utils import timezone
from datetime import timedelta

from .models import CustomUser, MagicLink, TwoFactorToken, PasswordReset
from apps.core.utils import send_email_async


class AccountServiceError(Exception):
    """Base exception for account service operations."""
    pass


class UserAlreadyExistsError(AccountServiceError):
    pass


class InvalidCredentialsError(AccountServiceError):
    pass


class InvalidTokenError(AccountServiceError):
    pass


class TokenExpiredError(AccountServiceError):
    pass


def create_user_account(email, password, first_name='', last_name=''):
    """
    Create a new user account with the 'viewer' role and dispatch
    a welcome email via the async task queue.

    Raises:
        UserAlreadyExistsError: If the email is already registered.

    Returns:
        CustomUser: The newly created user instance.
    """
    if CustomUser.objects.filter(email=email).exists():
        raise UserAlreadyExistsError('Email already registered')

    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role='viewer',
    )

    send_email_async.delay(
        subject='Welcome to Django Admin Pro!',
        message=f'Thank you for signing up, {first_name}!',
        recipient_list=[email],
        template='welcome',
    )

    return user


def generate_and_send_magic_link(email, base_url):
    """
    Generate a magic-link token for the given email and send it.
    Silently succeeds even if the user does not exist (security best-practice).

    Returns:
        bool: True if a link was sent, False if the user was not found.
    """
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return False

    # Invalidate any existing magic links for this user
    MagicLink.objects.filter(user=user).delete()

    token = MagicLink.generate_token()
    MagicLink.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(hours=24),
    )

    magic_url = f"{base_url}{token}/"
    send_email_async.delay(
        subject='Your Django Admin Pro Magic Link',
        message=f'Click here to login: {magic_url}',
        recipient_list=[email],
        template='magic_link',
    )

    return True


def verify_magic_link_token(token):
    """
    Validate and consume a magic-link token.

    Raises:
        InvalidTokenError: If the token does not exist.
        TokenExpiredError: If the token has already been used or expired.

    Returns:
        CustomUser: The user associated with the magic link.
    """
    try:
        magic_link = MagicLink.objects.get(token=token)
    except MagicLink.DoesNotExist:
        raise InvalidTokenError('Invalid or expired link')

    if not magic_link.is_valid():
        raise TokenExpiredError('Link has expired')

    magic_link.used = True
    magic_link.save()
    return magic_link.user


def create_and_send_2fa_token(user):
    """
    Create a time-limited 2FA token and email it to the user.

    Returns:
        TwoFactorToken: The created token instance.
    """
    token = TwoFactorToken.objects.create(
        user=user,
        token=TwoFactorToken.generate_token(),
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    send_email_async.delay(
        subject='Your 2FA Code',
        message=f'Your 2FA code is: {token.token}',
        recipient_list=[user.email],
    )

    return token


def verify_2fa_token(user, token_value):
    """
    Validate and consume a 2FA OTP token.

    Raises:
        InvalidTokenError: If the token does not exist.
        TokenExpiredError: If the token has already been used or expired.

    Returns:
        TwoFactorToken: The consumed token instance.
    """
    try:
        otp = TwoFactorToken.objects.get(user=user, token=token_value)
    except TwoFactorToken.DoesNotExist:
        raise InvalidTokenError('Invalid 2FA code')

    if not otp.is_valid():
        raise TokenExpiredError('Code has expired')

    otp.used = True
    otp.save()
    return otp


def initiate_password_reset(email, base_url):
    """
    Create a password-reset token and email the reset link.
    Silently succeeds even if the user does not exist (security best-practice).

    Returns:
        bool: True if a reset link was sent, False if user was not found.
    """
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return False

    PasswordReset.objects.filter(user=user).delete()

    token = PasswordReset.generate_token()
    PasswordReset.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(hours=24),
    )

    reset_url = f"{base_url}{token}/"
    send_email_async.delay(
        subject='Reset Your Password',
        message=f'Click here to reset: {reset_url}',
        recipient_list=[email],
    )

    return True


def reset_password_with_token(token, new_password):
    """
    Validate a password-reset token and set the user's new password.

    Raises:
        InvalidTokenError: If the token does not exist.
        TokenExpiredError: If the token has already been used or expired.

    Returns:
        CustomUser: The user whose password was reset.
    """
    try:
        reset = PasswordReset.objects.get(token=token)
    except PasswordReset.DoesNotExist:
        raise InvalidTokenError('Invalid or expired link')

    if not reset.is_valid():
        raise TokenExpiredError('Link has expired')

    reset.used = True
    reset.save()

    user = reset.user
    user.set_password(new_password)
    user.save()
    return user
