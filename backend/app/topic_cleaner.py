CLEANING_OVERRIDES = {
    "positive": {
        "positive_feedback": ["excellent", "great", "fast", "good", "happy", "perfect"]
    },
    "any": {
        "refund_request": ["refund", "return", "money back"],
        "product_defect": ["broken", "damaged", "defective", "stopped working"],
        "payment_problem": ["payment", "charged", "transaction", "bank"],
        "technical_bug": ["app", "crash", "bug", "error", "login", "freeze"],
        "support_delay": ["support", "reply", "response", "email", "emails", "contacted", "no reply", "no response", "nobody replied"]
    },
    "negative": {
        "delivery_issue": ["delivery", "delivered", "shipment", "courier", "late", "delay", "delayed", "took forever"]
    },
    "fallback": {
        "general_complaint": ["frustrating", "bad experience", "terrible", "disappointed", "unhappy"]
    }
}

def clean_topic(raw_topic: str, text: str, sentiment_label: str) -> str:
    t = (text or "").lower()
    
    # Priority 1: Delivery exception with 'but'
    if "but" in t and any(w in t for w in ["delivery", "delay", "late"]):
        return "delivery_issue"
        
    # Priority 2: Positive sentiment overrides
    if sentiment_label == "positive":
        for topic, keywords in CLEANING_OVERRIDES["positive"].items():
            if any(w in t for w in keywords):
                return topic

    # Priority 3: General keyword matches (any sentiment)
    for topic, keywords in CLEANING_OVERRIDES["any"].items():
        if any(w in t for w in keywords):
            return topic

    # Priority 4: Negative sentiment specific matches
    if sentiment_label == "negative":
        for topic, keywords in CLEANING_OVERRIDES["negative"].items():
            if any(w in t for w in keywords):
                return topic
                
    # Priority 5: Fallback complaints
    for topic, keywords in CLEANING_OVERRIDES["fallback"].items():
        if any(w in t for w in keywords):
            return topic

    return raw_topic