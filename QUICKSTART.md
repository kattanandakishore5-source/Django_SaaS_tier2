# Django Admin Pro - Quick Start Guide

Get up and running in 5 minutes!

## 🚀 Quick Start with Docker (Recommended)

### Prerequisites
- Docker & Docker Compose installed
- Git installed

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/django-admin-pro.git
cd django-admin-pro

# 2. Copy environment file
cp .env.example .env

# 3. Start services
docker-compose up -d

# 4. Run migrations
docker-compose exec web python manage.py migrate

# 5. Create demo data
docker-compose exec web python manage.py create_demo_data

# 6. Access the app
# Dashboard: http://localhost:8000/dashboard/
# Admin: http://localhost:8000/admin/
# API Docs: http://localhost:8000/api/docs/
```

**Demo Credentials:**
- Email: `owner@example.com`
- Password: `password123`

---

## 🐍 Local Setup (Without Docker)

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- pip & virtualenv

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/django-admin-pro.git
cd django-admin-pro

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env

# 5. Configure .env
nano .env
# Update database credentials, email settings, etc.

# 6. Run migrations
python manage.py migrate

# 7. Create demo data
python manage.py create_demo_data

# 8. Start development server (Terminal 1)
python manage.py runserver

# 9. Start Celery worker (Terminal 2)
celery -A config worker -l info

# 10. Start Celery Beat scheduler (Terminal 3)
celery -A config beat -l info

# 11. Access the app
# Dashboard: http://localhost:8000/dashboard/
# Admin: http://localhost:8000/admin/
```

---

## 📝 Common Commands

### Database
```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Revert migrations
python manage.py migrate app_name 0001

# Show migration status
python manage.py showmigrations
```

### Users
```bash
# Create superuser
python manage.py createsuperuser

# Create demo data
python manage.py create_demo_data

# Change user password
python manage.py changepassword username
```

### Development
```bash
# Run tests
python manage.py test

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report

# Django shell
python manage.py shell

# Lint code
pylint apps/

# Format code
black .
```

### Celery
```bash
# Start worker
celery -A config worker -l info

# Start scheduler
celery -A config beat -l info

# Purge queue
celery -A config purge

# Inspect active tasks
celery -A config inspect active
```

### Static Files
```bash
# Collect static files
python manage.py collectstatic --noinput

# Clear stale static files
python manage.py collectstatic --clear --noinput
```

---

## 🔌 API Examples

### Authentication

```bash
# Sign up
curl -X POST http://localhost:8000/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@example.com",
    "password": "password123"
  }'

# Get current user
curl -X GET http://localhost:8000/api/auth/users/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Dashboard

```bash
# Get stats
curl -X GET http://localhost:8000/api/dashboard/stats/

# Get signup chart data
curl -X GET "http://localhost:8000/api/dashboard/chart-signups/?months=6"

# Get role distribution
curl -X GET http://localhost:8000/api/dashboard/chart-role-distribution/

# Get recent activity
curl -X GET "http://localhost:8000/api/dashboard/recent-activity/?limit=10"
```

### Audit Logs

```bash
# Get audit logs
curl -X GET http://localhost:8000/api/audit/logs/

# Export to CSV
curl -X GET http://localhost:8000/api/audit/logs/export_csv/ > logs.csv

# Export to JSON
curl -X GET http://localhost:8000/api/audit/logs/export_json/ > logs.json
```

---

## 🧪 Testing

### Run All Tests
```bash
python manage.py test
```

### Run Specific App Tests
```bash
python manage.py test apps.accounts
python manage.py test apps.dashboard
python manage.py test apps.audit
```

### Run Specific Test Class
```bash
python manage.py test apps.accounts.tests.CustomUserTestCase
```

### Run with Coverage
```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

---

## 📦 Project Structure

```
django-admin-pro/
├── config/                 # Django configuration
│   ├── settings.py        # Main settings
│   ├── urls.py            # URL routing
│   ├── wsgi.py            # WSGI server
│   └── celery.py          # Celery config
├── apps/                  # Django apps
│   ├── accounts/          # User auth & profiles
│   ├── dashboard/         # Dashboard views
│   ├── audit/             # Audit logging
│   └── core/              # Utilities & helpers
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── sidebar.html      # Navigation sidebar
│   ├── dashboard/        # Dashboard pages
│   └── emails/           # Email templates
├── static/               # CSS, JS, images
├── manage.py            # Django CLI
├── docker-compose.yml   # Docker services
├── Dockerfile           # Container image
├── requirements.txt     # Python dependencies
└── README.md           # Main documentation
```

---

## 🛠️ Customization

### Adding a New App

```bash
# Create app
python manage.py startapp myapp

# Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    ...
    'apps.myapp',
]

# Create models, views, urls, etc.
# Run migrations
python manage.py makemigrations
python manage.py migrate
```

### Customizing User Model

The project uses a custom `CustomUser` model with:
- Email-based authentication (no username)
- Role-based access control
- Two-factor authentication support
- API key management

Edit `apps/accounts/models.py` to add more fields:

```python
class CustomUser(AbstractUser):
    # Add custom fields
    company = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    # ... more fields
```

Then run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Adding RBAC to Views

```python
from apps.core.decorators import role_required
from apps.core.permissions import IsOwner

# Function-based views
@role_required('owner', 'manager')
def admin_view(request):
    return Response({'message': 'Admin only'})

# Class-based views
from rest_framework.permissions import IsAuthenticated
from apps.core.permissions import IsManager

class AdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsManager]
    # ... view code
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Error
```bash
# Check PostgreSQL is running
sudo service postgresql status

# Verify .env database settings
cat .env | grep DB_
```

### Celery Not Working
```bash
# Check Redis connection
redis-cli ping

# Verify REDIS_URL in .env
# Check Celery logs for errors
celery -A config worker -l debug
```

### Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --noinput --clear

# Check STATIC_URL and STATIC_ROOT in settings
```

---

## 📚 Useful Resources

- Django Docs: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- Celery: https://docs.celeryproject.org/
- PostgreSQL: https://www.postgresql.org/docs/
- Redis: https://redis.io/documentation

---

## 💬 Need Help?

- Check the main [README.md](README.md)
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- Open an issue on GitHub
- Email: support@djangoadminpro.com

---

**Happy coding! 🚀**
