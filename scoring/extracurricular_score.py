def score_extracurricular(extra_features):

    if not extra_features["has_extra"]:
        return 0

    return min(extra_features["leadership_score"], 5)