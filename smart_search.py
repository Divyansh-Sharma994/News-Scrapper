import google.generativeai as genai
import json
import re

# Your API Key
GEMINI_API_KEY = "AIzaSyCqByj1Uuw8O4tGcEWbhS7uuVEVLeG0MOY"
genai.configure(api_key=GEMINI_API_KEY)

def get_sector_via_gemini(query):
    """
    Uses Gemini AI to determine the industry sector of a keyword.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Stricter prompt to ensure mapping to existing categories or descriptive ones
        prompt = f"""
        You are a professional industry analyst. Analyze the following search term: "{query}"
        
        Task: Identify the industry sector for this term.
        
        CRITICAL RULE: The "sector" name MUST NOT be exactly the same as the search term "{query}". 
        Even if the term is a sector name, broaden it (e.g., if query is "Finance", return "Financial Services" or "Banking & Fintech").
        
        Steps:
        1. Categorize it into one of these 8 core sectors if possible:
           - Lifestyle & Consumer
           - Sustainability & Environment
           - Tech, AI & Digital
           - Health & MedTech
           - Finance & Fintech
           - Education & Learning
           - Sports & Entertainment
           - Startups & Venture
        
        2. If it doesn't fit the above, provide a more descriptive 2-3 word industry category.
        
        Output: You MUST respond ONLY with a JSON object:
        {{"sector": "Descriptive Sector Name"}}
        """
        
        response = model.generate_content(prompt)
        res_text = response.text.strip()
        
        # Robust JSON cleaning
        if "```json" in res_text:
            res_text = res_text.split("```json")[-1].split("```")[0].strip()
        elif "```" in res_text:
            res_text = res_text.split("```")[-1].split("```")[0].strip()
        
        # Remove any leading/trailing non-JSON characters just in case
        match = re.search(r'\{.*\}', res_text, re.DOTALL)
        if match:
            res_text = match.group(0)
            
        data = json.loads(res_text)
        return data.get("sector")
    except Exception as e:
        print(f"Smart Search Gemini Error: {e}")
        return None

def expand_query(user_query: str) -> dict:
    """
    Expands user terms with Gemini-powered sector identification.
    Prioritizes Core 8 categories but allows for descriptive specific sectors.
    """
    q = user_query.lower().strip()
    
    # 1. Ask Gemini for the sector
    identified_label = get_sector_via_gemini(user_query)
    
    # 2. Fallback only if Gemini fails
    if not identified_label:
        identified_label = user_query.strip().title()

    # Core 8 Search Query optimization
    search_queries = {
        "Lifestyle": "lifestyle trends OR consumer behavior OR luxury goods news",
        "Sustainability": "sustainability initiatives OR renewable energy news OR circular economy",
        "Tech & AI": "technology sector news OR software companies OR AI startups",
        "Health": "health sector news OR medical advancements OR wellness industry",
        "Finance": "banking sector news OR fintech trends OR stock market",
        "Education": "education technology news OR higher education trends OR edtech",
        "Sports": "sports industry news OR sports business OR athletic brands",
        "Startups": "startup funding news OR venture capital OR entrepreneurial ecosystem"
    }

    # If it's one of our core 8, use the optimized query. 
    # Otherwise, generate a specific search for that identified sector.
    final_query = search_queries.get(identified_label, f"{user_query} {identified_label} news trends")

    return {
        "original": user_query,
        "optimized_query": final_query,
        "context_keywords": ["inc", "corp", "ltd", "group", "holdings"],
        "sector_identified": identified_label
    }
