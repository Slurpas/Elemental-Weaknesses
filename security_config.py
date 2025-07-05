"""
Security configuration for Pokemon PvP Analyzer
"""

import os
from datetime import timedelta

# Security Settings
SECURITY_CONFIG = {
    # Session security
    'SESSION_COOKIE_SECURE': True,  # Only send cookies over HTTPS
    'SESSION_COOKIE_HTTPONLY': True,  # Prevent JavaScript access to cookies
    'SESSION_COOKIE_SAMESITE': 'Lax',  # CSRF protection
    
    # Rate limiting
    'RATE_LIMIT_ENABLED': True,
    'RATE_LIMIT_REQUESTS': 100,  # requests per window
    'RATE_LIMIT_WINDOW': 60,  # seconds
    
    # Input validation
    'MAX_INPUT_LENGTH': 100,
    'ALLOWED_FILE_EXTENSIONS': ['.png', '.jpg', '.jpeg', '.gif'],
    
    # CORS settings
    'CORS_ENABLED': False,  # Disable CORS for local app
    
    # Content Security Policy
    'CSP_POLICY': {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", "data:"],
        'font-src': ["'self'"],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"]
    }
}

# Environment-specific settings
def get_security_config():
    """Get security configuration based on environment"""
    config = SECURITY_CONFIG.copy()
    
    # Development overrides
    if os.environ.get('FLASK_ENV') == 'development':
        config['SESSION_COOKIE_SECURE'] = False
        config['RATE_LIMIT_ENABLED'] = False
        config['CORS_ENABLED'] = True
    
    return config

# Input sanitization patterns
INPUT_PATTERNS = {
    'pokemon_name': r'^[a-zA-Z0-9\-\_\s]+$',
    'search_query': r'^[a-zA-Z0-9\-\_\s\']+$',
    'move_name': r'^[a-zA-Z0-9\-\_\s]+$',
    'numeric': r'^[0-9]+$',
    'decimal': r'^[0-9]+(\.[0-9]+)?$'
}

# Blocked patterns (security threats)
BLOCKED_PATTERNS = [
    r'\.\.',  # Path traversal
    r'[<>"\']',  # HTML/script injection
    r'javascript:',  # JavaScript injection
    r'data:text/html',  # Data URI attacks
    r'vbscript:',  # VBScript injection
    r'on\w+\s*=',  # Event handler injection
]

# Rate limiting storage
rate_limit_storage = {}

def check_rate_limit(client_ip):
    """Simple rate limiting implementation"""
    if not SECURITY_CONFIG['RATE_LIMIT_ENABLED']:
        return True
    
    current_time = os.times()[4]  # System time
    window_start = current_time - SECURITY_CONFIG['RATE_LIMIT_WINDOW']
    
    # Clean old entries
    rate_limit_storage[client_ip] = [
        req_time for req_time in rate_limit_storage.get(client_ip, [])
        if req_time > window_start
    ]
    
    # Check limit
    if len(rate_limit_storage[client_ip]) >= SECURITY_CONFIG['RATE_LIMIT_REQUESTS']:
        return False
    
    # Add current request
    rate_limit_storage[client_ip].append(current_time)
    return True 