from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from apps.accounts.views import root_redirect

schema_view = get_schema_view(
    openapi.Info(
        title='Django Starter API',
        default_version='v1',
        description='Starter dashboard API',
        contact=openapi.Contact(email='kattanandakishore5@gmail.com'),
        license=openapi.License(name='MIT License'),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', root_redirect, name='root-redirect'),
    path('accounts/', include('apps.accounts.browser_urls')),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('dashboard/', include('apps.dashboard.views_urls')),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
