# Documentation Deployment Guide

Quick guide for building and deploying MkDocs documentation in production.

## Quick Start

### 1. Build Documentation

**Windows (PowerShell):**
```powershell
.\scripts\build_docs.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/build_docs.sh
./scripts/build_docs.sh
```

**Or manually:**
```bash
mkdocs build --clean
```

### 2. Verify Build

Check that the `site/` directory was created:
```bash
ls site/
```

### 3. Test Locally (Optional)

```bash
mkdocs serve
```

Visit: http://127.0.0.1:8000

### 4. Deploy to Production

The documentation is automatically served by Django at `/docs/` after building.

**Access documentation at:**
- `https://yourdomain.com/docs/` - Redirects to home (HTTPS)
- `https://yourdomain.com/docs/home/` - Home page
- `https://yourdomain.com/docs/introduction/` - Introduction page

**Note:** In production with HTTPS enabled, all HTTP requests are automatically redirected to HTTPS.

## Production Deployment

### Option 1: Django (Current Setup)

The documentation is already configured to be served by Django:

1. **Build documentation:**
   ```bash
   mkdocs build --clean
   ```

2. **Restart Django application:**
   ```bash
   # If using systemd
   sudo systemctl restart uams
   
   # If using Gunicorn directly
   pkill -f gunicorn
   gunicorn user_access_management.wsgi:application
   ```

3. **Access at:** `https://yourdomain.com/docs/` (HTTPS)

### Option 2: Nginx with HTTPS (Recommended for High Traffic)

For better performance and security, serve static files directly with Nginx over HTTPS:

1. **Build documentation:**
   ```bash
   mkdocs build --clean
   ```

2. **Update Nginx configuration with HTTPS:**
   ```nginx
   # HTTP to HTTPS redirect
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       return 301 https://$server_name$request_uri;
   }

   # HTTPS server
   server {
       listen 443 ssl http2;
       server_name yourdomain.com www.yourdomain.com;

       # SSL certificates (Let's Encrypt)
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       # SSL configuration
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;
       ssl_prefer_server_ciphers on;
       ssl_session_cache shared:SSL:10m;
       ssl_session_timeout 10m;

       # Security headers
       add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
       add_header X-Frame-Options "DENY" always;
       add_header X-Content-Type-Options "nosniff" always;
       add_header X-XSS-Protection "1; mode=block" always;

       # Documentation
       location /docs/ {
           alias /path/to/User-Access-Management-System/site/;
           try_files $uri $uri/ /docs/home/index.html;
           index index.html;
           
           # Cache static assets
           location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
               expires 1y;
               add_header Cache-Control "public, immutable";
           }
       }

       # Django application
       location / {
           include proxy_params;
           proxy_pass http://unix:/run/uams/uams.sock;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_set_header X-Forwarded-Host $host;
           proxy_set_header X-Forwarded-Port $server_port;
       }

       # Static files
       location /static/ {
           alias /path/to/User-Access-Management-System/staticfiles/;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }

       # Media files
       location /media/ {
           alias /path/to/User-Access-Management-System/media/;
       }
   }
   ```

3. **Obtain SSL Certificate (Let's Encrypt):**
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

4. **Reload Nginx:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

5. **Access at:** `https://yourdomain.com/docs/`

## Updating Documentation

1. Edit files in `doc/` directory
2. Rebuild: `mkdocs build --clean`
3. Restart Django or reload Nginx

## Automated Deployment

### CI/CD Pipeline

Add to your deployment script:

```bash
# Build docs
mkdocs build --clean

# Copy to production (if using separate web server)
rsync -avz --delete site/ production-server:/var/www/docs/
```

### Cron Job (Auto-rebuild)

```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/project && mkdocs build --clean
```

## Troubleshooting

### Documentation Not Showing

1. **Check if site/ directory exists:**
   ```bash
   ls -la site/
   ```

2. **Rebuild if needed:**
   ```bash
   mkdocs build --clean
   ```

3. **Check Django URLs:**
   - Verify `user_access_management/urls.py` has docs routes
   - Check Django logs for errors

4. **Check file permissions:**
   ```bash
   chmod -R 755 site/
   ```

### Build Errors

```bash
# Check MkDocs version
mkdocs --version

# Install/update dependencies
pip install --upgrade mkdocs-material

# Build with verbose output
mkdocs build --verbose
```

## Requirements

- Python 3.8+
- mkdocs-material (in requirements.txt)
- Django (for serving via Django)

## For More Details

See [doc/DEPLOYMENT.md](doc/DEPLOYMENT.md) for comprehensive deployment guide.

