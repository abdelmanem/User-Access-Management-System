# Documentation Deployment Guide

This guide covers deploying MkDocs documentation in production.

## Building Documentation

### Step 1: Install MkDocs and Material Theme

```bash
pip install mkdocs-material
```

Or add to `requirements.txt`:
```
mkdocs-material>=9.0.0
```

### Step 2: Build Documentation

Build the static HTML site:

```bash
mkdocs build
```

This creates a `site/` directory with all static HTML files.

### Step 3: Verify Build

Check that the site directory was created:

```bash
ls -la site/
```

You should see:
- `index.html` (home page)
- Various HTML files for each documentation page
- `assets/` directory with CSS, JS, and images

## Production Deployment Options

### Option 1: Serve via Django (Current Setup)

Your Django application already has a view to serve documentation. Update it for production:

#### Update URLs for Production

Edit `user_access_management/urls.py` to serve docs in production:

```python
# Add this to urlpatterns (not just in DEBUG block)
urlpatterns += [
    path('docs/', lambda request: HttpResponseRedirect('/docs/home/')),
    path('docs/home/', serve_docs, {'path': 'home/index.html'}),
    re_path(r'^docs/(?P<path>.*)$', serve_docs),
]
```

#### Update serve_docs Function

Ensure it works in production:

```python
def serve_docs(request, path):
    """Serve documentation files"""
    site_dir = settings.BASE_DIR / 'site'
    
    # Normalize path
    clean_path = path.strip('/')
    if not clean_path:
        clean_path = 'home/index.html'
    elif clean_path.endswith('/'):
        clean_path = f"{clean_path}index.html"
    
    file_path = site_dir / clean_path
    
    # Try index.html if file doesn't exist
    if not file_path.exists() and clean_path:
        file_path = site_dir / clean_path / "index.html"
    
    if not file_path.exists():
        raise Http404("Documentation file not found")
    
    relative_path = str(file_path.relative_to(site_dir))
    return serve(request, relative_path, document_root=str(site_dir))
```

### Option 2: Serve via Nginx (Recommended for Production)

Nginx is more efficient for serving static files.

#### Nginx Configuration

Add to your Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

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
    }
}
```

#### Build Script

Create a deployment script `scripts/build_docs.sh`:

```bash
#!/bin/bash
# Build documentation for production

set -e

echo "Building MkDocs documentation..."

# Activate virtual environment if needed
# source venv/bin/activate

# Build documentation
mkdocs build --clean

# Verify build
if [ ! -d "site" ]; then
    echo "Error: site directory not created"
    exit 1
fi

echo "Documentation built successfully in site/ directory"
echo "Ready for deployment"
```

### Option 3: Deploy to Static Hosting

#### GitHub Pages

```bash
# Build and deploy to GitHub Pages
mkdocs gh-deploy
```

#### Netlify

Create `netlify.toml`:

```toml
[build]
  command = "mkdocs build"
  publish = "site"
```

#### AWS S3 + CloudFront

```bash
# Build
mkdocs build

# Sync to S3
aws s3 sync site/ s3://your-docs-bucket/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## Automated Deployment

### CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/docs.yml`:

```yaml
name: Build and Deploy Documentation

on:
  push:
    branches: [ main ]
    paths:
      - 'doc/**'
      - 'mkdocs.yml'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install mkdocs-material
      
      - name: Build documentation
        run: mkdocs build
      
      - name: Deploy to server
        uses: SamKirkland/FTP-Deploy-Action@4.3.0
        with:
          server: ${{ secrets.FTP_SERVER }}
          username: ${{ secrets.FTP_USERNAME }}
          password: ${{ secrets.FTP_PASSWORD }}
          local-dir: ./site/
```

### Deployment Script

Create `scripts/deploy_docs.sh`:

```bash
#!/bin/bash
# Deploy documentation to production

set -e

echo "Building documentation..."
mkdocs build --clean

echo "Deploying to production..."

# Option 1: Copy to web server
# scp -r site/* user@server:/var/www/docs/

# Option 2: Use rsync
# rsync -avz --delete site/ user@server:/var/www/docs/

# Option 3: Use Docker
# docker cp site/. container_name:/usr/share/nginx/html/docs/

echo "Documentation deployed successfully"
```

## Production Checklist

### Before Deployment

- [ ] Build documentation: `mkdocs build`
- [ ] Verify `site/` directory exists
- [ ] Test locally: `mkdocs serve`
- [ ] Check all links work
- [ ] Verify images load correctly
- [ ] Test search functionality

### Deployment Steps

1. **Build Documentation**:
   ```bash
   mkdocs build --clean
   ```

2. **Copy to Production**:
   ```bash
   # Via rsync
   rsync -avz --delete site/ production-server:/var/www/docs/
   
   # Or via SCP
   scp -r site/* production-server:/var/www/docs/
   ```

3. **Set Permissions** (if needed):
   ```bash
   chown -R www-data:www-data /var/www/docs/
   chmod -R 755 /var/www/docs/
   ```

4. **Restart Web Server** (if using Nginx):
   ```bash
   sudo systemctl reload nginx
   ```

### Post-Deployment

- [ ] Verify documentation is accessible
- [ ] Test all navigation links
- [ ] Verify search works
- [ ] Check mobile responsiveness
- [ ] Monitor error logs

## Updating Documentation

### Manual Update Process

1. Edit documentation files in `doc/`
2. Build: `mkdocs build`
3. Deploy: Copy `site/` to production

### Automated Update

Set up a cron job or CI/CD pipeline to rebuild and deploy automatically.

## Troubleshooting

### Build Errors

```bash
# Check MkDocs version
mkdocs --version

# Verify configuration
mkdocs build --verbose

# Check for missing dependencies
pip install -r requirements.txt
```

### Serving Issues

- **404 Errors**: Check file paths and Nginx configuration
- **CSS/JS Not Loading**: Verify static file paths
- **Search Not Working**: Ensure search index is built

## Best Practices

1. **Version Control**: Keep `mkdocs.yml` and `doc/` in version control
2. **Automated Builds**: Use CI/CD for automatic deployments
3. **Backup**: Keep backups of built documentation
4. **Monitoring**: Monitor documentation access and errors
5. **Updates**: Regularly update MkDocs and Material theme

## Next Steps

- [Installation & Upgrade](installation_upgrade.md) - Application installation
- [Configuration](configuration.md) - System configuration
- [Administration](administration.md) - Administrative tasks

---

For questions or issues, consult the [MkDocs documentation](https://www.mkdocs.org/) or [Material theme documentation](https://squidfunk.github.io/mkdocs-material/).

