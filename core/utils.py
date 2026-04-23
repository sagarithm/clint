import re
from typing import Set, List, Optional

# --- CONFIGURATION: QUALITY CONTROL ---
EMAIL_BLACKLIST: Set[str] = {
    "email@email.com", "user@example.com", "info@example.com", 
    "test@test.com", "yourname@domain.com", "sagar@pixartual.studio",
    "hello@pixartual.studio", "info@pixartual.studio", "noreply@google.com"
}

# Common non-email asset extensions to ignore
ASSET_EXTENSIONS: tuple = (
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', 
    '.pdf', '.zip', '.mp4', '.js', '.css', '.woff', '.woff2', '.ico', '.xml'
)

def is_valid_email(email: Optional[str]) -> bool:
    """
    Validates if a string is a legitimate business contact email.
    
    Args:
        email: The raw email string to validate.
        
    Returns:
        True if the email passes all quality and format checks, False otherwise.
    """
    if not email:
        return False
    
    email = email.lower().strip()
    
    # 1. Basic Structure check
    if len(email) < 5 or "@" not in email:
        return False
        
    # 2. Blacklist check (Placeholders & Internal)
    if email in EMAIL_BLACKLIST:
        return False
        
    # 3. Asset Extension check
    if any(email.endswith(ext) for ext in ASSET_EXTENSIONS):
        return False
        
    # 4. Regex validation for standard format
    # This prevents 'logo@2x' and other partial matches
    email_pattern = re.compile(r'^[a-z0-9._%+-]+@(?![0-9]x)[a-z0-9.-]+\.[a-z]{2,}$')
    if not email_pattern.match(email):
        return False
        
    return True

def sanitize_emails(email_string: Optional[str]) -> List[str]:
    """
    Parses a combined email string, validates each, and returns a unique list.
    
    Args:
        email_string: A comma-separated string of raw emails.
        
    Returns:
        A sorted list of unique, valid email addresses.
    """
    if not email_string or email_string == "N/A":
        return []
    
    raw_emails = email_string.split(',')
    valid_emails = {e.lower().strip() for e in raw_emails if is_valid_email(e)}
    
    return sorted(list(valid_emails))

import warnings
from core.logger import logger

def warn_deprecated(feature_name: str, reason: str, version_removal: str) -> None:
    """
    Standardizes deprecation warnings across the CLI and API products.
    """
    msg = f"DEPRECATION WARNING: {feature_name} is deprecated and will be removed in v{version_removal}. Reason: {reason}"
    logger.warning(msg)
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
