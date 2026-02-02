# 🔍 How to Find and Use the NER Feature

## ✅ The Button is Now Always Visible!

The "Top Trending Agencies & Brands Analyzer" section is now **always visible** at the bottom of the page.

## 📍 Where to Find It

### Visual Guide:

```
┌─────────────────────────────────────────────┐
│  📰 News Search Engine                      │
│  [Search Box] [Duration]                    │
│  [🚀 Analyze Sector Button]                 │
└─────────────────────────────────────────────┘
              ↓ (scroll down)
┌─────────────────────────────────────────────┐
│  📋 Results for 'your search'               │
│  [Article 1]                                │
│  [Article 2]                                │
│  [Article 3]                                │
│  ...                                        │
│  [📥 Download Excel] [📥 Download CSV]      │
└─────────────────────────────────────────────┘
              ↓ (scroll down more)
┌─────────────────────────────────────────────┐
│  ═══════════════════════════════════════    │
│  ═══════════════════════════════════════    │
│                                             │
│  🏢 Top Trending Agencies & Brands Analyzer │
│  ℹ️ Extract and rank the most mentioned... │
│                                             │
│  ⚠️ Please fetch news articles first...    │  ← Shows BEFORE fetching
│     OR                                      │
│  ✅ Ready to analyze 150 articles...       │  ← Shows AFTER fetching
│                                             │
│  [Slider: Minimum mentions]                │
│  [🔍 Extract Trending Entities] ← BUTTON!  │
└─────────────────────────────────────────────┘
```

## 🎯 Step-by-Step Instructions

### Step 1: Open the App
- URL: **http://localhost:8501**
- The app should auto-reload with the new changes

### Step 2: Scroll to the Bottom
- **Scroll all the way down** the page
- You'll see two horizontal lines (separators)
- Below that: **"🏢 Top Trending Agencies & Brands Analyzer"**

### Step 3: Two Scenarios

#### Scenario A: No Articles Yet
You'll see:
```
⚠️ Please fetch news articles first using the search above,
   then come back here to extract trending entities.
```

**What to do**: 
1. Scroll back to top
2. Enter a search query (e.g., "artificial intelligence")
3. Click the search button
4. Wait for articles to load
5. Scroll back down to this section

#### Scenario B: Articles Already Fetched
You'll see:
```
✅ Ready to analyze 150 articles from 'your search'

[Slider: Minimum mentions to include]
[🔍 Extract Trending Entities] ← Click this!
```

**What to do**:
1. Adjust the slider if needed (default: 3)
2. Click **"🔍 Extract Trending Entities"**
3. Wait for analysis
4. See results appear below!

## 🎨 What You'll See

### Before Clicking:
- Section header
- Info message
- Status (warning or success)
- Slider (if articles available)
- **Blue button** (if articles available)

### After Clicking:
- Loading spinner: "🧠 Analyzing articles with NER..."
- Success message: "✅ Found 10 trending agencies/brands!"
- **Top 10 list** with colored cards:
  - 🟢 Green = High confidence
  - 🟡 Yellow = Medium confidence
  - 🟠 Orange = Lower confidence
- Download button for CSV

## 🔧 Troubleshooting

### "I don't see the section at all"
- **Refresh the page**: Press F5 or Ctrl+R
- The app should have auto-reloaded
- Check you're on: http://localhost:8501

### "I see the section but no button"
- You need to **fetch articles first**
- Scroll to top → Search → Fetch articles
- Then scroll back down

### "The button doesn't work"
- Check browser console for errors (F12)
- Try refreshing the page
- Make sure you have articles fetched

### "I get an error when clicking"
- The system will use pattern-based fallback
- You'll still get results
- For best results: `pip install spacy && python -m spacy download en_core_web_sm`

## 📊 Example Workflow

1. **Open**: http://localhost:8501
2. **Search**: Enter "electric vehicles"
3. **Duration**: Set to 7 days
4. **Fetch**: Click search button
5. **Wait**: Articles load (may take 1-2 minutes)
6. **Scroll Down**: All the way to bottom
7. **See Section**: "Top Trending Agencies & Brands Analyzer"
8. **See Status**: "✅ Ready to analyze 150 articles..."
9. **Adjust Slider**: Set minimum mentions (e.g., 3)
10. **Click Button**: "🔍 Extract Trending Entities"
11. **Wait**: NER analysis (10-30 seconds)
12. **View Results**: Top 10 list appears!
13. **Download**: Click CSV button if needed

## ✨ What Changed

**Before**: Section only appeared AFTER fetching articles (hidden)
**Now**: Section ALWAYS visible at bottom (with helpful status)

This makes it much easier to find and use! 🎉

---

**The button is there - just scroll to the very bottom of the page!**
