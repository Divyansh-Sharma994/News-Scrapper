# 📰 News Intelligence & Aggregation System

A professional-grade AI-powered news engine designed for deep-market analysis, automated industry classification, and high-accuracy summarization. This platform turns raw global news into structured, actionable intelligence.

---

## 🚀 Overview

This system allows users to monitor industry sectors or specific niche keywords across global sources. It doesn't just find links; it visits every website, extracts full-text content, and uses **Gemini 1.5 Flash AI** to classify and summarize findings.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Generative AI** | Google Gemini 1.5 Flash (Classifier & Summarizer) |
| **Frontend** | Streamlit (Interactive Dashboard) |
| **Backend** | Python 3.10+ |
| **Networking** | `aiohttp` (Asynchronous parallel fetching), `requests` |
| **Processing** | `pandas`, `BeautifulSoup4` (Scraping), `re` (Pattern Matching) |
| **Data Export** | `xlsxwriter` (Excel), `python-docx` (Word) |

---

## 📁 Project Structure

```text
├── app2.py                 # Primary High-Accuracy Dashboard (Main Entry)
├── app.py                  # Legacy/Alternative Dashboard (Keyword-based)
├── article_scraper.py      # Async "Digital Reader" - Visits links & extracts text
├── gdelt_fetcher.py        # Link discovery engine (Google News / GDELT)
├── smart_search.py         # AI Sector Identifier & Query Expander
├── article_scraper.py      # Content extraction heuristics
├── requirements.txt        # System dependencies
└── CHANGELOG.md            # Project history and updates
```

---

## 🔄 The Workflow (How it Works)

The application follows a 5-stage automated pipeline:

### 1. Smart Query Expansion (`smart_search.py`)
- User inputs a term (e.g., *"shoes"*).
- **Gemini AI** analyzes the intent and identifies the sector (e.g., *"Lifestyle & Fashion"*).
- The query is expanded into professional search strings to ensure high-quality results.

### 2. Multi-Source Link Discovery (`gdelt_fetcher.py`)
- The system fetches news from **Google News RSS** and **GDELT**.
- It uses a custom **Redirect Decoder** to resolve encrypted URLs into direct destination links.

### 3. High-Speed Parallel Scraping (`article_scraper.py`)
- Using `asyncio`, the system opens 20+ connections simultaneously.
- It "reads" the full article content, ignoring ads, sidebars, and junk scripts.
- It identifies paywalls and subscription blocks automatically.

### 4. AI Analysis & Sector Intelligence
- **Classification**: Gemini analyzes the *actual content* of each article to assign it a specific industry sector.
- **Summarization**: Gemini generates professional bulleted summaries for every extracted article.

### 5. Interactive UI & Export
- Results are displayed in a sleek, scrollable Streamlit interface.
- Users can export the entire intelligence report as **Excel** or **CSV**.

---

## ⚙️ Installation & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Main Application
```bash
python -m streamlit run app2.py
```

---

## 📜 Key Configuration
- **API Key**: The system uses a dedicated Gemini API key for all AI operations.
- **Duration**: Search period is adjustable from 1 to 30 days.
- **Anti-Blocking**: Uses rotated User-Agents and Referer headers to ensure high success rates.

---
*Developed for High-Speed News Intelligence Analysis.*
