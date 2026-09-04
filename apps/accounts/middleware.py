from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from django.conf import settings


class Pending2FAMiddleware:
    """
    Middleware that strictly blocks access to protected routes (/dashboard, /billing, /admin)
    if the session is in a pending-2FA state or if an authenticated user with 2FA enabled
    has not completed TOTP verification.
    """

    EXEMPT_PATHS = [
        '/accounts/2fa/verify/',
        '/accounts/logout/',
        '/accounts/login/',
        '/api/auth/2fa-verify/',
        '/api/auth/logout/',
        '/api/auth/login/',
        '/static/',
        '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Check if the path is explicitly exempt
        is_exempt = any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)

        pending_user_id = request.session.get('pending_2fa_user_id')
        user_is_authenticated = hasattr(request, 'user') and request.user.is_authenticated
        user_has_2fa = user_is_authenticated and getattr(request.user, 'is_2fa_enabled', False)
        is_verified = request.session.get('is_2fa_verified', False)

        is_pending = bool(pending_user_id) or (user_has_2fa and not is_verified)

        if is_pending and not is_exempt:
            # Block access to protected routes
            if path.startswith('/api/'):
                return JsonResponse(
                    {'error': '2FA verification required before accessing protected resources.'},
                    status=403,
                )
            return redirect(reverse('2fa_verify'))

        return self.get_response(request)
