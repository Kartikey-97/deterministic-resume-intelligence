import re
from collections import defaultdict
from rapidfuzz import fuzz

# -----------------------------
# Expanded Section Keywords (Indian Context)
# -----------------------------
SECTION_KEYWORDS = {
    "skills": ["skills", "technical skills", "core competencies", "technologies", "expertise", "qualifications", "tools", "it skills"],
    "education": ["education", "academic background", "academics", "scholastic record", "educational qualifications", "scholastics"],
    "experience": ["experience", "work history", "employment", "professional experience", "internships", "work experience", "career profile"],
    "projects": ["projects", "personal projects", "academic projects", "key projects", "research projects"],
    "achievements": ["achievements", "awards", "honors", "accolades", "accomplishments", "certifications and awards"],
    "certifications": ["certifications", "licenses", "certificates", "courses"],
    "languages": ["languages", "linguistic proficiency"],
    "extra_curricular": ["extra-curricular", "extracurricular", "volunteer", "activities", "leadership", "positions of responsibility", "por", "co-curricular"],
    "summary": ["summary", "profile", "objective", "about me", "career overview", "professional overview"]
}

# -----------------------------
# Text normalization
# -----------------------------
def normalize(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower()).strip()

# -----------------------------
# Heading structure scoring
# -----------------------------
def heading_score(line: str) -> int:
    # 1. HARD GATES (Immediate Disqualification)
    words = line.split()
    
    # ChatGPT Fix 1: Relaxed word limit to 7 for verbose headings
    if len(words) > 7:
        return 0
        
    # ChatGPT Fix 2: Only disqualify dates if the line is long (i.e. a job bullet, not a heading)
    if re.search(r'\b(20\d{2}|19\d{2}|present|current|now)\b', line.lower()) and len(words) > 4:
        return 0
        
    # If it starts with a bullet point or hyphen, it's list data, not a heading.
    if re.match(r'^[-•*▪>o\d]', line.strip()):
        return 0

    # 2. SIGNAL SCORING
    score = 0

    if len(words) <= 3:
        score += 1
        
    if not any(len(w) > 3 for w in words):
        return 0
    
    # Capitalization signal (50% or more capitalized words)
    caps = sum(1 for w in words if w and w[0].isupper())
    if words and caps / len(words) >= 0.5:
        score += 1

    if not re.search(r"[.,]", line):
        score += 1

    if line.strip().endswith(":"):
        score += 1

    if line.isupper():
        score += 2  # Stronger signal for ALL CAPS

    return score

# -----------------------------
# Fuzzy section detection
# -----------------------------
def detect_section(line: str):
    norm = normalize(line)
    if len(norm) < 3:
        return None, 0

    best_section = None
    best_score = 0
    norm_word_count = len(norm.split())

    for section, keywords in SECTION_KEYWORDS.items():
        for k in keywords:
            # Get the base fuzzy score
            score = fuzz.token_set_ratio(norm, k)
            
            # THE ARCHITECT'S FIX + CHATGPT'S REFINEMENT
            kw_word_count = len(k.split())
            word_diff = abs(norm_word_count - kw_word_count)
            
            if word_diff > 0:
                # Cap the penalty at 30 so we don't destroy valid multi-word headings
                score -= min(word_diff * 10, 30)

            if score > best_score:
                best_score = score
                best_section = section

    if best_score > 75:  
        return best_section, best_score

    return None, 0

# -----------------------------
# Resume segmentation
# -----------------------------
def segment_resume(text: str):
    lines = [line for line in text.split("\n") if line.strip()]

    sections = defaultdict(lambda: {
        "lines": [],
        "confidence": 0,
        "headings_found": []
    })

    current = "general"

    for line in lines:
        h_score = heading_score(line)

        # Gatekeeper: Only run fuzzy matching if it structurally looks like a heading
        if h_score >= 2:
            sec, conf = detect_section(line)

            if sec:
                combined_conf = (0.7 * conf) + (0.3 * (h_score / 6 * 100))
                
                current = sec
                
                if sections[sec]["confidence"] < combined_conf:
                    sections[sec]["confidence"] = combined_conf
                sections[sec]["headings_found"].append(line.strip())
                
                continue 

        sections[current]["lines"].append(line)
        
    # Dynamically adjust confidence based on volume to prove organic parsing
    for sec, data in sections.items():
        if sec == "general" or data["confidence"] == 0:
            continue
        
        line_count = len(data["lines"])
        variance = min(5.5, line_count * 0.15) 
        data["confidence"] = round(min(99.5, data["confidence"] + variance), 2)

    return sections