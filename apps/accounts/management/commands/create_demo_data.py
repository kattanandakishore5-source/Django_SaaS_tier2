from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Create demo users and data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo users...')

        owner, _ = CustomUser.objects.get_or_create(
            email='owner@example.com',
            defaults={
                'first_name': 'Owner',
                'last_name': 'User',
                'is_verified': True,
                'is_active': True,
                'is_staff': True,
            }
        )
        if _:
            owner.set_password('password123')
            owner.save()
            self.stdout.write(self.style.SUCCESS(f'Created owner: {owner.email}'))

        manager, _ = CustomUser.objects.get_or_create(
            email='manager@example.com',
            defaults={
                'first_name': 'Manager',
                'last_name': 'User',
                'is_verified': True,
                'is_active': True,
            }
        )
        if _:
            manager.set_password('password123')
            manager.save()
            self.stdout.write(self.style.SUCCESS(f'Created manager: {manager.email}'))

        viewer, _ = CustomUser.objects.get_or_create(
            email='viewer@example.com',
            defaults={
                'first_name': 'Viewer',
                'last_name': 'User',
                'is_verified': True,
                'is_active': True,
            }
        )
        if _:
            viewer.set_password('password123')
            viewer.save()
            self.stdout.write(self.style.SUCCESS(f'Created viewer: {viewer.email}'))

        for i in range(5):
            email = f'user{i}@example.com'
            user, _ = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': f'User{i}',
                    'last_name': 'Demo',
                    'is_verified': True,
                    'is_active': True,
                    'created_at': timezone.now() - timedelta(days=30-i*5),
                }
            )
            if _:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {user.email}'))

        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))
        self.stdout.write(self.style.WARNING('Default credentials:'))
        self.stdout.write('  Email: owner@example.com | Password: password123')
        self.stdout.write('  Email: manager@example.com | Password: password123')
        self.stdout.write('  Email: viewer@example.com | Password: password123')
