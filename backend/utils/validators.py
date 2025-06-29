# 🔧 VALIDATION UTILITIES
# Input validation and security helpers

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def validate_api_key(api_key: str, service_name: str = "API") -> bool:
    """
    Validate API key format and basic security requirements
    
    Args:
        api_key: The API key to validate
        service_name: Name of the service for logging
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not api_key or not isinstance(api_key, str):
        logger.warning(f"❌ {service_name} API key is empty or invalid type")
        return False
    
    # Remove whitespace
    api_key = api_key.strip()
    
    # Basic length check (most API keys are at least 20 characters)
    if len(api_key) < 10:
        logger.warning(f"❌ {service_name} API key too short: {len(api_key)} characters")
        return False
    
    # Check for obvious test/placeholder values
    test_patterns = [
        r'^test[-_]?key',
        r'^your[-_]?api[-_]?key',
        r'^placeholder',
        r'^example',
        r'^demo[-_]?key',
        r'^fake[-_]?key'
    ]
    
    for pattern in test_patterns:
        if re.match(pattern, api_key.lower()):
            logger.warning(f"❌ {service_name} API key appears to be a test/placeholder value")
            return False
    
    # Check for valid characters (alphanumeric, hyphens, underscores, dots)
    if not re.match(r'^[a-zA-Z0-9\-_.]+$', api_key):
        logger.warning(f"❌ {service_name} API key contains invalid characters")
        return False
    
    logger.info(f"✅ {service_name} API key validation passed")
    return True

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid email format, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(email_pattern, email.strip()):
        logger.debug(f"✅ Email validation passed: {email}")
        return True
    else:
        logger.warning(f"❌ Invalid email format: {email}")
        return False

def validate_url(url: str, require_https: bool = False) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        require_https: Whether to require HTTPS protocol
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # Basic URL pattern
    if require_https:
        url_pattern = r'^https://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    else:
        url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    
    if re.match(url_pattern, url):
        logger.debug(f"✅ URL validation passed: {url}")
        return True
    else:
        logger.warning(f"❌ Invalid URL format: {url}")
        return False

def validate_database_url(database_url: str) -> bool:
    """
    Validate database URL format
    
    Args:
        database_url: Database URL to validate
        
    Returns:
        bool: True if valid database URL, False otherwise
    """
    if not database_url or not isinstance(database_url, str):
        return False
    
    database_url = database_url.strip()
    
    # Support common database URL formats
    db_patterns = [
        r'^postgresql://[^:]+:[^@]+@[^:/]+:\d+/\w+$',  # PostgreSQL
        r'^sqlite:///.*\.db$',  # SQLite
        r'^mysql://[^:]+:[^@]+@[^:/]+:\d+/\w+$',  # MySQL
    ]
    
    for pattern in db_patterns:
        if re.match(pattern, database_url):
            logger.debug("✅ Database URL validation passed")
            return True
    
    logger.warning(f"❌ Invalid database URL format: {database_url[:20]}...")
    return False

