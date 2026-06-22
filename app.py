import streamlit as st
import os
import database
import rss_fetcher
import gemini_analyzer
import config
from datetime import datetime
import html

# Page configuration
st.set_page_config(
    page_title="SpaceIntel AI - Space Intelligence Platform",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Space Theme
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');
    
    /* Global Styles */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: #ffffff;
    }

    /* Glassmorphic card styling for articles */
    .article-card {
        background: rgba(26, 28, 35, 0.65);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .article-card:hover {
        transform: translateY(-4px);
        border-color: rgba(0, 191, 255, 0.4);
        box-shadow: 0 10px 20px rgba(0, 191, 255, 0.08);
    }
    
    /* Category and Meta Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-astronomy { background-color: rgba(155, 89, 182, 0.2); color: #c39bd3; border: 1px solid rgba(155, 89, 182, 0.4); }
    .badge-exploration { background-color: rgba(52, 152, 219, 0.2); color: #85c1e9; border: 1px solid rgba(52, 152, 219, 0.4); }
    .badge-tech { background-color: rgba(230, 126, 34, 0.2); color: #f5b041; border: 1px solid rgba(230, 126, 34, 0.4); }
    .badge-business { background-color: rgba(46, 204, 113, 0.2); color: #82e0aa; border: 1px solid rgba(46, 204, 113, 0.4); }
    .badge-research { background-color: rgba(26, 188, 156, 0.2); color: #76d7c4; border: 1px solid rgba(26, 188, 156, 0.4); }
    .badge-unanalyzed { background-color: rgba(127, 140, 141, 0.2); color: #bdc3c7; border: 1px solid rgba(127, 140, 141, 0.4); }
    
    .source-tag {
        color: #8892b0;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 8px;
    }
    
    /* Details section */
    .intel-section {
        background: rgba(17, 24, 39, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .section-header {
        border-left: 4px solid #00bfff;
        padding-left: 12px;
        margin-top: 24px;
        margin-bottom: 12px;
        color: #e2e8f0;
    }
    
    /* Score display */
    .score-container {
        font-size: 2rem;
        font-weight: 700;
        color: #00bfff;
        text-shadow: 0 0 10px rgba(0, 191, 255, 0.3);
    }
    
    .who-cares-tag {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #cbd5e1;
        padding: 5px 12px;
        border-radius: 8px;
        margin-right: 8px;
        margin-bottom: 8px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to get badge class based on category
def get_category_badge(category):
    if not category:
        return '<span class="badge badge-unanalyzed">Unanalyzed</span>'
    cat = category.strip().lower()
    if "astronomy" in cat:
        return '<span class="badge badge-astronomy">Astronomy</span>'
    elif "exploration" in cat:
        return '<span class="badge badge-exploration">Space Exploration</span>'
    elif "tech" in cat:
        return '<span class="badge badge-tech">Space Technology</span>'
    elif "business" in cat:
        return '<span class="badge badge-business">Space Business</span>'
    elif "research" in cat or "discovery" in cat or "discoveries" in cat:
        return '<span class="badge badge-research">Research & Discoveries</span>'
    else:
        return f'<span class="badge badge-unanalyzed">{category}</span>'

# Initialize Database
db_name = "spaceintel.db"
database.init_db(db_name)

# Initialize Session State
if "selected_article_id" not in st.session_state:
    st.session_state.selected_article_id = None
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "All"

# Load API key from environment (server-side only)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Sidebar Configuration
with st.sidebar:
    st.image("spaceintel_banner.png", use_container_width=True)
    st.title("🛰️ Control Center")
    st.write("---")
    
    # Synchronization
    st.subheader("🔄 Synchronize Feed")
    st.write("Retrieve the latest updates from NASA, ESA, Space.com, and SpaceNews.")
    
    if st.button("Sync RSS Feeds", use_container_width=True):
        with st.spinner("Fetching latest space news and generating AI intelligence..."):
            sync_res = rss_fetcher.sync_all_feeds(limit_per_feed=5, db_path=db_name, api_key=GEMINI_API_KEY)
            
            # Show detailed sync results
            success_msg = f"Sync complete! Processed {sync_res['processed']} entries. Added {sync_res['new_inserted']} new articles, with {sync_res['new_analyzed']} analyzed automatically!"
            
            if sync_res.get('skipped_due_to_limit', 0) > 0:
                success_msg += f"\n\n⚠️ {sync_res['skipped_due_to_limit']} articles skipped due to daily analysis limit."
            
            st.success(success_msg)
            
            # Show daily limit info
            if sync_res.get('daily_remaining', 0) == 0:
                st.warning(f"🛑 Daily analysis limit reached ({sync_res['daily_count']}/{config.DAILY_ANALYSIS_LIMIT}). Limit resets at midnight.")
            elif config.should_show_warning(sync_res.get('daily_count', 0)):
                st.info(f"⚠️ Approaching daily limit: {sync_res['daily_count']}/{config.DAILY_ANALYSIS_LIMIT} analyses used today.")
            
            st.rerun()
            
    st.write("---")
    
    # DB Statistics
    st.subheader("📊 Platform Metrics")
    stats = database.get_db_stats(db_name)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Feeds", stats["total"])
        st.metric("Avg Score", f"{stats['avg_importance_score']}/10")
    with col2:
        st.metric("AI Analyzed", stats["analyzed"])
        st.metric("Unanalyzed", stats["unanalyzed"])
    
    st.write("---")
    
    # Daily Analysis Limit Status
    st.subheader("📈 Daily Analysis Limit")
    can_analyze, daily_count, daily_remaining = database.can_analyze_more_articles(db_name)
    
    # Progress bar for daily limit
    progress_percentage = daily_count / config.DAILY_ANALYSIS_LIMIT
    st.progress(progress_percentage, text=f"{daily_count} / {config.DAILY_ANALYSIS_LIMIT} analyses used today")
    
    # Status indicator
    if not can_analyze:
        st.error(f"🛑 Limit reached! Resets at midnight.")
    elif config.should_show_warning(daily_count):
        st.warning(f"⚠️ {daily_remaining} analyses remaining")
    else:
        st.success(f"✅ {daily_remaining} analyses available")

# Main Application Layout
if st.session_state.selected_article_id is None:
    # --- HOME PAGE (FEED VIEW) ---
    
    # Banner and Header
    st.image("spaceintel_banner.png", use_container_width=True)
    st.title("SpaceIntel AI 🌌")
    st.caption("### *AI-Powered Space Intelligence Platform*")
    
    st.markdown(
        """
        Welcome to **SpaceIntel AI**, your primary hub for curated space intelligence. 
        We scan official feeds, eliminate duplicate coverages, and use the power of the **Gemini API** 
        to synthesize raw news into actionable intelligence: what happened, why it matters, who benefits, and its long-term significance.
        """
    )
    
    # Sync prompt if empty
    if stats["total"] == 0:
        st.warning("⚠️ The database is currently empty. Click the 'Sync RSS Feeds' button in the sidebar to fetch space news.")
        st.stop()
        
    st.write("---")
    
    # Category Filter Buttons
    st.subheader("📂 Categories")
    categories_list = ["All", "Astronomy", "Space Exploration", "Space Technology", "Space Business", "Research & Discoveries"]
    
    cols = st.columns(6)
    for idx, cat_name in enumerate(categories_list):
        with cols[idx]:
            # Use visual indicators for the active category
            button_type = "primary" if st.session_state.selected_category == cat_name else "secondary"
            if st.button(cat_name, use_container_width=True, type=button_type):
                st.session_state.selected_category = cat_name
                st.rerun()

    # Search Bar
    st.write("")
    search_query = st.text_input("🔍 Search news articles by title or keyword:", value="")
    
    st.write("---")
    
    # Fetch articles
    articles = database.get_articles(category=st.session_state.selected_category, limit=50, db_path=db_name)
    
    # Apply search filter if specified
    if search_query:
        articles = [art for art in articles if search_query.lower() in art["title"].lower() or search_query.lower() in art["source"].lower()]
        
    # Render Feed
    st.write(f"Showing **{len(articles)}** articles under **{st.session_state.selected_category}**:")
    
    if not articles:
        st.info("No articles found matching the criteria. Try syncing feeds or changing your filters.")
        
    for art in articles:
        # Card Layout - HTML escape all dynamic content to prevent HTML injection
        card_html = f"""
        <div class="article-card">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                <span class="source-tag">📡 {html.escape(art['source'])}</span>
                <div>
                    {get_category_badge(art['category'])}
                    {f'<span class="badge" style="background-color: rgba(0, 191, 255, 0.15); color: #00bfff; border: 1px solid rgba(0, 191, 255, 0.3)">★ {art["importance_score"]}/10</span>' if art['analyzed'] else ''}
                </div>
            </div>
            <h3 style="margin: 0 0 12px 0; font-size: 1.25rem; font-weight: 600; line-height: 1.4;">
                {html.escape(art['title'])}
            </h3>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: #8892b0;">
                <span>📅 Published: {html.escape(art['published_date'])}</span>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Action button just below the markdown card
        col_btn, _ = st.columns([1.5, 8.5])
        with col_btn:
            btn_label = "⚡ View AI Intel" if art['analyzed'] else "🧠 Generate AI Analysis"
            if st.button(btn_label, key=f"btn_{art['id']}", use_container_width=True):
                st.session_state.selected_article_id = art["id"]
                st.rerun()
        st.write("")

else:
    # --- DETAIL / AI ANALYSIS PAGE ---
    art_id = st.session_state.selected_article_id
    art = database.get_article_by_id(art_id, db_path=db_name)
    
    if not art:
        st.error("Article not found.")
        if st.button("← Back to Feed"):
            st.session_state.selected_article_id = None
            st.rerun()
        st.stop()
        
    # Navigation Header
    if st.button("← Back to Feed", type="secondary"):
        st.session_state.selected_article_id = None
        st.rerun()
        
    st.write("---")
    
    # Check if we need to run AI analysis
    if not art["analyzed"]:
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            st.error("⚠️ Gemini API Key is not configured!")
            st.info("Please configure the GEMINI_API_KEY in the .env file on the server.")
            st.stop()
        
        # Check daily analysis limit before analyzing
        can_analyze, daily_count, daily_remaining = database.can_analyze_more_articles(db_name)
        
        if not can_analyze:
            st.error(f"🛑 Daily Analysis Limit Reached ({daily_count}/{config.DAILY_ANALYSIS_LIMIT})")
            st.warning("You have reached the maximum number of article analyses allowed per day.")
            st.info(f"The limit will reset at midnight (00:00). Current analyses today: {daily_count}/{config.DAILY_ANALYSIS_LIMIT}")
            st.stop()
        
        # Show warning if approaching limit
        if config.should_show_warning(daily_count):
            st.warning(f"⚠️ Approaching Daily Limit: {daily_count}/{config.DAILY_ANALYSIS_LIMIT} analyses used today. Only {daily_remaining} remaining.")
            
        with st.spinner("🧠 Initializing Gemini AI Space Intelligence engine..."):
            try:
                # Call Gemini Analyzer
                analysis = gemini_analyzer.analyze_article(
                    title=art["title"],
                    source=art["source"],
                    content_hint="",
                    api_key=GEMINI_API_KEY
                )
                
                # Update SQLite DB
                database.update_article_analysis(
                    article_id=art["id"],
                    category=analysis["category"],
                    summary=analysis["summary"],
                    why_it_matters=analysis["why_it_matters"],
                    importance_score=analysis["importance_score"],
                    impact_type=analysis["impact_type"],
                    who_cares=",".join(analysis["who_cares"]) if isinstance(analysis["who_cares"], list) else str(analysis["who_cares"]),
                    db_path=db_name
                )
                
                # Increment daily analysis counter
                new_count = database.increment_daily_analysis_count(db_name)
                
                # Refresh local article data
                art = database.get_article_by_id(art_id, db_path=db_name)
                st.balloons()
                
                # Show success message with updated count
                st.success(f"✅ Analysis complete! Daily count: {new_count}/{config.DAILY_ANALYSIS_LIMIT}")
                
                # Check if limit just reached
                if new_count >= config.DAILY_ANALYSIS_LIMIT:
                    st.info("🛑 Daily analysis limit has been reached. No more analyses can be performed until midnight.")
                
            except Exception as e:
                st.error(f"Failed to analyze article with Gemini: {e}")
                st.info("Ensure your API key is valid and you have an active internet connection.")
                st.stop()

    # --- Render Fully Analyzed Article Intel ---
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <div style="font-size: 0.95rem; color: #8892b0; margin-bottom: 10px;">📡 {html.escape(art['source'])} | 📅 Published: {html.escape(art['published_date'])}</div>
            <h1 style="font-size: 2.2rem; font-weight: 700; margin-top: 0; line-height: 1.3;">{html.escape(art['title'])}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Category, Importance Score, and Impact Type badges
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.markdown(
            f"""
            <div class="article-card" style="text-align: center; margin-bottom: 0;">
                <div style="font-size: 0.85rem; color: #8892b0; margin-bottom: 5px;">CATEGORY</div>
                <div>{get_category_badge(art['category'])}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    with col_stat2:
        # Format importance score with text colors
        score = art["importance_score"]
        score_color = "#2ecc71" if score >= 8 else ("#f39c12" if score >= 5 else "#e74c3c")
        st.markdown(
            f"""
            <div class="article-card" style="text-align: center; margin-bottom: 0;">
                <div style="font-size: 0.85rem; color: #8892b0; margin-bottom: 5px;">IMPORTANCE SCORE</div>
                <div style="font-size: 1.6rem; font-weight: 700; color: {score_color};">{score} / 10</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    with col_stat3:
        impact = art["impact_type"]
        impact_color = "#3498db" if "long" in impact.lower() else "#e67e22"
        st.markdown(
            f"""
            <div class="article-card" style="text-align: center; margin-bottom: 0;">
                <div style="font-size: 0.85rem; color: #8892b0; margin-bottom: 5px;">IMPACT TYPE</div>
                <div style="font-size: 1.6rem; font-weight: 700; color: {impact_color};">{impact}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    st.write("")
    
    # Intelligence Core Content
    st.markdown('<div class="intel-section">', unsafe_allow_html=True)
    
    st.markdown('<h3 class="section-header">🤖 AI Summary</h3>', unsafe_allow_html=True)
    st.write(art["summary"] if art["summary"] else "")
    
    st.markdown('<h3 class="section-header">💡 Why It Matters</h3>', unsafe_allow_html=True)
    st.write(art["why_it_matters"] if art["why_it_matters"] else "")
    
    st.markdown('<h3 class="section-header">🎯 Target Stakeholders (Who Cares)</h3>', unsafe_allow_html=True)
    whocares_list = [w.strip() for w in art["who_cares"].split(",") if w.strip()]
    
    tags_html = ""
    for stakeholder in whocares_list:
        tags_html += f'<span class="who-cares-tag">👥 {html.escape(stakeholder)}</span>'
    st.markdown(tags_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("")
    st.write("---")
    
    # Call to action
    col_act1, col_act2 = st.columns([2, 8])
    with col_act1:
        st.link_button("🌐 Read Full Article", url=art["link"], use_container_width=True, type="primary")
    with col_act2:
        st.write("*Verify the detailed metrics and references directly on the publisher's official platform.*")
