# Changelog - News Intelligence System

## [Dev4 Branch] - 2026-02-02

### Added - NER-Based Entity Extraction Feature

#### New Files Created:
1. **`ner_entity_extractor.py`** - Core NER module
   - Implements `NEREntityExtractor` class with spaCy integration
   - Uses pre-trained `en_core_web_sm` model for Named Entity Recognition
   - Extracts ORG (organizations), PRODUCT, and GPE (geopolitical entities)
   - Advanced filtering to remove noise words and generic terms
   - Entity normalization (removes suffixes like Inc., Corp., Ltd.)
   - Dual-mode operation: spaCy NER (preferred) + Pattern-based fallback
   - Confidence scoring based on mention frequency and article coverage
   - Entity type classification (company, government_agency, research_org)

#### Modified Files:
1. **`app2.py`** - Main application
   - Added new section: "🏢 Top Trending Agencies & Brands"
   - Integrated NER entity extraction after article display
   - Added interactive controls:
     - Slider for minimum mentions threshold (2-10)
     - "Extract Trending Entities" button
   - Display features:
     - Top 10 ranked entities with visual cards
     - Color-coded confidence badges (🟢 High, 🟡 Medium, 🟠 Low)
     - Entity type icons (🏢 Company, 🏛️ Government, 🔬 Research)
     - Metrics: mentions count, percentage, confidence score
   - Download option for trending agencies (CSV format)
   - Error handling with helpful installation tips

2. **`requirements.txt`**
   - Added: `spacy>=3.7.0`

### Technical Implementation Details:

#### NER Extraction Pipeline:
1. **Text Preprocessing**:
   - Combines title, description, and first 500 chars of full text
   - Prioritizes title content (3x weight multiplier)

2. **Entity Recognition**:
   - Primary: spaCy's statistical NER model
   - Fallback: Regex-based capitalized word extraction
   - Filters: Noise words, generic terms, dates, numbers

3. **Entity Normalization**:
   - Removes common corporate suffixes
   - Deduplicates variations of same entity

4. **Ranking Algorithm**:
   - Frequency-based scoring
   - Percentage of articles mentioning entity
   - Confidence calculation: min(95, (count / (total_articles * 0.1)) * 100)
   - Minimum mentions threshold (user-configurable)

5. **Classification**:
   - Government agencies: Keywords like "ministry", "department", "bureau"
   - Research orgs: Keywords like "university", "institute", "lab"
   - Default: Company

### User Experience:
- **Workflow**: Fetch articles → Extract entities → View ranked list → Download CSV
- **Visual Design**: Color-coded confidence indicators, entity type icons
- **Flexibility**: Adjustable minimum mentions threshold
- **Error Handling**: Graceful fallback if spaCy not installed

### Installation Requirements:
```bash
pip install spacy>=3.7.0
python -m spacy download en_core_web_sm
```

### Usage:
1. Run the app and fetch news articles (existing functionality)
2. Scroll to "Top Trending Agencies & Brands" section
3. Adjust minimum mentions slider if needed
4. Click "Extract Trending Entities"
5. View ranked list of top 10 agencies/brands
6. Download CSV for further analysis

### Benefits:
- **Accuracy**: Uses state-of-the-art NER instead of simple keyword matching
- **Context-Aware**: Understands entity boundaries and types
- **Robust**: Filters out noise and generic terms
- **Scalable**: Handles large article datasets efficiently
- **User-Friendly**: Simple one-click extraction with visual results

### Future Enhancements (Potential):
- Multi-language NER support
- Entity linking to knowledge bases (Wikipedia, Wikidata)
- Sentiment analysis per entity
- Trend visualization over time
- Entity relationship extraction
