"""
Security configuration and utilities for the Flask application.
"""
from flask import request, jsonify
from functools import wraps
from flask_wtf.csrf import CSRFProtect
import secrets
import os

class SecurityConfig:
    """Security configuration class"""
    
    # CSRF Protection
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 3600  # 1 hour
    CSRF_HEADER = 'X-CSRFToken'
    
    # Session Security
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'  # Only secure in production
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    SESSION_COOKIE_MAX_AGE = 3600  # 1 hour
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains' if os.getenv('FLASK_ENV') == 'production' else None,
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }

def configure_security(app, csrf):
    """Configure security settings for the Flask app"""
    
    app.config['SESSION_COOKIE_SECURE'] = SecurityConfig.SESSION_COOKIE_SECURE
    app.config['SESSION_COOKIE_HTTPONLY'] = SecurityConfig.SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = SecurityConfig.SESSION_COOKIE_SAMESITE
    app.config['SESSION_COOKIE_MAX_AGE'] = SecurityConfig.SESSION_COOKIE_MAX_AGE
    
    app.config['WTF_CSRF_ENABLED'] = SecurityConfig.CSRF_ENABLED
    app.config['WTF_CSRF_TIME_LIMIT'] = SecurityConfig.CSRF_TIME_LIMIT
    app.config['WTF_CSRF_SSL_STRICT'] = os.getenv('FLASK_ENV') == 'production'
    
    @app.after_request
    def add_security_headers(response):
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            if value is not None:  # Only add non-None headers
                response.headers[header] = value
        return response

def csrf_exempt(view_func):
    """Decorator to exempt a view from CSRF protection"""
    view_func.csrf_exempt = True
    return view_func

def validate_csrf_token():
    """Validate CSRF token for non-GET requests"""
    if request.method == 'GET':
        return True
    
    if request.path.startswith('/socket.io/'):
        return True
    
    if request.path.startswith('/api/auth/login') or request.path.startswith('/api/auth/register'):
        return True
    
    # For other endpoints, CSRF protection is handled by Flask-WTF
    return True

def generate_secure_token():
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def sanitize_input(data):
    """Basic input sanitization"""
    if isinstance(data, str):
        dangerous_chars = ['<', '>', '"', "'", '&']
        for char in dangerous_chars:
            data = data.replace(char, '')
    return data

def rate_limit_key():
    """Generate a key for rate limiting based on IP and user"""
    user_id = getattr(request, 'user_id', None)
    return f"{request.remote_addr}:{user_id or 'anonymous'}"

def handle_csrf_error(error):
    """Handle CSRF validation errors"""
    return jsonify({
        'error': 'CSRF token validation failed',
        'message': 'Invalid or missing CSRF token. Please refresh the page and try again.'
    }), 400

def handle_security_error(error):
    """Handle general security errors"""
    return jsonify({
        'error': 'Security validation failed',
        'message': 'Request blocked for security reasons.'
    }), 403 