from app.models import Interaction


def calculate_customer_risk(interactions):

    score = 0

    for i in interactions:

        # sentiment weight
        if i.sentiment_label == "negative":
            score += 2
        elif i.sentiment_label == "positive":
            score -= 1

        # topic weight
        if i.topic == "refund_request":
            score += 3

        if i.topic == "delivery_issue":
            score += 2

        if i.topic == "support_delay":
            score += 2

        if i.topic == "technical_bug":
            score += 2

    # classify risk level
    if score >= 8:
        level = "high_risk"
    elif score >= 4:
        level = "medium_risk"
    else:
        level = "low_risk"

    return {
        "risk_score": score,
        "risk_level": level
    }