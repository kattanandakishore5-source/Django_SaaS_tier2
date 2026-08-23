from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import CustomUser, MagicLink, PasswordReset, TwoFactorToken
from django.utils import timezone
from datetime import timedelta


class CustomUserTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_roles(self):
        self.assertEqual(self.user.role, 'viewer')
        owner = CustomUser.objects.create_superuser(
            email='owner@example.com',
            password='ownerpass123'
        )
        self.assertEqual(owner.role, 'owner')


class MagicLinkTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )

    def test_magic_link_generation(self):
        magic_link = MagicLink.objects.create(
            user=self.user,
            token=MagicLink.generate_token(),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        self.assertFalse(magic_link.used)
        self.assertTrue(magic_link.is_valid())

    def test_magic_link_expiry(self):
        magic_link = MagicLink.objects.create(
            user=self.user,
            token=MagicLink.generate_token(),
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        self.assertFalse(magic_link.is_valid())


class PasswordResetTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='oldpass123',
        )

    def test_password_reset_generation(self):
        reset = PasswordReset.objects.create(
            user=self.user,
            token=PasswordReset.generate_token(),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        self.assertFalse(reset.used)
        self.assertTrue(reset.is_valid())

    def test_password_reset_usage(self):
        reset = PasswordReset.objects.create(
            user=self.user,
            token=PasswordReset.generate_token(),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        reset.used = True
        reset.save()
        self.assertFalse(reset.is_valid())


class TwoFactorTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
        self.user.two_factor_enabled = True
        self.user.save()

    def test_2fa_token_generation(self):
        otp = TwoFactorToken.objects.create(
            user=self.user,
            token=TwoFactorToken.generate_token(),
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        self.assertEqual(len(otp.token), 6)
        self.assertTrue(otp.is_valid())
