"""
NER-based Entity Extraction for News Intelligence
Uses spaCy's pre-trained NER models to identify organizations, companies, and brands
"""

import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

# Try to import spaCy, fallback to pattern-based if not available
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        # If model not found, we'll download it later
        nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None


class NEREntityExtractor:
    """
    Advanced NER-based entity extractor for identifying trending agencies/brands
    """
    
    def __init__(self):
        self.nlp = nlp
        self.entity_cache = {}
        
        # Common noise words to filter out
        self.noise_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'what', 'which', 'who', 'when', 'where', 'why',
            'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 'just', 'now', 'new', 'first', 'last', 'long',
            'great', 'little', 'old', 'right', 'big', 'high', 'different', 'small',
            'large', 'next', 'early', 'young', 'important', 'public', 'bad',
            'india', 'indian', 'us', 'uk', 'china', 'america', 'american', 'says',
            'said', 'according', 'report', 'reports', 'news', 'today', 'yesterday',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        }
        
        # Generic terms that are not specific brands/agencies
        self.generic_terms = {
            'government', 'police', 'court', 'hospital', 'university', 'school',
            'company', 'corporation', 'industry', 'market', 'sector', 'department',
            'ministry', 'office', 'bureau', 'agency', 'organization', 'association',
            'committee', 'council', 'board', 'commission', 'authority', 'service',
            'center', 'institute', 'foundation', 'trust', 'group', 'team'
        }
    
    def _is_valid_entity(self, entity_text: str) -> bool:
        """Check if entity is valid (not noise or generic term)"""
        entity_lower = entity_text.lower().strip()
        
        # Filter out single characters and very short strings
        if len(entity_text) < 2:
            return False
        
        # Filter out noise words
        if entity_lower in self.noise_words:
            return False
        
        # Filter out purely generic terms (unless part of a longer name)
        words = entity_lower.split()
        if len(words) == 1 and entity_lower in self.generic_terms:
            return False
        
        # Filter out entities that are just numbers or dates
        if re.match(r'^[\d\s\-\/]+$', entity_text):
            return False
        
        return True
    
    def _normalize_entity(self, entity_text: str) -> str:
        """Normalize entity name for deduplication"""
        # Remove common suffixes
        normalized = entity_text.strip()
        suffixes = [' Inc', ' Inc.', ' Corp', ' Corp.', ' Ltd', ' Ltd.', 
                   ' LLC', ' Co', ' Co.', ' Group', ' Holdings']
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        return normalized
    
    def extract_entities_spacy(self, articles: List[Dict]) -> List[Tuple[str, int, str]]:
        """Extract entities using spaCy NER"""
        if not self.nlp:
            return []
        
        entity_counts = Counter()
        entity_types = {}
        entity_contexts = defaultdict(list)
        
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            full_text = article.get('full_text', '')
            
            # Combine all text, prioritizing title
            text = f"{title}. {description}. {full_text[:500]}"
            
            if not text.strip():
                continue
            
            # Process with spaCy
            doc = self.nlp(text[:5000])  # Limit to avoid memory issues
            
            for ent in doc.ents:
                # Focus on ORG (organizations) and PRODUCT entities
                if ent.label_ in ['ORG', 'PRODUCT', 'GPE']:
                    entity_text = ent.text.strip()
                    
                    if not self._is_valid_entity(entity_text):
                        continue
                    
                    # Normalize for counting
                    normalized = self._normalize_entity(entity_text)
                    
                    # Weight entities in title higher
                    weight = 3 if entity_text in title else 1
                    entity_counts[normalized] += weight
                    
                    # Store entity type
                    if normalized not in entity_types:
                        entity_types[normalized] = ent.label_
                    
                    # Store context
                    entity_contexts[normalized].append(title if entity_text in title else description)
        
        # Convert to list with type information
        entities_with_types = [
            (entity, count, entity_types.get(entity, 'ORG'))
            for entity, count in entity_counts.items()
        ]
        
        return entities_with_types
    
    def extract_entities_pattern(self, articles: List[Dict]) -> List[Tuple[str, int, str]]:
        """Fallback pattern-based extraction if spaCy not available"""
        entity_counts = Counter()
        
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            
            text = f"{title}. {description}"
            
            # Pattern: Capitalized words (likely proper nouns)
            pattern = r'\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\b'
            matches = re.findall(pattern, text)
            
            for match in matches:
                if self._is_valid_entity(match):
                    normalized = self._normalize_entity(match)
                    weight = 3 if match in title else 1
                    entity_counts[normalized] += weight
        
        # Return as tuples with default type
        return [(entity, count, 'company') for entity, count in entity_counts.items()]
    
    def rank_entities(self, entities_with_counts: List[Tuple[str, int, str]], 
                     total_articles: int, min_mentions: int = 3) -> List[Dict]:
        """
        Rank entities by relevance score
        
        Args:
            entities_with_counts: List of (entity_name, count, type) tuples
            total_articles: Total number of articles analyzed
            min_mentions: Minimum mentions to be considered
        
        Returns:
            List of ranked entity dictionaries
        """
        ranked = []
        
        for entity, count, entity_type in entities_with_counts:
            # Filter by minimum mentions
            if count < min_mentions:
                continue
            
            # Calculate metrics
            percentage = (count / total_articles) * 100
            
            # Confidence score based on frequency and consistency
            confidence = min(95, (count / max(total_articles * 0.1, 1)) * 100)
            
            # Determine entity category
            entity_lower = entity.lower()
            if any(word in entity_lower for word in ['ministry', 'department', 'government', 'bureau']):
                category = 'government_agency'
            elif any(word in entity_lower for word in ['university', 'institute', 'research', 'lab']):
                category = 'research_org'
            else:
                category = 'company'
            
            ranked.append({
                'name': entity,
                'mentions': count,
                'percentage': round(percentage, 2),
                'confidence': round(confidence, 1),
                'entity_type': category,
                'ner_label': entity_type
            })
        
        # Sort by mentions (descending)
        ranked.sort(key=lambda x: x['mentions'], reverse=True)
        
        return ranked


def extract_trending_agencies(articles: List[Dict], query: str, 
                              min_mentions: int = 3, top_n: int = 10) -> List[Dict]:
    """
    Main function to extract trending agencies/brands from articles
    
    Args:
        articles: List of article dictionaries
        query: Search query (for context)
        min_mentions: Minimum mentions to be included
        top_n: Number of top entities to return
    
    Returns:
        List of top N trending agencies/brands
    """
    if not articles:
        return []
    
    extractor = NEREntityExtractor()
    
    # Try spaCy first, fallback to pattern-based
    if extractor.nlp:
        entities_with_counts = extractor.extract_entities_spacy(articles)
    else:
        entities_with_counts = extractor.extract_entities_pattern(articles)
    
    # Rank entities
    ranked_entities = extractor.rank_entities(
        entities_with_counts, 
        len(articles), 
        min_mentions
    )
    
    # Add rank numbers
    for i, entity in enumerate(ranked_entities[:top_n], 1):
        entity['rank'] = i
    
    return ranked_entities[:top_n]


# Convenience function for backward compatibility
def extract_top_agencies_ner(articles: List[Dict], query: str, 
                             min_mentions: int = 3) -> List[Dict]:
    """Wrapper function matching the existing interface"""
    return extract_trending_agencies(articles, query, min_mentions, top_n=10)
