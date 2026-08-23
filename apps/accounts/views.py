from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import CustomUser, MagicLink, TwoFactorToken, PasswordReset, APIKey
from .serializers import (
    CustomUserSerializer, MagicLinkSerializer, PasswordResetSerializer,
    TwoFactorSerializer, APIKeySerializer
)
from apps.core.decorators import role_required
from apps.core.utils import send_email_async


class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints: signup, login, magic link, 2FA, password reset"""

    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def signup(self, request):
        """Register new user with email verification"""
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if CustomUser.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='viewer'
            )

            # Send verification email
            send_email_async.delay(
                subject='Welcome to Django Admin Pro!',
                message=f'Thank you for signing up, {first_name}!',
                recipient_list=[email],
                template='welcome'
            )

            return Response(
                {
                    'message': 'User created successfully. Check your email.',
                    'user': CustomUserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Email/password login"""
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user)

        # Check if 2FA is enabled
        if user.two_factor_enabled:
            token = TwoFactorToken.objects.create(
                user=user,
                token=TwoFactorToken.generate_token(),
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            send_email_async.delay(
                subject='Your 2FA Code',
                message=f'Your 2FA code is: {token.token}',
                recipient_list=[email]
            )
            return Response(
                {'message': '2FA code sent to email'},
                status=status.HTTP_200_OK
            )

        return Response(
            {
                'message': 'Login successful',
                'user': CustomUserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    def magic_link(self, request):
        """Send magic link for passwordless login"""
        email = request.data.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {'message': 'If email exists, link has been sent'},
                status=status.HTTP_200_OK
            )

        # Delete existing magic links
        MagicLink.objects.filter(user=user).delete()

        # Create new magic link
        token = MagicLink.generate_token()
        magic_link = MagicLink.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )

        # Send email with magic link
        magic_url = f"{request.build_absolute_uri('/dashboard/')}{token}/"
        send_email_async.delay(
            subject='Your Django Admin Pro Magic Link',
            message=f'Click here to login: {magic_url}',
            recipient_list=[email],
            template='magic_link'
        )

        return Response(
            {'message': 'Magic link sent to email'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='verify-magic-link')
    def verify_magic_link(self, request):
        """Verify and use magic link"""
        token = request.data.get('token')

        try:
            magic_link = MagicLink.objects.get(token=token)
        except MagicLink.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not magic_link.is_valid():
            return Response(
                {'error': 'Link has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )

        magic_link.used = True
        magic_link.save()

        user = magic_link.user
        login(request, user)

        return Response(
            {
                'message': 'Login successful',
                'user': CustomUserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='verify-2fa')
    def verify_2fa(self, request):
        """Verify 2FA token"""
        user = request.user
        token = request.data.get('token')

        try:
            otp = TwoFactorToken.objects.get(user=user, token=token)
        except TwoFactorToken.DoesNotExist:
            return Response(
                {'error': 'Invalid 2FA code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not otp.is_valid():
            return Response(
                {'error': 'Code has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp.used = True
        otp.save()

        return Response(
            {
                'message': '2FA verified',
                'user': CustomUserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        """Initiate password reset"""
        email = request.data.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {'message': 'If email exists, reset link has been sent'},
                status=status.HTTP_200_OK
            )

        # Delete existing reset links
        PasswordReset.objects.filter(user=user).delete()

        # Create new reset link
        token = PasswordReset.generate_token()
        reset = PasswordReset.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timedelta(hours=24)
        )

        # Send email with reset link
        reset_url = f"{request.build_absolute_uri('/reset/')}{token}/"
        send_email_async.delay(
            subject='Reset Your Password',
            message=f'Click here to reset: {reset_url}',
            recipient_list=[email]
        )

        return Response(
            {'message': 'Password reset link sent'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        """Reset password with token"""
        token = request.data.get('token')
        password = request.data.get('password')

        try:
            reset = PasswordReset.objects.get(token=token)
        except PasswordReset.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not reset.is_valid():
            return Response(
                {'error': 'Link has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reset.used = True
        reset.save()

        user = reset.user
        user.set_password(password)
        user.save()

        return Response(
            {'message': 'Password reset successful'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user"""
        # Delete all tokens if using token auth
        return Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK
        )


class UserViewSet(viewsets.ModelViewSet):
    """User profile management"""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'owner':
            return CustomUser.objects.all()
        return CustomUser.objects.filter(id=user.id)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        return Response(CustomUserSerializer(request.user).data)

    @action(detail=False, methods=['put'])
    def profile_update(self, request):
        """Update current user profile"""
        user = request.user
        serializer = CustomUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response(
                {'error': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password changed successfully'})

    @action(detail=False, methods=['post'], url_path='enable-2fa')
    def enable_2fa(self, request):
        """Enable 2FA for user"""
        user = request.user
        method = request.data.get('method', 'email')

        user.two_factor_enabled = True
        user.two_factor_method = method
        user.save()

        return Response({'message': '2FA enabled'})


class APIKeyViewSet(viewsets.ModelViewSet):
    """Manage API keys"""
    queryset = APIKey.objects.all()
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate API key"""
        api_key = self.get_object()
        api_key.key = APIKey.generate_key()
        api_key.save()
        return Response(APIKeySerializer(api_key).data)
