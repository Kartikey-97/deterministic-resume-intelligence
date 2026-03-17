import re
from rapidfuzz import fuzz
from features.skill_taxonomy import SKILL_TAXONOMY

def extract_skills(sections):
    detected = {}

    # Collect skills from multiple high-signal sections
    skill_lines = []
    for sec in ["skills", "projects", "experience", "certifications"]:
        skill_lines.extend(sections.get(sec, {}).get("lines", []))

    skill_text = " ".join(skill_lines).lower()
    
    # Tokenize text into words for fast lookup
    tokens = set(skill_text.split())

    for domain, skills in SKILL_TAXONOMY.items():
        domain_skills_found = []

        for skill, variations in skills.items():
            found = False

            # 1. THE EXACT MATCH (Safest & Fastest)
            for v in variations:
                # Use strict word boundaries
                pattern = r"\b" + re.escape(v) + r"\b"
                if re.search(pattern, skill_text):
                    domain_skills_found.append(skill)
                    found = True
                    break

            # 2. THE RESTRICTED FUZZY MATCH
            if not found:
                for v in variations:
                    # RULE 1: Only fuzzy match multi-word skills. 
                    # Single words (like "C" or "Java") should NEVER be fuzzy matched.
                    v_words = v.split()
                    if len(v_words) < 2:
                        continue
                    
                    # RULE 2: At least one critical word from the skill must exist in the text
                    # before we burn CPU cycles on fuzzy math.
                    if not any(word in tokens for word in v_words):
                        continue

                    # RULE 3: Strict token_sort_ratio instead of token_set_ratio. 
                    # Sort_ratio prevents a 10-word sentence from matching a 2-word skill just because they share words.
                    score = fuzz.token_sort_ratio(v, skill_text)

                    # RULE 4: Ultra-high threshold for multi-word phrases
                    if score > 92:
                        domain_skills_found.append(skill)
                        break
        
        # Only add the domain to the JSON if it actually found skills, keeping the JSON tiny and clean
        if domain_skills_found:
            detected[domain] = list(set(domain_skills_found))

    return detected