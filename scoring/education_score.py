"""
scoring/education_score.py

BUG FIXED: cgpa_norm=0 (no score detected) was returning cgpa_score=2.
When has_education=True but no CGPA/% was found, the 'else: return 2'
branch fired, giving 2 free points. Fixed to return 0.
"""


def score_education(edu_features: dict) -> dict:
    if not edu_features.get("has_education", False):
        return {"cgpa_score": 0, "degree_score": 0}

    cgpa_norm = edu_features.get("normalized_score_100", 0)

    if cgpa_norm == 0:
        cgpa_score = 0          # no data — do not award free points
    elif cgpa_norm >= 90:
        cgpa_score = 10
    elif cgpa_norm >= 80:
        cgpa_score = 8
    elif cgpa_norm >= 70:
        cgpa_score = 6
    elif cgpa_norm >= 60:
        cgpa_score = 4
    else:
        cgpa_score = 2          # data exists but below 60%

    degree_score = 3 if edu_features.get("degree_detected", False) else 0

    return {
        "cgpa_score":   cgpa_score,
        "degree_score": degree_score,
    }