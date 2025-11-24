# HTTPS/SSL Setup for Documentation

Complete guide for setting up HTTPS/SSL for MkDocs documentation in production.

## Overview

When running UAMS in production with HTTPS, the documentation should also be served over HTTPS for security and compliance.

## Quick Setup

### 1. Configure Django for HTTPS

Update your `.env` file:

```env
# HTTPS Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Reverse Proxy Settings
USE_X_FORWARDED_HOST=True
PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 2. Configure Nginx with SSL

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete Nginx HTTPS configuration.

### 3. Obtain SSL Certificate

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 4. Build and Deploy Documentation

```bash
# Build docs
mkdocs build --clean

# Restart services
sudo systemctl restart uams
sudo systemctl reload nginx
```

## Access Documentation

After setup, access documentation at:
- `https://yourdomain.com/doc/` - Home page
- `https://yourdomain.com/doc/introduction/` - Introduction
- `https://yourdomain.com/doc/features/` - Features

**Note:** HTTP requests automatically redirect to HTTPS.

## Verification

### Test HTTPS

```bash
# Test SSL connection
openssl s_client -connect yourdomain.com:443

# Test redirect
curl -I http://yourdomain.com/doc/
# Should return: HTTP/1.1 301 Moved Permanently
# Location: https://yourdomain.com/doc/
```

### Check Security Headers

```bash
curl -I https://yourdomain.com/doc/
```

Look for:
- `Strict-Transport-Security: max-age=31536000`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`

## Troubleshooting

### Mixed Content Warnings

If you see mixed content warnings, ensure:
1. All assets are loaded over HTTPS
2. MkDocs is configured to use HTTPS URLs
3. Check browser console for specific resources

### SSL Certificate Issues

```bash
# Check certificate expiration
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### Documentation Not Loading Over HTTPS

1. **Check Nginx configuration:**
   ```bash
   sudo nginx -t
   ```

2. **Verify SSL certificate:**
   ```bash
   sudo certbot certificates
   ```

3. **Check Django settings:**
   - Verify `SECURE_SSL_REDIRECT=True`
   - Check `CSRF_TRUSTED_ORIGINS` includes your domain

4. **Check file permissions:**
   ```bash
   ls -la site/
   chmod -R 755 site/
   ```

## Best Practices

1. **Always use HTTPS in production**
2. **Enable HSTS for security**
3. **Set up automatic certificate renewal**
4. **Monitor certificate expiration**
5. **Use strong SSL/TLS protocols (TLS 1.2+)**

## Certificate Renewal

Let's Encrypt certificates expire every 90 days. Auto-renewal is configured by default:

```bash
# Check renewal status
sudo certbot renew --dry-run

# Manual renewal
sudo certbot renew
```

Certbot automatically renews certificates before expiration.

## Next Steps

- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
- [Configuration](../configuration.md) - System configuration
- [Administration](../administration.md) - Administrative tasks

---

For SSL certificate issues, consult the [Certbot documentation](https://certbot.eff.org/).

