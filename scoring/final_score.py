from scoring.internship_score import score_internships
from scoring.experience_score import score_experience
from scoring.skill_score import score_skills
from scoring.project_score import score_projects
from scoring.education_score import score_education
from scoring.achievement_score import score_achievements
from scoring.extracurricular_score import score_extracurricular
from scoring.minor_score import score_minor

# -----------------------------
# Helper functions
# -----------------------------
def is_fresher(exp_features):
    return exp_features["total_experience_years"] < 1

def completeness_score(features):
    """Measure profile completeness for calibration."""
    score = 0
    if features.get("projects", {}).get("has_projects"):
        score += 1
    if features.get("achievements", {}).get("has_achievements"):
        score += 1
    if len(features.get("minor", {}).get("online_presence", [])) > 0:
        score += 1
    if len(features.get("minor", {}).get("languages_detected", [])) > 0:
        score += 1
    return score

def prestige_multiplier(features):
    """Boost strong company / college signals."""
    multiplier = 1.0
    company_tier = features.get("minor", {}).get("company_tier", 4)
    college_tier = features.get("minor", {}).get("college_tier", 4)

    if company_tier == 1:
        multiplier += 0.08
    elif company_tier == 2:
        multiplier += 0.04

    if college_tier == 1:
        multiplier += 0.05
    elif college_tier == 2:
        multiplier += 0.02

    return multiplier

# -----------------------------
# Main scoring engine
# -----------------------------
def compute_final_score(features):
    breakdown = {}
    fresher = is_fresher(features["experience"])

    # Core scoring
    breakdown["internships"] = score_internships(features["experience"])
    breakdown["experience"] = score_experience(features["experience"])
    breakdown["skills"] = score_skills(features["skills"])
    breakdown["projects"] = score_projects(features["projects"])

    edu = score_education(features["education"])
    breakdown.update(edu)

    breakdown["achievements"] = score_achievements(features["achievements"])
    breakdown["extracurricular"] = score_extracurricular(features["extracurricular"])

    minor = score_minor(features.get("minor", {}), features.get("school", {}))
    breakdown.update(minor)

    # Fresher vs experienced normalization
    if fresher:
        breakdown["experience"] *= 0.5
        breakdown["projects"] *= 1.2
        breakdown["internships"] *= 1.1

    # Completeness calibration
    raw_total = sum(breakdown.values())
    comp = completeness_score(features)
    raw_total *= (1 + 0.04 * comp)

    # Prestige multiplier
    raw_total *= prestige_multiplier(features)

    # SPARSE MATRIX CALIBRATION (The Curve)
    # A highly competitive candidate realistically maxes out around 75 raw points.
    # SPARSE MATRIX CALIBRATION (The Curve)
    REALISTIC_MAX_RAW = 75.0 
    
    # Dynamic Weight Shifting: If they have experience but no explicit "Projects" section, 
    # we shouldn't penalize them 15 points. We lower the expected curve.
    if breakdown["projects"] == 0 and breakdown["experience"] > 0:
        REALISTIC_MAX_RAW -= 10.0 # Adjust curve expectation down to 65

    curved_score = (raw_total / REALISTIC_MAX_RAW) * 100
    final_score = min(curved_score, 100.0)

    return {
        "total_score": round(final_score, 2),
        "raw_total": round(raw_total, 2),
        "breakdown": breakdown,
        "fresher": fresher,
        "completeness": comp
    }