"""
features/achievement_extractor.py — v2

BUG FIXED: has_achievements was always True.

Original scanned ["achievements", "education", "experience"], so every
candidate with any education/experience text (all 19 of them) returned
has_achievements=True. This gave everyone a free +1 in completeness_score.

Fix:
  1. Only scan the "achievements" section and "certifications" (hackathon wins
     often appear there). Do NOT scan education or experience.
  2. Require at least 1 keyword hit — a section existing but having no
     achievement keywords does not count as an achievement.
"""

import re

IMPACT_KEYWORDS = [
    "won", "winner", "rank", "ranked", "award", "awarded",
    "achievement", "recognition", "recognized",
    "scholarship", "medal", "honor", "honour",
    "top", "first place", "second place", "third place",
    "dean", "distinction", "merit",
    "hackathon", "competition", "contest", "finalist",
    "gold", "silver", "bronze",
    "selected", "shortlisted", "national", "international",
]


def _is_year(num):
    return 1900 <= num <= 2035


def extract_achievements(sections):
    ach_lines  = sections.get("achievements", {}).get("lines", [])
    cert_lines = sections.get("certifications", {}).get("lines", [])
    all_lines  = ach_lines + cert_lines

    if not all_lines:
        return {"has_achievements": False, "quantified": 0, "impact_score": 0}

    full_text = " ".join(all_lines).lower()

    keyword_hits = sum(1 for k in IMPACT_KEYWORDS if k in full_text)

    quant = re.findall(r"\b\d+(?:\.\d+)?(?:%|x|k|m)\b", full_text)
    filtered = [
        m for m in quant
        if not _is_year(float(re.findall(r"\d+(?:\.\d+)?", m)[0]))
    ]
    quantified = len(filtered)

    # Require at least 1 keyword hit — existence of the section is not enough
    has_achievements = keyword_hits > 0
    impact_score     = min(keyword_hits + quantified, 10)

    return {
        "has_achievements": has_achievements,
        "quantified":       quantified,
        "impact_score":     impact_score,
    }