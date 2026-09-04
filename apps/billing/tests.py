import json
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import CustomUser
from apps.billing.models import StripeCustomer, Subscription, WebhookEvent
from apps.billing.services import (
    create_checkout_session,
    process_stripe_webhook_event,
    user_has_active_subscription,
)


class StripeBillingTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='charlie@example.com',
            password='Password123!',
            first_name='Charlie',
        )

    def test_user_has_active_subscription_helper(self):
        self.assertFalse(user_has_active_subscription(self.user))

        # Create active subscription
        sub = Subscription.objects.create(
            user=self.user,
            stripe_subscription_id='sub_test_123',
            stripe_price_id='price_basic_test',
            status='active',
            current_period_end=timezone.now() + timedelta(days=30),
        )
        self.assertTrue(user_has_active_subscription(self.user))

        # Canceled subscription
        sub.status = 'canceled'
        sub.save()
        self.assertFalse(user_has_active_subscription(self.user))

    def test_server_side_checkout_session_creation(self):
        session = create_checkout_session(
            user=self.user,
            plan_id='pro',
            success_url='http://testserver/billing/?success',
            cancel_url='http://testserver/billing/?cancel',
        )
        self.assertIn('cs_test_mock_', session['id'])
        self.assertEqual(session['price_id'], 'price_pro_test')

        # Invalid plan raises ValueError
        with self.assertRaises(ValueError):
            create_checkout_session(self.user, 'invalid_plan', 'http://a', 'http://b')

    def test_webhook_signature_validation(self):
        payload = json.dumps({
            'id': 'evt_test_sig_check',
            'type': 'customer.subscription.deleted',
            'data': {'object': {'id': 'sub_test_sig'}}
        }).encode('utf-8')

        # Missing signature header
        with self.assertRaises(ValueError):
            process_stripe_webhook_event(payload, sig_header=None)

        # Invalid signature header
        with self.assertRaises(ValueError):
            process_stripe_webhook_event(payload, sig_header='test_sig_invalid')

        # Valid signature header
        res = process_stripe_webhook_event(payload, sig_header='test_sig_valid')
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['event_id'], 'evt_test_sig_check')

    def test_webhook_event_idempotency(self):
        payload = json.dumps({
            'id': 'evt_idempotency_101',
            'type': 'customer.subscription.deleted',
            'data': {'object': {'id': 'sub_idempotent_123'}}
        }).encode('utf-8')

        # First run
        res1 = process_stripe_webhook_event(payload, sig_header='test_sig_valid')
        self.assertEqual(res1['status'], 'success')
        self.assertEqual(WebhookEvent.objects.count(), 1)

        # Second run (replayed event)
        res2 = process_stripe_webhook_event(payload, sig_header='test_sig_valid')
        self.assertEqual(res2['status'], 'ignored')
        self.assertEqual(res2['reason'], 'already_processed')
        self.assertEqual(WebhookEvent.objects.count(), 1)

    def test_checkout_session_completed_webhook_creates_subscription(self):
        customer = StripeCustomer.objects.create(
            user=self.user,
            stripe_customer_id='cus_test_charlie',
        )

        payload = json.dumps({
            'id': 'evt_checkout_completed_001',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_session',
                    'customer': customer.stripe_customer_id,
                    'subscription': 'sub_new_subscription_101',
                    'client_reference_id': str(self.user.id),
                }
            }
        }).encode('utf-8')

        res = process_stripe_webhook_event(payload, sig_header='test_sig_valid')
        self.assertEqual(res['status'], 'success')

        sub = Subscription.objects.get(stripe_subscription_id='sub_new_subscription_101')
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.status, 'active')
        self.assertTrue(user_has_active_subscription(self.user))

    def test_subscription_updated_and_deleted_webhooks(self):
        sub = Subscription.objects.create(
            user=self.user,
            stripe_subscription_id='sub_lifecycle_001',
            stripe_price_id='price_basic_test',
            status='active',
        )

        # Update event
        update_payload = json.dumps({
            'id': 'evt_sub_updated_001',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': sub.stripe_subscription_id,
                    'status': 'past_due',
                    'cancel_at_period_end': True,
                }
            }
        }).encode('utf-8')

        process_stripe_webhook_event(update_payload, sig_header='test_sig_valid')
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'past_due')
        self.assertTrue(sub.cancel_at_period_end)

        # Delete event
        delete_payload = json.dumps({
            'id': 'evt_sub_deleted_001',
            'type': 'customer.subscription.deleted',
            'data': {
                'object': {
                    'id': sub.stripe_subscription_id,
                }
            }
        }).encode('utf-8')

        process_stripe_webhook_event(delete_payload, sig_header='test_sig_valid')
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'canceled')
        self.assertFalse(user_has_active_subscription(self.user))

    def test_webhook_http_endpoint(self):
        payload_data = {
            'id': 'evt_http_endpoint_test',
            'type': 'customer.subscription.deleted',
            'data': {'object': {'id': 'sub_http_test'}}
        }

        # Request with valid signature
        response = self.client.post(
            reverse('stripe_webhook'),
            data=json.dumps(payload_data),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_sig_valid',
        )
        self.assertEqual(response.status_code, 200)

        # Request with invalid signature
        response_invalid = self.client.post(
            reverse('stripe_webhook'),
            data=json.dumps(payload_data),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='test_sig_invalid',
        )
        self.assertEqual(response_invalid.status_code, 400)
