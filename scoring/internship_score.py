def score_internships(exp_features):

    count = exp_features["internship_count"]

    # Saturation model (prevents resume gaming)
    if count == 0:
        return 0
    elif count == 1:
        return 10
    elif count == 2:
        return 16
    else:
        return 20