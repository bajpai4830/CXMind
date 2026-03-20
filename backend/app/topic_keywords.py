KEYWORD_RULES = {
    "refund_request": ["refund", "money back", "return"],
    "product_defect": ["broken", "damaged", "defective", "stopped working"],
    "payment_problem": ["payment", "charged", "transaction", "bank"],
    "technical_bug": ["app", "crash", "bug", "error", "login", "freeze"],
    "support_delay": ["support", "reply", "response", "no reply", "no response", "emails", "contacted"],
    "delivery_issue": ["delivery", "delivered", "shipment", "courier", "package", "parcel", "delay", "late", "arrive"]
}

def keyword_topic(text: str) -> str | None:
    if not text:
        return None
    t = text.lower()
    for topic, keywords in KEYWORD_RULES.items():
        if any(w in t for w in keywords):
            return topic
    return None