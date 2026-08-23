from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import csv
import json
from io import StringIO


@shared_task
def send_email_async(subject, message, recipient_list, template=None, context=None):
    """Send email asynchronously"""
    try:
        if template and context:
            html_message = render_to_string(f'emails/{template}.html', context)
            message = strip_tags(html_message)
        else:
            html_message = None

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return f"Email sent to {recipient_list}"
    except Exception as e:
        return f"Error sending email: {e}"


class DataExporter:
    """Export data to CSV or JSON"""

    @staticmethod
    def export_to_csv(queryset, fields):
        """Export queryset to CSV"""
        output = StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(fields)

        # Write data
        for obj in queryset:
            row = [getattr(obj, field) for field in fields]
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def export_to_json(queryset, serializer_class):
        """Export queryset to JSON using DRF serializer"""
        serializer = serializer_class(queryset, many=True)
        return json.dumps(serializer.data, indent=2, default=str)


class GlobalSearch:
    """Global search across multiple models"""

    @staticmethod
    def search(query, models):
        """Search across multiple models"""
        results = {}
        for model, search_fields in models.items():
            from django.db.models import Q
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f'{field}__icontains': query})
            results[model.__name__] = model.objects.filter(q_objects)[:5]
        return results


class PaginationHelper:
    """Helper for pagination"""

    @staticmethod
    def paginate_queryset(queryset, page, page_size=20):
        """Paginate a queryset"""
        start = (page - 1) * page_size
        end = start + page_size
        total = queryset.count()
        paginated = queryset[start:end]
        return {
            'data': paginated,
            'page': page,
            'page_size': page_size,
            'total': total,
            'pages': (total + page_size - 1) // page_size,
        }
