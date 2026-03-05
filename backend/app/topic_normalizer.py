def normalize_topic(topic: str) -> str:

    if topic is None:
        return "general_complaint"

    t = topic.lower()

    # Delivery problems
    if any(w in t for w in [
        "delivery",
        "shipment",
        "courier",
        "package",
        "arrive",
        "late"
    ]):
        return "delivery_issue"

    # Support delay
    if any(w in t for w in [
        "reply",
        "support",
        "response",
        "email",
        "contact"
    ]):
        return "support_delay"

    # Product defect
    if any(w in t for w in [
        "broken",
        "damaged",
        "defect",
        "stop",
        "working"
    ]):
        return "product_defect"

    # Refund
    if any(w in t for w in [
        "refund",
        "return",
        "money"
    ]):
        return "refund_request"

    # Payment problems
    if any(w in t for w in [
        "payment",
        "charged",
        "transaction",
        "bank"
    ]):
        return "payment_problem"

    # Technical bugs
    if any(w in t for w in [
        "bug",
        "error",
        "crash",
        "login",
        "app"
    ]):
        return "technical_bug"

    return "general_complaint"