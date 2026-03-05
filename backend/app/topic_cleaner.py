def clean_topic(raw_topic: str, text: str, sentiment_label: str) -> str:

    t = text.lower()

    if "but" in t and any(w in t for w in ["delivery", "delay", "late"]):
        return "delivery_issue"

    # Positive sentiment overrides complaints
    if sentiment_label == "positive":
        if any(w in t for w in [
            "excellent",
            "great",
            "fast",
            "good",
            "happy",
            "perfect"
        ]):
            return "positive_feedback"

    # Refund / return
    if any(w in t for w in ["refund", "return", "money back"]):
        return "refund_request"

    # Product defect
    if any(w in t for w in [
        "broken",
        "damaged",
        "defective",
        "stopped working"
    ]):
        return "product_defect"

    # Payment issues
    if any(w in t for w in [
        "payment",
        "charged",
        "transaction",
        "bank"
    ]):
        return "payment_problem"

    # Technical issues
    if any(w in t for w in [
        "app",
        "crash",
        "bug",
        "error",
        "login",
        "freeze"
    ]):
        return "technical_bug"

    # Support issues
    if any(w in t for w in [
        "support",
        "reply",
        "response",
        "email",
        "emails",
        "contacted",
        "no reply",
        "no response",
        "nobody replied"
    ]):
        return "support_delay"

    # Delivery issues (only if negative)
    if sentiment_label == "negative":
        if any(w in t for w in [
            "delivery",
            "delivered",
            "shipment",
            "courier",
            "late",
            "delay",
            "delayed",
            "took forever"
        ]):
            return "delivery_issue"
        
    if any(w in t for w in [
        "frustrating",
        "bad experience",
        "terrible",
        "disappointed",
        "unhappy"
    ]):
        return "general_complaint"

    return raw_topic