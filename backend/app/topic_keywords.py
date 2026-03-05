def keyword_topic(text: str):

    t = text.lower()

    if any(w in t for w in ["refund", "money back", "return"]):
        return "refund_request"

    if any(w in t for w in ["broken", "damaged", "defective", "stopped working"]):
        return "product_defect"

    if any(w in t for w in ["payment", "charged", "transaction", "bank"]):
        return "payment_problem"

    if any(w in t for w in ["app", "crash", "bug", "error", "login", "freeze"]):
        return "technical_bug"

    if any(w in t for w in [
        "support",
        "reply",
        "response",
        "no reply",
        "no response",
        "emails",
        "contacted"
    ]):
        return "support_delay"

    if any(w in t for w in [
        "delivery",
        "delivered",
        "shipment",
        "courier",
        "package",
        "parcel",
        "delay",
        "late",
        "arrive"
    ]):
        return "delivery_issue"

    return None