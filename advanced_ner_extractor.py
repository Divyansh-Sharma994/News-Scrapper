"""
Production-Grade NER-based Entity Extraction for News Intelligence
Implements strict company/organization filtering with dominance-based ranking
"""

import re
from collections import defaultdict
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings("ignore")

# Use transformers-based NER (optional - fallback to pattern-based)
NER_AVAILABLE = False
ner_pipeline = None

import google.generativeai as genai
import os

# Initialize Gemini if key exists
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    except:
        GEMINI_AVAILABLE = False
else:
    GEMINI_AVAILABLE = False

try:
    from transformers import pipeline
    ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
    NER_AVAILABLE = True
    print("✅ Transformers NER loaded successfully")
except Exception as e:
    print(f"⚠️ Transformers not available, using pattern-based extraction: {e}")
    NER_AVAILABLE = False
    ner_pipeline = None


class AdvancedNERExtractor:
    """
    Production-grade entity extractor with strict company/organization filtering
    """
    
    def __init__(self):
        self.ner = ner_pipeline
        self.gemini_cache = {}  # Cache for Gemini validation
        
        # STRICT: Publishers and news outlets to exclude
        self.excluded_publishers = {
            'reuters', 'bloomberg', 'cnbc', 'cnn', 'bbc', 'forbes', 'techcrunch',
            'times', 'post', 'guardian', 'journal', 'news', 'press', 'media',
            'tribune', 'herald', 'gazette', 'chronicle', 'observer', 'telegraph',
            'associated press', 'ap news', 'afp', 'pti', 'ani', 'ians'
        }
        
        # STRICT: Generic terms that are NOT companies
        self.generic_terms = {
            'government', 'police', 'court', 'hospital', 'university', 'school',
            'company', 'corporation', 'industry', 'market', 'sector', 'department',
            'ministry', 'office', 'bureau', 'agency', 'service', 'center',
            'institute', 'foundation', 'trust', 'group', 'team', 'committee',
            'council', 'board', 'commission', 'authority', 'people', 'public',
            'officials', 'sources', 'experts', 'analysts', 'investors', 'customers',
            'budget', 'mission', 'fund', 'scheme', 'plan', 'survey'
        }
        
        # STRICT: Location/country indicators
        self.location_indicators = {
            'india', 'indian', 'us', 'usa', 'uk', 'china', 'chinese', 'japan',
            'america', 'american', 'europe', 'european', 'asia', 'asian',
            'delhi', 'mumbai', 'bangalore', 'london', 'new york', 'beijing',
            'tokyo', 'singapore', 'dubai', 'california', 'texas',
            'bharat', 'central', 'national', 'global', 'international'
        }
        
        # Known company suffixes for validation
        self.company_suffixes = {
            'inc', 'corp', 'ltd', 'llc', 'co', 'group', 'holdings', 'technologies',
            'systems', 'solutions', 'services', 'industries', 'enterprises',
            'international', 'global', 'motors', 'energy', 'pharma', 'labs'
        }
        
        # Main actor position indicators (headline structure)
        self.main_actor_positions = ['start', 'subject']  # First 3 words or subject position
    
    def _validate_with_gemini(self, entity: str, headline: str) -> bool:
        """
        FINAL VALIDATION LAYER: Uses Gemini to confirm entity is a company.
        Strict YES/NO decision. Cached.
        """
        if not GEMINI_AVAILABLE:
            return True  # Fallback: Assume valid if passed rules
            
        # Check cache (entity + headline context)
        cache_key = f"{entity}|{headline}"
        if cache_key in self.gemini_cache:
            return self.gemini_cache[cache_key]
        
        # Only validate ambiguous or short names (to save calls)
        # Long names with company suffixes (e.g. "Apple Inc") are already safe
        is_obvious_company = any(s in entity.lower() for s in self.company_suffixes)
        if len(entity.split()) > 2 and is_obvious_company:
            return True
            
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            Task: Validate if '{entity}' is a COMPANY or ORGANIZATION in this headline.
            Headline: "{headline}"
            
            Rules:
            1. Return "YES" if it is a specific commercial company, brand, or organization (e.g., Apple, OpenAI, WHO).
            2. Return "NO" if it is a person, location, government body, product, generic term, or abstract concept (e.g., Budget, AI Mission, London, ChatGPT).
            3. Strict YES or NO output only.
            """
            
            response = model.generate_content(prompt)
            result = response.text.strip().upper()
            
            is_valid = "YES" in result
            self.gemini_cache[cache_key] = is_valid
            return is_valid
            
        except Exception as e:
            # On error, fallback to True (don't block pipeline)
            print(f"⚠️ Gemini validation error: {e}")
            return True

    def _is_valid_company_name(self, entity: str) -> bool:
        """
        STRICT validation: Is this truly a company/organization name?
        """
        entity_lower = entity.lower().strip()
        
        # Rule 1: Exclude publishers
        if any(pub in entity_lower for pub in self.excluded_publishers):
            return False
        
        # Rule 2: Exclude generic terms (single word)
        if ' ' not in entity_lower and entity_lower in self.generic_terms:
            return False
        
        # Rule 3: Exclude locations
        if entity_lower in self.location_indicators:
            return False
        
        # Rule 4: Must be capitalized (proper noun)
        if not entity[0].isupper():
            return False
        
        # Rule 5: Minimum length
        if len(entity) < 3:  # Increased to 3 to filter "AI", "US"
            return False
        
        # Rule 6: Cannot be all uppercase (likely acronym without context)
        if entity.isupper() and len(entity) < 3:
            return False
        
        # Rule 7: Cannot contain only numbers
        if re.match(r'^[\d\s\-\/]+$', entity):
            return False
        
        return True
    
    def _calculate_involvement_score(self, entity: str, headline: str, position: int, total_words: int) -> float:
        """
        Determine if entity is MAIN ACTOR or incidental mention
        Score: 0.0 (incidental) to 1.0 (main actor)
        """
        score = 0.0
        entity_lower = entity.lower()
        headline_lower = headline.lower()
        
        # Factor 1: Position in headline (30% weight)
        # Main actors typically appear in first 40% of headline
        position_ratio = position / max(total_words, 1)
        if position_ratio <= 0.4:
            score += 0.3
        elif position_ratio <= 0.6:
            score += 0.15
        
        # Factor 2: Headline structure (40% weight)
        # Check if entity is the subject (before verb)
        action_verbs = ['launches', 'announces', 'reports', 'unveils', 'introduces',
                       'acquires', 'partners', 'expands', 'raises', 'files', 'wins']
        
        # Find if entity appears before action verb
        headline_words = headline_lower.split()
        entity_words = entity_lower.split()
        
        for verb in action_verbs:
            if verb in headline_words:
                verb_pos = headline_words.index(verb)
                # Check if entity is before verb
                for ent_word in entity_words:
                    if ent_word in headline_words:
                        ent_pos = headline_words.index(ent_word)
                        if ent_pos < verb_pos:
                            score += 0.4
                            break
                break
        
        # Factor 3: Possessive or attribution (20% weight)
        # "Company's product" = main actor
        # "according to Company" = incidental
        if f"{entity_lower}'s" in headline_lower or f"{entity_lower} said" in headline_lower:
            score += 0.2
        elif "according to" in headline_lower and entity_lower in headline_lower.split("according to")[1]:
            score -= 0.2  # Penalize citations
        
        # Factor 4: Standalone mention (10% weight)
        # Entity mentioned alone vs in a list
        if headline_lower.count(entity_lower) == 1:
            score += 0.1
        
        return min(max(score, 0.0), 1.0)
    
    def extract_entities_ner(self, articles: List[Dict]) -> Dict[str, Dict]:
        """
        Extract entities using NER with strict filtering & Gemini validation
        Returns: {entity_name: {mentions, involvement_scores, headlines}}
        """
        entity_data = defaultdict(lambda: {
            'mentions': 0,
            'involvement_scores': [],
            'headlines': [],
            'article_count': 0,
            'sources': set()
        })
        
        for article in articles:
            headline = article.get('title', '')
            source = article.get('source', 'Unknown')
            
            if not headline or len(headline) < 10:
                continue
            
            # Use NER or fallback to pattern-based
            if self.ner:
                entities = self._extract_with_transformers(headline)
            else:
                entities = self._extract_with_patterns(headline)
            
            headline_words = headline.split()
            total_words = len(headline_words)
            
            for entity, position in entities:
                # 1. STRICT: Validate company/organization name format
                if not self._is_valid_company_name(entity):
                    continue
                
                # 2. FINAL VALIDATION: Gemini (Context-aware check)
                if not self._validate_with_gemini(entity, headline):
                    continue
                
                # 3. Calculate involvement score
                involvement = self._calculate_involvement_score(
                    entity, headline, position, total_words
                )
                
                # Only count if involvement > threshold (main actor)
                # Lowered to 0.2 (20%) to capture more entities in smaller datasets
                if involvement >= 0.2:
                    entity_data[entity]['mentions'] += 1
                    entity_data[entity]['involvement_scores'].append(involvement)
                    entity_data[entity]['headlines'].append(headline)
                    entity_data[entity]['sources'].add(source)
        
        # Calculate article count
        for entity in entity_data:
            entity_data[entity]['article_count'] = len(entity_data[entity]['headlines'])
        
        return dict(entity_data)
    
    def _extract_with_transformers(self, text: str) -> List[Tuple[str, int]]:
        """Extract ORG entities using transformers NER"""
        try:
            results = self.ner(text)
            entities = []
            
            for item in results:
                # STRICT: Only ORG entities
                if item['entity_group'] == 'ORG':
                    entity_text = item['word'].strip()
                    # Estimate position
                    position = len(text[:item['start']].split())
                    entities.append((entity_text, position))
            
            return entities
        except:
            return self._extract_with_patterns(text)
    
    def _extract_with_patterns(self, text: str) -> List[Tuple[str, int]]:
        """Fallback: Pattern-based extraction"""
        entities = []
        words = text.split()
        
        i = 0
        while i < len(words):
            # Look for capitalized sequences (2-4 words)
            if words[i][0].isupper():
                entity_words = [words[i]]
                j = i + 1
                
                while j < len(words) and j < i + 4:
                    if words[j][0].isupper() or words[j].lower() in self.company_suffixes:
                        entity_words.append(words[j])
                        j += 1
                    else:
                        break
                
                if len(entity_words) >= 1:
                    entity = ' '.join(entity_words)
                    entities.append((entity, i))
                    i = j
                else:
                    i += 1
            else:
                i += 1
        
        return entities
    def rank_by_dominance(self, data: Dict, total_articles: int) -> List[Dict]:
        """
        Rank entities by DOMINANCE, not just frequency
        """
        ranked = []
        
        for name, d in data.items():
            mentions = d['mentions']
            # Support both structure names (in case of legacy data)
            article_count = d.get('article_count', len(d.get('articles', [])))
            sources = len(d['sources'])
            involvement_scores = d.get('involvement_scores', d.get('involvement', []))
            
            # NOISE REMOVAL: Minimum thresholds
            min_mentions = 1 if total_articles < 10 else 2
            if mentions < min_mentions:
                continue
            
            coverage_ratio = article_count / max(total_articles, 1)
            min_coverage = 0.003 if total_articles < 100 else 0.005
            if coverage_ratio < min_coverage:
                continue
            
            # DOMINANCE SCORE CALCULATION
            coverage_score = min(coverage_ratio * 100, 30)
            
            avg_involvement = 0
            if involvement_scores:
                avg_involvement = sum(involvement_scores) / len(involvement_scores)
            involvement_score = avg_involvement * 40
            
            diversity_score = min(sources / 10, 1.0) * 20
            
            consistency = mentions / max(article_count, 1)
            consistency_score = min(consistency / 3, 1.0) * 10
            
            dominance_score = coverage_score + involvement_score + diversity_score + consistency_score
            
            ranked.append({
                'name': name,
                'mentions': mentions,
                'articles': article_count,
                'coverage_pct': round(coverage_ratio * 100, 2),
                'avg_involvement': round(avg_involvement * 100, 1),
                'sources': sources,
                'dominance_score': round(dominance_score, 2),
                'entity_type': 'company'
            })
        
        ranked.sort(key=lambda x: x['dominance_score'], reverse=True)
        
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
        
        return ranked

def extract_top_companies(articles: List[Dict], query: str, top_n: int = 10) -> List[Dict]:
    """
    Main function: Extract top trending companies/organizations
    """
    if not articles:
        return []
    
    extractor = AdvancedNERExtractor()
    
    # Step 1: Extract entities with NER (and Gemini validation)
    entity_data = extractor.extract_entities_ner(articles)
    
    # Step 2: Rank by dominance
    ranked = extractor.rank_by_dominance(entity_data, len(articles))
    
    # Step 3: Return top N
    return ranked[:top_n]
