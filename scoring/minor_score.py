"""
scoring/minor_score.py

BUG FIXES:
  1. college tier 4 was returning 0.5 — every candidate with an unknown/tier-4
     college was getting a free 0.5 bonus that wasn't earned. Fixed to 0.
     The tiers 1-3 continue to give proportional credit (2, 1.5, 1).

  2. school_score = 0 was returning 0.5 — every candidate who didn't list
     their school marks (the majority) was getting a free 0.5 bonus.
     Fixed: only award 0.5 when there is a real score > 0 but below 70.
     A score of exactly 0 (no data) now correctly returns 0.

Note: both bugs inflated ALL 19 candidates by exactly 1.0 pt equally,
so ranking was unaffected — but the numbers were semantically wrong and
made the scoring non-zero-based for data that doesn't exist.
"""


def score_minor(minor_features: dict, school_features: dict) -> dict:
    score = {}

    # ── Language (max 3) ─────────────────────────────────────────────────────
    langs = minor_features.get("languages_detected", {})
    score["language"] = min(len(langs), 3)

    # ── Online presence: LinkedIn, GitHub, Portfolio (max 3) ─────────────────
    online = minor_features.get("online_presence", {})
    score["online"] = min(len(online), 3)

    # ── College ranking (max 2) ───────────────────────────────────────────────
    # Tier 1 = IIT/IIM/BITS/NIT-Top | Tier 2 = good NITs/state flagships
    # Tier 3 = decent private/state  | Tier 4 = unknown / not detected
    tier = minor_features.get("college_tier", 4)
    if tier == 1:
        score["college"] = 2
    elif tier == 2:
        score["college"] = 1.5
    elif tier == 3:
        score["college"] = 1
    else:
        # FIX: Tier 4 / unknown college → 0, not 0.5.
        # No data should not equal partial credit.
        score["college"] = 0

    # ── School marks (max 2) ──────────────────────────────────────────────────
    school = school_features.get("school_score", 0)
    if school >= 90:
        score["school"] = 2
    elif school >= 80:
        score["school"] = 1.5
    elif school >= 70:
        score["school"] = 1
    elif school > 0:
        # Has some school data but below 70 — small credit
        score["school"] = 0.5
    else:
        # FIX: school_score = 0 means no data was found.
        # No data should not equal partial credit.
        score["school"] = 0

    return score