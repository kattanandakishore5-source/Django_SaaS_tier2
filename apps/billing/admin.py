from django.contrib import admin
from .models import StripeCustomer, Subscription, WebhookEvent


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'stripe_customer_id', 'created_at')
    search_fields = ('user__email', 'stripe_customer_id')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'stripe_subscription_id', 'stripe_price_id', 'status', 'current_period_end', 'cancel_at_period_end')
    list_filter = ('status', 'cancel_at_period_end')
    search_fields = ('user__email', 'stripe_subscription_id', 'stripe_price_id')


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'event_type', 'processed', 'created_at')
    list_filter = ('processed', 'event_type')
    search_fields = ('event_id', 'event_type')
