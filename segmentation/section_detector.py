import re
from collections import defaultdict
from rapidfuzz import fuzz

# -----------------------------
# Section keywords
# -----------------------------
SECTION_KEYWORDS = {
    "skills": ["skills", "technical skills", "core competencies","technologies", "expertise", "qualifications"],

    "education": ["education", "academic background", "academics", "scholastic record", "educational qualifications"],

    "experience": ["experience", "work history", "employment", "professional experience", "internships", "work experience"],

    "projects": ["projects", "personal projects", "academic projects", "key projects"],

    "achievements": ["achievements", "awards", "honors", "accolades", "accomplishments"],

    "certifications": ["certifications", "licenses", "certificates"],

    "languages": ["languages"],

    "extra_curricular": ["extra-curricular", "extracurricular", "volunteer", "activities", "leadership"],

    "summary": ["summary", "profile", "objective", "about me", "career overview", "professional overview"]
}

# Priority when conflicts happen
SECTION_PRIORITY = [
    "experience",
    "skills",
    "projects",
    "education",
    "achievements",
    "certifications",
    "languages",
    "extra_curricular",
    "summary"
]


# -----------------------------
# Text normalization
# -----------------------------
def normalize(s: str) -> str:
    return re.sub(r"[^a-z ]", "", s.lower()).strip()


# -----------------------------
# Heading structure scoring
# -----------------------------
def heading_score(line: str) -> int:
    words = line.split()

    # HARD GATE: If it's longer than 6 words, it is absolutely not a heading. 
    # Return 0 immediately.
    if len(words) > 6:
        return 0

    score = 0

    # Short lines get a point
    if len(words) <= 4:
        score += 1
        
    # Must contain at least 1 alphabetic word longer than 3 letters
    if not any(len(w) > 3 for w in words):
        return 0
    
    # Capitalization signal
    caps = sum(1 for w in words if w and w[0].isupper())
    if words and caps / len(words) > 0.6:
        score += 1

    # Low punctuation
    if not re.search(r"[.,]", line):
        score += 1

    # Colon endings common in headings
    if line.strip().endswith(":"):
        score += 1

    # ALL CAPS
    if line.isupper():
        score += 1

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

    for section, keywords in SECTION_KEYWORDS.items():
        for k in keywords:
            score = fuzz.token_set_ratio(norm, k)

            if score > best_score:
                best_score = score
                best_section = section

    if best_score > 80:
        return best_section, best_score

    return None, 0


# can delete this one but keeping it incase 
def merge_broken_lines(lines):
    merged = []
    buffer = ""

    for line in lines:
        if len(line.strip()) < 20:
            buffer += " " + line.strip()
        else:
            if buffer:
                merged.append(buffer.strip())
                buffer = ""
            merged.append(line)

    if buffer:
        merged.append(buffer.strip())

    return merged


# -----------------------------
# Resume segmentation
# -----------------------------
def segment_resume(text: str):
    # Split text and remove completely empty lines
    lines = [line for line in text.split("\n") if line.strip()]

    sections = defaultdict(lambda: {
        "lines": [],
        "confidence": 0,
        "headings_found": [] # Helpful for debugging
    })

    current = "general" # Default bucket for contact info at the top

    for line in lines:
        h_score = heading_score(line)

        # Gatekeeper: Only run fuzzy matching if it looks like a heading
        if h_score >= 2:
            sec, conf = detect_section(line)

            if sec:
                combined_conf = (0.7 * conf) + (0.3 * (h_score / 5 * 100))
                
                # ALWAYS switch to the new section
                current = sec
                
                # Record the highest confidence and the exact heading text
                if sections[sec]["confidence"] < combined_conf:
                    sections[sec]["confidence"] = combined_conf
                sections[sec]["headings_found"].append(line.strip())
                
                continue # Skip appending the heading text to the actual data bucket

        # Append standard text to the currently active bucket
        sections[current]["lines"].append(line)

    return sections