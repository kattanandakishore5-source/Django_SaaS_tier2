from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings

from apps.audit.models import AuditLog
from apps.accounts.models import CustomUser


class AuditMiddlewareTests(TestCase):
    def setUp(self):
        settings.TESTING = True
        self.client = Client()
        AuditLog.objects.all().delete()

    def test_anonymous_request_does_not_crash(self):
        response = self.client.get(reverse('login'))
        self.assertIn(response.status_code, (200, 302))
        # Audit record should be created
        self.assertTrue(AuditLog.objects.exists())

    def test_authenticated_request_logs_user(self):
        email = 'audit-user@example.com'
        password = 'TestPass123!'
        user = CustomUser.objects.create_user(email=email, password=password)
        logged_in = self.client.login(username=email, password=password)
        self.assertTrue(logged_in)
        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        # Find latest audit for dashboard path
        logs = AuditLog.objects.filter(path__startswith='/dashboard').order_by('-created_at')
        self.assertTrue(logs.exists())
        latest = logs.first()
        self.assertIsNotNone(latest.user)
        self.assertEqual(latest.user.id, user.id)

    def test_password_in_post_is_redacted(self):
        AuditLog.objects.all().delete()
        url = reverse('signup')
        data = {
            'email': 'redact@example.com',
            'first_name': 'Red',
            'last_name': 'Action',
            'password1': 'SuperSecret!',
            'password2': 'SuperSecret!',
        }
        response = self.client.post(url, data, follow=True)
        # Ensure signup happened
        self.assertIn(response.status_code, (200, 302))
        # Get latest audit entry for signup path
        logs = AuditLog.objects.filter(path__startswith='/accounts/signup').order_by('-created_at')
        self.assertTrue(logs.exists())
        payload = logs.first().payload
        # payload keys may be lists from POST; redaction should replace value with '[REDACTED]'
        self.assertIn('password1', payload)
        self.assertEqual(payload['password1'], '[REDACTED]')
