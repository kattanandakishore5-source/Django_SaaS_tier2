from django.db import models
from django.conf import settings


class Subscription(models.Model):
    """
    Stripe subscription linked to a user account.
    Stores the essential Stripe identifiers and subscription state
    needed to gate features and manage billing lifecycle.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Stripe Customer ID (cus_...)',
    )
    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Stripe Subscription ID (sub_...)',
    )
    plan_name = models.CharField(
        max_length=100,
        blank=True,
        default='free',
        help_text='Human-readable plan name (e.g. free, pro, enterprise)',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )
    current_period_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text='End of the current billing period (from Stripe)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.plan_name} ({self.status})"
