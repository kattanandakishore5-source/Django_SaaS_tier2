from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login

from .models import CustomUser, APIKey
from .serializers import CustomUserSerializer, APIKeySerializer
from .services import (
    create_user_account,
    generate_and_send_magic_link,
    verify_magic_link_token,
    create_and_send_2fa_token,
    verify_2fa_token,
    initiate_password_reset,
    reset_password_with_token,
    UserAlreadyExistsError,
    InvalidTokenError,
    TokenExpiredError,
)
from apps.core.decorators import role_required


class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints: signup, login, magic link, 2FA, password reset"""

    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def signup(self, request):
        """Register new user with email verification"""
        try:
            user = create_user_account(
                email=request.data.get('email'),
                password=request.data.get('password'),
                first_name=request.data.get('first_name', ''),
                last_name=request.data.get('last_name', ''),
            )
            return Response(
                {
                    'message': 'User created successfully. Check your email.',
                    'user': CustomUserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except UserAlreadyExistsError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
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
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)

        # If 2FA is enabled, send a code instead of completing login
        if user.two_factor_enabled:
            create_and_send_2fa_token(user)
            return Response(
                {'message': '2FA code sent to email'},
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                'message': 'Login successful',
                'user': CustomUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'])
    def magic_link(self, request):
        """Send magic link for passwordless login"""
        email = request.data.get('email')
        base_url = request.build_absolute_uri('/dashboard/')

        generate_and_send_magic_link(email, base_url)

        # Always return a success message regardless of whether the user exists
        return Response(
            {'message': 'If email exists, link has been sent'},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='verify-magic-link')
    def verify_magic_link(self, request):
        """Verify and use magic link"""
        try:
            user = verify_magic_link_token(request.data.get('token'))
            login(request, user)
            return Response(
                {
                    'message': 'Login successful',
                    'user': CustomUserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        except (InvalidTokenError, TokenExpiredError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['post'], url_path='verify-2fa')
    def verify_2fa(self, request):
        """Verify 2FA token"""
        try:
            verify_2fa_token(request.user, request.data.get('token'))
            return Response(
                {
                    'message': '2FA verified',
                    'user': CustomUserSerializer(request.user).data,
                },
                status=status.HTTP_200_OK,
            )
        except (InvalidTokenError, TokenExpiredError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        """Initiate password reset"""
        email = request.data.get('email')
        base_url = request.build_absolute_uri('/reset/')

        initiate_password_reset(email, base_url)

        return Response(
            {'message': 'If email exists, reset link has been sent'},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        """Reset password with token"""
        try:
            reset_password_with_token(
                token=request.data.get('token'),
                new_password=request.data.get('password'),
            )
            return Response(
                {'message': 'Password reset successful'},
                status=status.HTTP_200_OK,
            )
        except (InvalidTokenError, TokenExpiredError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user"""
        # Delete all tokens if using token auth
        return Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK,
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
                status=status.HTTP_400_BAD_REQUEST,
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        data = serializer.data
        if hasattr(serializer.instance, '_raw_key'):
            data['raw_key'] = serializer.instance._raw_key

        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate API key"""
        import hashlib
        api_key = self.get_object()
        raw_key = APIKey.generate_key()
        api_key._raw_key = raw_key
        api_key.key = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key.save()
        data = APIKeySerializer(api_key).data
        data['raw_key'] = raw_key
        return Response(data)
