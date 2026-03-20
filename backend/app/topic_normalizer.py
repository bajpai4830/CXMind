NORMALIZATION_RULES = {
    "delivery_issue": ["delivery", "shipment", "courier", "package", "arrive", "late"],
    "support_delay": ["reply", "support", "response", "email", "contact"],
    "product_defect": ["broken", "damaged", "defect", "stop", "working"],
    "refund_request": ["refund", "return", "money"],
    "payment_problem": ["payment", "charged", "transaction", "bank"],
    "technical_bug": ["bug", "error", "crash", "login", "app"]
}

def normalize_topic(topic: str | None) -> str:
    if not topic:
        return "general_complaint"
    
    t = topic.lower()
    for normalized, keywords in NORMALIZATION_RULES.items():
        if any(w in t for w in keywords):
            return normalized
            
    return "general_complaint"