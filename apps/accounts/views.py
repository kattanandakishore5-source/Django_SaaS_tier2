from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .forms import (
    CustomUserCreationForm,
    EmailAuthenticationForm,
    MagicLinkRequestForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    TwoFactorSetupForm,
    TwoFactorVerifyForm,
)
from .models import CustomUser, PasswordReset
from .serializers import CustomUserSerializer
from .services import (
    InvalidTokenError,
    TokenExpiredError,
    UserAlreadyExistsError,
    create_user_account,
    initiate_magic_link,
    initiate_password_reset,
    reset_password_with_token,
    verify_magic_link_token,
)
from .totp import generate_qr_code_base64, generate_totp_secret, get_totp_uri, verify_totp_code


def get_safe_redirect(request, target_url, default_route='dashboard_home'):
    if target_url and url_has_allowed_host_and_scheme(
        url=target_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target_url
    return reverse(default_route)


def root_redirect(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'is_2fa_enabled', False) and not request.session.get('is_2fa_verified', False):
            return redirect('2fa_verify')
        return redirect('dashboard_home')
    return redirect('login')


def signup_view(request):
    if request.user.is_authenticated and request.session.get('is_2fa_verified', False):
        return redirect('dashboard_home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            request.session['is_2fa_verified'] = True
            messages.success(request, 'Your account has been created successfully.')
            return redirect('dashboard_home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated and request.session.get('is_2fa_verified', False):
        return redirect('dashboard_home')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            next_url = request.POST.get('next') or request.GET.get('next') or reverse('dashboard_home')
            safe_next = get_safe_redirect(request, next_url, 'dashboard_home')

            if user.is_2fa_enabled:
                request.session['pending_2fa_user_id'] = user.id
                request.session['is_2fa_verified'] = False
                request.session['pending_next_url'] = safe_next
                return redirect('2fa_verify')

            login(request, user)
            request.session['is_2fa_verified'] = True
            messages.success(request, 'Successfully signed in.')
            return redirect(safe_next)
    else:
        form = EmailAuthenticationForm(request)

    return render(request, 'registration/login.html', {'form': form})


@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been signed out.')
    return redirect('login')


def forgot_password_view(request):
    if request.user.is_authenticated and request.session.get('is_2fa_verified', False):
        return redirect('dashboard_home')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            base_url = request.build_absolute_uri('/accounts/reset/')
            initiate_password_reset(email, base_url)
            messages.success(request, 'If an account exists for that email, a reset link has been sent.')
            return redirect('password_reset_request')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'registration/forgot_password.html', {'form': form})


def password_reset_confirm_view(request, token):
    if request.user.is_authenticated and request.session.get('is_2fa_verified', False):
        return redirect('dashboard_home')

    try:
        reset = PasswordReset.objects.get(token=token)
    except PasswordReset.DoesNotExist:
        reset = None

    if reset is None or not reset.is_valid():
        return render(request, 'registration/reset_password.html', {'validlink': False})

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            reset_password_with_token(token, form.cleaned_data['new_password1'])
            messages.success(request, 'Your password has been reset successfully. Please sign in.')
            return redirect('login')
    else:
        form = PasswordResetConfirmForm()

    return render(request, 'registration/reset_password.html', {'form': form, 'validlink': True})


def magic_link_request_view(request):
    if request.user.is_authenticated and request.session.get('is_2fa_verified', False):
        return redirect('dashboard_home')

    if request.method == 'POST':
        form = MagicLinkRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            base_url = request.build_absolute_uri('/accounts/magic-link/verify/')
            initiate_magic_link(email, base_url)
            messages.success(request, 'If an account exists for that email, a magic login link has been sent.')
            return render(request, 'registration/magic_link_request.html', {'form': form, 'submitted': True})
    else:
        form = MagicLinkRequestForm()

    return render(request, 'registration/magic_link_request.html', {'form': form, 'submitted': False})


def magic_link_verify_view(request, token):
    raw_next = request.GET.get('next')
    safe_next = get_safe_redirect(request, raw_next, 'dashboard_home')

    try:
        user = verify_magic_link_token(token)
    except (InvalidTokenError, TokenExpiredError) as exc:
        messages.error(request, str(exc))
        return render(request, 'registration/magic_link_verify_failed.html', {'error': str(exc)})

    if user.is_2fa_enabled:
        request.session['pending_2fa_user_id'] = user.id
        request.session['is_2fa_verified'] = False
        request.session['pending_next_url'] = safe_next
        return redirect('2fa_verify')

    login(request, user)
    request.session['is_2fa_verified'] = True
    messages.success(request, 'Successfully authenticated via Magic Link.')
    return redirect(safe_next)


@login_required
def two_factor_setup_view(request):
    user = request.user
    if user.is_2fa_enabled and user.totp_secret:
        messages.info(request, 'Two-factor authentication is already enabled for your account.')
        return redirect('dashboard_profile')

    if request.method == 'POST':
        form = TwoFactorSetupForm(request.POST)
        if form.is_valid():
            secret = form.cleaned_data['secret']
            code = form.cleaned_data['code']
            if verify_totp_code(secret, code):
                user.totp_secret = secret
                user.is_2fa_enabled = True
                user.save()
                request.session['is_2fa_verified'] = True
                messages.success(request, 'Two-Factor Authentication enabled successfully.')
                return redirect('dashboard_profile')
            else:
                form.add_error('code', 'Invalid verification code. Please check your authenticator app.')
    else:
        secret = generate_totp_secret()
        totp_uri = get_totp_uri(user.email, secret)
        qr_code = generate_qr_code_base64(totp_uri)
        form = TwoFactorSetupForm(initial={'secret': secret})
        return render(
            request,
            'registration/2fa_setup.html',
            {
                'form': form,
                'secret': secret,
                'qr_code': qr_code,
            },
        )

    secret = request.POST.get('secret') or generate_totp_secret()
    totp_uri = get_totp_uri(user.email, secret)
    qr_code = generate_qr_code_base64(totp_uri)
    return render(
        request,
        'registration/2fa_setup.html',
        {
            'form': form,
            'secret': secret,
            'qr_code': qr_code,
        },
    )


def two_factor_verify_view(request):
    pending_user_id = request.session.get('pending_2fa_user_id')
    if not pending_user_id:
        if request.user.is_authenticated and request.user.is_2fa_enabled:
            pending_user_id = request.user.id
        else:
            return redirect('login')

    try:
        user = CustomUser.objects.get(id=pending_user_id)
    except CustomUser.DoesNotExist:
        request.session.pop('pending_2fa_user_id', None)
        return redirect('login')

    if request.method == 'POST':
        form = TwoFactorVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            if verify_totp_code(user.totp_secret, code):
                login(request, user)
                request.session['is_2fa_verified'] = True
                safe_next = request.session.pop('pending_next_url', reverse('dashboard_home'))
                request.session.pop('pending_2fa_user_id', None)
                messages.success(request, '2FA verification successful.')
                return redirect(safe_next)
            else:
                form.add_error('code', 'Invalid 2FA verification code.')
    else:
        form = TwoFactorVerifyForm()

    return render(request, 'registration/2fa_verify.html', {'form': form, 'user_email': user.email})


class AuthViewSet(viewsets.ViewSet):
    """Standard email/password, magic link, and 2FA authentication endpoints."""

    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def signup(self, request):
        try:
            user = create_user_account(
                email=request.data.get('email'),
                password=request.data.get('password'),
                first_name=request.data.get('first_name', ''),
                last_name=request.data.get('last_name', ''),
            )
            return Response(
                {
                    'message': 'User created successfully.',
                    'user': CustomUserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except UserAlreadyExistsError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if user.is_2fa_enabled:
            request.session['pending_2fa_user_id'] = user.id
            request.session['is_2fa_verified'] = False
            return Response(
                {
                    'message': '2FA verification required',
                    'pending_2fa': True,
                    'user_id': user.id,
                },
                status=status.HTTP_200_OK,
            )

        login(request, user)
        request.session['is_2fa_verified'] = True
        return Response(
            {
                'message': 'Login successful',
                'user': CustomUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='magic-link/request')
    def magic_link_request(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        base_url = request.build_absolute_uri('/accounts/magic-link/verify/')
        initiate_magic_link(email, base_url)
        return Response(
            {'message': 'If an account exists for that email, a magic link has been sent'},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='magic-link/verify')
    def magic_link_verify(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = verify_magic_link_token(token)
        except (InvalidTokenError, TokenExpiredError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_2fa_enabled:
            request.session['pending_2fa_user_id'] = user.id
            request.session['is_2fa_verified'] = False
            return Response(
                {
                    'message': '2FA verification required',
                    'pending_2fa': True,
                    'user_id': user.id,
                },
                status=status.HTTP_200_OK,
            )

        login(request, user)
        request.session['is_2fa_verified'] = True
        return Response(
            {
                'message': 'Magic link authentication successful',
                'user': CustomUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='2fa/verify')
    def two_factor_verify(self, request):
        code = request.data.get('code')
        user_id = request.data.get('user_id') or request.session.get('pending_2fa_user_id')

        if not code or not user_id:
            return Response({'error': 'Code and user_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid user'}, status=status.HTTP_400_BAD_REQUEST)

        if verify_totp_code(user.totp_secret, code):
            login(request, user)
            request.session['is_2fa_verified'] = True
            request.session.pop('pending_2fa_user_id', None)
            return Response(
                {
                    'message': '2FA verification successful',
                    'user': CustomUserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response({'error': 'Invalid 2FA code'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        email = request.data.get('email')
        base_url = request.build_absolute_uri('/reset/')

        initiate_password_reset(email, base_url)
        return Response(
            {'message': 'If email exists, reset link has been sent'},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        try:
            reset_password_with_token(
                token=request.data.get('token'),
                new_password=request.data.get('password'),
            )
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        except (InvalidTokenError, TokenExpiredError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    """User profile management."""

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomUser.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        return Response(CustomUserSerializer(request.user).data)

    @action(detail=False, methods=['put'])
    def profile_update(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully'})
