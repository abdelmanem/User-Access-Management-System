# Installation & Upgrade Guide

This guide covers installing UAMS from scratch and upgrading existing installations.

![Installation Process](../images/installation-process.png)

## Prerequisites

Before installing UAMS, ensure you have:

### Required Software

- **Python**: 3.8 or higher
- **pip**: Python package manager
- **Virtual Environment**: Python venv (recommended)
- **Database**: SQLite (development) or PostgreSQL (production)
- **Web Server**: Nginx or Apache (production)
- **WSGI Server**: Gunicorn or uWSGI (production)

### System Requirements

**Development Environment**:
- 2GB RAM minimum
- 1GB disk space
- Python 3.8+

**Production Environment**:
- 4GB RAM minimum (8GB recommended)
- 10GB disk space minimum
- Python 3.8+
- PostgreSQL 12+ (recommended)
- Nginx or Apache
- SSL certificate (recommended)

## Installation Methods

### Method 1: Standard Installation

#### Step 1: Clone or Download

```bash
# Clone from repository
git clone https://github.com/abdelmanem/User-Access-Management-System.git
cd User-Access-Management-System

# Or download and extract ZIP file
```

#### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# For production, install additional packages:
pip install gunicorn psycopg2-binary
```

#### Step 4: Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings
# Required settings:
# - SECRET_KEY
# - DEBUG
# - DATABASE_URL (for PostgreSQL)
# - ALLOWED_HOSTS
```

**Example .env file**:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/uams_db
USE_WHITENOISE=True
```

#### Step 5: Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (optional)
python manage.py loaddata initial_data.json
```

#### Step 6: Collect Static Files

```bash
# Collect static files
python manage.py collectstatic --noinput
```

#### Step 7: Run Development Server

```bash
# Start development server
python manage.py runserver

# Access at http://127.0.0.1:8000
```

### Method 2: Docker Installation

#### Step 1: Clone Repository

```bash
git clone https://github.com/abdelmanem/User-Access-Management-System.git
cd User-Access-Management-System
```

#### Step 2: Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env with your settings
```

#### Step 3: Build and Run

```bash
# Build Docker image
docker-compose build

# Start containers
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

#### Step 4: Access Application

```bash
# Access at http://localhost:8000
# Or the port configured in docker-compose.yml
```

**Docker Compose Configuration**:

```yaml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn user_access_management.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/uams_db
    depends_on:
      - db

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=uams_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password

volumes:
  postgres_data:
```

## Production Deployment

### Using Gunicorn

#### Step 1: Install Gunicorn

```bash
pip install gunicorn
```

#### Step 2: Create Gunicorn Configuration

Create `gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

#### Step 3: Start Gunicorn

```bash
gunicorn -c gunicorn_config.py user_access_management.wsgi:application
```

### Using Nginx

#### Step 1: Install Nginx

```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### Step 2: Configure Nginx

Create `/etc/nginx/sites-available/uams`:

```nginx

# /etc/nginx/sites-available/uams.conf  (fixed)

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate     /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Static
    location /static/ {
        alias /srv/uams/app/staticfiles/;
        autoindex off; access_log off; expires 7d;
    }

    # Media
    location /media/ {
        alias /srv/uams/app/media/;
        autoindex off; expires 7d;
    }

    # Documentation
    location /doc/ {
        alias /path/to/User-Access-Management-System/site/;
        try_files $uri $uri/ /doc/index.html;
        index index.html;
        
        # Cache static assets
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }



    # App (HTTP over unix socket)
    location / {
        include proxy_params;               # keep this
        proxy_pass http://unix:/run/uams/uams.sock;

        # REMOVE duplicate headers:
        # proxy_set_header Host $host;
        # proxy_set_header X-Forwarded-Proto $scheme;
        # proxy_set_header X-Real-IP $remote_addr;
        # proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_read_timeout 300;
        proxy_connect_timeout 60;
        proxy_send_timeout 300;
    }

    client_max_body_size 20M;
}

server {
    listen 80;
    server_name yourdomain.com Server_IPadd;
    return 301 https://$host$request_uri;
}

```

#### Step 3: Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/uams /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Using Systemd

#### Step 1: Create Service File

Create `/etc/systemd/system/uams.service`:

