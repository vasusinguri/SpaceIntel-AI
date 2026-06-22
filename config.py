"""
SpaceIntel AI Configuration
Contains application-wide settings and constants.
"""

import os
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# DAILY ANALYSIS LIMIT CONFIGURATION
# ============================================================================

# Maximum number of articles to analyze per day using Gemini API
# This helps control API costs and usage
DAILY_ANALYSIS_LIMIT = 100

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DEFAULT_DB_PATH = "spaceintel.db"

# ============================================================================
# API CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ============================================================================
# HELPER FUNCTIONS FOR DAILY LIMIT TRACKING
# ============================================================================

def get_current_date():
    """
    Returns the current date in YYYY-MM-DD format.
    Used for tracking daily analysis counts.
    """
    return date.today().strftime("%Y-%m-%d")

def get_current_datetime():
    """
    Returns the current datetime in ISO format.
    Used for logging and timestamps.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_new_day(last_reset_date):
    """
    Checks if we've crossed into a new day since the last reset.
    
    Args:
        last_reset_date (str): Date string in YYYY-MM-DD format
        
    Returns:
        bool: True if it's a new day, False otherwise
    """
    if not last_reset_date:
        return True
    
    try:
        current_date = get_current_date()
        return current_date != last_reset_date
    except Exception:
        return True

def get_remaining_analyses(current_count):
    """
    Calculates how many analyses are remaining for today.
    
    Args:
        current_count (int): Number of analyses performed today
        
    Returns:
        int: Number of remaining analyses allowed (0 if limit reached)
    """
    remaining = DAILY_ANALYSIS_LIMIT - current_count
    return max(0, remaining)

def is_limit_reached(current_count):
    """
    Checks if the daily analysis limit has been reached.
    
    Args:
        current_count (int): Number of analyses performed today
        
    Returns:
        bool: True if limit is reached or exceeded, False otherwise
    """
    return current_count >= DAILY_ANALYSIS_LIMIT

def get_limit_warning_threshold():
    """
    Returns the threshold at which to warn users about approaching the limit.
    Set to 90% of the daily limit.
    
    Returns:
        int: Number of analyses at which to show warning
    """
    return int(DAILY_ANALYSIS_LIMIT * 0.9)

def should_show_warning(current_count):
    """
    Checks if we should show a warning about approaching the daily limit.
    
    Args:
        current_count (int): Number of analyses performed today
        
    Returns:
        bool: True if warning should be shown, False otherwise
    """
    return current_count >= get_limit_warning_threshold() and current_count < DAILY_ANALYSIS_LIMIT

# Made with Bob
