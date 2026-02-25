def score_projects(project_features):

    if not project_features["has_projects"]:
        return 0

    count = project_features["project_count"]
    advanced = project_features["advanced_keyword_count"]
    impact = project_features["impact_score"]
    urls = project_features["has_urls"]

    # Saturation curve
    if count == 1:
        base = 5
    elif count <= 3:
        base = 10
    else:
        base = 12

    # Advanced tech bonus
    advanced_bonus = min(advanced, 2)

    # Impact bonus
    impact_bonus = min(impact / 5, 3)

    # Credibility bonus
    url_bonus = 1 if urls else 0

    return min(base + advanced_bonus + impact_bonus + url_bonus, 15)