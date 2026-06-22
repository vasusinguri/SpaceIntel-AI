import feedparser
import time
from datetime import datetime
import database
import config
from bs4 import BeautifulSoup
import html
import re

# Dict of reliable Space RSS Feeds
FEEDS = {
    "NASA News": "https://www.nasa.gov/rss/breaking_news.rss",
    "ESA Top News": "https://www.esa.int/rssfeed/TopNews",
    "SpaceNews": "https://spacenews.com/feed/",
    "Space.com": "https://www.space.com/feeds/all"
}

def clean_html(text):
    """
    Robust HTML cleaning utility that removes all HTML tags, inline styles,
    and decodes HTML entities to produce clean, readable text.
    
    Uses BeautifulSoup for proper HTML parsing and handles:
    - All HTML tags (<div>, <p>, <h1>, etc.)
    - Inline styles and attributes
    - HTML entities (&nbsp;, &, etc.)
    - Nested tags
    - Malformed HTML
    
    Args:
        text: String that may contain HTML markup
        
    Returns:
        Clean text with all HTML removed and entities decoded
    """
    if not text:
        return ""
    
    # Parse HTML and extract text using BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove script and style elements completely
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Get text with space separator to preserve word boundaries
    text = soup.get_text(separator=' ', strip=True)
    
    # Decode HTML entities (e.g., &nbsp;, &, ')
    text = html.unescape(text)
    
    # Remove extra whitespace (multiple spaces, tabs, newlines)
    text = ' '.join(text.split())
    
    return text.strip()

def normalize_date(entry):
    """
    Extracts and normalizes the publication date from a feed entry.
    Converts it to standard sortable string format 'YYYY-MM-DD HH:MM:SS'.
    """
    # feedparser attempts to parse date into a struct_time object automatically
    struct_time = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    
    if struct_time:
        try:
            # Safely format struct_time (UTC format)
            return time.strftime("%Y-%m-%d %H:%M:%S", struct_time)
        except Exception:
            pass
            
    # Fallback if no struct_time could be parsed
    raw_date = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if raw_date:
        return raw_date
        
    # Final fallback is current UTC time
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def fetch_feed_articles(source_name, feed_url, limit=15):
    """
    Fetches articles from a single RSS feed, parses them, and returns a list.
    """
    articles = []
    try:
        # Parse the RSS feed using feedparser
        feed = feedparser.parse(feed_url)
        
        # Check if feed failed to load
        if feed.bozo and not feed.entries:
            print(f"Warning: Feeds from {source_name} returned bozo exception, but attempting to read anyway.")
            
        for entry in feed.entries[:limit]:
            # Clean HTML from title - RSS feeds often include HTML markup
            title = clean_html(getattr(entry, "title", "No Title"))
            link = getattr(entry, "link", "")
            
            if not link:
                continue
            
            # Extract and clean description/summary if available
            # These fields often contain HTML tags, inline styles, etc.
            description = getattr(entry, "description", "")
            summary = getattr(entry, "summary", "")
            
            # Use description if available, otherwise summary, clean both
            content_preview = clean_html(description) if description else clean_html(summary)
                
            published_date = normalize_date(entry)
            
            articles.append({
                "title": title,
                "source": source_name,
                "link": link,
                "published_date": published_date,
                "content_preview": content_preview  # Clean preview for potential future use
            })
    except Exception as e:
        print(f"Error fetching RSS feed from {source_name} ({feed_url}): {e}")
        
    return articles

