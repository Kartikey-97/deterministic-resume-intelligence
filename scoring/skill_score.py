"""
scoring/skill_score.py

BUG FIX — Skill deduplication:
  The original summed len(v) across ALL domains independently.
  Skills like "tensorflow", "pytorch", "pandas", "numpy" appear in BOTH
  the "data" domain AND the "ai_ml" / "aiml" domains in skill_taxonomy.py.
  A candidate with those 4 skills was scored 8 points (4×2 domain hits)
  instead of 4. This inflated scores for ML candidates by up to 10 points.

  Fix: collect all skills into a set() first, then count unique skills.
  Advanced domain detection still works per-domain (a skill counts as
  "advanced" if it appears in any advanced domain).
"""

ADVANCED_DOMAINS = [
    "cloud", "devops", "data", "security",
    "ai_ml", "aiml", "machine_learning", "cybersecurity"
]


def score_skills(skill_features: dict) -> int:
    """
    Returns a score from 0 to 20.

    Formula:
      base  = min(unique_total_skills, 10)   — breadth signal
      bonus = min(advanced_domain_skills, 10) — depth signal
      score = min(base + bonus, 20)

    Both components are capped so that having 30 basic skills doesn't
    beat having 10 basic + 5 advanced skills.

    ── Advanced domain bonus ─────────────────────────────────────────────
    We count skills that appear under any advanced domain.
    We use a set to avoid double-counting (tensorflow in both data + ai_ml
    should count once toward the advanced bonus, not twice).
    """
    # Step 1: Collect all skills, deduplicating across domains
    all_skills     = set()
    advanced_skills = set()

    for domain, skill_dict in skill_features.items():
        if isinstance(skill_dict, dict):
            domain_skills = set(skill_dict.values())
        elif isinstance(skill_dict, list):
            domain_skills = set(skill_dict)
        else:
            continue

        all_skills.update(domain_skills)

        if domain.lower() in ADVANCED_DOMAINS:
            advanced_skills.update(domain_skills)

    # Step 2: Score
    base  = min(len(all_skills),     10)
    bonus = min(len(advanced_skills), 10)
    return min(base + bonus, 20)