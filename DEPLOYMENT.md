# Django Starter - Deployment Guide

This guide covers deploying Django Starter to production environments.

## 🔒 Security Checklist

Before deploying to production, ensure:

- [ ] `DEBUG = False` in settings
- [ ] Generate new `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS/SSL
- [ ] Set secure cookie flags
- [ ] Configure strong passwords for database
- [ ] Use environment variables for secrets
- [ ] Enable CSRF protection
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Enable logging and monitoring

## Environment Variables

Create a `.env.production` file with production settings:

```bash
# Django
DEBUG=False
SECRET_KEY=your-long-random-secret-key-change-this
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL)
DB_NAME=django_admin_pro_prod
DB_USER=db_user
DB_PASSWORD=strong-password-here
DB_HOST=db.yourdomain.com
DB_PORT=5432

# Redis
REDIS_URL=redis://redis.yourdomain.com:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key

# AWS S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Stripe
STRIPE_PUBLIC_KEY=pk_live_your_key
STRIPE_SECRET_KEY=sk_live_your_key

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## Deployment Options

### Option 1: DigitalOcean App Platform

1. **Create PostgreSQL Database**
   ```bash
   # In DigitalOcean Console
   - Create new Database Cluster (PostgreSQL 15)
   - Note connection string
   ```

2. **Create Redis Cache**
   ```bash
   # In DigitalOcean Console
   - Create new Database (Redis)
   - Note connection string
   ```

3. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial Django Starter setup"
   git push origin main
   ```

4. **Deploy via App Platform**
   - Connect GitHub repository
   - Create new app
   - Add PostgreSQL and Redis resources
   - Configure environment variables
   - Deploy

### Option 2: Heroku

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Ubuntu
   curl https://cli-assets.heroku.com/install-ubuntu.sh | sh
   ```

2. **Create app and add-ons**
   ```bash
   heroku login
   heroku create your-app-name
   
   # Add PostgreSQL
   heroku addons:create heroku-postgresql:standard-0
   
   # Add Redis
   heroku addons:create heroku-redis:premium-0
   ```

3. **Create Procfile**
   ```
   web: gunicorn config.wsgi:application --log-file -
   worker: celery -A config worker -l info
   beat: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

4. **Deploy**
   ```bash
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py create_demo_data
   ```

### Option 3: AWS EC2

1. **Launch EC2 Instance**
   - Amazon Linux 2 or Ubuntu 22.04
   - t3.medium or larger
   - Security group with ports 80, 443, 22 open

2. **Install dependencies**
   ```bash
   ssh -i your-key.pem ec2-user@your-instance-ip
   
   # Ubuntu
   sudo apt update && sudo apt install -y python3.11 python3-pip postgresql-client redis-tools nginx supervisor git
   
   # Amazon Linux
   sudo yum install -y python3.11 python3-pip postgresql postgresql-contrib nginx supervisor git
   ```

3. **Clone and setup**
   ```bash
   git clone your-repo-url
   cd django-admin-pro
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with production values
   ```

5. **Setup Gunicorn**
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/gunicorn.service
   ```

   ```ini
   [Unit]
   Description=Gunicorn Django Starter
   After=network.target
   
   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/home/ubuntu/django-admin-pro
   Environment="PATH=/home/ubuntu/django-admin-pro/venv/bin"
   ExecStart=/home/ubuntu/django-admin-pro/venv/bin/gunicorn \
       --workers 3 \
       --bind unix:/run/gunicorn.sock \
       config.wsgi:application
   
   [Install]
   WantedBy=multi-user.target
   ```

6. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/django-admin-pro
   ```

   ```nginx
   upstream gunicorn {
       server unix:/run/gunicorn.sock;
   }
   
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       
       location / {
           proxy_pass http://gunicorn;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static/ {
           alias /home/ubuntu/django-admin-pro/staticfiles/;
       }
   }
   ```

   ```bash
   sudo ln -s /etc/nginx/sites-available/django-admin-pro /etc/nginx/sites-enabled/
   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

7. **Setup SSL with Let's Encrypt**
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

8. **Start services**
   ```bash
   sudo systemctl start gunicorn
   sudo systemctl enable gunicorn
   sudo systemctl start celery
   sudo systemctl start celery-beat
   ```

### Option 4: Docker on VPS

1. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Setup Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Configure and deploy**
   ```bash
   git clone your-repo-url
   cd django-admin-pro
   cp .env.example .env
   nano .env  # Set production values
   
   # Build and run
   docker-compose up -d
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py create_demo_data
   ```

4. **Setup Nginx reverse proxy**
   ```bash
   sudo apt install -y nginx
   
   sudo tee /etc/nginx/sites-available/default > /dev/null <<EOF
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host \$host;
           proxy_set_header X-Real-IP \$remote_addr;
       }
   }
   EOF
   
   sudo systemctl restart nginx
   ```

## Database Backups

### PostgreSQL Backup Strategy

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="django_admin_pro"

pg_dump -U $DB_USER -h $DB_HOST $DB_NAME > $BACKUP_DIR/backup_$TIMESTAMP.sql
gzip $BACKUP_DIR/backup_$TIMESTAMP.sql

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### Restore from Backup

```bash
gunzip < backup_20240115_120000.sql.gz | psql -U user -h host django_admin_pro
```

## Monitoring & Logging

### Sentry Integration

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)
```

### Application Logs

```python
# Configure logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

## Performance Optimization

### Database Optimization

```python
# Use select_related for foreign keys
users = CustomUser.objects.select_related('dashboard')

# Use prefetch_related for reverse relations
from django.db.models import Prefetch
logs = AuditLog.objects.prefetch_related(
    Prefetch('user', queryset=CustomUser.objects.only('id', 'email'))
)

# Add database indexes
class AuditLog(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
```

### Caching

```python
# Redis caching
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # 5 minutes
def dashboard_stats(request):
    # Expensive query
    pass
```

## Troubleshooting

### Common Issues

**Issue: "connect() failed: No such file or directory"**
- Check PostgreSQL is running
- Verify connection string in .env

**Issue: "Celery tasks not running"**
- Verify Redis is accessible
- Check Celery worker logs
- Ensure tasks are imported

**Issue: "Static files not loading"**
- Run `python manage.py collectstatic`
- Check STATIC_URL and STATIC_ROOT
- Verify Nginx configuration

---

For more help, visit: https://djangoadminpro.com/docs
