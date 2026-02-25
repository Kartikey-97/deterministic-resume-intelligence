import re

ADVANCED_KEYWORDS = [
    "machine learning", "deep learning", "nlp", "llm",
    "cloud", "microservices", "distributed", "pipeline",
    "docker", "kubernetes", "aws", "gcp", "azure", "scalable",
    "big data", "optimization", "ci/cd", "api"
]

IMPACT_KEYWORDS = [
    "improved", "increased", "reduced", "decreased",
    "optimized", "accuracy", "performance", "efficiency",
    "achieved", "spearheaded", "automated", "resolved"
]

def get_project_count(lines):
    """
    Safely estimate the number of projects without grouping text.
    Looks for short, highly capitalized lines that DO NOT start with bullets.
    """
    count = 0
    for line in lines:
        line = line.strip()
        # 1. Ignore bullets and dates
        if re.match(r'^[-•*▪>]', line) or re.search(r'(20\d{2}|19\d{2})', line):
            continue
            
        words = line.split()
        if not words:
            continue
            
        # 2. Heuristic: Titles are usually short (1 to 8 words) and mostly Title Case
        capital_ratio = sum(1 for w in words if w and w[0].isupper()) / len(words)
        if 1 <= len(words) <= 8 and capital_ratio >= 0.5:
            count += 1
            
    # If we couldn't find explicit titles but text exists, assume it's 1 big project block
    if count == 0 and len(lines) > 0:
        return 1
        
    return count


def extract_projects(sections):
    project_lines = sections.get("projects", {}).get("lines", [])

    # NO FALLBACK TO EXPERIENCE. If they didn't list projects, they get 0. 
    # They will earn their points in the Experience section instead.

    if not project_lines:
        return {
            "has_projects": False,
            "project_count": 0,
            "word_count": 0,
            "advanced_keyword_count": 0,
            "impact_score": 0,
            "has_urls": False
        }

    full_text = " ".join(project_lines).lower()

    # 1. Estimate project count safely
    project_count = get_project_count(project_lines)

    # 2. Advanced tech detection (using word boundaries \b)
    advanced_found = sum(1 for k in ADVANCED_KEYWORDS if re.search(r"\b" + re.escape(k) + r"\b", full_text))

    # 3. Impact scoring
    impact_score = sum(1 for k in IMPACT_KEYWORDS if k in full_text)
    
    # Quantifiable metrics (numbers + %, x, k, m, or large numbers)
    quantifiable_matches = re.findall(r'\b(\d+(?:\.\d+)?(?:%|x|k|m)|\d{3,})\b', full_text)
    impact_score += len(quantifiable_matches) * 2

    # Cap gaming (Maximum 10 impact points allowed)
    impact_score = min(impact_score, 10)

    # 4. URL presence
    has_urls = bool(re.search(r'(github\.com|gitlab\.com|bitbucket|portfolio|vercel|netlify|http)', full_text))

    return {
        "has_projects": True,
        "project_count": project_count,
        "word_count": len(full_text.split()),
        "advanced_keyword_count": advanced_found,
        "impact_score": impact_score,
        "has_urls": has_urls
    }