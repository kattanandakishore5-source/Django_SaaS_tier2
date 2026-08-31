from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .forms import (
    CustomUserCreationForm,
    EmailAuthenticationForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
)
from .models import CustomUser, PasswordReset
from .serializers import CustomUserSerializer
from .services import (
    InvalidTokenError,
    TokenExpiredError,
    UserAlreadyExistsError,
    create_user_account,
    initiate_password_reset,
    reset_password_with_token,
)


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    return redirect('login')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account has been created successfully.')
            return redirect('dashboard_home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.POST.get('next') or 'dashboard_home'
            return redirect(next_url)
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
    if request.user.is_authenticated:
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
    if request.user.is_authenticated:
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


class AuthViewSet(viewsets.ViewSet):
    """Standard email/password authentication endpoints."""

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

        login(request, user)
        return Response(
            {
                'message': 'Login successful',
                'user': CustomUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

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
