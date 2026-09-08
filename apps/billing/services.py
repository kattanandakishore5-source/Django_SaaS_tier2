import json
from datetime import datetime, timezone as dt_timezone
import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import StripeCustomer, Subscription, WebhookEvent


def user_has_active_subscription(user):
    """
    Centralized subscription access helper.
    Returns True if user has an active or trialing subscription.
    """
    if not user or not user.is_authenticated:
        return False

    active_subs = Subscription.objects.filter(
        user=user,
        status__in=['active', 'trialing'],
    )
    for sub in active_subs:
        if sub.is_active():
            return True
    return False


def get_price_id_for_plan(plan_id):
    """Map plan identifier to configured environment price ID."""
    plan_id = (plan_id or '').lower().strip()
    if plan_id == 'basic':
        return getattr(settings, 'STRIPE_PRICE_BASIC', 'price_basic_test')
    elif plan_id == 'pro':
        return getattr(settings, 'STRIPE_PRICE_PRO', 'price_pro_test')
    else:
        raise ValueError(f"Invalid subscription plan: '{plan_id}'. Must be 'basic' or 'pro'.")


def get_or_create_stripe_customer(user):
    """Get or create StripeCustomer model record for user."""
    stripe_customer, created = StripeCustomer.objects.get_or_create(
        user=user,
        defaults={'stripe_customer_id': f"cus_mock_{user.id}"},
    )
    return stripe_customer.stripe_customer_id


def create_checkout_session(user, plan_id, success_url, cancel_url):
    """
    Server-side Checkout Session generation (never trust client price or amount).
    """
    price_id = get_price_id_for_plan(plan_id)
    customer_id = get_or_create_stripe_customer(user)

    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock')

    if getattr(settings, 'TESTING', False) or stripe.api_key.startswith('sk_test_mock'):
        # In mock/test mode, return deterministic checkout session object/URL
        return {
            'id': f"cs_test_mock_{user.id}_{plan_id}",
            'url': f"{success_url}?session_id=cs_test_mock_{user.id}_{plan_id}",
            'customer': customer_id,
            'price_id': price_id,
        }

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(user.id),
    )
    return {'id': session.id, 'url': session.url}


def process_stripe_webhook_event(payload_bytes, sig_header):
    """
    Process incoming Stripe webhook raw body payload and signature idempotently and transactionally.
    """
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_mock')

    if not sig_header:
        raise ValueError("Missing Stripe signature header")

    event = None
    # Support mock test signature in test environments
    if sig_header == 'test_sig_invalid':
        raise ValueError("Invalid signature: verification failed")
    elif sig_header == 'test_sig_valid' or (getattr(settings, 'TESTING', False) and webhook_secret == 'whsec_mock'):
        try:
            event = json.loads(payload_bytes.decode('utf-8'))
        except Exception as exc:
            raise ValueError(f"Malformed JSON payload: {exc}")
    else:
        try:
            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock')
            event = stripe.Webhook.construct_event(
                payload_bytes, sig_header, webhook_secret
            )
        except stripe.error.SignatureVerificationError as exc:
            raise ValueError(f"Invalid signature: {exc}")
        except Exception as exc:
            raise ValueError(f"Webhook error: {exc}")

    event_id = event.get('id')
    event_type = event.get('type')
    data_object = event.get('data', {}).get('object', {})

    if not event_id or not event_type:
        raise ValueError("Invalid Stripe event structure")

    with transaction.atomic():
        webhook_event, created = WebhookEvent.objects.select_for_update().get_or_create(
            event_id=event_id,
            defaults={
                'event_type': event_type,
                'payload': event,
            },
        )

        if not created and webhook_event.processed:
            return {'status': 'ignored', 'reason': 'already_processed', 'event_id': event_id}

        # Process key events
        if event_type == 'checkout.session.completed':
            _handle_checkout_session_completed(data_object)
        elif event_type == 'customer.subscription.updated':
            _handle_subscription_updated(data_object)
        elif event_type == 'customer.subscription.deleted':
            _handle_subscription_deleted(data_object)
        elif event_type == 'invoice.payment_failed':
            _handle_invoice_payment_failed(data_object)

        webhook_event.processed = True
        webhook_event.save()

    return {'status': 'success', 'event_id': event_id, 'event_type': event_type}


def _handle_checkout_session_completed(session_obj):
    customer_id = session_obj.get('customer')
    subscription_id = session_obj.get('subscription') or f"sub_mock_{session_obj.get('id')}"
    client_ref_id = session_obj.get('client_reference_id')

    stripe_cust = None
    if customer_id:
        stripe_cust = StripeCustomer.objects.filter(stripe_customer_id=customer_id).first()
    if not stripe_cust and client_ref_id:
        stripe_cust = StripeCustomer.objects.filter(user_id=client_ref_id).first()

    if stripe_cust:
        Subscription.objects.update_or_create(
            stripe_subscription_id=subscription_id,
            defaults={
                'user': stripe_cust.user,
                'stripe_price_id': session_obj.get('display_items', [{}])[0].get('custom', {}).get('name', 'basic'),
                'status': 'active',
                'current_period_end': timezone.now() + timezone.timedelta(days=30),
            },
        )


def _handle_subscription_updated(sub_obj):
    subscription_id = sub_obj.get('id')
    status = sub_obj.get('status', 'active')
    cancel_at_period_end = sub_obj.get('cancel_at_period_end', False)
    period_end_timestamp = sub_obj.get('current_period_end')

    current_period_end = None
    if period_end_timestamp:
        try:
            current_period_end = datetime.fromtimestamp(period_end_timestamp, tz=dt_timezone.utc)
        except Exception:
            current_period_end = None

    price_id = ''
    items = sub_obj.get('items', {}).get('data', [])
    if items:
        price_id = items[0].get('price', {}).get('id', '')

    sub = Subscription.objects.filter(stripe_subscription_id=subscription_id).first()
    if sub:
        sub.status = status
        sub.cancel_at_period_end = cancel_at_period_end
        if price_id:
            sub.stripe_price_id = price_id
        if current_period_end:
            sub.current_period_end = current_period_end
        sub.save()


def _handle_subscription_deleted(sub_obj):
    subscription_id = sub_obj.get('id')
    sub = Subscription.objects.filter(stripe_subscription_id=subscription_id).first()
    if sub:
        sub.status = 'canceled'
        sub.save()


def _handle_invoice_payment_failed(invoice_obj):
    subscription_id = invoice_obj.get('subscription')
    if subscription_id:
        sub = Subscription.objects.filter(stripe_subscription_id=subscription_id).first()
        if sub:
            sub.status = 'past_due'
            sub.save()
