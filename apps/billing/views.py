import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Subscription
from .services import (
    create_checkout_session,
    process_stripe_webhook_event,
    user_has_active_subscription,
)


@login_required
def billing_dashboard_view(request):
    user_sub = Subscription.objects.filter(user=request.user).order_by('-created_at').first()
    has_active = user_has_active_subscription(request.user)

    context = {
        'subscription': user_sub,
        'has_active': has_active,
    }
    return render(request, 'billing/dashboard.html', context)


@login_required
@require_POST
def checkout_session_view(request):
    plan_id = request.POST.get('plan_id') or request.GET.get('plan_id') or 'basic'
    success_url = request.build_absolute_uri('/billing/?checkout=success')
    cancel_url = request.build_absolute_uri('/billing/?checkout=cancel')

    try:
        session = create_checkout_session(request.user, plan_id, success_url, cancel_url)
        if request.headers.get('Accept') == 'application/json' or request.content_type == 'application/json':
            return JsonResponse({'checkout_url': session['url'], 'session_id': session['id']})
        return redirect(session['url'])
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('billing_dashboard')


import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    payload_bytes = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        result = process_stripe_webhook_event(payload_bytes, sig_header)
        return HttpResponse(json.dumps(result), content_type='application/json', status=200)
    except ValueError as exc:
        logger.warning("Stripe webhook validation error: %s", exc)
        return HttpResponse(json.dumps({'error': str(exc)}), content_type='application/json', status=400)
    except Exception as exc:
        logger.error("Internal server error processing Stripe webhook", exc_info=True)
        return HttpResponse(json.dumps({'error': "Internal server error"}), content_type='application/json', status=500)


class BillingViewSet(viewsets.ViewSet):
    """API viewset for Stripe Billing operations."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def subscription(self, request):
        user_sub = Subscription.objects.filter(user=request.user).order_by('-created_at').first()
        has_active = user_has_active_subscription(request.user)

        return Response({
            'has_active_subscription': has_active,
            'subscription': {
                'id': user_sub.stripe_subscription_id if user_sub else None,
                'status': user_sub.status if user_sub else 'none',
                'price_id': user_sub.stripe_price_id if user_sub else None,
                'cancel_at_period_end': user_sub.cancel_at_period_end if user_sub else False,
            } if user_sub else None,
        })

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        plan_id = request.data.get('plan_id', 'basic')
        success_url = request.build_absolute_uri('/billing/?checkout=success')
        cancel_url = request.build_absolute_uri('/billing/?checkout=cancel')

        try:
            session = create_checkout_session(request.user, plan_id, success_url, cancel_url)
            return Response({'checkout_url': session['url'], 'session_id': session['id']}, status=status.HTTP_200_OK)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
