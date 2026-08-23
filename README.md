# Django Admin Pro - SaaS Dashboard Boilerplate

**Django Admin Pro** is a production-ready SaaS dashboard boilerplate built with Django 4.2, designed to help developers rapidly build customer-facing admin panels. Unlike traditional Django admin themes (like Unfold, Jazzmin), Django Admin Pro escapes the admin jail with custom views, modern authentication, RBAC, and pre-wired analytics.

## 🚀 Features

### ✅ Authentication & Authorization
- **Email-based authentication** (no username needed)
- **Magic link login** (passwordless authentication)
- **Two-factor authentication (2FA)** - Email, SMS, Authenticator app
- **Password reset flow** - Secure token-based reset
- **Role-based access control (RBAC)** - Owner, Manager, Viewer roles
- **API key management** - For programmatic access

### 📊 Dashboard & Analytics
- **Pre-built metric cards** - Total users, active users, verified users, signups
- **Chart.js integration** - User signups by month, role distribution
- **Real-time activity feed** - System-wide activity tracking
- **Responsive design** - Mobile-first with Tailwind CSS

### 🔍 Advanced Features
- **System audit logging** - Track all CRUD operations with middleware
- **One-click data exports** - CSV/JSON export for any data table
- **Global search** - Search across multiple models via HTMX
- **Profile management** - User avatars, bio, phone number
- **Dark/Light mode toggle** - Persistent theme with Alpine.js

### 🔧 Developer Experience
- **Dockerized setup** - Docker Compose with PostgreSQL, Redis
- **Pre-configured Celery** - Async tasks for emails, reports
- **DRF integration** - REST API with pagination, filtering
- **Stripe/Lemonsqueezy ready** - Payment processing hooks
- **API documentation** - Swagger/ReDoc auto-generated docs

---

## 📋 Project Structure

```
django-admin-pro/
├── config/                  # Django settings & WSGI/ASGI
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/                    # Django apps
│   ├── accounts/           # User authentication & profiles
│   ├── dashboard/          # Dashboard views & metrics
│   ├── audit/              # Audit logging
│   └── core/               # Utilities, decorators, permissions
├── templates/              # HTML templates (Tailwind + Alpine.js)
├── static/                 # CSS, JavaScript, images
├── manage.py
├── docker-compose.yml      # Docker services
├── Dockerfile
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (if running without Docker)
- PostgreSQL 15+ (if running without Docker)
- Redis 7+ (if running without Docker)

### Installation

#### Option 1: With Docker (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd django-admin-pro

# Copy environment file
cp .env.example .env

# Start Docker services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access the dashboard
# - Dashboard: http://localhost:8000/dashboard/
# - Admin: http://localhost:8000/admin/
# - API Docs: http://localhost:8000/api/docs/
```

#### Option 2: Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Configure .env with your database and email settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start Celery (in another terminal)
celery -A config worker -l info

# Start Celery Beat (in another terminal)
celery -A config beat -l info

# Run development server
python manage.py runserver
```

---

## 📖 Usage Guide

### Authentication Endpoints

```bash
# Sign up
POST /api/auth/signup/
{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}

# Login
POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "securepassword"
}

# Magic link login
POST /api/auth/magic_link/
{
  "email": "user@example.com"
}

# Verify magic link
POST /api/auth/verify-magic-link/
{
  "token": "<magic_link_token>"
}

# Enable 2FA
POST /api/auth/enable-2fa/
{
  "method": "email"  # or "sms", "authenticator"
}

# Verify 2FA
POST /api/auth/verify-2fa/
{
  "token": "123456"
}

# Password reset request
POST /api/auth/forgot-password/
{
  "email": "user@example.com"
}

# Reset password
POST /api/auth/reset-password/
{
  "token": "<reset_token>",
  "password": "newpassword"
}
```

### Dashboard Endpoints

```bash
# Get dashboard stats
GET /api/dashboard/stats/

# Get signup chart data
GET /api/dashboard/chart-signups/?months=6

# Get role distribution
GET /api/dashboard/chart-role-distribution/

# Get recent activity
GET /api/dashboard/recent-activity/?limit=10
```

### Audit Logging

```bash
# Get audit logs
GET /api/audit/logs/

# Filter by action
GET /api/audit/logs/?action=create

# Search
GET /api/audit/logs/?search=email

# Export to CSV
GET /api/audit/logs/export_csv/

# Export to JSON
GET /api/audit/logs/export_json/
```

### User Management

```bash
# Get current user profile
GET /api/auth/users/profile/

