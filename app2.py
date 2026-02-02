import os
import requests
import feedparser
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from io import BytesIO
import asyncio
import aiohttp
import re
import google.generativeai as genai
import json

# Import our helper tools (which we wrote in other files)
from gdelt_fetcher import fetch_gdelt_simple
from article_scraper import enhance_articles_async
from smart_search import expand_query

# --- GEMINI SETUP ---
# Removed hardcoded key for security. Use environment variable 'GEMINI_API_KEY'.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
# Use gemini-1.5-flash for high-speed, reliable intelligence and long-context processing
gemini_model = genai.GenerativeModel('gemini-1.5-flash') if GEMINI_API_KEY else None

def classify_article_gemini(headline, source, content, cluster_names):
    """
    Uses Gemini to classify an article into one of the provided clusters.
    """
    if not content or len(content.strip()) < 50:
        content = "No content available. Classify based on headline only."
    
    if not gemini_model:
        return "GENERAL"
        
    clusters_str = ", ".join(cluster_names)
    prompt = f"""
    You are a professional news analyst. Classify the following news article into EXACTLY ONE of these sectors/clusters:
    [{clusters_str}]

    If it fits multiple, pick the most relevant one. 
    If it fits NONE of them, respond with "NONE".

    Article Headline: {headline}
    Source: {source}
    Full Content snippet: {content[:3000]}

    Respond ONLY with the name of the cluster or "NONE". Do not provide any explanation.
    """
    try:
        response = gemini_model.generate_content(prompt)
        result = response.text.strip()
        # Clean up in case Gemini adds markdown or extra text
        result = result.replace("**", "").replace('"', '').replace("'", "").strip()
        
        if result in cluster_names:
            return result
        else:
            # Check for case-insensitive match
            for c in cluster_names:
                if result.lower() == c.lower():
                    return c
            return "GENERAL"
    except Exception:
        return "GENERAL"

def summarize_text_gemini(text: str) -> str:
    """
    Uses Gemini 1.5 Pro to provide a comprehensive, deep-dive summary of the article.
    """
    if not text or not text.strip():
        return "No content to summarize."
    if not gemini_model:
        # Fallback to a simple 6-line slice if Gemini is not configured
        words = text.split()
        return " ".join(words[:100]) + "..."

    try:
        prompt = f"""
        You are an expert news intelligence analyst. Provide a COMPREHENSIVE and DETAILED summary of the following news article.
        
        Guidelines:
        1. Capture the core event/announcement.
        2. Detail all involved stakeholders (companies, individuals, agencies).
        3. Explain the industry implications and future outlook.
        4. Include any critical financial data or specific statistics mentioned.
        5. Structure the response with a clear hierarchy (Headings/Bullets/Paragraphs) to make it highly professional.
        
        Article Content:
        {text[:15000]}
        """
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini Summarization Error: {e}"


