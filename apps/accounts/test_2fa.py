import pyotp
from django.test import TestCase
from django.urls import reverse
from apps.accounts.models import CustomUser, MagicLinkToken
from apps.accounts.totp import generate_totp_secret, verify_totp_code
from django.utils import timezone
from datetime import timedelta


class TwoFactorAuthTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='bob@example.com',
            password='StrongPassword123!',
            first_name='Bob',
        )

    def test_totp_generation_and_verification(self):
        secret = generate_totp_secret()
        self.assertEqual(len(secret), 32)

        totp = pyotp.TOTP(secret)
        current_code = totp.now()

        self.assertTrue(verify_totp_code(secret, current_code))
        self.assertFalse(verify_totp_code(secret, '000000'))

    def test_2fa_pending_state_blocks_protected_routes(self):
        # Enable 2FA for user
        secret = generate_totp_secret()
        self.user.totp_secret = secret
        self.user.is_2fa_enabled = True
        self.user.save()

        # Login via password
        response = self.client.post(
            reverse('login'),
            {'username': 'bob@example.com', 'password': 'StrongPassword123!'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('2fa_verify'))

        # Attempt to bypass 2FA and directly visit protected route /dashboard/
        dashboard_response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(dashboard_response.status_code, 302)
        self.assertRedirects(dashboard_response, reverse('2fa_verify'))

        # Attempt to visit /billing/
        billing_response = self.client.get(reverse('billing_dashboard'))
        self.assertEqual(billing_response.status_code, 302)
        self.assertRedirects(billing_response, reverse('2fa_verify'))

        # Attempt API access
        api_response = self.client.get('/api/dashboard/')
        self.assertEqual(api_response.status_code, 403)
        self.assertIn('2FA verification required', api_response.json()['error'])

        # Now submit invalid 2FA code
        verify_failed = self.client.post(
            reverse('2fa_verify'),
            {'code': '999999'},
        )
        self.assertEqual(verify_failed.status_code, 200)
        self.assertContains(verify_failed, 'Invalid 2FA verification code')

        # Submit valid 2FA code
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        verify_success = self.client.post(
            reverse('2fa_verify'),
            {'code': valid_code},
            follow=True,
        )
        self.assertEqual(verify_success.status_code, 200)
        self.assertTrue(verify_success.wsgi_request.user.is_authenticated)

        # Now dashboard access is granted
        dashboard_after_2fa = self.client.get(reverse('dashboard_home'))
        self.assertEqual(dashboard_after_2fa.status_code, 200)

    def test_magic_link_with_2fa_enabled(self):
        secret = generate_totp_secret()
        self.user.totp_secret = secret
        self.user.is_2fa_enabled = True
        self.user.save()

        token = MagicLinkToken.generate_token()
        MagicLinkToken.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=15),
        )

        response = self.client.get(reverse('magic_link_verify', args=[token]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('2fa_verify'))

    def test_standard_user_without_2fa_logs_in_normally(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'bob@example.com', 'password': 'StrongPassword123!'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.path, reverse('dashboard_home'))
