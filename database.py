import sqlite3
import os
from datetime import datetime
import config

DEFAULT_DB_PATH = "spaceintel.db"

def get_connection(db_path=DEFAULT_DB_PATH):
    """
    Establishes and returns a connection to the SQLite database.
    Enables sqlite3.Row to allow accessing columns by name.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DEFAULT_DB_PATH):
    """
    Initializes the SQLite database and creates the articles table if it doesn't exist.
    Also creates the analysis_tracking table for daily limit management.
    """
    articles_query = """
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        source TEXT NOT NULL,
        link TEXT UNIQUE NOT NULL,
        published_date TEXT NOT NULL,
        category TEXT,
        summary TEXT,
        why_it_matters TEXT,
        importance_score INTEGER,
        impact_type TEXT,
        who_cares TEXT,
        analyzed INTEGER DEFAULT 0
    );
    """
    
    # Table to track daily analysis counts
    tracking_query = """
    CREATE TABLE IF NOT EXISTS analysis_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE NOT NULL,
        count INTEGER DEFAULT 0,
        last_updated TEXT NOT NULL
    );
    """
    
    with get_connection(db_path) as conn:
        conn.execute(articles_query)
        conn.execute(tracking_query)
        conn.commit()

def insert_article(title, source, link, published_date, db_path=DEFAULT_DB_PATH):
    """
    Inserts a new raw RSS article into the database if the link doesn't already exist.
    Returns True if a new article was inserted, False if it was a duplicate.
    """
    query = """
    INSERT OR IGNORE INTO articles (title, source, link, published_date, analyzed)
    VALUES (?, ?, ?, ?, 0)
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (title, source, link, published_date))
        conn.commit()
        # rowcount is 1 if inserted, 0 if ignored due to UNIQUE constraint
        return cursor.rowcount > 0

