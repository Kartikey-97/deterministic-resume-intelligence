def score_achievements(ach_features):

    if not ach_features["has_achievements"]:
        return 0

    impact = ach_features["impact_score"]

    # Direct mapping with cap
    return min(impact, 10)