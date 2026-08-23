from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserViewSet, APIKeyViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='users')
router.register(r'api-keys', APIKeyViewSet, basename='api-keys')

urlpatterns = [
    path('', include(router.urls)),
]
