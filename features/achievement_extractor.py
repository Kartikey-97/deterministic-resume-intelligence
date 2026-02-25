import re

IMPACT_KEYWORDS = [
    "won", "rank", "award", "achievement",
    "recognition", "scholarship", "medal",
    "top", "first", "second", "third",
    "dean"
]

def is_year(num):
    """Filter out year-like numbers."""
    return 1900 <= num <= 2035


def extract_achievements(sections):

    # Scan multiple sections for robustness
    ach_lines = []
    for sec in ["achievements", "education", "experience"]:
        ach_lines.extend(sections.get(sec, {}).get("lines", []))

    if not ach_lines:
        return {
            "has_achievements": False,
            "quantified": 0,
            "impact_score": 0
        }

    full_text = " ".join(ach_lines).lower()

    # -----------------------------
    # 1. Impact keyword detection
    # -----------------------------
    keyword_hits = sum(1 for k in IMPACT_KEYWORDS if k in full_text)

    # -----------------------------
    # 2. Quantifiable impact
    # -----------------------------
    # Only count meaningful metrics
    quantifiable_matches = re.findall(
        r"\b\d+(?:\.\d+)?(?:%|x|k|m)\b",
        full_text
    )

    # Filter out suspicious values
    filtered = []
    for m in quantifiable_matches:
        num = float(re.findall(r"\d+(?:\.\d+)?", m)[0])
        if not is_year(num):
            filtered.append(m)

    quantified = len(filtered)

    # -----------------------------
    # 3. Final score
    # -----------------------------
    impact_score = min(keyword_hits + quantified, 10)

    return {
        "has_achievements": True,
        "quantified": quantified,
        "impact_score": impact_score
    }