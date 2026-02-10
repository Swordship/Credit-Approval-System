from datetime import date, datetime
from django.conf import settings

def get_current_date():
    """
    Get the current date for the system.
    
    In demo/testing mode: Returns the reference date from settings
    In production mode: Returns the actual current date
    
    This allows the system to work with historical data during development
    while being production-ready.
    """
    reference_date = getattr(settings, 'SYSTEM_REFERENCE_DATE', None)
    
    if reference_date:
        # Demo mode - use reference date
        if isinstance(reference_date, str):
            return datetime.strptime(reference_date, '%Y-%m-%d').date()
        return reference_date
    else:
        # Production mode - use real current date
        return date.today()