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

# Import our helper tools (which we wrote in other files)
from gdelt_fetcher import fetch_gdelt_simple
from article_scraper import enhance_articles_async

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

# --- INPUT SECTION (Search Bar) ---
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("🔍 Enter Keyword", "Artificial Intelligence", help="Type any topic")
with col2:
    duration = st.number_input("📅 Days back", min_value=1, max_value=30, value=7)

st.markdown("---")

# --- SEARCH ACTION ---
# This runs when you click the big red button
if st.button("🚀 Find News Articles", type="primary", use_container_width=True):
    # --- PROGRESSIVE LOADING STATUS ---
    # This creates the "box" that shows you what the AI is doing.
    with st.status("🤖 AI Agent is working...", expanded=True) as status:
        
        # STEP 1: FIND LINKS
        status.write(f"🔍 Searching Google News for '{query}'...")
        # We ask for up to 5000 links
        raw_articles = fetch_gdelt_simple(query, days=duration, max_articles=5000)
        
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
                # Update text every few items
                if current % 5 == 0 or current == total:
                     status.update(label=f"📖 Reading articles... ({percent}%)")
            
            # RUN THE SCRAPER! (This visits all sites)
            enhanced_articles = asyncio.run(enhance_articles_async(
                raw_articles, 
                limit=None, 
                progress_callback=update_progress
            ))
            
            progress_bar.progress(100)
            
            st.session_state.articles = enhanced_articles
            st.session_state.last_query = query
            
            # Collapse the status box when done
            status.update(label="✅ All Done! Articles ready.", state="complete", expanded=False)

# --- DISPLAY RESULTS ---
if st.session_state.articles:
    st.subheader(f"📋 Results for '{st.session_state.get('last_query', query)}'")
    
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
                st.caption(f"**Source:** {source} | **Published:** {published}")
                
                # DROPDOWN: "Read Full Article Content"
                # Everything inside here is hidden until clicked
                with st.expander("📖 Read Full Article Content"):
                    # 1. Summary
                    st.markdown("#### Summary")
                    st.info(summary)
                    
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
