def score_education(edu_features):

    if not edu_features["has_education"]:
        return {"cgpa_score": 0, "degree_score": 0}

    cgpa_norm = edu_features["normalized_score_100"]

    # CGPA mapping
    if cgpa_norm >= 90:
        cgpa_score = 10
    elif cgpa_norm >= 80:
        cgpa_score = 8
    elif cgpa_norm >= 70:
        cgpa_score = 6
    elif cgpa_norm >= 60:
        cgpa_score = 4
    else:
        cgpa_score = 2

    degree_score = 3 if edu_features["degree_detected"] else 0

    return {
        "cgpa_score": cgpa_score,
        "degree_score": degree_score
    }