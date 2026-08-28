from django.test import TestCase, Client

from apps.accounts.models import CustomUser
from apps.dashboard.models import Dashboard


class DashboardTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_dashboard_home_view(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/home.html')

    def test_dashboard_stats_api(self):
        response = self.client.get('/api/dashboard/stats/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_users', data)
        self.assertIn('active_users', data)

    def test_dashboard_user_creation(self):
        dashboard, created = Dashboard.objects.get_or_create(user=self.user)
        self.assertEqual(dashboard.user, self.user)
        self.assertEqual(dashboard.theme, 'light')


class DashboardChartTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_signups_chart(self):
        response = self.client.get('/api/dashboard/chart-signups/?months=6')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('labels', data)
        self.assertIn('data', data)
