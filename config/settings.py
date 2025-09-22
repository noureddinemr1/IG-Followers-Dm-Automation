"""
Configuration settings for Instagram Scraper
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Instagram credentials
INSTAGRAM_CREDENTIALS = {
    'username': os.getenv('INSTAGRAM_USERNAME', ''),
    'password': os.getenv('INSTAGRAM_PASSWORD', ''),
}

# Rate limiting settings
RATE_LIMIT_SETTINGS = {
    'min_delay': float(os.getenv('MIN_DELAY', '1.0')),  # Minimum delay between requests
    'max_delay': float(os.getenv('MAX_DELAY', '3.0')),  # Maximum delay between requests
    'requests_per_minute': int(os.getenv('REQUESTS_PER_MINUTE', '60')),  # Max requests per minute
    'max_retries': int(os.getenv('MAX_RETRIES', '3')),  # Max retries for failed requests
    'retry_delay': float(os.getenv('RETRY_DELAY', '5.0')),  # Delay between retries
}

# Scraping settings
SCRAPING_SETTINGS = {
    'default_max_followers': int(os.getenv('DEFAULT_MAX_FOLLOWERS', '5000')),
    'default_max_following': int(os.getenv('DEFAULT_MAX_FOLLOWING', '5000')),
    'save_profile_pics': os.getenv('SAVE_PROFILE_PICS', 'false').lower() == 'true',
    'include_profile_info': os.getenv('INCLUDE_PROFILE_INFO', 'true').lower() == 'true',
    'auto_save': os.getenv('AUTO_SAVE', 'true').lower() == 'true',
}

# Output settings
OUTPUT_SETTINGS = {
    'data_dir': str(DATA_DIR),
    'session_dir': str(DATA_DIR / 'sessions'),
    'export_format': os.getenv('EXPORT_FORMAT', 'json'),  # json, csv, xlsx
    'timestamp_format': os.getenv('TIMESTAMP_FORMAT', '%Y%m%d_%H%M%S'),
    'file_naming': {
        'followers': '{username}_followers_{timestamp}.json',
        'following': '{username}_following_{timestamp}.json',
        'complete': '{username}_complete_{timestamp}.json',
        'profile': '{username}_profile_{timestamp}.json',
    }
}

# Logging settings
LOGGING_SETTINGS = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': str(DATA_DIR / 'scraper.log'),
    'max_size': int(os.getenv('LOG_MAX_SIZE', '10485760')),  # 10MB
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5')),
}

# Security settings
SECURITY_SETTINGS = {
    'use_proxy': os.getenv('USE_PROXY', 'false').lower() == 'true',
    'proxy_url': os.getenv('PROXY_URL', ''),
    'user_agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
    'max_login_attempts': int(os.getenv('MAX_LOGIN_ATTEMPTS', '3')),
    'session_timeout': int(os.getenv('SESSION_TIMEOUT', '3600')),  # 1 hour
}

# Database settings (for future use)
DATABASE_SETTINGS = {
    'enabled': os.getenv('DATABASE_ENABLED', 'false').lower() == 'true',
    'url': os.getenv('DATABASE_URL', 'sqlite:///instagram_scraper.db'),
    'echo': os.getenv('DATABASE_ECHO', 'false').lower() == 'true',
}

# Notification settings
NOTIFICATION_SETTINGS = {
    'enabled': os.getenv('NOTIFICATIONS_ENABLED', 'false').lower() == 'true',
    'webhook_url': os.getenv('WEBHOOK_URL', ''),
    'email_notifications': os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true',
    'email_settings': {
        'smtp_server': os.getenv('SMTP_SERVER', ''),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'smtp_username': os.getenv('SMTP_USERNAME', ''),
        'smtp_password': os.getenv('SMTP_PASSWORD', ''),
        'from_email': os.getenv('FROM_EMAIL', ''),
        'to_email': os.getenv('TO_EMAIL', ''),
    }
}

# Combine all settings
SETTINGS = {
    'instagram': INSTAGRAM_CREDENTIALS,
    'rate_limit': RATE_LIMIT_SETTINGS,
    'scraping': SCRAPING_SETTINGS,
    'output': OUTPUT_SETTINGS,
    'logging': LOGGING_SETTINGS,
    'security': SECURITY_SETTINGS,
    'database': DATABASE_SETTINGS,
    'notifications': NOTIFICATION_SETTINGS,
}


def get_setting(key_path: str, default: Any = None) -> Any:
    """
    Get a setting value using dot notation
    
    Args:
        key_path: Dot-separated path to the setting (e.g., 'rate_limit.min_delay')
        default: Default value if setting not found
        
    Returns:
        Setting value or default
    """
    keys = key_path.split('.')
    value = SETTINGS
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def update_setting(key_path: str, value: Any):
    """
    Update a setting value using dot notation
    
    Args:
        key_path: Dot-separated path to the setting
        value: New value to set
    """
    keys = key_path.split('.')
    setting_dict = SETTINGS
    
    # Navigate to the parent dictionary
    for key in keys[:-1]:
        if key not in setting_dict:
            setting_dict[key] = {}
        setting_dict = setting_dict[key]
    
    # Set the value
    setting_dict[keys[-1]] = value


def validate_settings() -> Dict[str, str]:
    """
    Validate settings and return any errors
    
    Returns:
        Dictionary of validation errors
    """
    errors = {}
    
    # Check required Instagram credentials
    if not INSTAGRAM_CREDENTIALS['username']:
        errors['instagram.username'] = 'Instagram username is required'
    
    if not INSTAGRAM_CREDENTIALS['password']:
        errors['instagram.password'] = 'Instagram password is required'
    
    # Validate rate limiting settings
    if RATE_LIMIT_SETTINGS['min_delay'] < 0:
        errors['rate_limit.min_delay'] = 'Minimum delay must be >= 0'
    
    if RATE_LIMIT_SETTINGS['max_delay'] < RATE_LIMIT_SETTINGS['min_delay']:
        errors['rate_limit.max_delay'] = 'Maximum delay must be >= minimum delay'
    
    if RATE_LIMIT_SETTINGS['requests_per_minute'] <= 0:
        errors['rate_limit.requests_per_minute'] = 'Requests per minute must be > 0'
    
    # Validate scraping settings
    if SCRAPING_SETTINGS['default_max_followers'] < 0:
        errors['scraping.default_max_followers'] = 'Default max followers must be >= 0'
    
    if SCRAPING_SETTINGS['default_max_following'] < 0:
        errors['scraping.default_max_following'] = 'Default max following must be >= 0'
    
    return errors


def print_settings():
    """Print current settings (excluding sensitive data)"""
    print("Current Settings:")
    print("=" * 50)
    
    safe_settings = SETTINGS.copy()
    # Hide sensitive information
    safe_settings['instagram']['password'] = '***HIDDEN***'
    if safe_settings['notifications']['email_settings']['smtp_password']:
        safe_settings['notifications']['email_settings']['smtp_password'] = '***HIDDEN***'
    
    def print_dict(d, indent=0):
        for key, value in d.items():
            if isinstance(value, dict):
                print('  ' * indent + f"{key}:")
                print_dict(value, indent + 1)
            else:
                print('  ' * indent + f"{key}: {value}")
    
    print_dict(safe_settings)


if __name__ == "__main__":
    # Test settings
    print_settings()
    
    # Validate settings
    errors = validate_settings()
    if errors:
        print("\nValidation Errors:")
        for key, error in errors.items():
            print(f"  {key}: {error}")
    else:
        print("\n✓ All settings are valid")
