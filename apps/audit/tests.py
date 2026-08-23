from django.test import TestCase, Client
from django.contrib.contenttypes.models import ContentType
from apps.accounts.models import CustomUser
from apps.audit.models import AuditLog, AuditExport


class AuditLogTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='owner',
        )
        self.content_type = ContentType.objects.get_for_model(CustomUser)

    def test_audit_log_creation(self):
        log = AuditLog.objects.create(
            user=self.user,
            action='create',
            content_type=self.content_type,
            object_id=self.user.id,
            object_repr='test@example.com',
            ip_address='127.0.0.1',
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'create')

    def test_audit_log_filtering(self):
        log1 = AuditLog.objects.create(
            user=self.user,
            action='create',
            object_repr='User 1',
            ip_address='127.0.0.1',
        )
        log2 = AuditLog.objects.create(
            user=self.user,
            action='update',
            object_repr='User 2',
            ip_address='127.0.0.1',
        )
        
        creates = AuditLog.objects.filter(action='create')
        self.assertEqual(creates.count(), 1)
        self.assertEqual(creates.first().object_repr, 'User 1')


class AuditExportTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='owner',
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_audit_export_creation(self):
        content_type = ContentType.objects.get_for_model(CustomUser)
        export = AuditExport.objects.create(
            user=self.user,
            content_type=content_type,
            format='csv',
            row_count=100,
        )
        self.assertEqual(export.user, self.user)
        self.assertEqual(export.format, 'csv')

    def test_audit_export_api(self):
        response = self.client.get('/api/audit/logs/')
        self.assertEqual(response.status_code, 200)
