from django.test import TestCase
from unittest.mock import patch

from apps.accounts import services
from apps.accounts.models import CustomUser, PasswordReset


class TestCeleryEmailTasks(TestCase):
    def test_create_user_dispatches_email_task(self):
        with patch('apps.core.utils.send_email_async') as mock_task:
            # mock_task.delay is a Mock as well
            services.create_user_account('async-task-test@example.com', 'pass123', first_name='A', last_name='B')
            self.assertTrue(CustomUser.objects.filter(email='async-task-test@example.com').exists())
            self.assertTrue(mock_task.delay.called or mock_task.called)

    def test_initiate_password_reset_dispatches_email_task(self):
        user = CustomUser.objects.create_user(email='async-magic-test@example.com', password='pw123')
        with patch('apps.core.utils.send_email_async') as mock_task:
            result = services.initiate_password_reset('async-magic-test@example.com', base_url='https://example.com/reset/')
            self.assertTrue(result)
            self.assertTrue(PasswordReset.objects.filter(user=user).exists())
            self.assertTrue(mock_task.delay.called or mock_task.called)

    def test_send_email_task_is_shared_task(self):
        # The Celery shared_task creates an object with a .delay attribute when imported
        try:
            from apps.core import tasks
            self.assertTrue(hasattr(tasks.send_email_async, 'delay'))
        except ImportError:
            self.fail('apps.core.tasks cannot be imported')
