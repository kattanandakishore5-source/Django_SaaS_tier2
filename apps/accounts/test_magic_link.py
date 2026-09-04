from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import CustomUser, MagicLinkToken
from apps.accounts.services import (
    InvalidTokenError,
    TokenExpiredError,
    initiate_magic_link,
    verify_magic_link_token,
)


class MagicLinkTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='alice@example.com',
            password='Password123!',
            first_name='Alice',
        )

    @patch('apps.core.utils.send_email_async.delay')
    def test_magic_link_initiation_and_async_email(self, mock_send_email):
        success = initiate_magic_link('alice@example.com', 'http://testserver/accounts/magic-link/verify/')
        self.assertTrue(success)

        # Check DB token created
        token_obj = MagicLinkToken.objects.get(user=self.user)
        self.assertFalse(token_obj.used)
        self.assertTrue(token_obj.is_valid())

        # Check email dispatched
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]
        self.assertEqual(call_kwargs['recipient_list'], ['alice@example.com'])
        self.assertIn(token_obj.token, call_kwargs['message'])

    @patch('apps.core.utils.send_email_async.delay')
    def test_user_enumeration_prevention(self, mock_send_email):
        # Non-existent email returns success response without raising error
        success = initiate_magic_link('nonexistent@example.com', 'http://testserver/accounts/magic-link/verify/')
        self.assertTrue(success)
        mock_send_email.assert_not_called()

        # Browser endpoint enumeration test
        response = self.client.post(
            reverse('magic_link_request'),
            {'email': 'unknown@example.com'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'If an account exists for that email')

    def test_magic_link_verification_and_single_use(self):
        token = MagicLinkToken.generate_token()
        MagicLinkToken.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=15),
        )

        verified_user = verify_magic_link_token(token)
        self.assertEqual(verified_user, self.user)

        # Token is now used; second verification must fail
        with self.assertRaises(InvalidTokenError):
            verify_magic_link_token(token)

    def test_magic_link_expiration(self):
        token = MagicLinkToken.generate_token()
        MagicLinkToken.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() - timedelta(minutes=1), # Expired
        )

        with self.assertRaises(TokenExpiredError):
            verify_magic_link_token(token)

    def test_tampered_token_rejection(self):
        with self.assertRaises(InvalidTokenError):
            verify_magic_link_token('invalid_tampered_token_string')

    def test_open_redirect_prevention(self):
        token = MagicLinkToken.generate_token()
        MagicLinkToken.objects.create(
            user=self.user,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=15),
        )

        # Attempt external open redirect
        verify_url = f"{reverse('magic_link_verify', args=[token])}?next=https://evil-attacker.com/steal-data"
        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, 302)
        # Must redirect to dashboard_home, NOT evil-attacker.com
        self.assertEqual(response.url, reverse('dashboard_home'))
