def score_experience(exp_features):

    years = exp_features["total_experience_years"]

    if years == 0:
        return 0
    elif years < 1:
        return 2
    elif years < 3:
        return 3
    elif years < 5:
        return 4
    else:
        return 5