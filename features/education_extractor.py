"""
features/education_extractor.py

Nuclear Edition: Aggressively hunts for CGPA, GPA, CPI, SPI, Grades, Scores, 
Marks, Percentages, and complex fractions across the entire global scope of the resume.
"""

import re

def _normalize_spaced_numbers(text):
    """
    Collapse OCR-spaced digit sequences produced by stylized PDF fonts.
    """
    text = re.sub(r'(\d)\s*[.]\s*(\d)', r'\1.\2', text)
    text = re.sub(r'(\d[.]\d)\s+(\d)', r'\1\2', text)
    return text

def extract_education(sections):
    # LOCAL SCOPE: Only lines safely classified as Education or General
    edu_lines = sections.get("education", {}).get("lines", [])
    gen_lines = sections.get("general", {}).get("lines", [])
    local_lines = edu_lines + gen_lines
    
    # GLOBAL SCOPE: Every single line in the resume (Bypasses segmenter failures)
    global_lines = []
    for sec in sections.values():
        global_lines.extend(sec.get("lines", []))
        
    local_text = " ".join([_normalize_spaced_numbers(l) for l in local_lines]).lower()
    global_text = " ".join([_normalize_spaced_numbers(l) for l in global_lines]).lower()

    # ------------------------------------------------------------------
    # 1. Degree Detection (Aggressively Greedy)
    # ------------------------------------------------------------------
    degree_patterns = [
        r"\bb[.]?\s*tech\b", r"\bb[.]?\s*e\b",                 # B.Tech, BTech, B Tech, B.E
        r"\bb[.]?\s*s[.]?\s*c\b", r"\bb[.]?\s*s\b",            # B.Sc, BSc, B.S.c
        r"\bbachelor", r"\bbachelors\b", r"\bundergrad\b",     # Bachelor, Bachelors
        r"\bm[.]?\s*tech\b", r"\bm[.]?\s*s\b",                 # M.Tech, M.S
        r"\bmaster", r"\bmasters\b", r"\bpostgrad\b",          # Master, Masters
        r"\bmba\b", r"\bmca\b", r"\bbca\b", r"\bbba\b",        # MBA, MCA, BCA, BBA
        r"\bphd\b", r"\bdoctorate\b", r"\bdoctor of\b",        # PhD
        r"\bb[.]?\s*com\b", r"\bm[.]?\s*com\b",                # B.Com, M.Com
        r"\bb[.]?\s*a\b", r"\bm[.]?\s*a\b",                    # B.A, M.A
        r"\bdiploma\b", r"\bpgdm\b", r"\bpgdca\b",             # Diplomas
        r"\bengineering\b", r"\bgraduated\b"                   # Fallbacks
    ]
    degree_detected = any(re.search(p, global_text) for p in degree_patterns)

    # ------------------------------------------------------------------
    # 2. Score Extraction (Nuclear Mode)
    # ------------------------------------------------------------------
    normalized_score = 0.0

    # Strategy A: Fraction (Catches 8.5/10, 8.5 / 10.00, 3.8/4.0)
    fraction_matches = re.findall(
        r'\b(\d{1,2}(?:[.]\d{1,2})?)\s*/\s*(10(?:[.]0+)?|4(?:[.]0+)?)\b',
        global_text
    )
    if fraction_matches:
        best = 0.0
        for val, scale in fraction_matches:
            v, s = float(val), float(scale)
            best = max(best, (v / 4.0) * 100.0 if s <= 4.0 else v * 10.0)
        normalized_score = best

    # Strategy B: Reverse Grade (Catches "7.96 CGPA", "8.5 CPI", "85 Aggregate")
    if normalized_score == 0:
        rev = re.findall(r'\b(100(?:[.]0+)?|\d{1,2}(?:[.]\d{1,2})?)\s*(?:cgpa|gpa|cpi|spi|aggregate)\b', global_text)
        if rev:
            val = max(float(m) for m in rev)
            # If they wrote "85 Aggregate", handle it like a percentage
            if val > 10.0:
                normalized_score = val
            else:
                normalized_score = (val / 4.0) * 100.0 if val <= 4.0 else val * 10.0

    # Strategy C: Forward Grade (Catches "CGPA: 7.96", "Score - 85", "Grade: 8")
    if normalized_score == 0:
        fwd = re.findall(
            r'\b(?:cgpa|gpa|cpi|spi|score|grade|marks|aggregate)\s*(?:of|is)?\s*[:\-=]?\s*(100(?:[.]0+)?|\d{1,2}(?:[.]\d{1,2})?)\b',
            global_text
        )
        if fwd:
            val = max(float(m) for m in fwd)
            if val > 10.0:
                normalized_score = val
            else:
                normalized_score = (val / 4.0) * 100.0 if val <= 4.0 else val * 10.0

    # Strategy D: Explicit Percentage with symbol (85%, 100.0%)
    if normalized_score == 0:
        pct = re.findall(r'\b(100(?:[.]0+)?|[4-9]\d(?:[.]\d{1,2})?)\s*(?:%|percent)\b', global_text)
        if pct:
            normalized_score = max(float(m) for m in pct)

    # Strategy E: Orphaned Table Fallback (Catches numbers sitting naked in tables)
    if normalized_score == 0:
        # Check if the resume contains ANY academic grading word anywhere
        if re.search(r'\b(?:cgpa|gpa|cpi|spi|percentage|score|grade|marks)\b', global_text):
            # Look for 10-point scale numbers (4.0 to 10.0)
            cgpa_standalone = re.findall(r'\b([4-9][.]\d{1,2}|10(?:[.]0+)?)\b', global_text)
            if cgpa_standalone:
                val = max(float(m) for m in cgpa_standalone)
                normalized_score = (val / 4.0) * 100.0 if val <= 4.0 else val * 10.0
            
            # Look for percentage-scale numbers (40.0 to 100.0) in local text only to avoid project metrics
            if normalized_score == 0:
                pct_standalone = re.findall(r'\b(100(?:[.]0+)?|[4-9]\d(?:[.]\d{1,2})?)\b', local_text)
                if pct_standalone:
                    # Filter out years (1900-2035) to prevent "2024" being scored as 100%
                    valid_pcts = [float(m) for m in pct_standalone if not (1900 <= float(m) <= 2035)]
                    if valid_pcts:
                        normalized_score = max(valid_pcts)

    normalized_score = min(normalized_score, 100.0)

    # Dynamic flag: If we found a valid score, they inherently have education
    has_edu = True if (degree_detected or normalized_score > 0) else False

    return {
        "has_education":        has_edu,
        "normalized_score_100": round(normalized_score, 2),
        "degree_detected":      degree_detected,
    }