# --- PAGE SETUP ---
# This configures the browser tab title and layout
st.set_page_config(page_title="News Intelligence", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM STYLING (CSS) ---
# We hide the default Streamlit menu to make it look like a real app.
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# --- THEME CONTROL ---
# This remembers if you like Dark Mode or Light Mode.
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

col_theme = st.columns([0.95, 0.05])
with col_theme[1]:
    # The toggle button for theme
    if st.button("🌓" if st.session_state.theme == 'dark' else "🌞", help="Toggle theme"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()

# Apply Light Mode colors if selected
if st.session_state.theme == 'light':
    st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; color: #000000; }
        .stMarkdown, .stText, h1, h2, h3 { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- APP HEADER ---
if os.path.exists("Mavericks logo.png"):
    st.image("Mavericks logo.png", width=150)
st.title("📰 News Search Engine")
st.caption("Enter a keyword to find the latest news articles with full content previews.")

# Initialize our "memory" to store articles
if "articles" not in st.session_state:
    st.session_state.articles = []

if "custom_mode" not in st.session_state:
    st.session_state.custom_mode = False


# --- INPUT SECTION (Sector & Keyword) ---
sector_options = ["Lifestyle", "Sustainability", "Tech & AI", "Health", "Finance", "Education", "Sports", "Startups"]

# Toggle Logic
if st.button("🔄 Switch to " + ("Sector Mode" if st.session_state.custom_mode else "Manual Custom Search")):
    st.session_state.custom_mode = not st.session_state.custom_mode
    st.rerun()

if not st.session_state.custom_mode:
    # 🏢 SECTOR MODE
    selected_sector = st.selectbox("📂 Select Industry Sector", 
                                  sector_options,
                                  help="Choose a predefined sector for automated deep-market analysis")
    active_query = selected_sector
    st.info(f"� AI analyzing standard sector: **{selected_sector}**")
else:
    # ⌨️ MANUAL MODE
    manual_query = st.text_input("📝 Type Your Specific Niche/Sector", "Electric Aviation", 
                                 help="Define any industry or topic not in the list")
    active_query = manual_query
    st.success(f"� AI performing deep-dive search for: **{manual_query}**")

# Duration remains common
duration = st.number_input("📅 Analysis Period (Days)", min_value=1, max_value=30, value=7)


# --- SEARCH ACTION ---
if st.session_state.custom_mode:
    button_label = f"🔍 Search Custom: {active_query}"
else:
    button_label = f"🚀 Analyze {selected_sector} Sector"

if st.button(button_label, type="primary", use_container_width=True):
    # --- PROGRESSIVE LOADING STATUS ---
    with st.status("🤖 AI Agent is working...", expanded=True) as status:
        
        # STEP 0: Identifies sector context via Gemini AI
        status.write("🧠 Consulting Gemini AI for sector classification...")
        result_context = expand_query(active_query)
        st.session_state.sector_identified = result_context['sector_identified']
        optimized_query = result_context['optimized_query']

        # STEP 1: FIND LINKS
        status.write(f"🔍 Searching Google News for '{optimized_query}'...")
        raw_articles = fetch_gdelt_simple(optimized_query, days=duration, max_articles=5000)
        
        if not raw_articles:
            status.update(label="❌ No news found!", state="error", expanded=False)
            st.error("No news found for this keyword. Please try another.")
            st.session_state.articles = []
        else:
            status.write(f"✅ Found {len(raw_articles)} links from around the web.")
            
            # STEP 2: READ CONTENT
            status.write(f"📖 Visiting all {len(raw_articles)} websites to extract content...")
            
            # Setup the loading bar (0% initially)
            progress_bar = status.progress(0)
            
            # This little function updates the blue bar
            def update_progress(current, total):
                percent = int((current / total) * 100)
                progress_bar.progress(percent)
                if current % 5 == 0 or current == total:
                     status.update(label=f"📖 Reading articles... ({percent}%)")
            
            # RUN THE SCRAPER! (This visits all sites)
            enhanced_articles = asyncio.run(enhance_articles_async(
                raw_articles, 
                limit=None, 
                progress_callback=update_progress
            ))
            
            # STEP 3: CLASSIFY & SUMMARIZE WITH GEMINI
            status.write("🤖 Performing AI Classification & Summarization...")
            for art in enhanced_articles:
                headline = art.get('title', '')
                source = art.get('source', '')
                content = art.get('full_text', '')
                
                # Classify
                art['gemini_sector'] = classify_article_gemini(headline, source, content, sector_options)
                
                # Summarize
                if content and not art.get('is_paywall'):
                    art['gemini_summary'] = summarize_text_gemini(content)
            
            progress_bar.progress(100)
            
            st.session_state.articles = enhanced_articles
            st.session_state.last_query = active_query
            
            # Collapse the status box when done
            status.update(label="✅ All Done! Articles ready.", state="complete", expanded=False)

# --- DISPLAY RESULTS ---
if st.session_state.articles:
    sector_label = st.session_state.get('sector_identified', 'GENERAL')
    st.subheader(f"📋 Results for '{st.session_state.get('last_query', active_query)}' | Sector: {sector_label}")

    
    # --- SCROLLABLE CONTAINER ---
    # A box with fixed height (800px) so you can scroll inside it.
    with st.container(height=800):
        for i, article in enumerate(st.session_state.articles):
            title = article['title']
            source = article['source']
            summary = article.get('summary', 'No summary available.')
            full_text = article.get('full_text', '')
            is_paywall = article.get('is_paywall', False)
            link = article['link']
            published = article['published']
            
            # --- ARTICLE CARD ---
            with st.container():
                # Title fits?
                st.markdown(f"### {i+1}. [{title}]({link})")
                gemini_sector = article.get('gemini_sector', 'GENERAL')
                st.markdown(f"**AI Classification:** `{gemini_sector}`")
                st.caption(f"**Source:** {source} | **Published:** {published}")
                
                # DROPDOWN: "Read Full Article Content"
                # Everything inside here is hidden until clicked
                with st.expander("📖 Read AI Intelligence Summary & Content"):
                    # 1. Structured 6-Line Summary
                    st.markdown("#### 📄 Intelligence Summary (AI Generated)")
                    
                    gemini_summary = article.get('gemini_summary')
                    if gemini_summary:
                        st.markdown(f"<div style='background-color: #f0f2f6; padding: 15px; border-radius: 8px; color: #000000;'>{gemini_summary.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
                    else:
                        # Fallback to local 6-line splitting
                        sent_list = re.split(r'(?<=[.!?])\s+', summary)
                        clean_sents = [s.strip() for s in sent_list if len(s.strip()) > 20]
                        
                        if len(clean_sents) < 6:
                            words = summary.split()
                            if len(words) > 60:
                                chunk = len(words) // 6
                                clean_sents = [" ".join(words[j*chunk:(j+1)*chunk]) for j in range(6)]
                        
                        summary_box = "".join([f"• {s}<br><br>" for s in clean_sents[:6]])
                        st.markdown(f"<div style='background-color: #f0f2f6; padding: 15px; border-radius: 8px; color: #000000;'>{summary_box}</div>", unsafe_allow_html=True)

                    
                    # 2. Full Text
                    st.markdown("#### Full Article")
                    if is_paywall:
                        st.warning("🔒 **Subscription Required**: This article seems to be behind a paywall.")
                    
                    if full_text:
                        st.write(full_text)
                    else:
                        st.warning("⚠️ Could not extract full text.")

                st.markdown(f"🔗 [**Go to Valid Original Article**]({link})")
                st.markdown("---")

    # --- DOWNLOAD BUTTONS ---
    df = pd.DataFrame(st.session_state.articles)
    
    # Prepare Excel file
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='News')
    buffer.seek(0)
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            label="📥 Download as Excel",
            data=buffer,
            file_name=f"news_{st.session_state.get('last_query', 'results')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col_dl2:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"news_{st.session_state.get('last_query', 'results')}.csv",
            mime="text/csv"
        )


# --- NER ENTITY EXTRACTION SECTION (STANDALONE - ALWAYS VISIBLE) ---
st.markdown("---")
st.markdown("---")
st.subheader("🏢 Top Trending Agencies & Brands Analyzer")
st.info("📊 Extract and rank the most mentioned companies, agencies, and brands from your fetched articles using advanced Named Entity Recognition (NER)")

# Initialize session state for agencies
if "trending_agencies" not in st.session_state:
    st.session_state.trending_agencies = []

# Check if articles are available
if not st.session_state.articles:
    st.warning("⚠️ Please fetch news articles first using the search above, then come back here to extract trending entities.")
else:
    st.success(f"✅ Ready to analyze {len(st.session_state.articles)} articles from '{st.session_state.get('last_query', 'your search')}'")
    
    extract_button = st.button("🔍 Extract Top Trending Companies", type="primary", use_container_width=True, key="extract_ner_btn")
    
    if extract_button:
        with st.spinner("🧠 Analyzing articles with advanced NER to identify top companies..."):
            try:
                # Use advanced NER extractor
                from advanced_ner_extractor import extract_top_companies
                
                # Extract top 10 companies using dominance-based ranking
                top_companies = extract_top_companies(
                    st.session_state.articles,
                    st.session_state.get('last_query', 'search'),
                    top_n=10
                )
                
                # Map to display format
                st.session_state.trending_agencies = []
                for company in top_companies:
                    st.session_state.trending_agencies.append({
                        'rank': company['rank'],
                        'name': company['name'],
                        'mentions': company['mentions'],
                        'percentage': company['coverage_pct'],
                        'confidence': company['dominance_score'],
                        'entity_type': company['entity_type'],
                        'context_diversity': company['sources']
                    })
                
                if st.session_state.trending_agencies:
                    st.success(f"✅ Found {len(st.session_state.trending_agencies)} dominant companies/organizations!")
                else:
                    st.warning("⚠️ No companies found. Try fetching more articles.")
            except Exception as e:
                st.error(f"❌ Error during entity extraction: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Display trending agencies
    if st.session_state.trending_agencies:
        st.markdown("### 📊 Top 10 Dominant Companies & Organizations")
        st.caption("Ranked by dominance score (involvement + coverage + diversity)")
        
        for agency in st.session_state.trending_agencies:
            rank = agency['rank']
            name = agency['name']
            mentions = agency['mentions']
            percentage = agency['percentage']
            dominance = agency['confidence']  # This is dominance_score
            sources = agency.get('context_diversity', 0)
            entity_type = agency['entity_type']
            
            # Color coding based on dominance score
            if dominance >= 70:
                badge = "🟢"
                color = "#28a745"
                level = "High Dominance"
            elif dominance >= 50:
                badge = "🟡"
                color = "#ffc107"
                level = "Medium Dominance"
            else:
                badge = "🟠"
                color = "#fd7e14"
                level = "Emerging"
            
            # Entity type emoji
            type_emoji = '🏢'  # All are companies/organizations
            
            st.markdown(f"""
            <div style='padding: 15px; margin: 10px 0; border-left: 5px solid {color}; 
                        background-color: rgba(0,0,0,0.05); border-radius: 5px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <strong style='font-size: 1.2em;'>{badge} #{rank} {name}</strong> {type_emoji}
                        <br>
                        <small style='opacity: 0.8;'>
                            📰 {mentions} mentions • 📊 {percentage}% coverage • 
                            🎯 Dominance: {dominance:.1f} ({level}) • 
                            🌐 {sources} sources
                        </small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Download option for agencies
        st.markdown("---")
        agencies_df = pd.DataFrame(st.session_state.trending_agencies)
        agencies_csv = agencies_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Trending Agencies (CSV)",
            data=agencies_csv,
            file_name=f"trending_agencies_{st.session_state.get('last_query', 'results')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_agencies_btn"
        )