def sync_all_feeds(limit_per_feed=5, db_path=database.DEFAULT_DB_PATH, api_key=None):
    """
    Fetches all configured RSS feeds, attempts to insert each article into SQLite.
    Automatically runs Gemini AI analysis on new articles if api_key is available.
    Respects the daily analysis limit configured in config.py.
    Returns statistics of the sync (total processed, total new inserted, total analyzed, limit info).
    """
    import gemini_analyzer
    database.init_db(db_path)
    
    total_processed = 0
    new_inserted = 0
    new_analyzed = 0
    skipped_due_to_limit = 0
    
    # Check daily analysis limit before starting
    can_analyze, current_count, remaining = database.can_analyze_more_articles(db_path)
    
    print(f"\n{'='*60}")
    print(f"Daily Analysis Limit Status:")
    print(f"  - Limit: {config.DAILY_ANALYSIS_LIMIT} articles/day")
    print(f"  - Already analyzed today: {current_count}")
    print(f"  - Remaining: {remaining}")
    print(f"{'='*60}\n")
    
    # Show warning if approaching limit
    if config.should_show_warning(current_count):
        print(f"⚠️  WARNING: Approaching daily analysis limit! ({current_count}/{config.DAILY_ANALYSIS_LIMIT})")
        print(f"   Only {remaining} analyses remaining for today.\n")
    
    # If limit already reached, skip analysis entirely
    if not can_analyze:
        print(f"🛑 DAILY ANALYSIS LIMIT REACHED ({config.DAILY_ANALYSIS_LIMIT}/{config.DAILY_ANALYSIS_LIMIT})")
        print(f"   No more articles will be analyzed today.")
        print(f"   Limit will reset at midnight (00:00).\n")
    
    # If api_key is not passed, check environment variable
    if not api_key:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        
    for source_name, feed_url in FEEDS.items():
        print(f"Fetching articles from {source_name}...")
        articles = fetch_feed_articles(source_name, feed_url, limit=limit_per_feed)
        
        for art in articles:
            total_processed += 1
            inserted = database.insert_article(
                title=art["title"],
                source=art["source"],
                link=art["link"],
                published_date=art["published_date"],
                db_path=db_path
            )
            if inserted:
                new_inserted += 1
                
                # Check if we can still analyze more articles
                can_analyze, current_count, remaining = database.can_analyze_more_articles(db_path)
                
                # Automatically analyze if API key is configured AND limit not reached
                if api_key and api_key != "your_gemini_api_key_here" and api_key.strip():
                    if can_analyze:
                        try:
                            print(f"Analyzing ({current_count + 1}/{config.DAILY_ANALYSIS_LIMIT}): '{art['title']}'...")
                            
                            # Open temporary connection to find the ID
                            conn = sqlite3_conn = database.get_connection(db_path)
                            row = conn.execute("SELECT id FROM articles WHERE link = ?", (art["link"],)).fetchone()
                            conn.close()
                            
                            if row:
                                art_id = row["id"]
                                analysis = gemini_analyzer.analyze_article(
                                    title=art["title"],
                                    source=art["source"],
                                    content_hint="",
                                    api_key=api_key
                                )
                                
                                # Save to SQLite
                                database.update_article_analysis(
                                    article_id=art_id,
                                    category=analysis["category"],
                                    summary=analysis["summary"],
                                    why_it_matters=analysis["why_it_matters"],
                                    importance_score=analysis["importance_score"],
                                    impact_type=analysis["impact_type"],
                                    who_cares=",".join(analysis["who_cares"]) if isinstance(analysis["who_cares"], list) else str(analysis["who_cares"]),
                                    db_path=db_path
                                )
                                
                                # Increment the daily analysis counter
                                new_count = database.increment_daily_analysis_count(db_path)
                                new_analyzed += 1
                                
                                # Check if we just hit the limit
                                if new_count >= config.DAILY_ANALYSIS_LIMIT:
                                    print(f"\n🛑 DAILY ANALYSIS LIMIT REACHED ({new_count}/{config.DAILY_ANALYSIS_LIMIT})")
                                    print(f"   Remaining articles will be stored but not analyzed.")
                                    print(f"   Limit will reset at midnight (00:00).\n")
                                elif config.should_show_warning(new_count):
                                    remaining_now = config.get_remaining_analyses(new_count)
                                    print(f"⚠️  WARNING: Approaching limit! Only {remaining_now} analyses remaining today.\n")
                                    
                        except Exception as e:
                            print(f"Failed to analyze article '{art['title']}' during sync: {e}")
                            # Keep going for other articles
                            pass
                    else:
                        # Limit reached, skip analysis
                        skipped_due_to_limit += 1
                        print(f"⏭️  Skipped analysis (limit reached): '{art['title']}'")
                        
    print(f"\n{'='*60}")
    print(f"Sync complete!")
    print(f"  - Processed: {total_processed} articles")
    print(f"  - New articles added: {new_inserted}")
    print(f"  - Analyzed: {new_analyzed}")
    if skipped_due_to_limit > 0:
        print(f"  - Skipped (limit reached): {skipped_due_to_limit}")
    
    # Get final count
    final_count = database.get_daily_analysis_count(db_path)
    final_remaining = config.get_remaining_analyses(final_count)
    print(f"  - Daily analysis count: {final_count}/{config.DAILY_ANALYSIS_LIMIT}")
    print(f"  - Remaining today: {final_remaining}")
    print(f"{'='*60}\n")
    
    return {
        "processed": total_processed,
        "new_inserted": new_inserted,
        "new_analyzed": new_analyzed,
        "skipped_due_to_limit": skipped_due_to_limit,
        "daily_count": final_count,
        "daily_remaining": final_remaining
    }

if __name__ == "__main__":
    # Test execution
    print("Testing RSS Fetcher...")
    stats = sync_all_feeds(limit_per_feed=2)
    print("Stats:", stats)
