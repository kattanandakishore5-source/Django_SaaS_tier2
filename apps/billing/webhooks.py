import json
import logging

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# TODO: Uncomment once stripe is installed and configured
# import stripe
# from django.conf import settings
# stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle incoming Stripe webhook events.

    Production checklist:
        1. pip install stripe
        2. Set STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET in .env
        3. Uncomment the stripe import and signature verification below
        4. Implement your business logic in each event handler
    """
    payload = request.body

    # ------------------------------------------------------------------
    # TODO: Verify webhook signature in production
    # ------------------------------------------------------------------
    # sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    # endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    # try:
    #     event = stripe.Webhook.construct_event(
    #         payload, sig_header, endpoint_secret
    #     )
    # except (ValueError, stripe.error.SignatureVerificationError) as e:
    #     logger.warning('Stripe webhook signature verification failed: %s', e)
    #     return HttpResponseBadRequest('Invalid payload or signature')
    # ------------------------------------------------------------------

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON payload')

    event_type = event.get('type', '')
    logger.info('Received Stripe event: %s', event_type)

    # ----- Event Routing -----

    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        # TODO: Provision the subscription for the customer
        # 1. Retrieve or create the user from session['customer_email']
        # 2. Create/update the Subscription model with:
        #    - stripe_customer_id = session['customer']
        #    - stripe_subscription_id = session['subscription']
        #    - status = 'active'
        #    - plan_name = <resolve from session line items or metadata>
        logger.info(
            'Checkout completed for customer %s', session.get('customer')
        )

    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # TODO: Handle subscription cancellation
        # 1. Look up local Subscription by stripe_subscription_id
        # 2. Update status to 'canceled'
        # 3. Optionally revoke access or downgrade the user's plan
        logger.info(
            'Subscription deleted: %s', subscription.get('id')
        )

    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        # TODO: Handle plan changes, payment failures, renewals
        # 1. Look up local Subscription by stripe_subscription_id
        # 2. Update status, plan_name, current_period_end as needed
        logger.info(
            'Subscription updated: %s', subscription.get('id')
        )

    elif event_type == 'invoice.payment_failed':
        invoice = event['data']['object']
        # TODO: Handle failed payments
        # 1. Look up local Subscription by stripe_subscription_id
        # 2. Update status to 'past_due'
        # 3. Optionally notify the user
        logger.info(
            'Invoice payment failed for customer %s', invoice.get('customer')
        )

    else:
        logger.debug('Unhandled Stripe event type: %s', event_type)

    return HttpResponse(status=200)
