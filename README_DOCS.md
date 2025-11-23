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
- `http://yourdomain.com/docs/` - Redirects to home
- `http://yourdomain.com/docs/home/` - Home page
- `http://yourdomain.com/docs/introduction/` - Introduction page

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

3. **Access at:** `http://yourdomain.com/docs/`

### Option 2: Nginx (Recommended for High Traffic)

For better performance, serve static files directly with Nginx:

1. **Build documentation:**
   ```bash
   mkdocs build --clean
   ```

2. **Update Nginx configuration:**
   ```nginx
   location /docs/ {
       alias /path/to/User-Access-Management-System/site/;
       try_files $uri $uri/ /docs/home/index.html;
       index index.html;
   }
   ```

3. **Reload Nginx:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

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

