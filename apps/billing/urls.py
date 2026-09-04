from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BillingViewSet, billing_dashboard_view, checkout_session_view, stripe_webhook_view

router = DefaultRouter()
router.register(r'billing', BillingViewSet, basename='api-billing')

urlpatterns = [
    path('', billing_dashboard_view, name='billing_dashboard'),
    path('checkout/', checkout_session_view, name='billing_checkout'),
    path('webhook/', stripe_webhook_view, name='stripe_webhook'),
    path('api/', include(router.urls)),
]
