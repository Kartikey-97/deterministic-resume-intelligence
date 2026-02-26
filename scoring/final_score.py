from scoring.internship_score import score_internships
from scoring.experience_score import score_experience
from scoring.skill_score import score_skills
from scoring.project_score import score_projects
from scoring.education_score import score_education
from scoring.achievement_score import score_achievements
from scoring.extracurricular_score import score_extracurricular
from scoring.minor_score import score_minor

def is_fresher(exp_features):
    return exp_features["total_experience_years"] < 1

def completeness_score(features):
    score = 0
    if features.get("projects", {}).get("has_projects"): score += 1
    if features.get("achievements", {}).get("has_achievements"): score += 1
    if len(features.get("minor", {}).get("online_presence", [])) > 0: score += 1
    if len(features.get("minor", {}).get("languages_detected", [])) > 0: score += 1
    return score

def prestige_multiplier(features):
    multiplier = 1.0
    company_tier = features.get("minor", {}).get("company_tier", 4)
    college_tier = features.get("minor", {}).get("college_tier", 4)
    if company_tier == 1: multiplier += 0.08
    elif company_tier == 2: multiplier += 0.04
    if college_tier == 1: multiplier += 0.05
    elif college_tier == 2: multiplier += 0.02
    return multiplier

# The default maximum possible points per category based on original rules
DEFAULT_MAX = {
    "internships": 20.0, "experience": 5.0, "skills": 20.0, "projects": 15.0,
    "cgpa_score": 10.0, "achievements": 10.0, "extracurricular": 5.0,
    "degree_score": 3.0, "language": 3.0, "online": 3.0, "college": 2.0, "school": 2.0
}

def compute_final_score(features, custom_weights=None):
    breakdown = {}
    fresher = is_fresher(features["experience"])
    
    # 1. Gather Raw Scores
    raw = {}
    raw["internships"] = score_internships(features["experience"])
    raw["experience"] = score_experience(features["experience"])
    raw["skills"] = score_skills(features["skills"])
    raw["projects"] = score_projects(features["projects"])
    
    edu = score_education(features["education"])
    raw["cgpa_score"] = edu["cgpa_score"]
    raw["degree_score"] = edu["degree_score"]
    
    raw["achievements"] = score_achievements(features["achievements"])
    raw["extracurricular"] = score_extracurricular(features["extracurricular"])
    
    minor = score_minor(features.get("minor", {}), features.get("school", {}))
    raw["language"] = minor.get("language", 0)
    raw["online"] = minor.get("online", 0)
    raw["college"] = minor.get("college", 0)
    raw["school"] = minor.get("school", 0)

    # 2. Apply Custom Weights Proportionally
    if custom_weights:
        for key in raw:
            if DEFAULT_MAX[key] > 0: # Prevent division by zero
                # Calculate what % of the max they earned, then multiply by the new UI weight
                percentage_earned = raw[key] / DEFAULT_MAX[key]
                breakdown[key] = percentage_earned * custom_weights.get(key, DEFAULT_MAX[key])
            else:
                breakdown[key] = 0
    else:
        # Fallback to defaults
        breakdown = raw.copy()

    # 3. Completeness & Prestige calibration
    comp = completeness_score(features)
    raw_total = sum(breakdown.values())
    
    total = raw_total * (1 + 0.04 * comp)
    total *= prestige_multiplier(features)
    final_score = min(total, 100.0)
    
    return {
        "total_score": round(final_score, 2),
        "raw_total": round(raw_total, 2),
        "breakdown": {k: round(v, 2) for k, v in breakdown.items() if isinstance(v, (int, float))},
        "fresher": fresher,
        "completeness": comp
    }