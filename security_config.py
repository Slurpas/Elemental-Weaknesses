"""
Security configuration for Pokemon PvP Helper
"""

import os
import re
from datetime import timedelta

# Security Settings
SECURITY_CONFIG = {
    # Session security
    'SESSION_COOKIE_SECURE': True,  # Only send cookies over HTTPS
    'SESSION_COOKIE_HTTPONLY': True,  # Prevent JavaScript access to cookies
    'SESSION_COOKIE_SAMESITE': 'Lax',  # CSRF protection
    'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour session timeout
    
    # Rate limiting
    'RATE_LIMIT_ENABLED': True,
    'RATE_LIMIT_REQUESTS': 100,  # requests per window
    'RATE_LIMIT_WINDOW': 60,  # seconds
    'RATE_LIMIT_BURST': 10,  # burst allowance
    
    # Input validation
    'MAX_INPUT_LENGTH': 100,
    'MAX_SEARCH_LENGTH': 50,
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
        'frame-ancestors': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"]
    },
    
    # Additional security headers
    'STRICT_TRANSPORT_SECURITY': 'max-age=31536000; includeSubDomains',
    'PERMISSIONS_POLICY': 'geolocation=(), microphone=(), camera=()',
    
    # Logging
    'SECURITY_LOGGING_ENABLED': True,
    'LOG_SENSITIVE_ACTIONS': True
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
    """Enhanced rate limiting implementation with burst protection"""
    if not SECURITY_CONFIG['RATE_LIMIT_ENABLED']:
        return True
    
    current_time = os.times()[4]  # System time
    window_start = current_time - SECURITY_CONFIG['RATE_LIMIT_WINDOW']
    
    # Clean old entries
    rate_limit_storage[client_ip] = [
        req_time for req_time in rate_limit_storage.get(client_ip, [])
        if req_time > window_start
    ]
    
    # Check burst limit first
    recent_requests = [req_time for req_time in rate_limit_storage[client_ip] 
                      if current_time - req_time < 5]  # Last 5 seconds
    if len(recent_requests) >= SECURITY_CONFIG['RATE_LIMIT_BURST']:
        return False
    
    # Check overall limit
    if len(rate_limit_storage[client_ip]) >= SECURITY_CONFIG['RATE_LIMIT_REQUESTS']:
        return False
    
    # Add current request
    rate_limit_storage[client_ip].append(current_time)
    return True

def log_security_event(event_type, details, client_ip=None):
    """Log security events for monitoring"""
    if not SECURITY_CONFIG['SECURITY_LOGGING_ENABLED']:
        return
    
    import logging
    from datetime import datetime
    
    logger = logging.getLogger('security')
    if not logger.handlers:
        handler = logging.FileHandler('security.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    log_message = f"SECURITY_EVENT: {event_type} - {details}"
    if client_ip:
        log_message += f" - IP: {client_ip}"
    
    logger.warning(log_message)

def validate_input(input_str, input_type='general'):
    """Enhanced input validation with logging"""
    if not input_str:
        return False, "Input cannot be empty"
    
    # Check length limits
    max_length = SECURITY_CONFIG.get(f'MAX_{input_type.upper()}_LENGTH', 
                                   SECURITY_CONFIG['MAX_INPUT_LENGTH'])
    if len(input_str) > max_length:
        log_security_event('INPUT_TOO_LONG', f'{input_type}: {len(input_str)} chars')
        return False, f"Input too long (max {max_length} characters)"
    
    # Check for blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, input_str, re.IGNORECASE):
            log_security_event('BLOCKED_PATTERN', f'{input_type}: {pattern}')
            return False, "Input contains invalid characters"
    
    # Type-specific validation
    if input_type in INPUT_PATTERNS:
        if not re.match(INPUT_PATTERNS[input_type], input_str):
            log_security_event('PATTERN_MISMATCH', f'{input_type}: {input_str}')
            return False, f"Invalid {input_type} format"
    
    return True, "Valid input"

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal"""
    if not filename:
        return ""
    
    # Remove path traversal characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\.\.', '', filename)
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename.strip() 