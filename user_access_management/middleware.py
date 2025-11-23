"""
Custom middleware for the User Access Management System.
"""

import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class FixMalformedHostHeaderMiddleware(MiddlewareMixin):
    """
    Middleware to fix malformed HTTP_HOST headers that contain duplicate values
    separated by commas.
    
    This can occur when reverse proxies (nginx, etc.) incorrectly forward
    duplicate host headers. This middleware sanitizes the HTTP_HOST header
    by extracting the first valid host value.
    
    Example: 'example.com,example.com' -> 'example.com'
    """
    
    def process_request(self, request):
        """
        Process the request and fix malformed HTTP_HOST headers.
        """
        http_host = request.META.get('HTTP_HOST', '')
        
        # Check if HTTP_HOST contains a comma (indicating duplicate values)
        if ',' in http_host:
            # Split by comma and take the first valid host
            hosts = [h.strip() for h in http_host.split(',') if h.strip()]
            
            if hosts:
                # Use the first host value
                sanitized_host = hosts[0]
                
                # Log warning in production to help diagnose proxy configuration issues
                if not request.META.get('DEBUG', False):
                    logger.warning(
                        f"Fixed malformed HTTP_HOST header: '{http_host}' -> '{sanitized_host}'. "
                        f"Consider fixing your reverse proxy configuration to prevent duplicate headers."
                    )
                
                # Update the HTTP_HOST in META
                request.META['HTTP_HOST'] = sanitized_host
                
                # Also fix related headers if they have the same issue
                # Fix X-Forwarded-For if duplicated
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
                if ',' in x_forwarded_for and x_forwarded_for.count(',') > x_forwarded_for.count('.'):
                    # Check if it looks like a duplicate (more commas than expected for IP list)
                    ips = [ip.strip() for ip in x_forwarded_for.split(',') if ip.strip()]
                    # Remove duplicates while preserving order (proxy chain order)
                    seen = set()
                    unique_ips = []
                    for ip in ips:
                        if ip not in seen:
                            seen.add(ip)
                            unique_ips.append(ip)
                    if unique_ips:
                        request.META['HTTP_X_FORWARDED_FOR'] = ', '.join(unique_ips)
                
                # Fix X-Forwarded-Proto if duplicated
                x_forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO', '')
                if ',' in x_forwarded_proto:
                    protocols = [p.strip() for p in x_forwarded_proto.split(',') if p.strip()]
                    if protocols:
                        request.META['HTTP_X_FORWARDED_PROTO'] = protocols[0]
                
                # Fix X-Real-IP if duplicated
                x_real_ip = request.META.get('HTTP_X_REAL_IP', '')
                if ',' in x_real_ip:
                    ips = [ip.strip() for ip in x_real_ip.split(',') if ip.strip()]
                    if ips:
                        request.META['HTTP_X_REAL_IP'] = ips[0]
        
        return None

