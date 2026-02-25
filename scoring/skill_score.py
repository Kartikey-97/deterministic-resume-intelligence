ADVANCED_DOMAINS = [
    "cloud", "devops", "data", "security"
]

def score_skills(skill_features):

    total = sum(len(v) for v in skill_features.values())

    advanced = sum(
        len(skill_features[d])
        for d in ADVANCED_DOMAINS
        if d in skill_features
    )

    base = min(total, 10)

    bonus = min(advanced, 10)

    return min(base + bonus, 20)