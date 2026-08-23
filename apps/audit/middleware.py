from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .models import AuditLog
import json


class AuditLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all requests to audit trail"""

    def process_request(self, request):
        request._audit_start = True
        return None

    def process_response(self, request, response):
        if not getattr(request, '_audit_start', False):
            return response

        # Skip excluded URLs
        excluded_urls = settings.AUDIT_LOG_EXCLUDED_URLS
        if any(request.path.startswith(url) for url in excluded_urls):
            return response

        # Skip excluded methods
        excluded_methods = settings.AUDIT_LOG_EXCLUDED_METHODS
        if request.method in excluded_methods:
            return response

        # Get user IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        # Log to AuditLog
        try:
            action = 'view' if request.method == 'GET' else 'update' if request.method in ['PUT', 'PATCH'] else 'create' if request.method == 'POST' else 'delete' if request.method == 'DELETE' else 'view'
            user_id = request.user.id if request.user.is_authenticated else None

            from .tasks import log_audit_action_async
            log_audit_action_async.delay(
                user_id=user_id,
                action=action,
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            )
        except Exception as e:
            print(f"Error logging audit: {e}")

        return response
