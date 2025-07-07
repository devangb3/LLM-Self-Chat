"""
Security configuration and utilities for the Flask application.
"""
from flask import request, jsonify
from functools import wraps
from flask_wtf.csrf import CSRFProtect
import secrets
import os
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration class"""
    
    # CSRF Protection
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 3600  # 1 hour
    CSRF_HEADER = 'X-CSRFToken'
    
    # Session Security
    # For development: don't use secure cookies (http is allowed)
    # For production: use secure cookies (https required)
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    
    SESSION_COOKIE_MAX_AGE = 3600  # 1 hour
    SESSION_COOKIE_PATH = '/'
    
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
    logger.info("Configuring security settings")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"CSRF Enabled: {SecurityConfig.CSRF_ENABLED}")
    logger.info(f"Session Cookie Secure: {SecurityConfig.SESSION_COOKIE_SECURE}")
    
    if os.getenv('FLASK_ENV') == 'production':
        session_samesite = 'Lax'
        session_domain = None
    else:
        session_samesite = 'Lax'
        session_domain = None
    
    logger.info(f"Session Cookie SameSite: {session_samesite}")
    logger.info(f"Session Cookie Domain: {session_domain}")
    
    app.config['SESSION_COOKIE_SECURE'] = SecurityConfig.SESSION_COOKIE_SECURE
    app.config['SESSION_COOKIE_HTTPONLY'] = SecurityConfig.SESSION_COOKIE_HTTPONLY
    app.config['SESSION_COOKIE_SAMESITE'] = session_samesite
    app.config['SESSION_COOKIE_MAX_AGE'] = SecurityConfig.SESSION_COOKIE_MAX_AGE
    app.config['SESSION_COOKIE_DOMAIN'] = session_domain
    app.config['SESSION_COOKIE_PATH'] = SecurityConfig.SESSION_COOKIE_PATH
    
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = SecurityConfig.SESSION_COOKIE_MAX_AGE
    
    app.config['WTF_CSRF_ENABLED'] = SecurityConfig.CSRF_ENABLED
    app.config['WTF_CSRF_TIME_LIMIT'] = SecurityConfig.CSRF_TIME_LIMIT
    app.config['WTF_CSRF_SSL_STRICT'] = os.getenv('FLASK_ENV') == 'production'
    
    logger.info(f"CSRF SSL Strict: {app.config['WTF_CSRF_SSL_STRICT']}")
    logger.info(f"CSRF Time Limit: {app.config['WTF_CSRF_TIME_LIMIT']}")
    
        # Log final session configuration
    logger.info(f"Final session config - Secure: {app.config['SESSION_COOKIE_SECURE']}")
    logger.info(f"Final session config - SameSite: {app.config['SESSION_COOKIE_SAMESITE']}")
    logger.info(f"Final session config - Domain: {app.config['SESSION_COOKIE_DOMAIN']}")
    logger.info(f"Final session config - Path: {app.config['SESSION_COOKIE_PATH']}")
    
    @app.after_request
    def add_security_headers(response):
        logger.debug(f"Adding security headers to response for {request.path}")
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            if value is not None:  # Only add non-None headers
                response.headers[header] = value
                logger.debug(f"Added header {header}: {value}")
        return response

def csrf_exempt(view_func):
    """Decorator to exempt a view from CSRF protection"""
    logger.info(f"Exempting view {view_func.__name__} from CSRF protection")
    view_func.csrf_exempt = True
    return view_func

def handle_csrf_error(error):
    """Handle CSRF validation errors"""
    logger.error(f"CSRF validation failed for {request.method} {request.path}")
    logger.error(f"Request headers: {dict(request.headers)}")
    logger.error(f"Request form data: {dict(request.form)}")
    logger.error(f"Request JSON: {request.get_json() if request.is_json else 'Not JSON'}")
    logger.error(f"Error details: {str(error)}")
    
    return jsonify({
        'error': 'CSRF token validation failed',
        'message': 'Invalid or missing CSRF token. Please refresh the page and try again.',
        'debug_info': {
            'path': request.path,
            'method': request.method,
            'headers': dict(request.headers),
            'has_csrf_header': 'X-CSRFToken' in request.headers,
            'has_csrf_form': 'csrf_token' in request.form
        }
    }), 400

def handle_security_error(error):
    """Handle general security errors"""
    logger.error(f"Security validation failed for {request.method} {request.path}")
    logger.error(f"Error details: {str(error)}")
    
    return jsonify({
        'error': 'Security validation failed',
        'message': 'Request blocked for security reasons.',
        'debug_info': {
            'path': request.path,
            'method': request.method,
            'error': str(error)
        }
    }), 403 