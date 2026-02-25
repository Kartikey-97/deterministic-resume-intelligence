import re
from features.tier_taxonomy import COMPANY_TIERS, COLLEGE_TIERS


def normalize_text(text):
    """Lowercase and remove punctuation for robust matching."""
    text = text.lower()
    return re.sub(r'[^a-z0-9\s]', ' ', text)


def get_best_tier(text, taxonomy_dict):
    """
    Returns best tier found and matched keyword.
    Tier 1 is best. Tier 4 is default.
    """
    text = normalize_text(text)

    # Always search best tiers first
    for tier in ["tier_1", "tier_2", "tier_3"]:
        for kw in taxonomy_dict.get(tier, []):
            kw_norm = normalize_text(kw)
            if re.search(r"\b" + re.escape(kw_norm) + r"\b", text):
                return int(tier.split("_")[1]), kw

    return 4, None


def extract_minor_features(sections, raw_text):

    results = {}

    # -----------------------------
    # College Tier Detection
    # -----------------------------
    edu_text = " ".join(
        sections.get("education", {}).get("lines", [])
    )

    college_tier, matched_college = get_best_tier(edu_text, COLLEGE_TIERS)

    results["college_tier"] = college_tier
    results["college_matched"] = matched_college

    # -----------------------------
    # Company Tier Detection
    # -----------------------------
    exp_text = " ".join(
        sections.get("experience", {}).get("lines", [])
    )

    company_tier, matched_company = get_best_tier(exp_text, COMPANY_TIERS)

    results["company_tier"] = company_tier
    results["company_matched"] = matched_company

    # -----------------------------
    # Language Detection
    # -----------------------------
    lang_text = " ".join(
        sections.get("languages", {}).get("lines", [])
    ).lower()

    known_languages = ["english", "hindi", "spanish", "german", "french"]

    detected_langs = [
        l for l in known_languages if l in lang_text
    ]

    results["languages_detected"] = detected_langs

    # -----------------------------
    # Online Presence
    # -----------------------------
    online_signals = []

    if re.search(r"github\.com", raw_text.lower()):
        online_signals.append("github")

    if re.search(r"linkedin\.com", raw_text.lower()):
        online_signals.append("linkedin")

    if re.search(r"portfolio|vercel|netlify", raw_text.lower()):
        online_signals.append("portfolio")

    results["online_presence"] = online_signals

    return results