```ini
[Unit]
Description=UAMS Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/User-Access-Management-System
ExecStart=/path/to/venv/bin/gunicorn \
    --access-logfile - \
    --workers 4 \
    --bind unix:/run/uams.sock \
    user_access_management.wsgi:application

[Install]
WantedBy=multi-user.target
```

#### Step 2: Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl start uams
sudo systemctl enable uams
```

### SSL Configuration

#### Using Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
```

## Database Setup

### SQLite (Development)

SQLite is used by default for development. No additional setup required.

### PostgreSQL (Production)

#### Step 1: Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
```

#### Step 2: Create Database

```bash
sudo -u postgres psql

CREATE DATABASE uams_db;
CREATE USER uams_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE uams_db TO uams_user;
\q
```

#### Step 3: Configure Django

Update `.env`:

```env
DATABASE_URL=postgresql://uams_user:your_password@localhost:5432/uams_db
```

#### Step 4: Run Migrations

```bash
python manage.py migrate
```

## Upgrade Procedures

### Pre-Upgrade Checklist

1. **Backup Database**: Create full database backup
2. **Backup Files**: Backup media files and static files
3. **Review Release Notes**: Check [Release Notes](release_notes.md)
4. **Test in Staging**: Test upgrade in staging environment
5. **Notify Users**: Inform users of maintenance window

### Upgrade Steps

#### Step 1: Backup

```bash
# Backup database
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Backup media files
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Backup static files
tar -czf static_backup_$(date +%Y%m%d).tar.gz staticfiles/
```

#### Step 2: Update Code

```bash
# Pull latest code
git pull origin main

# Or download new release
```

#### Step 3: Update Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Update packages
pip install -r requirements.txt --upgrade
```

#### Step 4: Run Migrations

```bash
# Run database migrations
python manage.py migrate

# Check for migration issues
python manage.py showmigrations
```

#### Step 5: Update Static Files

```bash
# Collect static files
python manage.py collectstatic --noinput
```

#### Step 6: Restart Services

```bash
# Restart Gunicorn
sudo systemctl restart uams

# Restart Nginx (if needed)
sudo systemctl restart nginx
```

#### Step 7: Verify

- Check application is running
- Verify database migrations applied
- Test critical functionality
- Check error logs

### Rollback Procedure

If upgrade fails:

#### Step 1: Stop Services

```bash
sudo systemctl stop uams
```

#### Step 2: Restore Code

```bash
# Restore previous version
git checkout <previous-version-tag>
```

#### Step 3: Restore Database

```bash
# Restore database backup
python manage.py loaddata backup_YYYYMMDD.json
```

#### Step 4: Restart Services

```bash
sudo systemctl start uams
```

## Post-Installation Configuration

### Initial Setup

1. **Create Superuser**: Already done during installation
2. **Configure Settings**: Review [Configuration](configuration.md)
3. **Set Up Departments**: Create organizational structure
4. **Import Users**: Import user data if available
5. **Configure Systems**: Add systems to catalog
6. **Set Permissions**: Configure user roles and permissions

### Security Hardening

1. **Change Default Passwords**: Change all default passwords
2. **Configure HTTPS**: Set up SSL certificates
3. **Set ALLOWED_HOSTS**: Configure allowed hosts
4. **Disable DEBUG**: Set DEBUG=False in production
5. **Set SECRET_KEY**: Use strong secret key
6. **Configure CSRF**: Set CSRF_TRUSTED_ORIGINS

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check database is running
sudo systemctl status postgresql

# Verify connection string
python manage.py dbshell
```

#### Migration Errors

```bash
# Check migration status
python manage.py showmigrations

# Fake migrations if needed (use with caution)
python manage.py migrate --fake
```

#### Static Files Not Loading

```bash
# Recollect static files
python manage.py collectstatic --noinput --clear

# Check static file permissions
chmod -R 755 staticfiles/
```

#### Permission Errors

```bash
# Fix file permissions
chown -R www-data:www-data /path/to/User-Access-Management-System
chmod -R 755 /path/to/User-Access-Management-System
```

## Next Steps

After installation:

1. [Getting Started](getting_started.md) - Learn to use UAMS
2. [Configuration](configuration.md) - Configure for your organization
3. [Administration](administration.md) - Administer the system
4. [Best Practices](best_practices.md) - Recommended practices

---

For detailed configuration options, see [Configuration](configuration.md). For deployment best practices, see [Best Practices](best_practices.md).

