import re


def extract_education(sections):

    edu_lines = sections.get("education", {}).get("lines", [])

    if not edu_lines:
        return {
            "has_education": False,
            "normalized_score_100": 0.0,
            "degree_detected": False
        }

    full_text = " ".join(edu_lines).lower()

    # -----------------------------
    # 1. Degree Detection (robust)
    # -----------------------------
    degree_patterns = [
        r"\bb\.?tech\b", r"\bb\.?e\b",
        r"\bb\.?sc\b", r"\bb\.?s\b",
        r"\bbachelor",
        r"\bm\.?tech\b", r"\bm\.?s\b",
        r"\bmaster", r"\bmba\b",
        r"\bphd\b", r"\bdoctorate\b"
    ]

    degree_detected = any(
        re.search(p, full_text) for p in degree_patterns
    )

    # -----------------------------
    # 2. CGPA / Percentage extraction
    # -----------------------------
    normalized_score = 0.0

    # Strategy A: Fraction formats (8.5/10, 3.7/4)
    fraction_matches = re.findall(
        r'\b(\d{1,2}(?:\.\d{1,2})?)\s*/\s*(10|4(?:\.0)?)\b',
        full_text
    )

    if fraction_matches:
        best_score = 0.0

        for val, scale in fraction_matches:
            val_f = float(val)
            scale_f = float(scale)

            if scale_f == 10:
                best_score = max(best_score, val_f * 10)

            elif scale_f == 4:
                best_score = max(best_score, (val_f / 4.0) * 100)

        normalized_score = best_score

    # Strategy B: Percent
    if normalized_score == 0:
        pct_matches = re.findall(
            r'\b([4-9]\d(?:\.\d{1,2})?)\s*(?:%|percent)\b',
            full_text
        )
        if pct_matches:
            normalized_score = max(float(m) for m in pct_matches)

    # Strategy C: GPA / CGPA
    if normalized_score == 0:
        gpa_matches = re.findall(
            r'(?:cgpa|gpa)[\s:=]*([0-9]\.\d{1,2}|10(?:\.0)?)\b',
            full_text
        )

        if gpa_matches:
            val_f = max(float(m) for m in gpa_matches)

            # heuristic: assume 4 scale if <= 4
            if val_f <= 4:
                normalized_score = (val_f / 4.0) * 100
            else:
                normalized_score = val_f * 10

    normalized_score = min(normalized_score, 100.0)

    return {
        "has_education": True,
        "normalized_score_100": round(normalized_score, 2),
        "degree_detected": degree_detected
    }