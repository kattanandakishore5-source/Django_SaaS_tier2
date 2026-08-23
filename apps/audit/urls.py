from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, AuditExportViewSet

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-logs')
router.register(r'exports', AuditExportViewSet, basename='audit-exports')

urlpatterns = [
    path('', include(router.urls)),
]
