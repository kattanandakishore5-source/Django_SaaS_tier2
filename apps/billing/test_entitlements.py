import json
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import CustomUser
from apps.billing.models import StripeCustomer, Subscription
from apps.billing.services import (
    process_stripe_webhook_event,
    user_has_active_subscription,
)
from apps.billing.entitlements import (
    FEATURE_ADVANCED_CHARTS,
    FEATURE_BASIC_ANALYTICS,
    FEATURE_USER_MANAGEMENT,
    PLAN_BASIC,
    PLAN_FREE,
    PLAN_PRO,
    get_user_plan,
    has_feature_access,
)


class SubscriptionEntitlementsTestCase(TestCase):
    def setUp(self):
        # 1. Free User (No subscription)
        self.free_user = CustomUser.objects.create_user(
            email='free@example.com',
            password='Password123!',
            first_name='FreeUser',
        )

        # 2. Basic User (Active Basic Plan)
        self.basic_user = CustomUser.objects.create_user(
            email='basic@example.com',
            password='Password123!',
            first_name='BasicUser',
        )
        StripeCustomer.objects.create(user=self.basic_user, stripe_customer_id='cus_basic_101')
        Subscription.objects.create(
            user=self.basic_user,
            stripe_subscription_id='sub_basic_101',
            stripe_price_id='price_basic_test',
            status='active',
            current_period_end=timezone.now() + timedelta(days=30),
        )

        # 3. Pro User (Active Pro Plan)
        self.pro_user = CustomUser.objects.create_user(
            email='pro@example.com',
            password='Password123!',
            first_name='ProUser',
        )
        StripeCustomer.objects.create(user=self.pro_user, stripe_customer_id='cus_pro_102')
        Subscription.objects.create(
            user=self.pro_user,
            stripe_subscription_id='sub_pro_102',
            stripe_price_id='price_pro_test',
            status='active',
            current_period_end=timezone.now() + timedelta(days=30),
        )

        # 4. Canceled User
        self.canceled_user = CustomUser.objects.create_user(
            email='canceled@example.com',
            password='Password123!',
            first_name='CanceledUser',
        )
        StripeCustomer.objects.create(user=self.canceled_user, stripe_customer_id='cus_canceled_103')
        Subscription.objects.create(
            user=self.canceled_user,
            stripe_subscription_id='sub_canceled_103',
            stripe_price_id='price_basic_test',
            status='canceled',
        )

        # 5. Past Due User
        self.past_due_user = CustomUser.objects.create_user(
            email='pastdue@example.com',
            password='Password123!',
            first_name='PastDueUser',
        )
        StripeCustomer.objects.create(user=self.past_due_user, stripe_customer_id='cus_pastdue_104')
        Subscription.objects.create(
            user=self.past_due_user,
            stripe_subscription_id='sub_pastdue_104',
            stripe_price_id='price_pro_test',
            status='past_due',
        )

    def test_plan_resolution_matrix(self):
        self.assertEqual(get_user_plan(self.free_user), PLAN_FREE)
        self.assertEqual(get_user_plan(self.basic_user), PLAN_BASIC)
        self.assertEqual(get_user_plan(self.pro_user), PLAN_PRO)
        self.assertEqual(get_user_plan(self.canceled_user), PLAN_FREE)
        self.assertEqual(get_user_plan(self.past_due_user), PLAN_FREE)

    def test_feature_entitlement_access_matrix(self):
        # Free user has no feature permissions
        self.assertFalse(has_feature_access(self.free_user, FEATURE_USER_MANAGEMENT))
        self.assertFalse(has_feature_access(self.free_user, FEATURE_BASIC_ANALYTICS))
        self.assertFalse(has_feature_access(self.free_user, FEATURE_ADVANCED_CHARTS))

        # Basic user has user management and basic analytics, but NOT advanced charts
        self.assertTrue(has_feature_access(self.basic_user, FEATURE_USER_MANAGEMENT))
        self.assertTrue(has_feature_access(self.basic_user, FEATURE_BASIC_ANALYTICS))
        self.assertFalse(has_feature_access(self.basic_user, FEATURE_ADVANCED_CHARTS))

        # Pro user has all features
        self.assertTrue(has_feature_access(self.pro_user, FEATURE_USER_MANAGEMENT))
        self.assertTrue(has_feature_access(self.pro_user, FEATURE_BASIC_ANALYTICS))
        self.assertTrue(has_feature_access(self.pro_user, FEATURE_ADVANCED_CHARTS))

    def test_direct_url_bypass_prevention(self):
        # Free user attempting direct URL access to /dashboard/users/
        self.client.force_login(self.free_user)
        res_free = self.client.get(reverse('dashboard_users'))
        self.assertEqual(res_free.status_code, 302)
        self.assertRedirects(res_free, reverse('billing_dashboard'))

        # Canceled user attempting direct URL access
        self.client.force_login(self.canceled_user)
        res_canceled = self.client.get(reverse('dashboard_users'))
        self.assertEqual(res_canceled.status_code, 302)
        self.assertRedirects(res_canceled, reverse('billing_dashboard'))

        # Basic user allowed access to /dashboard/users/
        self.client.force_login(self.basic_user)
        res_basic = self.client.get(reverse('dashboard_users'))
        self.assertEqual(res_basic.status_code, 200)

    def test_api_bypass_and_tier_permissions(self):
        # Free user attempting /api/dashboard/stats/
        self.client.force_login(self.free_user)
        res_stats_free = self.client.get('/api/dashboard/stats/')
        self.assertEqual(res_stats_free.status_code, 403)

        # Basic user allowed /api/dashboard/stats/ but denied /api/dashboard/chart-signups/
        self.client.force_login(self.basic_user)
        res_stats_basic = self.client.get('/api/dashboard/stats/')
        self.assertEqual(res_stats_basic.status_code, 200)

        res_charts_basic = self.client.get('/api/dashboard/chart-signups/')
        self.assertEqual(res_charts_basic.status_code, 403)

        # Pro user allowed /api/dashboard/chart-signups/
        self.client.force_login(self.pro_user)
        res_charts_pro = self.client.get('/api/dashboard/chart-signups/')
        self.assertEqual(res_charts_pro.status_code, 200)

    def test_cancel_at_period_end_expiration(self):
        # Active subscription with cancel_at_period_end=True but expired current_period_end
        expired_sub = Subscription.objects.create(
            user=self.free_user,
            stripe_subscription_id='sub_expired_cancel',
            stripe_price_id='price_basic_test',
            status='active',
            cancel_at_period_end=True,
            current_period_end=timezone.now() - timedelta(days=1), # Expired yesterday
        )
        self.assertFalse(user_has_active_subscription(self.free_user))
        self.assertEqual(get_user_plan(self.free_user), PLAN_FREE)

    def test_cross_user_and_client_tampering_prevention(self):
        # Free user attempts to checkout injecting arbitrary plan='pro' or spoofing customer_id
        self.client.force_login(self.free_user)

        # Attempting checkout with invalid price string
        res_invalid_plan = self.client.post(
            reverse('billing_checkout'),
            {'plan_id': 'hacked_free_pro'},
            follow=True,
        )
        self.assertEqual(res_invalid_plan.status_code, 200)
        self.assertContains(res_invalid_plan, 'Invalid subscription plan')

        # Verify free user remains free
        self.assertEqual(get_user_plan(self.free_user), PLAN_FREE)

    def test_webhook_access_propagation_revokes_access(self):
        # Basic user starts with active access
        self.assertTrue(user_has_active_subscription(self.basic_user))

        # Payment failed webhook arrives
        fail_payload = json.dumps({
            'id': 'evt_pay_failed_test_909',
            'type': 'invoice.payment_failed',
            'data': {'object': {'subscription': 'sub_basic_101'}}
        }).encode('utf-8')

        process_stripe_webhook_event(fail_payload, sig_header='test_sig_valid')

        # Access is immediately revoked
        self.basic_user.refresh_from_db()
        self.assertFalse(user_has_active_subscription(self.basic_user))
        self.assertEqual(get_user_plan(self.basic_user), PLAN_FREE)

        # Direct API access now returns 403 Forbidden
        self.client.force_login(self.basic_user)
        res_blocked = self.client.get('/api/dashboard/stats/')
        self.assertEqual(res_blocked.status_code, 403)
