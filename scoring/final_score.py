from scoring.internship_score import score_internships
from scoring.experience_score import score_experience
from scoring.skill_score import score_skills
from scoring.project_score import score_projects
from scoring.education_score import score_education
from scoring.achievement_score import score_achievements
from scoring.extracurricular_score import score_extracurricular
from scoring.minor_score import score_minor


def is_fresher(exp_features):
    """Standard Indian HR boundary: 0-2 years = Fresher/Junior."""
    return exp_features["total_experience_years"] < 2.0


def completeness_score(features):
    """
    Returns 0-4. One point per genuinely-present profile signal.

    BUG FIX: Original code used `len(projs) > 0` which is ALWAYS True because
    extract_projects always returns a dict with 6 keys. Same for achievements.
    The fix checks the semantic boolean flags instead.
    """
    score = 0

    # 1. Projects: candidate must have real projects detected
    if features.get("projects", {}).get("has_projects", False):
        score += 1

    # 2. Achievements: candidate must have real achievements detected
    if features.get("achievements", {}).get("has_achievements", False):
        score += 1

    # 3. Online presence: LinkedIn, GitHub, Portfolio links
    if len(features.get("minor", {}).get("online_presence", [])) > 0:
        score += 1

    # 4. Languages: any spoken/written languages detected
    if len(features.get("minor", {}).get("languages_detected", [])) > 0:
        score += 1

    return score


def prestige_multiplier(features):
    """
    Adds up to 13% bonus for elite college/company tiers.
    Capped to prevent a weak IIT candidate from beating a strong non-IIT.
    """
    multiplier = 1.0
    company_tier = features.get("minor", {}).get("company_tier", 4)
    college_tier = features.get("minor", {}).get("college_tier", 4)
    if company_tier == 1:   multiplier += 0.08
    elif company_tier == 2: multiplier += 0.04
    if college_tier == 1:   multiplier += 0.05
    elif college_tier == 2: multiplier += 0.02
    return multiplier


# The raw maximum each scorer can return.
# Import this into any file that uses raw scores to avoid silent breakage
# if a scorer's output range changes.
DEFAULT_MAX = {
    "internships":    20.0,  # score_internships() max
    "experience":      5.0,  # score_experience() max
    "skills":         20.0,  # score_skills() max
    "projects":       15.0,  # score_projects() max
    "cgpa_score":     10.0,  # score_education()["cgpa_score"] max
    "achievements":   10.0,  # score_achievements() max
    "extracurricular": 5.0,  # score_extracurricular() max
    "degree_score":    3.0,  # score_education()["degree_score"] max
    "language":        3.0,  # score_minor()["language"] max
    "online":          3.0,  # score_minor()["online"] max
    "college":         3.0,  # score_minor()["college"] max
    "school":          3.0,  # score_minor()["school"] max
}


def compute_final_score(features, custom_weights=None):
    """
    Master scoring orchestrator.

    Flow:
      1. Collect raw scores from each domain scorer.
      2. Determine fresher vs experienced status.
      3. Apply dynamic weight redistribution for experienced candidates.
      4. Normalize each raw score to [0, 1] and multiply by its weight.
      5. Apply completeness bonus (+4% per completeness point, max +16%).
      6. Apply prestige multiplier (up to +13% for elite college/company).
      7. Clamp to [0, 100].
    """
    breakdown = {}
    fresher   = is_fresher(features["experience"])

    # ── Step 1: Collect raw scores ─────────────────────────────────────────
    raw = {}
    raw["internships"]    = score_internships(features["experience"])
    raw["experience"]     = score_experience(features["experience"])
    raw["skills"]         = score_skills(features["skills"])
    raw["projects"]       = score_projects(features["projects"])

    edu                   = score_education(features["education"])
    raw["cgpa_score"]     = edu["cgpa_score"]
    raw["degree_score"]   = edu["degree_score"]

    raw["achievements"]   = score_achievements(features["achievements"])
    raw["extracurricular"]= score_extracurricular(features["extracurricular"])

    minor                 = score_minor(features.get("minor", {}), features.get("school", {}))
    raw["language"]       = minor.get("language", 0)
    raw["online"]         = minor.get("online", 0)
    raw["college"]        = minor.get("college", 0)
    raw["school"]         = minor.get("school", 0)

    # ── Step 2: Set up weight baseline ────────────────────────────────────
    weights = custom_weights.copy() if custom_weights else DEFAULT_MAX.copy()

    # ── Step 3: Dynamic weight redistribution for experienced candidates ───
    # When a candidate has 2+ years FT experience, internship/extracurricular/
    # school weights become irrelevant. Redistribute them into the signals
    # that actually matter for experienced hiring.
    if not fresher:
        weights["experience"]  += weights.get("internships", 20.0)
        weights["internships"]  = 0.0

        extra_pool = weights.get("extracurricular", 5.0) + weights.get("school", 3.0)
        weights["skills"]        += extra_pool * 0.6
        weights["achievements"]  += extra_pool * 0.4
        weights["extracurricular"] = 0.0
        weights["school"]          = 0.0

    # ── Step 4: Normalize + weight ────────────────────────────────────────
    for key in raw:
        dmax = DEFAULT_MAX.get(key, 1)
        if dmax > 0:
            pct_earned    = raw[key] / dmax
            breakdown[key] = pct_earned * weights.get(key, 0)
        else:
            breakdown[key] = 0

    # ── Step 5: Completeness bonus (up to +16%) ────────────────────────────
    comp      = completeness_score(features)
    raw_total = sum(breakdown.values())
    total     = raw_total * (1 + 0.04 * comp)

    # ── Step 6: Prestige multiplier (up to +13%) ──────────────────────────
    total *= prestige_multiplier(features)

    # ── Step 7: Clamp ─────────────────────────────────────────────────────
    final_score = max(0.0, min(total, 100.0))

    return {
        "total_score": round(final_score, 2),
        "raw_total":   round(raw_total, 2),
        "breakdown":   {k: round(v, 2) for k, v in breakdown.items()
                        if isinstance(v, (int, float))},
        "fresher":     fresher,
        "completeness": comp,
    }