# Update profile
PUT /api/auth/users/profile_update/
{
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}

# Change password
POST /api/auth/users/change_password/
{
  "old_password": "current",
  "new_password": "new"
}

# Create API key
POST /api/auth/api-keys/
{
  "name": "Production API"
}

# Regenerate API key
POST /api/auth/api-keys/{id}/regenerate/
```

---

## 🔐 Role-Based Access Control

Django Admin Pro includes three predefined roles:

| Role | Permissions |
|------|------------|
| **Owner** | Full access - can manage users, view all logs, billing |
| **Manager** | Can view logs, manage users, but no billing access |
| **Viewer** | Read-only access - can view dashboard, own data |

### Using RBAC Decorators

```python
from apps.core.decorators import role_required, owner_required

@role_required('owner', 'manager')
def admin_only_view(request):
    return Response({'message': 'Owner or manager only'})

@owner_required
def owner_only_view(request):
    return Response({'message': 'Owner only'})
```

### DRF Permission Classes

```python
from apps.core.permissions import IsOwner, IsManager, OwnerOrReadOnly

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwner]  # Only owners can access
```

---

## 📨 Email Configuration

### Using Gmail SMTP

```bash
# In .env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Generate in Google Account Security
```

### Sending Emails Asynchronously

```python
from apps.core.utils import send_email_async

send_email_async.delay(
    subject='Welcome!',
    message='Welcome to Django Admin Pro',
    recipient_list=['user@example.com'],
    template='welcome',
    context={'name': 'John'}
)
```

---

## 💳 Payment Integration

### Stripe Integration Example

```python
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create a checkout session
session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{
        'price_data': {
            'currency': 'usd',
            'product_data': {'name': 'Professional Plan'},
            'unit_amount': 9900,
        },
        'quantity': 1,
    }],
    mode='subscription',
    success_url='http://localhost:8000/dashboard/?session_id={CHECKOUT_SESSION_ID}',
    cancel_url='http://localhost:8000/dashboard/',
)
```

---

## 🗄️ Database Schema

### Key Models

**CustomUser**
- Email-based authentication
- RBAC roles
- Two-factor authentication
- Profile fields (avatar, phone, bio)

**AuditLog**
- System-wide activity tracking
- IP address & user agent logging
- Indexed by date and user for fast queries

**MagicLink**
- Passwordless authentication tokens
- 24-hour expiry

**PasswordReset**
- Secure password reset tokens
- 24-hour expiry

**APIKey**
- User API keys for programmatic access
- Last used tracking

---

## 🛠️ Celery Tasks

### Built-in Tasks

```python
# Send weekly digest
send_weekly_digest()

# Clean up expired sessions
cleanup_expired_sessions()

# Generate daily report
generate_daily_report()
```

### Scheduling

Edit `config/celery.py` to add recurring tasks:

```python
app.conf.beat_schedule = {
    'send-weekly-digest': {
        'task': 'apps.accounts.tasks.send_weekly_digest',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
}
```

---

## 🧪 Testing

```bash
# Run tests
python manage.py test

# With coverage
coverage run --source='.' manage.py test
coverage report
```

---

## 📦 Deployment

### Production Checklist

```bash
# 1. Set DEBUG=False
DEBUG=False

# 2. Generate new SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# 3. Enable HTTPS
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Run migrations
python manage.py migrate

# 6. Use production server (not runserver)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Docker Production Build

```bash
# Build production image
docker build -t django-admin-pro:latest .

# Run with environment
docker run -d \
  --name django-admin-pro \
  -e DEBUG=False \
  -e SECRET_KEY=your-key \
  -p 8000:8000 \
  django-admin-pro:latest
```

---

## 📚 API Documentation

Swagger docs available at: `http://localhost:8000/api/docs/`
ReDoc docs available at: `http://localhost:8000/api/redoc/`

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 💬 Support

For questions or issues:
- GitHub Issues: [Link to issues]
- Email: support@djangoadminpro.com
- Documentation: [Link to docs]

---

## 🙏 Acknowledgments

- Built with [Django](https://www.djangoproject.com/)
- UI with [Tailwind CSS](https://tailwindcss.com/)
- Interactivity with [Alpine.js](https://alpinejs.dev/) & [HTMX](https://htmx.org/)
- Charts with [Chart.js](https://www.chartjs.org/)
- Async tasks with [Celery](https://docs.celeryproject.org/)

---

**Happy coding! 🚀**
