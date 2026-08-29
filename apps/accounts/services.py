from datetime import timedelta

from django.utils import timezone

from apps.core.utils import send_email_async
from .models import CustomUser, PasswordReset


class AccountServiceError(Exception):
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
    if CustomUser.objects.filter(email=email).exists():
        raise UserAlreadyExistsError('Email already registered')

    user = CustomUser.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    send_email_async.delay(
        subject='Welcome to Django Starter!',
        message=f'Thank you for signing up, {first_name}!',
        recipient_list=[email],
        template='welcome',
    )
    return user


def initiate_password_reset(email, base_url):
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