def update_article_analysis(article_id, category, summary, why_it_matters, importance_score, impact_type, who_cares, db_path=DEFAULT_DB_PATH):
    """
    Updates the article with AI-generated analysis and marks it as analyzed.
    """
    query = """
    UPDATE articles
    SET category = ?,
        summary = ?,
        why_it_matters = ?,
        importance_score = ?,
        impact_type = ?,
        who_cares = ?,
        analyzed = 1
    WHERE id = ?
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (
            category,
            summary,
            why_it_matters,
            importance_score,
            impact_type,
            who_cares,
            article_id
        ))
        conn.commit()
        return cursor.rowcount > 0

def get_articles(category=None, limit=50, db_path=DEFAULT_DB_PATH):
    """
    Retrieves latest articles from the database, ordered by published_date (newest first).
    Allows optional filtering by category.
    """
    with get_connection(db_path) as conn:
        if category and category.lower() != "all":
            query = """
            SELECT * FROM articles
            WHERE category = ?
            ORDER BY published_date DESC
            LIMIT ?
            """
            cursor = conn.execute(query, (category, limit))
        else:
            query = """
            SELECT * FROM articles
            ORDER BY published_date DESC
            LIMIT ?
            """
            cursor = conn.execute(query, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

def get_article_by_id(article_id, db_path=DEFAULT_DB_PATH):
    """
    Retrieves a single article's full details by its ID.
    """
    query = "SELECT * FROM articles WHERE id = ?"
    with get_connection(db_path) as conn:
        row = conn.execute(query, (article_id,)).fetchone()
        return dict(row) if row else None

def get_db_stats(db_path=DEFAULT_DB_PATH):
    """
    Calculates summary stats of the database to display on the dashboard.
    Returns a dict with: total, analyzed, unanalyzed, and avg_importance_score.
    """
    stats = {
        "total": 0,
        "analyzed": 0,
        "unanalyzed": 0,
        "avg_importance_score": 0.0
    }
    
    # Check if table exists
    with get_connection(db_path) as conn:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='articles';"
        ).fetchone()
        
        if not table_exists:
            return stats
            
        row = conn.execute("SELECT COUNT(*) FROM articles").fetchone()
        stats["total"] = row[0] if row else 0
        
        row = conn.execute("SELECT COUNT(*) FROM articles WHERE analyzed = 1").fetchone()
        stats["analyzed"] = row[0] if row else 0
        
        stats["unanalyzed"] = stats["total"] - stats["analyzed"]
        
        row = conn.execute("SELECT AVG(importance_score) FROM articles WHERE analyzed = 1").fetchone()
        stats["avg_importance_score"] = round(row[0], 1) if row and row[0] is not None else 0.0
        
    return stats


# ============================================================================
# DAILY ANALYSIS LIMIT TRACKING FUNCTIONS
# ============================================================================

def get_daily_analysis_count(db_path=DEFAULT_DB_PATH):
    """
    Gets the current count of articles analyzed today.
    Automatically resets the count if it's a new day.
    
    Returns:
        int: Number of articles analyzed today
    """
    current_date = config.get_current_date()
    
    with get_connection(db_path) as conn:
        # Check if there's a record for today
        row = conn.execute(
            "SELECT count, date FROM analysis_tracking WHERE date = ?",
            (current_date,)
        ).fetchone()
        
        if row:
            return row["count"]
        else:
            # No record for today, check if we need to reset from previous day
            last_record = conn.execute(
                "SELECT date FROM analysis_tracking ORDER BY date DESC LIMIT 1"
            ).fetchone()
            
            if last_record and config.is_new_day(last_record["date"]):
                # It's a new day, create a fresh record
                conn.execute(
                    "INSERT INTO analysis_tracking (date, count, last_updated) VALUES (?, 0, ?)",
                    (current_date, config.get_current_datetime())
                )
                conn.commit()
            elif not last_record:
                # First time tracking, create initial record
                conn.execute(
                    "INSERT INTO analysis_tracking (date, count, last_updated) VALUES (?, 0, ?)",
                    (current_date, config.get_current_datetime())
                )
                conn.commit()
            
            return 0

def increment_daily_analysis_count(db_path=DEFAULT_DB_PATH):
    """
    Increments the daily analysis count by 1.
    Creates a new record if one doesn't exist for today.
    
    Returns:
        int: New count after increment
    """
    current_date = config.get_current_date()
    current_datetime = config.get_current_datetime()
    
    with get_connection(db_path) as conn:
        # Try to update existing record
        cursor = conn.execute(
            """
            UPDATE analysis_tracking 
            SET count = count + 1, last_updated = ?
            WHERE date = ?
            """,
            (current_datetime, current_date)
        )
        
        if cursor.rowcount == 0:
            # No record exists for today, create one
            conn.execute(
                "INSERT INTO analysis_tracking (date, count, last_updated) VALUES (?, 1, ?)",
                (current_date, current_datetime)
            )
        
        conn.commit()
        
        # Return the new count
        row = conn.execute(
            "SELECT count FROM analysis_tracking WHERE date = ?",
            (current_date,)
        ).fetchone()
        
        return row["count"] if row else 1

def can_analyze_more_articles(db_path=DEFAULT_DB_PATH):
    """
    Checks if we can analyze more articles today based on the daily limit.
    
    Returns:
        tuple: (bool, int, int) - (can_analyze, current_count, remaining)
    """
    current_count = get_daily_analysis_count(db_path)
    remaining = config.get_remaining_analyses(current_count)
    can_analyze = not config.is_limit_reached(current_count)
    
    return can_analyze, current_count, remaining

def get_analysis_stats_by_date(start_date=None, end_date=None, db_path=DEFAULT_DB_PATH):
    """
    Gets analysis statistics for a date range.
    
    Args:
        start_date (str, optional): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        db_path (str): Path to database
        
    Returns:
        list: List of dicts with date and count information
    """
    with get_connection(db_path) as conn:
        if start_date and end_date:
            query = """
            SELECT date, count, last_updated 
            FROM analysis_tracking 
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
            """
            cursor = conn.execute(query, (start_date, end_date))
        elif start_date:
            query = """
            SELECT date, count, last_updated 
            FROM analysis_tracking 
            WHERE date >= ?
            ORDER BY date DESC
            """
            cursor = conn.execute(query, (start_date,))
        else:
            query = """
            SELECT date, count, last_updated 
            FROM analysis_tracking 
            ORDER BY date DESC
            LIMIT 30
            """
            cursor = conn.execute(query)
        
        return [dict(row) for row in cursor.fetchall()]

def count_articles_analyzed_today(db_path=DEFAULT_DB_PATH):
    """
    Counts how many articles were actually analyzed today from the articles table.
    This provides a verification method against the tracking table.
    
    Returns:
        int: Number of articles analyzed today
    """
    current_date = config.get_current_date()
    
    with get_connection(db_path) as conn:
        # Count articles that were analyzed today
        # Note: This assumes articles have a timestamp when analyzed
        # For now, we'll use the tracking table as the source of truth
        row = conn.execute(
            "SELECT count FROM analysis_tracking WHERE date = ?",
            (current_date,)
        ).fetchone()
        
        return row["count"] if row else 0

def reset_daily_analysis_count(db_path=DEFAULT_DB_PATH):
    """
    Manually resets the daily analysis count.
    This is typically called automatically at midnight, but can be used for testing.
    
    Returns:
        bool: True if reset was successful
    """
    current_date = config.get_current_date()
    current_datetime = config.get_current_datetime()
    
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO analysis_tracking (date, count, last_updated)
            VALUES (?, 0, ?)
            """,
            (current_date, current_datetime)
        )
        conn.commit()
        return True
