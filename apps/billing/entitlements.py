from functools import wraps
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from rest_framework import permissions

from .models import Subscription

PLAN_FREE = 'free'
PLAN_BASIC = 'basic'
PLAN_PRO = 'pro'

FEATURE_BASIC_ANALYTICS = 'basic_analytics'
FEATURE_USER_MANAGEMENT = 'user_management'
FEATURE_ADVANCED_CHARTS = 'advanced_charts'

PLAN_FEATURES = {
    PLAN_FREE: set(),
    PLAN_BASIC: {FEATURE_BASIC_ANALYTICS, FEATURE_USER_MANAGEMENT},
    PLAN_PRO: {FEATURE_BASIC_ANALYTICS, FEATURE_USER_MANAGEMENT, FEATURE_ADVANCED_CHARTS},
}


def get_active_subscription(user):
    """
    Server-authoritative check for a user's active/valid subscription.
    Returns the active Subscription object if valid, else None.
    """
    if not user or not user.is_authenticated:
        return None

    sub = Subscription.objects.filter(user=user, status__in=['active', 'trialing']).order_by('-created_at').first()
    if not sub:
        return None

    if sub.status in ['active', 'trialing']:
        if sub.current_period_end and timezone.now() > sub.current_period_end:
            return None
        return sub

    return None


def get_user_plan(user):
    """
    Resolve user's current subscription plan ('free', 'basic', 'pro').
    Strictly server-determined based on validated active Subscription in DB.
    """
    sub = get_active_subscription(user)
    if not sub:
        return PLAN_FREE

    price_basic = getattr(settings, 'STRIPE_PRICE_BASIC', 'price_basic_test')
    price_pro = getattr(settings, 'STRIPE_PRICE_PRO', 'price_pro_test')

    price_id = sub.stripe_price_id or ''
    if price_id == price_pro or 'pro' in price_id.lower():
        return PLAN_PRO
    elif price_id == price_basic or 'basic' in price_id.lower():
        return PLAN_BASIC

    # Default active fallback
    return PLAN_BASIC


def has_feature_access(user, feature_key):
    """
    Server-authoritative check if user's subscription plan grants access to feature_key.
    """
    plan = get_user_plan(user)
    return feature_key in PLAN_FEATURES.get(plan, set())


def subscription_required(view_func):
    """
    View decorator: Requires an active paid subscription (Basic or Pro).
    Redirects browser requests to /billing/ and returns HTTP 403 for API requests.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not get_active_subscription(request.user):
            if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
                return JsonResponse({'error': 'Active subscription required.'}, status=403)
            messages.warning(request, 'An active subscription is required to access this page.')
            return redirect('billing_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def require_feature(feature_key):
    """
    View decorator: Requires specific feature entitlement for browser/Django views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not has_feature_access(request.user, feature_key):
                if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
                    return JsonResponse({'error': f"Upgrade required. Feature '{feature_key}' is not included in your plan."}, status=403)
                messages.warning(request, f"Upgrade required to access this feature.")
                return redirect('billing_dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


class HasActiveSubscription(permissions.BasePermission):
    """DRF Permission class enforcing active subscription."""
    message = 'Active subscription required.'

    def has_permission(self, request, view):
        return bool(get_active_subscription(request.user))


class HasFeatureAccess(permissions.BasePermission):
    """
    DRF Permission class enforcing feature entitlement.
    Can be instantiated with feature_key or set via view attribute `required_feature`.
    """
    def __init__(self, feature_key=None):
        self.feature_key = feature_key

    def __call__(self):
        return self

    def has_permission(self, request, view):
        feat = self.feature_key or getattr(view, 'required_feature', None)
        if not feat:
            return True
        if not has_feature_access(request.user, feat):
            self.message = f"Upgrade required. Feature '{feat}' is not included in your subscription plan."
            return False
        return True
